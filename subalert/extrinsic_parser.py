import os
import urllib.parse
import urllib.request

from subalert.base import Numbers, SubQuery, CoinGecko, Public_API, Utils
from subalert.logger import log_events
from .config import Configuration

utils = Utils()
log = log_events(filename='extrinsic-monitor.log', debug=False)

from pathlib import Path

file = Path(__file__).resolve()
package_root_directory = file.parents[1]

class ParseExtrinsic:
    def __init__(self, data):
        self.data = data
        self.subquery = SubQuery()
        self.config = Configuration()
        self.utils = Utils()
        self.substrate = self.config.substrate

        self.threshold = self.config.yaml_file['alert']['transact_usd_threshold']
        self.nft_threshold = self.config.yaml_file['alert']['nft_threshold']
        self.whale_threshold = self.config.yaml_file['alert']['whale_threshold']
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    @property
    def remark_batch_all(self):
        log.info("Running remark_batch_all() from extrinsic_parser")
        batch_author = self.data['address']
        nft_local_path = ''
        remark_call_data = {batch_author: {}}
        rmrk_events = ["BUY"]
        tweet_body = None
        monitored = False

        for batch_calls in self.data["call"]['call_args']:
            call_counter = 0

            for batch_call in batch_calls["value"]:
                call_function = batch_call['call_function']
                call_module = batch_call['call_module']
                call_counter += 1
                log.debug(f"""
                Call: #{call_counter}\n
                Call_function: {call_function}\n
                Call_module: {call_module}\n
                Total_args: {len(batch_call['call_args'])}\n
                Batch_call_data: {batch_call}
                """)

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
                    split_nft_id = nft_id.split('-')
                    collection_id = f"{split_nft_id[1]}-{split_nft_id[2]}"

                    if 'nft-creator' in value:
                        monitored = utils.check_collection([collection_id, value['nft-creator']])

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

                    log.info(f"RMRK batch_all parsed to read-able format")

                    # Check if hourly-rmrk-sales.json exists
                    if not os.path.isfile(f'{package_root_directory}/data-cache/hourly-rmrk-sales.json'):
                        self.utils.cache_data('data-cache/hourly-rmrk-sales.json', [remark_call_data])

                    hourly_sales = utils.open_cache('data-cache/hourly-rmrk-sales.json')
                    hourly_sales.append(remark_call_data)
                    self.utils.cache_data('data-cache/hourly-rmrk-sales.json', hourly_sales)

                    return tweet_body, nft_local_path, monitored, remark_call_data, direct_link

    @property
    def transactions(self):
        log.info("Running transactions() from extrinsic_parser")
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
                log.info(f"Transaction parsed to read-able format")
                return tweet_body
