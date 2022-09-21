import json
import os
import asyncio

import deepdiff
from subalert.base import Utils, SubQuery

from .config import Configuration
from .subq import Queue

queue = Queue()


class ValidatorWatch:
    def __init__(self):
        self.config = Configuration()
        self.subquery = SubQuery()
        self.utils = Utils()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])
        self.commission_change = self.config.yaml_file['alert']['validator_change']
        self.loop = asyncio.get_event_loop()

    def has_commission_updated(self):
        """
        This function uses DeepDiff to determine what type of data has changed.
        :return: check if a validator has updated there commission since you last checked.
        """
        commission_data = self.subquery.get_current_commission()
        _1kv_candidates = self.utils.get_1kv_candidates()
        value_difference = float()
        validators_list = {}
        change = ""

        if not os.path.isfile('data-cache/validators-commission.cache'):
            self.utils.cache_data('data-cache/validators-commission.cache', commission_data)

        cached_commission_data = self.utils.open_cache('data-cache/validators-commission.cache')

        # use DeepDiff to check if any values have changed since we ran has_commission_updated().
        difference = deepdiff.DeepDiff(cached_commission_data, commission_data, ignore_order=True).to_json()
        result = json.loads(difference)

        if len(result) == 0:
            print("🔧 No changes to commission have been found since the last execution")
            exit(1)

        print("🔧 changes have been found since the last time has_commission_updated was invoked")

        validator_construct = {"validators": []}

        for key, value in result.items():
            if key == 'values_changed':
                # format DeepDiff into usable json
                for obj, attributes in result['values_changed'].items():
                    if 'blocked' in obj:
                        pass
                    elif 'commission' in obj:
                        address = obj.replace("root['", "").replace("']", "").replace("['commission", "")
                        validators_list.update({address: attributes})

                for validator_address, changed_attributes in validators_list.items():
                    old_value = float(f"{100 * float(changed_attributes['old_value']) / float(1000000000):,.2f}")
                    new_value = float(f"{100 * float(changed_attributes['new_value']) / float(1000000000):,.2f}")

                    # check identity of validator
                    identity = self.subquery.check_identity_depth(validator_address)
                    if identity is None:
                        identity = f"🆔 Unknown"

                    if new_value > old_value:
                        value_difference = float(f'{new_value - old_value:,.2f}')
                        change = (f"{identity}\n"
                                  f"⬆️ increased by: +{value_difference}%")

                    if new_value < old_value:
                        value_difference = float(f'{old_value - new_value:,.2f}')
                        change = (f"{identity}\n"
                                  f"⬇️ decreased by: -{value_difference}%")

                    stamp_1kv = ''
                    if validator_address in _1kv_candidates:
                        stamp_1kv = '#1KV'

                    # only tweet when the commission has been changed > 3%.
                    if value_difference > self.commission_change:
                        tweet_body = (
                            f"{self.subquery.check_identity(validator_address)} {stamp_1kv} has updated there commission from {old_value:,.2f}% to {new_value:,.2f}%.\n\n"
                            f"{change}\n\n"
                            f"https://{self.hashtag.lower()}.subscan.io/validator/{validator_address}\n#{self.hashtag}")

                        validator_construct['validators'].append(tweet_body)
                queue.enqueue(validator_construct)

            if queue.size() >= 1:
                task = self.loop.create_task(queue.process_queue())
                self.loop.run_until_complete(task)

            self.utils.cache_data('data-cache/validators-commission.cache', commission_data)
