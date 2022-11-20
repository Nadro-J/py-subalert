from .config import Configuration
import tweepy
import time

config = Configuration()


class Tweet:
    def __init__(self, account, nft_collection=None):
        self.account = account
        if self.account not in config.yaml_file['twitter']['sub_twitter']:
            pass

        if nft_collection is None:
            consumer_key = config.yaml_file['twitter']['sub_twitter'][account]['OAuthHandler']['consumer_key']
            consumer_sec = config.yaml_file['twitter']['sub_twitter'][account]['OAuthHandler']['consumer_secret']
            access_key = config.yaml_file['twitter']['sub_twitter'][account]['access_token']['key']
            access_sec = config.yaml_file['twitter']['sub_twitter'][account]['access_token']['secret']
        else:
            consumer_key = config.yaml_file['twitter']['collections'][nft_collection][account]['OAuthHandler']['consumer_key']
            consumer_sec = config.yaml_file['twitter']['collections'][nft_collection][account]['OAuthHandler']['consumer_secret']
            access_key = config.yaml_file['twitter']['collections'][nft_collection][account]['access_token']['key']
            access_sec = config.yaml_file['twitter']['collections'][nft_collection][account]['access_token']['secret']

        if not consumer_key:
            return

        self.authorize = tweepy.OAuthHandler(consumer_key, consumer_sec)
        self.authorize.set_access_token(access_key, access_sec)
        self.api = tweepy.API(self.authorize, wait_on_rate_limit=True)
        self.supported_types = ['jpg', 'png', 'gif', 'webp', 'mp3', 'mp4']
        self.client = tweepy.Client(consumer_key=consumer_key, consumer_secret=consumer_sec, access_token=access_key, access_token_secret=access_sec)

    def alert(self, message, filename=None, verbose=False):
        try:
            if message is None:
                return "You can't send a blank tweet!"

            if verbose:
                print(f"==== [ Tweepy input ] ======\n"
                      f"{message}\n")

            # only attach media if the filepath is provided and is a supported file type.
            # .jpg, .png, .gif, .mp3, .mp4
            if filename and filename.split('.')[1] in self.supported_types:
                media = self.api.media_upload(filename)
                self.client.create_tweet(text=message, media_ids=[media.media_id], user_auth=True)
                print("🐤 tweet successfully sent with media!")
                time.sleep(5)
            else:
                self.client.create_tweet(text=message, user_auth=True)
                print("🐤 tweet successfully sent!")
                time.sleep(5)

        except Exception as tweepy_err:
            if tweepy_err == "[{'code': 187, 'message': 'Status is a duplicate.'}]":
                pass
            else:
                print(f"An error has occurred with Tweepy: {tweepy_err}")

    def latest_tweet(self):
        return self.api.search_tweets(q="", count=1)
