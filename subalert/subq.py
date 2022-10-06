from subalert.discord_webhook import DiscordWebhook, DiscordEmbed
from .config import Configuration
from .subtweet import Tweet
from subalert.base import SubQuery
import time
import os

config = Configuration()


class Queue:
    def __init__(self):
        self.items = []
        self.subquery = SubQuery()

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
            webhook = DiscordWebhook(url=f"{config.yaml_file['twitter']['sub_twitter']['KusamaValidator']['discord_webhook']}")
            for validator in self.items[0]['validators']:
                embed = DiscordEmbed(title='Validator', color='03b2f8', description=validator)
                webhook.add_embed(embed)
                webhook.execute()
                Tweet("KusamaValidator").alert(message=validator, verbose=True)

        if 'proposals' in self.items[0] and len(self.items[0]['proposals']) >= 1 and self.items[0]['proposals'][0] is not None:
            webhook = DiscordWebhook(url=f"{config.yaml_file['twitter']['sub_twitter']['KusamaDemocracy']['discord_webhook']}")
            for proposal in self.items[0]['proposals']:
                embed = DiscordEmbed(title='Referenda', color='03b2f8', description=proposal)
                webhook.add_embed(embed)
                webhook.execute()
                Tweet('KusamaDemocracy').alert(message=proposal)

        if 'tips' in self.items[0] and len(self.items[0]['tips']) >= 1 and self.items[0]['tips'][0] is not None:
            webhook = DiscordWebhook(url=f"{config.yaml_file['twitter']['sub_twitter']['KusamaTip']['discord_webhook']}")
            for tip in self.items[0]['tips']:
                embed = DiscordEmbed(title='Tip', color='03b2f8', description=tip)
                webhook.add_embed(embed)
                webhook.execute()
                Tweet("KusamaTip").alert(message=tip, verbose=True)

        if 'batch_all' in self.items[0] and len(self.items[0]['batch_all']) >= 1 and self.items[0]['batch_all'][0] is not None:
            webhook = DiscordWebhook(url=f"{config.yaml_file['twitter']['sub_twitter']['NonFungibleTxs']['discord_webhook']}")
            for tweet, media, collection_id, raw_json, link in self.items[0]['batch_all']:

                if media:
                    with open(media, "rb") as f:
                        webhook.add_file(file=f.read(), filename='example.jpg')

                # iterate over tweets that are blank.
                # usually they're blank due to not matching conditions in set in config.local.yaml
                if not tweet:
                    continue

                Tweet("NonFungibleTxs").alert(message=tweet, filename=media, verbose=True)
                embed = DiscordEmbed(title='RMRK interaction', color='03b2f8')
                embed.set_thumbnail(url="attachment://example.jpg")

                for author, value in raw_json.items():
                    embed.add_embed_field(name='Buyer', value=self.subquery.check_identity(address=author), inline=True)
                    if 'lister' in value:
                        embed.add_embed_field(name='Seller', value=self.subquery.check_identity(address=value['lister']), inline=True)

                    embed.add_embed_field(name="\u200b", value=f"[:art: singular.app]({link})", inline=True)

                    if 'platform-fees' in value:
                        embed.add_embed_field(name='Royalties', value=f"{value['nft-creator-royalties']} KSM", inline=True)

                    embed.add_embed_field(name='Received', value=f"{value['nft-price']} KSM", inline=True)

                    if 'platform-fees' in value:
                        embed.add_embed_field(name='Platform fees', value=f"{value['platform-fees']} KSM", inline=True)
                embed.set_timestamp(timestamp=int(time.time()))
                embed.set_footer(text='https://kusamahub.com', icon_url='https://i.imgur.com/IR7ZHk5.jpg')

                webhook.add_embed(embed)
                webhook.execute()

                # Handle monitored collections
                # ----------------------------
                # If collection_id returns anything, fetch the account from the yaml
                # config and tweet the result.
                if collection_id:
                    monitored_collection = config.yaml_file['twitter']['collections'][collection_id]
                    account = list(monitored_collection.keys())[0]
                    webhook = DiscordWebhook(url=f"{monitored_collection[account]['discord_webhook']}")
                    if media:
                        with open(media, "rb") as f:
                            webhook.add_file(file=f.read(), filename='example.jpg')

                    Tweet(account, nft_collection=collection_id).alert(message=tweet, filename=media, verbose=True)
                    embed = DiscordEmbed(title='RMRK interaction', color='03b2f8')
                    embed.set_thumbnail(url="attachment://example.jpg")

                    for author, value in raw_json.items():
                        embed.add_embed_field(name='Buyer', value=self.subquery.check_identity(address=author),
                                              inline=True)
                        if 'lister' in value:
                            embed.add_embed_field(name='Seller',
                                                  value=self.subquery.check_identity(address=value['lister']),
                                                  inline=True)

                        embed.add_embed_field(name="\u200b", value=f"[:art: singular.app]({link})", inline=True)

                        if 'platform-fees' in value:
                            embed.add_embed_field(name='Royalties', value=f"{value['nft-creator-royalties']} KSM",
                                                  inline=True)

                        embed.add_embed_field(name='Received', value=f"{value['nft-price']} KSM", inline=True)

                        if 'platform-fees' in value:
                            embed.add_embed_field(name='Platform fees', value=f"{value['platform-fees']} KSM",
                                                  inline=True)
                    embed.set_timestamp(timestamp=int(time.time()))
                    embed.set_footer(text='https://kusamahub.com', icon_url='https://i.imgur.com/IR7ZHk5.jpg')

                    webhook.add_embed(embed)
                    webhook.execute()

                # only remove media if it actually returns anything.
                if media and media != False:
                    os.remove(path=media)

        if 'transactions' in self.items[0] and len(self.items[0]['transactions']) >= 1:
            webhook = DiscordWebhook(url=f"{config.yaml_file['twitter']['sub_twitter']['KusamaTxs']['discord_webhook']}")
            for tx in self.items[0]['transactions']:
                if not tx:
                    continue

                embed = DiscordEmbed(title='Transaction', color='03b2f8', description=tx)
                webhook.add_embed(embed)
                webhook.execute()
                Tweet("KusamaTxs").alert(message=tx, verbose=True)
