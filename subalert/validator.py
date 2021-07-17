from subalert.base import Tweet  # local library
from subalert.base import Configuration, Utils, Queue  # local library
from deepdiff import DeepDiff
import json, os, time


class ValidatorWatch:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.queue = Queue()
        self.substrate = self.config.substrate

    def get_identity(self, address):
        result = self.substrate.query_map(
            module='Identity',
            storage_function='IdentityOf')

        for identity_address, information in result:

           # print(identity_address.value, information)
            if address == identity_address.value:
                return information.value

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
        validators_list = {}
        change = ""

        # create if it doest exist
        if not os.path.isfile('validators-commission.cache'):
            Utils.cache_data('validators-commission.cache', commission_data)

        cached_commission_data = Utils.open_cache('validators-commission.cache')

        # use DeepDiff to check if any values have changed since we last checked.
        difference = DeepDiff(cached_commission_data, commission_data, ignore_order=True).to_json()

        if difference != '{ }':
            result = json.loads(difference)

            # format DeepDiff into usable json
            for obj, attributes in result['values_changed'].items():
                address = obj.replace("root['", "").replace("']", "").replace("['commission", "")
                validators_list.update({address: attributes})

            for validator_address, changed_attributes in validators_list.items():
                old_value = float(f"{100 * float(changed_attributes['old_value'])/float(1000000000):,.2f}")
                new_value = float(f"{100 * float(changed_attributes['new_value'])/float(1000000000):,.2f}")

                if old_value < new_value:
                    change = f"⬆️increased by: +{new_value - old_value}%"

                if old_value > new_value:
                    change = f"⬇️decreased by: -{old_value - new_value}%"

                tweet_body = (f"🕵️{validator_address} has updated their commission from {old_value}% to {new_value}%.\n\n"
                              f"{change}")

                self.queue.enqueue(tweet_body)

            # When the queue size is greater than 1, throttle how quick it tweets by 5 seconds to mitigate rapid API
            # requests.
            if self.queue.size() > 1:
                for i in self.queue.items:
                    print(i)
                    time.sleep(5)
