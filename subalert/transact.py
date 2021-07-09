import json
from subalert.base import Tweet  # local library
from subalert.base import Configuration  # local library
from substrateinterface import SubstrateInterface, ExtrinsicReceipt
from scalecodec import ScaleBytes, ExtrinsicsDecoder
from scalecodec.metadata import MetadataDecoder
class TransactionSubscription:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.threshold = self.config.yaml_file['alert']['transact_threshold']
        self.substrate = self.config.substrate

    def system_account(self, address):
        """
        :param address: On-chain address to lookup.
        :return: {'nonce': 24799, 'consumers': 0, 'providers': 1, 'sufficients': 0,
                    'data': {
                        'free': 14574104215557330,
                        'reserved': 0,
                        'miscFrozen': 0,
                        'feeFrozen': 0
                    }
                  }
        """
        result = self.substrate.query(
            module='System',
            storage_function='Account',
            params=[address]
        )
        return json.loads(str(result).replace("\'", "\""))

    def check_transaction(self, block_hash, threshold):
        """
        :param block_hash:
        :param threshold: >= the amount to alert on
        :return: How much has been sent from one address to another, who it was signed by and the receivers
                 balance, reserved, miscFrozen.
        """
        result = self.substrate.get_block(block_hash=block_hash, ignore_decoding_errors=True)
        data = {}

        for extrinsic in result['extrinsics']:

            if extrinsic.address:
                signed_by_address = extrinsic.address.value
            else:
                signed_by_address = None

            if extrinsic.call.name != "transfer":
                continue

            data.update(
                {
                    signed_by_address: {}
                }
            )

            receipt = ExtrinsicReceipt(
                substrate=self.substrate,
                extrinsic_hash=f"0x{extrinsic.extrinsic_hash}",
                block_hash=block_hash
            )

            if not receipt.is_success:
                print("Extrinsic not successful")
                return 0
            else:

                # Loop through call params
                for param in extrinsic.params:
                    if param['type'] == 'Compact<Balance>':
                        if isinstance(param['value'], int):
                            param['value'] = '{}'.format(param['value'] / 10 ** self.substrate.token_decimals)
                        else:
                            param['value'] = '{}'.format(param['value'])

                    data[signed_by_address].update({param['name']: param['value']})
                # print(json.dumps(data, indent=4)) # debugging

                destination = data[signed_by_address]['dest']
                amount = float(data[signed_by_address]['value'])

                if amount > threshold:
                    account = self.system_account(destination)['data']
                    balance = account['free'] / 10 ** self.substrate.token_decimals
                    reserved = account['reserved'] / 10 ** self.substrate.token_decimals
                    miscFrozen = account['miscFrozen'] / 10 ** self.substrate.token_decimals

                    print(f"💵 {amount:,.2f} $DOT sent to {destination} signed by {signed_by_address}")

                    tweet_body = (f"{amount:,.2f} $DOT sent to {destination}\n\nsigned by: {signed_by_address}\n\n"
                            f"🏦 Balance: {balance:,.2f}\n"
                            f"💵 Reserved: {reserved:,.2f}\n"
                            f"💵 miscFrozen: {miscFrozen:,.2f}\n\n"
                            f"https://polkadot.subscan.io/account/{destination} #Polkadot\n")

                    self.tweet.alert(tweet_body)

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        print(f"🔨 New block: {obj['header']['parentHash']}")
        self.check_transaction(obj['header']['parentHash'], self.threshold)
