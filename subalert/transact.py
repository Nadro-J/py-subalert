import json
import subalert.base
from subalert.base import Numbers, Tweet, Configuration, SubQuery, CoinGecko, Queue
from substrateinterface import ExtrinsicReceipt


class TransactionSubscription:
    def __init__(self):
        self.config = Configuration()
        self.subquery = SubQuery()
        self.queue = Queue()
        self.threshold = self.config.yaml_file['alert']['transact_usd_threshold']
        self.whale_threshold = self.config.yaml_file['alert']['whale_threshold']
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def system_account(self, address):
        """
        :param address: On-chain address to lookup.
        :return: Information regarding a specific address on the network
        """
        result = self.substrate.query(
            module='System',
            storage_function='Account',
            params=[address]
        )
        return json.loads(str(result).replace("\'", "\""))

    def check_transaction(self, block_height, threshold, whale_threshold):
        """
        :param block_height:
        :param threshold: >= the amount to alert on
        :return: How much has been sent from one address to another, who it was signed by and the receivers
                 balance, reserved, miscFrozen.
        """
        result = self.substrate.get_block(block_number=block_height, ignore_decoding_errors=True)
        blockhash = result['header']['hash']
        parsed_extrinsic_data = {}

        for extrinsic in result['extrinsics']:
            extrinsic_hash = extrinsic.value['extrinsic_hash']

            if extrinsic is None:
                continue

            receipt = ExtrinsicReceipt(
                substrate=self.substrate,
                extrinsic_hash=extrinsic_hash,
                block_hash=blockhash)

            # only process extrinsic(s) where call_function is == 'transfer' and the extrinsic is successful.
            if extrinsic['call']['call_function']['name'] == "transfer" and receipt.is_success:
                if 'address' in extrinsic:
                    signed_by_address = extrinsic['address'].value
                else:
                    continue

                parsed_extrinsic_data.update({signed_by_address: {}})

                for param in extrinsic.value["call"]['call_args']:
                    parsed_extrinsic_data[signed_by_address].update({param['name']: param['value']})

        if len(parsed_extrinsic_data) != 0:
            price = CoinGecko(coin='polkadot', currency='usd').price()

            for signer, attributes in parsed_extrinsic_data.items():
                destination, value = attributes['dest'], attributes['value']

                if isinstance(value, int):
                    amount = value / 10 ** self.substrate.token_decimals
                else:
                    amount = value

                amount_sent = float(amount)
                amount_sent_usd = amount_sent * float(price)

                # ignore transactions if destination = signed_by_address
                if amount_sent_usd > threshold and destination != signer:

                    # Sender
                    sender_account = self.system_account(signer)['data']
                    sender_balance = sender_account['free'] / 10 ** self.substrate.token_decimals
                    sender_locked = sender_account['misc_frozen'] / 10 ** self.substrate.token_decimals

                    # Destination
                    destination_account = self.system_account(destination)['data']
                    destination_balance = destination_account['free'] / 10 ** self.substrate.token_decimals
                    destination_locked = destination_account['misc_frozen'] / 10 ** self.substrate.token_decimals

                    s_whale_emoji, r_whale_emoji = '', ''
                    if sender_balance > whale_threshold or sender_locked > whale_threshold:
                        s_whale_emoji = '🐳'
                    if destination_balance > whale_threshold or destination_locked > whale_threshold:
                        r_whale_emoji = '🐳'

                    usd_sender_balance = sender_balance * float(price.replace('$', ''))
                    usd_sender_locked = sender_locked * float(price.replace('$', ''))
                    usd_destination_balance = destination_balance * float(price.replace('$', ''))
                    usd_destination_locked = destination_locked * float(price.replace('$', ''))

                    tweet_body = (
                        f"{amount_sent:,.2f} ${self.ticker} ({price} - ${Numbers(amount_sent_usd).human_format()}) successfully sent to {self.subquery.short_address(destination)}\n\n"
                        f"🏦 Sender balance: {Numbers(sender_balance).human_format()} (${Numbers(usd_sender_balance).human_format()}) {s_whale_emoji}{s_whale_emoji}\n"
                        f"🔒 Locked: {Numbers(sender_locked).human_format()} (${Numbers(usd_sender_locked).human_format()})\n\n"
                        f"🏦 Receiver balance: {Numbers(destination_balance).human_format()} (${Numbers(usd_destination_balance).human_format()}) {r_whale_emoji}{r_whale_emoji}\n"
                        f"🔒 Locked: {Numbers(destination_locked).human_format()} (${Numbers(usd_destination_locked).human_format()})\n\n"
                        f"https://{self.hashtag.lower()}.subscan.io/extrinsic/{extrinsic_hash}")

                    Tweet().alert(message=tweet_body, verbose=True)

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        print(f"🔨 New block: {obj['header']['number']} produced by {obj['author']}")
        self.check_transaction(obj['header']['number'], self.threshold, self.whale_threshold)
