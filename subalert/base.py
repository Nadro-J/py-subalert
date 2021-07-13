import yaml
import tweepy
from substrateinterface import SubstrateInterface
from urllib.request import urlopen
import urllib.request, json


class Configuration:
    def __init__(self):
        self.yaml_file = yaml.safe_load(open("config.local.yaml", "r"))
        self.substrate = SubstrateInterface(
            url=self.yaml_file['chain']['url'],
            ss58_format=self.yaml_file['chain']['ss58_format'],
            type_registry_preset=self.yaml_file['chain']['type_registry_preset']
        )

        # Authenticate to Twitter
        self.auth = tweepy.OAuthHandler(self.yaml_file['twitter']['OAuthHandler']['consumer_key'],
                                        self.yaml_file['twitter']['OAuthHandler']['consumer_secret'])
        self.auth.set_access_token(self.yaml_file['twitter']['access_token']['key'],
                                   self.yaml_file['twitter']['access_token']['secret'])

        # Create API object
        self.api = tweepy.API(self.auth)


class CoinGecko:
    def __init__(self, coin: str, currency):
        self.coin = coin.lower()
        self.currency = currency
        self.url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&C{currency}"

    def price(self):
        api_response = json.loads(urlopen(url=self.url, timeout=60).read())
        return '${:,.2f}'.format(api_response[self.coin][self.currency])


class Tweet:
    def __init__(self):
        self.auth = Configuration()
        self.hashtag = self.auth.yaml_file['twitter']['hashtag']

    def alert(self, message):
        try:
            self.auth.api.update_status(f"{message} #{self.hashtag}")
            print("🐤 tweet successfully sent!")
        except tweepy.error.TweepError as error:
            if error == "[{'code': 187, 'message': 'Status is a duplicate.'}]":
                print("Disregarding duplicate tweet")
                pass
            else:
                raise error


class GitWatch:
    def __init__(self):
        self.config = Configuration()
        self.url = self.config.yaml_file['github']['repository']

    def latest_release(self):
        with urllib.request.urlopen(self.url) as repository:
            data = json.loads(repository.read().decode())
            return data

    @staticmethod
    def cache_release(data):
        with open('git-release.cache', 'w') as cache:
            cache.write(json.dumps(data, indent=4))
        cache.close()

    @staticmethod
    def has_updated(data, cache):
        if data['tag_name'] != cache['tag_name']:
            print("🔧 new release found!")
            return True
        else:
            print("🔧 no releases found")
            return False
