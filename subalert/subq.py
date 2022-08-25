from .subtweet import Tweet
from .config import Configuration
import os

config = Configuration()


class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        if len(self.items) == 1:
            d = self.items[0]

            # list comprehension
            return sum([len(d[x]) for x in d if isinstance(d[x], list)])
        else:
            return len(self.items)

    def clear(self):
        return self.items.clear()

    async def process_queue(self):
        if 'validators' in self.items[0] and len(self.items[0]['validators']) >= 1 and self.items[0]['validators'][0] is not None:
            for validator in self.items[0]['validators']:
                Tweet("KusamaValidator").alert(message=validator, verbose=True)

        if 'proposals' in self.items[0] and len(self.items[0]['proposals']) >= 1 and self.items[0]['proposals'][0] is not None:
            for proposal in self.items[0]['proposals']:
                Tweet('KusamaDemocracy').alert(message=proposal)

        if 'tips' in self.items[0] and len(self.items[0]['tips']) >= 1 and self.items[0]['tips'][0] is not None:
            for tip in self.items[0]['tips']:
                Tweet("KusamaTip").alert(message=tip, verbose=True)

        if 'batch_all' in self.items[0] and len(self.items[0]['batch_all']) >= 1 and self.items[0]['batch_all'][0] is not None:
            for tweet, media, collection_id in self.items[0]['batch_all']:
                if not tweet:
                    pass

                Tweet("NonFungibleTxs").alert(message=tweet, filename=media, verbose=True)

                # Handle monitored collections
                # ----------------------------
                # If collection_id returns anything, fetch the account from the yaml
                # config and tweet the result.
                if collection_id:
                    monitored_collection = config.yaml_file['twitter']['collections'][collection_id]
                    account = list(monitored_collection.keys())[0]
                    Tweet(account, nft_collection=collection_id).alert(message=tweet, filename=media, verbose=True)

                # only remove media if it actually returns anything.
                if media:
                    os.remove(path=media)

        if 'transactions' in self.items[0] and len(self.items[0]['transactions']) >= 1:
            for tx in self.items[0]['transactions']:
                if not tx:
                    pass

                Tweet("KusamaTxs").alert(message=tx, verbose=True)
