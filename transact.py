import json
from substrateinterface import SubstrateInterface
from subalert.base import Tweet          # local library
from subalert.base import Configuration  # local library

class TransactionSubscription:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()

        self.substrate = SubstrateInterface(
            url=self.config.yaml_file['chain']['url'],
            ss58_format=self.config.yaml_file['chain']['ss58_format'],
            type_registry_preset=self.config.yaml_file['chain']['type_registry_preset']
        )

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
        result = self.substrate.get_block(block_hash=block_hash)
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
            amount_f = '{0:,.2f}'.format(amount)  # Formatted two decimals with comma/

            if amount > threshold:
                sQuery = self.system_account(destination)['data']
                balance = sQuery['free'] / 10 ** self.substrate.token_decimals
                reserved = sQuery['reserved'] / 10 ** self.substrate.token_decimals
                miscFrozen = sQuery['miscFrozen'] / 10 ** self.substrate.token_decimals

                print(f"{amount_f} $DOT sent to {destination}\n\nsigned by: {signed_by_address}\n\n"
                      f"🏦 Balance: {balance}$DOT\n"
                      f"ℹ️Reserved: {reserved}\n"
                      f"ℹ️miscFrozen: {miscFrozen}\n\n"
                      f"https://polkascan.io/polkadot/account/{destination} #Polkadot\n")

                self.tweet.alert(f"{amount_f} $DOT sent to {destination}\n\nsigned by: {signed_by_address}\n\n🏦 Balance: {balance}$DOT\nℹ️Reserved: {reserved}\nℹ️miscFrozen: {miscFrozen}\n\nhttps://polkascan.io/polkadot/account/{destination} #Polkadot\n")
                # tweet_alert(f"{amount_f} $DOT sent to {destination}\n\nsigned by: {signed_by_address}\n\n🏦 Balance: {balance}$DOT\nℹ️Reserved: {reserved}\nℹ️miscFrozen: {miscFrozen}\n\nhttps://polkascan.io/polkadot/account/{destination} #Polkadot\n")

    def new_block_sub(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        print(f"🔨 New block: {obj['header']['parentHash']}")
        self.check_transaction(obj['header']['parentHash'], 50000)


if __name__ == '__main__':
    txSub = TransactionSubscription()
    txSub.substrate.subscribe_block_headers(txSub.new_block_sub, include_author=True)