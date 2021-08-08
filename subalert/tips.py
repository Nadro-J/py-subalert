from subalert.base import Tweet  # local library
from subalert.base import Configuration, Utils, Queue  # local library
from deepdiff import DeepDiff
import json, os, time, statistics

class TipsSubscription:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.utils = Utils()
        self.queue = Queue()
        self.substrate = self.config.substrate
        self.ticker = self.config.yaml_file['chain']['ticker']
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def tips_info(self):
        tips_list = {}
        result = self.substrate.query_map(
            module='Tips',
            storage_function='Tips',
            params=None
        )

        for tip_hash, attributes in result.records:
            tips_list.update({tip_hash.value: attributes.value})
        return tips_list

    def tip_info(self, tip_hash):
        result = self.substrate.query(
            module='Tips',
            storage_function='Tips',
            params=[tip_hash]
        )
        return result.serialize()

    def tip_reason(self, reason_hash):
        result = self.substrate.query(
            module='Tips',
            storage_function='Reasons',
            params=[reason_hash]
        )
        return result

    def has_tips_updated(self):
        tips_data = self.tips_info()

        if not os.path.isfile('data-cache/tips.cache'):
            Utils.cache_data('data-cache/tips.cache', tips_data)

        cached_tips_data = Utils.open_cache('data-cache/tips.cache')

        difference = DeepDiff(cached_tips_data, tips_data, ignore_order=True).to_json()
        result = json.loads(difference)

        if len(result) == 0:
            print("🔧 No changes to commission have been found since the last execution")
            exit(1)

        for key, value in result.items():
            # type_change ['closes'] goes from null to an integer value (block height) of when the tip will be closed.
            tip_values = []
            if key == 'type_changes':
                for tip_hash, attributes in result[key].items():
                    if 'closes' in tip_hash:
                        tip_hash = tip_hash.replace("root['", "").replace("']", "").replace("['closes", "")
                        reason = self.tip_reason(cached_tips_data[tip_hash]['reason'])
                        close_height = attributes['new_value']
                        for tip in cached_tips_data[tip_hash]['tips']:
                            tip_values.append(tip['balance'])

                        print(f"-- [Tip closing] -----\n"
                              f"hash: {tip_hash}\n"
                              f"closing at: {close_height}\n"
                              f"reason: {reason}\n"
                              f"tip: {statistics.median(tip_values) / 10 ** self.substrate.token_decimals}\n"
                              f"----------------------\n")

                        tweet_body = (
                            f"💰Tip closed for {statistics.median(tip_values) / 10 ** self.substrate.token_decimals} {self.ticker}\n\n"
                            f"{reason}\n\n"
                            f"https://{self.hashtag.lower()}.polkassembly.io/tip/{tip_hash}"
                        )
                        self.queue.enqueue(tweet_body)

            if key == 'dictionary_item_added':
                for tip_hash in result[key]:

                    tip_hash = tip_hash.replace("root['", "").replace("']", "")
                    reason = self.tip_reason(self.tip_info(tip_hash)['reason'])

                    tweet_body = (
                        f"🖐️A new tip has been proposed.\n\n"
                        f"{reason}\n\n"
                        f"https://{self.hashtag.lower()}.polkassembly.io/tip/{tip_hash}"
                    )
                    self.queue.enqueue(tweet_body)

        # When the queue size is greater than 1, throttle how quick it tweets by 5 seconds to mitigate rapid API
        # requests.
        if self.queue.size() >= 1:
            for tweet in self.queue.items:
                self.tweet.alert(tweet)
                time.sleep(5)
