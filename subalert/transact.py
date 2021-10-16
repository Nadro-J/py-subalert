import json
import subalert.base
from subalert.base import Numbers, Tweet, Configuration, SubQuery
from substrateinterface import ExtrinsicReceipt


class TransactionSubscription:
    def __init__(self):
        self.config = Configuration()
        self.subquery = SubQuery()
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

    def check_transaction(self, block_hash, threshold, whale_threshold):
        """
        :param block_hash:
        :param threshold: >= the amount to alert on
        :return: How much has been sent from one address to another, who it was signed by and the receivers
                 balance, reserved, miscFrozen.
        """
        result = self.substrate.get_block(block_hash=block_hash, ignore_decoding_errors=True)
        data = {}

        for extrinsic in result['extrinsics']:
            if extrinsic is None:
                continue

            extrinsic_function_call = extrinsic["call"]["call_function"]["name"]
            print(f"extrinsic_function_call: {extrinsic_function_call}")
            if extrinsic_function_call != "transfer":
                continue

            extrinsic_hash = extrinsic.value['extrinsic_hash']
            receipt = ExtrinsicReceipt(
                substrate=self.substrate,
                extrinsic_hash=extrinsic_hash,
                block_hash=block_hash)

            if not receipt.is_success:
                print("[!] Extrinsic failed, skipping")
                continue

            if 'address' in extrinsic:
                signed_by_address = extrinsic['address'].value
            else:
                signed_by_address = None

            data.update(
                {
                    signed_by_address: {}
                }
            )

            # Loop through call params
            for param in extrinsic["call"]['call_args']:
                name = param['name'].value
                value = param['value'].value

                if 'Balance' in param['typeName'].value:
                    if isinstance(value, int):
                        value = '{}'.format(value / 10 ** self.substrate.token_decimals)
                    else:
                        value = '{}'.format(value)

                    print(f"-- Extrinsic: Debugging ] ---\n"
                          f"Extrinsic_hash: {extrinsic_hash}\n"
                          f"Function call: {extrinsic['call']['call_function'].name}\n"
                          f"Type: {param['typeName']}\n"
                          f"------------------")

                data[signed_by_address].update({name: value})

            destination = data[signed_by_address]['dest']
            amount = float(data[signed_by_address]['value'])

            price = subalert.base.CoinGecko(coin=self.hashtag, currency='usd').price()
            usd_amount = amount * float(price)

            # ignore transactions if destination = signed_by_address
            if usd_amount > threshold and destination != signed_by_address:

                # Sender
                sender_account = self.system_account(signed_by_address)['data']
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
                    f"{amount:,.2f} ${self.ticker} ({price} - ${Numbers(usd_amount).human_format()}) successfully sent to {self.subquery.short_address(destination)}\n\n"
                    f"🏦 Sender balance: {Numbers(sender_balance).human_format()} (${Numbers(usd_sender_balance).human_format()}) {s_whale_emoji}{s_whale_emoji}\n"
                    f"🔒 Locked: {Numbers(sender_locked).human_format()} (${Numbers(usd_sender_locked).human_format()})\n\n"
                    f"🏦 Receiver balance: {Numbers(destination_balance).human_format()} (${Numbers(usd_destination_balance).human_format()}) {r_whale_emoji}{r_whale_emoji}\n"
                    f"🔒 Locked: {Numbers(destination_locked).human_format()} (${Numbers(usd_destination_locked).human_format()})\n\n"
                    f"https://{self.hashtag.lower()}.subscan.io/account/{destination}")

                print(f"-- Tweet: Debugging ] ---\n"
                      f"{tweet_body}\n"
                      f"-------------------------\n")
                Tweet(message=tweet_body).alert()

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        print(f"🔨 New block: {obj['header']['parentHash']}")
        self.check_transaction(obj['header']['parentHash'], self.threshold, self.whale_threshold)
