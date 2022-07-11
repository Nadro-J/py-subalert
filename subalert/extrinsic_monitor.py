import asyncio
import json
import urllib.parse
import urllib.request

from colorama import Fore, Style
from subalert.base import Numbers, SubQuery, CoinGecko, Public_API
from substrateinterface import ExtrinsicReceipt

from .config import Configuration
from .subq import Queue

queue = Queue()


class ProcessExtrinsicData:
    def __init__(self, data):
        self.data = data
        self.queue = Queue()
        self.subquery = SubQuery()
        self.config = Configuration()
        self.substrate = self.config.substrate

        self.threshold = self.config.yaml_file['alert']['transact_usd_threshold']
        self.nft_threshold = self.config.yaml_file['alert']['nft_threshold']
        self.whale_threshold = self.config.yaml_file['alert']['whale_threshold']
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    @property
    def remark_batch_all(self):
        print("\033[0;34;40m========== [ (remark) batch_all ] ========== \033[0m")
        batch_author = self.data['address']
        nft_local_path = ''
        remark_call_data = {batch_author: {}}
        rmrk_events = ["BUY"]
        tweet_body = None

        for batch_calls in self.data["call"]['call_args']:
            call_counter = 0

            for batch_call in batch_calls["value"]:
                call_function = batch_call['call_function']
                call_module = batch_call['call_module']
                call_counter += 1
                print(f"\033[1;34;40m    ====== [ call: {call_counter} ] =========\033[0m")
                print(f"    * call_function: {call_function}")
                print(f"    * call_module: {call_module}")
                print(f"    * total_args: {len(batch_call['call_args'])}")
                print(f"    * batch_call_data: \033[0;33;40m{batch_call}\033[0m\n")

                for call in batch_call["call_args"]:
                    # If the first call in batch_all isn't remark, then disregard.
                    if call_function != "remark" and call_counter == 1:
                        return

                    if call_function == "remark" and call_counter == 1:
                        # Reference:  https://github.com/rmrk-team/rmrk-spec/tree/master/standards/rmrk2.0.0
                        call_value = urllib.parse.unquote(call['value'])
                        call_split = call_value.split('::')

                        # Example below includes snippet from call_split after splitting remark call_functions.
                        # ['RMRK','BUY', '2.0.0', '5105000-0aff6865bed3a66b-VALHELLO-POTION_HEAL-00000001']
                        # ['RMRK', 'SEND', '1.0.0', '9862100-b6e98494bff52d3b1e-SPIRIT-SPIRIT1589-00001589', 'DoVJWXGwy91aAWsaBsmVn4DA78D25mPGfzKxj4aZVihnJ13']
                        interaction = call_split[1]

                        #  only process specific data i.e. SEND/BUY
                        if interaction not in rmrk_events:
                            return

                        remark_call_data[batch_author].update({"interaction": interaction, "version": call_split[2]})

                        if interaction == "SEND":
                            remark_call_data[batch_author].update({
                                call_split[3]: call_split[4]
                            })
                        elif interaction == "BUY":
                            remark_call_data[batch_author].update({
                                'nft': call_split[3]
                            })
                        else:
                            pass

                    if call_function == "transfer" and call_counter == 2:
                        if call['name'] == "dest":
                            remark_call_data[batch_author].update({
                                'lister': call['value']
                            })

                        if call['name'] == "value":
                            remark_call_data[batch_author].update({
                                'nft-price': call['value'] / 10 ** 12
                            })

                    # NFT Platform fees
                    if call_function == "transfer" and call_counter == 3:
                        if call['name'] == "dest":
                            remark_call_data[batch_author].update({
                                'platform-address': call['value']
                            })

                        if call['name'] == "value":
                            remark_call_data[batch_author].update({
                                'platform-fees': call['value'] / 10 ** 12
                            })

                    # Creator royalties
                    if call_function == "transfer" and call_counter == 4:
                        if call['name'] == "dest":
                            remark_call_data[batch_author].update({
                                'nft-creator': call['value']
                            })

                        if call['name'] == "value":
                            remark_call_data[batch_author].update({
                                'nft-creator-royalties': call['value'] / 10 ** 12
                            })

        if remark_call_data:
            for author, value in remark_call_data.items():
                if len(value) > 0:
                    # quote nft_id using urllib to mitigate issues where people include emojis in the ID.
                    nft_id = urllib.parse.quote(value['nft'])
                    if value['version'] == '1.0.0':
                        direct_link = f"https://singular.rmrk.app/collectibles/{nft_id}"
                        nft_local_path = (Public_API(
                            url=f"https://singular.rmrk.app/api/rmrk1/nft/{nft_id}").IPFS_RMRK(
                            rmrk_version=value['version']))

                    elif value['version'] == '2.0.0':
                        direct_link = f"https://singular.app/collectibles/{nft_id}"
                        nft_local_path = (Public_API(
                            url=f"https://singular.app/api/rmrk2/nft/{nft_id}").IPFS_RMRK(
                            rmrk_version=value['version']))

                    nft_price = float("{:.4f}".format(value['nft-price']))

                    # Only process purchases > threshold set in yaml file
                    if nft_price >= self.nft_threshold:
                        tweet_body = f"RMRK interaction from {self.subquery.check_identity(author)}\n\n🧑 Lister: {self.subquery.check_identity(value['lister'])}\n💵 Received: {nft_price} $KSM\n\n"

                        if 'nft-creator-royalties' in value:
                            royalties = float("{:.4f}".format(value['nft-creator-royalties']))
                            tweet_body += f"🎨 Creator: {self.subquery.check_identity(value['nft-creator'])}\n"
                            tweet_body += f"💵 Creator royalties: {royalties} $KSM\n"

                        if 'platform-address' in value:
                            nft_fee = float("{:.4f}".format(value['platform-fees']))
                            tweet_body += f"\n🛒 Platform fee: {self.subquery.check_identity(value['platform-address'])} (Fee: {nft_fee} $KSM)\n\n{direct_link}"

                        if nft_price >= 100:
                            tweet_body += f"\n\n#Over100KSM_NFT_Purchase 💰💰💰💰"
                        elif nft_price >= 50:
                            tweet_body += f"\n\n#Over50KSM_NFT_Purchase 💰💰💰"
                        elif nft_price >= 25:
                            tweet_body += f"\n\n#Over25KSM_NFT_Purchase 💰💰"
                        elif nft_price >= 10:
                            tweet_body += f"\n\n#Over10KSM_NFT_Purchase 💰"

        return tweet_body, nft_local_path

    @property
    def transactions(self):
        print("checking for transactions")
        """
        :param block_height:
        :param threshold: >= the amount to alert on
        :return: How much has been sent from one address to another, who it was signed by and the receivers
                 balance, reserved, miscFrozen.
        """

        parsed_extrinsic_data = {}
        tweet_body = None

        # only process extrinsic(s) where call_function is == 'transfer' and the extrinsic is successful.
        if self.data['call']['call_function'] == "transfer":
            if 'address' in self.data:
                signed_by_address = self.data['address']

            parsed_extrinsic_data.update({signed_by_address: {}})

            for param in self.data["call"]['call_args']:
                parsed_extrinsic_data[signed_by_address].update({param['name']: param['value']})

        if len(parsed_extrinsic_data) != 0:
            price = CoinGecko(coin=self.hashtag, currency='usd').price()

            for signer, attributes in parsed_extrinsic_data.items():
                destination, value = attributes['dest'], attributes['value']

                if isinstance(value, int):
                    amount = value / 10 ** self.substrate.token_decimals
                else:
                    amount = value

                amount_sent = float(amount)
                amount_sent_usd = amount_sent * float(price)

                # ignore transactions if destination = signed_by_address
                if amount_sent_usd > self.threshold and destination != signer:

                    # Sender
                    sender_account = self.subquery.system_account(signer)['data']
                    sender_balance = sender_account['free'] / 10 ** self.substrate.token_decimals
                    sender_locked = sender_account['misc_frozen'] / 10 ** self.substrate.token_decimals

                    # Destination
                    destination_account = self.subquery.system_account(destination)['data']
                    destination_balance = destination_account['free'] / 10 ** self.substrate.token_decimals
                    destination_locked = destination_account['misc_frozen'] / 10 ** self.substrate.token_decimals

                    s_whale_emoji, r_whale_emoji = '', ''
                    if sender_balance > self.whale_threshold or sender_locked > self.whale_threshold:
                        s_whale_emoji = '🐳'
                    if destination_balance > self.whale_threshold or destination_locked > self.whale_threshold:
                        r_whale_emoji = '🐳'

                    usd_sender_balance = sender_balance * float(price.replace('$', ''))
                    usd_sender_locked = sender_locked * float(price.replace('$', ''))
                    usd_destination_balance = destination_balance * float(price.replace('$', ''))
                    usd_destination_locked = destination_locked * float(price.replace('$', ''))

                    tweet_body = (
                        f"{amount_sent:,.2f} / ${self.ticker} ${Numbers(amount_sent_usd).human_format()} successfully sent to {self.subquery.short_address(destination)}\n\n"
                        f"🏦 Sender balance: {Numbers(sender_balance).human_format()} (${Numbers(usd_sender_balance).human_format()}) {s_whale_emoji}{s_whale_emoji}\n"
                        f"🔒 Locked: {Numbers(sender_locked).human_format()} (${Numbers(usd_sender_locked).human_format()})\n\n"
                        f"🏦 Receiver balance: {Numbers(destination_balance).human_format()} (${Numbers(usd_destination_balance).human_format()}) {r_whale_emoji}{r_whale_emoji}\n"
                        f"🔒 Locked: {Numbers(destination_locked).human_format()} (${Numbers(usd_destination_locked).human_format()})\n\n"
                        f"https://{self.hashtag.lower()}.subscan.io/account/{destination}")

                return tweet_body


