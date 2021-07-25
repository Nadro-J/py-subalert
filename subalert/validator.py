from subalert.base import Tweet  # local library
from subalert.base import Configuration, Utils, Queue  # local library
from deepdiff import DeepDiff
import json, os, time


class ValidatorWatch:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.queue = Queue()
        self.utils = Utils()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def check_super_of(self, address):
        result = self.substrate.query(
            module='Identity',
            storage_function='SuperOf',
            params=[address])

        if result.value is not None:
            return result.value[0]
        else:
            return 0

    def check_identity(self, address):
        result = self.substrate.query_map(
            module='Identity',
            storage_function='IdentityOf')

        super_of = self.check_super_of(address)
        if super_of:
            address = super_of

        for identity_address, information in result:
            identification = ''

            if address == identity_address.value:
                for identity_type, values in information.value['info'].items():
                    if 'display' in identity_type or 'twitter' in identity_type:
                        for value_type, value in values.items():
                            if identity_type == 'display' and value_type == 'Raw':
                                identification += f"🆔 {value} "

                            if identity_type == 'twitter' and value_type == 'Raw':
                                identification += f"🐦 {value}"
                return identification

    def get_current_commission(self):
        validators_list = {}
        result = self.substrate.query_map(
            module='Staking',
            storage_function='Validators',
            params=None
        )

        for validator_address, validator_attributes in result:
            validators_list.update({validator_address.value: validator_attributes.value})

        return validators_list

    def has_commission_updated(self):
        commission_data = self.get_current_commission()
        _1kv_candidates = self.utils.get_1kv_candidates()
        value_difference = float()
        validators_list = {}
        change = ""

        # create if it doest exist
        if not os.path.isfile('validators-commission.cache'):
            Utils.cache_data('validators-commission.cache', commission_data)

        cached_commission_data = Utils.open_cache('validators-commission.cache')

        # use DeepDiff to check if any values have changed since we last checked.
        difference = DeepDiff(cached_commission_data, commission_data, ignore_order=True).to_json()

        result = json.loads(difference)

        if len(result) == 0:
            print("🔧 No changes to commission have been found since the last execution")
            exit(1)

        print("🔧 changes have been found since the last time has_commission_updated was invoked")

        # need to sort out what happens when a new validator is found,.5T
        for key, value in result.items():
            if key == 'dictionary_item_added':
                for new_address in value:
                    address = new_address.replace("root['", "").replace("']", "").replace("['commission", "")
                    tweet_body = (
                            f"👨‍🔧 new address found, {address}\n"
                            f"{self.check_identity(address)}\n\n"
                            f"https://{self.hashtag.lower()}.subscan.io/validator/{address}")

                    self.queue.enqueue(tweet_body)

            elif key == 'values_changed':
                # format DeepDiff into usable json
                for obj, attributes in result['values_changed'].items():
                    address = obj.replace("root['", "").replace("']", "").replace("['commission", "")
                    validators_list.update({address: attributes})

                for validator_address, changed_attributes in validators_list.items():
                    old_value = float(f"{100 * float(changed_attributes['old_value']) / float(1000000000):,.2f}")
                    new_value = float(f"{100 * float(changed_attributes['new_value']) / float(1000000000):,.2f}")

                    # check identity of validator
                    identity = self.check_identity(validator_address)
                    if identity is None:
                        identity = f"🆔 Unknown"

                    if new_value > old_value:
                        value_difference = float(f'{new_value - old_value:,.2f}')
                        change = (f"{identity}\n"
                                  f"⬆️increased by: +{value_difference}%")

                    if new_value < old_value:
                        value_difference = float(f'{old_value - new_value:,.2f}')
                        change = (f"{identity}\n"
                                  f"⬇️decreased by: -{value_difference}%")

                    stamp_1kv = ''
                    if validator_address in _1kv_candidates:
                        stamp_1kv = '#1KV'

                    # only tweet when the commission has been changed > 3%.
                    if value_difference > 3:
                        tweet_body = (
                            f"🕵️{validator_address} {stamp_1kv} has updated their commission from {old_value:,.2f}% to {new_value:,.2f}%.\n\n"
                            f"{change}\n\n"
                            f"https://{self.hashtag.lower()}.subscan.io/validator/{validator_address}")

                        self.queue.enqueue(tweet_body)

                # When the queue size is greater than 1, throttle how quick it tweets by 5 seconds to mitigate rapid API
                # requests.
                if self.queue.size() >= 1:
                    for tweet in self.queue.items:
                        self.tweet.alert(tweet)
                        time.sleep(5)
                    Utils.cache_data('validators-commission.cache', commission_data)
