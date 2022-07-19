import json
import os
import statistics
import asyncio
import deepdiff

from subalert.base import  Utils, SubQuery

from .config import Configuration
from .subq import Queue

queue = Queue()


class TipsSubscription:
    def __init__(self):
        self.config = Configuration()
        self.utils = Utils()
        self.subquery = SubQuery()
        self.substrate = self.config.substrate
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])
        self.loop = asyncio.get_event_loop()

    def has_tips_updated(self):
        """
        :return: check if tips data has updated since you last checked.
        """
        tip_construct = []

        if not os.path.isfile('data-cache/tips.cache'):
            self.utils.cache_data('data-cache/tips.cache', self.subquery.tips_info())

        cached_tips_data = self.utils.open_cache('data-cache/tips.cache')

        difference = deepdiff.DeepDiff(cached_tips_data, self.subquery.tips_info(), ignore_order=True).to_json()
        result = json.loads(difference)

        if len(result) == 0:
            print("🔧 No changes to commission have been found since the last execution")
            exit(1)

        tips_construct = {"tips": []}

        for key, value in result.items():
            # type_change ['closes'] goes from null to an integer value (block height) of when the tip will be closed.
            if key == 'dictionary_item_added':
                for tip_hash in value:
                    tip_hash = tip_hash.replace("root['", "").replace("']", "").replace("['finders_fee", "")
                    reason = self.subquery.tip_reason(self.subquery.tip_info(tip_hash)['reason'])

                    tweet_body = (
                        f"🖐️A new tip has been proposed.\n\n"
                        f"{reason}\n\n"
                        f"https://www.dotreasury.com/{self.ticker}/tips/{tip_hash}"
                    )
                    tips_construct['tips'].append(tweet_body)
                queue.enqueue(tips_construct)
            elif key == 'type_changes':
                for tip_hash, attributes in result[key].items():
                    if 'closes' in tip_hash:
                        tip_hash = tip_hash.replace("root['", "").replace("']", "").replace("['closes", "")
                        reason = self.subquery.tip_reason(cached_tips_data[tip_hash]['reason'])
                        close_height = attributes['new_value']
                        tip_values = []

                        # tips_data[tip_hash]['tips'] = tuple: (tipper, amount)
                        for tipper, amount in self.subquery.tips_info()[tip_hash]['tips']:
                            tip_values.append(amount)

                        median = statistics.median(tip_values) / 10 ** self.substrate.token_decimals

                        if median <= 0.0:
                            pass
                        else:
                            tweet_body = (
                                f"💰Tip closed for {median} {self.ticker}\n\n"
                                f"{reason}\n\n"
                                f"payout scheduled on block {close_height:,}\n\n"
                                f"https://www.dotreasury.com/{self.ticker}/tips/{tip_hash}"
                            )

                            tips_construct['tips'].append(tweet_body)
                queue.enqueue(tips_construct)
            else:
                continue

        if queue.size() >= 1:
            task = self.loop.create_task(queue.process_queue())
            self.loop.run_until_complete(task)

        self.utils.cache_data('data-cache/tips.cache', self.subquery.tips_info())