class ExtrinsicMonitor:
    def __init__(self):
        self.config = Configuration()
        self.subquery = SubQuery()
        self.threshold = self.config.yaml_file['alert']['transact_usd_threshold']
        self.whale_threshold = self.config.yaml_file['alert']['whale_threshold']
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

        # Queue events
        self.loop = asyncio.get_event_loop()

    def extrinsic(self, block, extrinsic_types, check_receipt):
        result = self.substrate.get_block(block_number=block, ignore_decoding_errors=True)
        block_hash, extrinsics_list = result['header']['hash'], []

        for extrinsic in result['extrinsics']:
            extrinsic_hash = extrinsic.value['extrinsic_hash']

            if extrinsic_hash is None:
                continue

            if extrinsic['call']['call_function']['name'] in extrinsic_types:
                if check_receipt:
                    extrinsic_receipt = ExtrinsicReceipt(
                        substrate=self.substrate,
                        extrinsic_hash=extrinsic_hash,
                        block_hash=block_hash)

                    if extrinsic_receipt.is_success is not True:
                        print("extrinsic is not successful")
                        continue

                    extrinsics_list.append(extrinsic.value)

        self.substrate.websocket.ping()
        return block_hash, extrinsics_list

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        block = obj['header']['number']
        block_event_construct = {"transactions": [], 'batch_all': []}

        calls = ['batch_all', 'remark', 'transfer']  # 12329404, 12341041
        blockhash, extrinsics = self.extrinsic(block=13487091, extrinsic_types=calls, check_receipt=True)

        print(f"{Style.DIM}🔨 New block: {Style.RESET_ALL}{Style.BRIGHT}{block}{Style.RESET_ALL} {Style.DIM}produced by: {Style.RESET_ALL}{Style.BRIGHT}{obj['author']}{Style.RESET_ALL}")
        print(f"{Style.DIM}Monitored extrinsics found in block: {Style.RESET_ALL}{Fore.LIGHTGREEN_EX}{len(extrinsics)}{Style.RESET_ALL}\n")

        for extrinsic in extrinsics:
            if extrinsic is not None:
                call_type = extrinsic['call']['call_function']
                extrinsic_data = ProcessExtrinsicData(extrinsic)

                if call_type == 'transfer':
                    transaction = extrinsic_data.transactions
                    block_event_construct['transactions'].append(transaction)

                elif call_type == 'batch_all':
                    batch_all = extrinsic_data.remark_batch_all
                    block_event_construct['batch_all'].append(batch_all)

        queue.enqueue(block_event_construct)

        # Run queue task if size is >= 1, clear queue & block_event_construct once complete.
        if queue.size() >= 1:
            task = self.loop.create_task(queue.process_queue())
            self.loop.run_until_complete(task)

        queue.clear()
        block_event_construct.clear()

