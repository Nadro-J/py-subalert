from .subtweet import Tweet
import os


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

        print(len(self.items))

        if len(self.items) == '1':
            d = self.items[0]

            # list comprehension
            return sum([len(d[x]) for x in d if isinstance(d[x], list)])
        else:
            return len(self.items)

    def clear(self):
        return self.items.clear()

    async def process_queue(self):
        print("+++ process_queue called")
        counter = 0

        if 'tips' in self.items[0] and len(self.items[0]['tips']) >= 1 and self.items[0]['tips'][0] is not None:
            for tip in self.items[0]['tips']:
                counter += 1
                print(f"##[ Tip ({counter}) ]###\n{tip}")
                #Tweet("KusamaTip").alert(message=tip, verbose=True)

        # Process extrinsic extraction tweets containing
        #   * batch_all
        #   * transfers
        if 'batch_all' in self.items[0] and len(self.items[0]['batch_all']) >= 1 and self.items[0]['batch_all'][0] is not None:
            for tweet, media in self.items[0]['batch_all']:
                counter += 1
                print(f"\n##[ batch_all ({counter}) ]###\n{tweet}\n{media}\n------\n")
                #Tweet("NonFungibleTxs").alert(message=tweet, filename=media, verbose=True)

                # only remove media if it actually returns anything.
                if media:
                    os.remove(path=media)

        if 'transactions' in self.items[0] and len(self.items[0]['transactions']) >= 1 and self.items[0]['transactions'][0] is not None:
            for tx in self.items[0]['transactions']:
                counter += 1
                print(f"##[ transaction ({counter}) ]###\n{tx}")
                #Tweet("KusamaTxs").alert(message=tx, verbose=True)