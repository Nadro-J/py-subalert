import yaml
import tweepy
from substrateinterface import SubstrateInterface


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


class Tweet:
    def __init__(self):
        self.auth = Configuration()

    def alert(self, message):
        try:
            self.auth.api.update_status(message)
        except tweepy.error.TweepError as error:
            if error == "[{'code': 187, 'message': 'Status is a duplicate.'}]":
                print("Disregarding duplicate tweet")
                pass
            else:
                raise error
