from .config import Configuration
import tweepy
import time

config = Configuration()


class Tweet:
    def __init__(self, account):
        self.account = account
        if self.account not in config.yaml_file['twitter']['sub_twitter']:
            pass

        consumer_key = config.yaml_file['twitter']['sub_twitter'][account]['OAuthHandler']['consumer_key']
        consumer_sec = config.yaml_file['twitter']['sub_twitter'][account]['OAuthHandler']['consumer_secret']
        access_key = config.yaml_file['twitter']['sub_twitter'][account]['access_token']['key']
        access_sec = config.yaml_file['twitter']['sub_twitter'][account]['access_token']['secret']
        self.authorize = tweepy.OAuthHandler(consumer_key, consumer_sec)
        self.authorize.set_access_token(access_key, access_sec)
        self.api = tweepy.API(self.authorize, wait_on_rate_limit=True)
        self.supported_types = ['jpg', 'png', 'gif', 'webp', 'mp3', 'mp4']

    def alert(self, message, filename=None, verbose=False):
        try:
            if verbose:
                print(f"==== [ Tweepy input ] ======\n"
                      f"{message}\n")

            # only attach media if the filepath is provided and is a supported file type.
            # .jpg, .png, .gif, .mp3, .mp4
            if filename and filename.split('.')[1] in self.supported_types:
                media = self.api.media_upload(filename)
                self.api.update_status(status=message, media_ids=[media.media_id])
                print("🐤 tweet successfully sent with media!")
                time.sleep(5)
            else:
                self.api.update_status(status=message)
                print("🐤 tweet successfully sent!")
                time.sleep(5)

        except Exception as tweepy_err:
            if tweepy_err == "[{'code': 187, 'message': 'Status is a duplicate.'}]":
                pass
            else:
                print(f"An error has occurred with Tweepy: {tweepy_err}")