from datetime import datetime
import requests


class DiscordWebhook:
    def __init__(self, url):
        """
        https://discord.com/developers/docs/resources/webhook#execute-webhook
        :param url:
        """
        self.webhook = url

    def make_request(self, data):
        try:
            response = requests.post(url=self.webhook, json=data)
            response_code = response.status_code

            if response_code == 204:
                return 'Message sent!'
            else:
                raise Exception(f'response  - {response_code}')
        except requests.exceptions.Timeout as timeout:
            raise SystemError(timeout)
        except requests.exceptions.TooManyRedirects as redirects:
            raise SystemError(redirects)
        except requests.exceptions.RequestException as error:
            raise SystemExit(error)

    def send(self, content: str, username: str):
        data = {
            'content': content,
            'username': username
        }
        self.make_request(data=data)

    def embeds(self, description, thumbnail, footer):
        data = {
            'content': '',
            'embeds': [{
                'description': description,
                "color": "	16756224",
                "timestamp": f"{datetime.now()}",
                "thumbnail": {
                    "url": thumbnail
                },
                "footer": {
                    "text": footer,
                }
            }]
        }
        self.make_request(data=data)


class DiscordAPI:
    def __init__(self, token: str, guild: str):
        """
        https://discord.com/developers/docs/getting-started
        :param token:
        :param guild:
        """
        self.token = token
        self.guild = guild
        self.headers = {'Authorization': f'Bot {self.token}'}
        self.base_url = 'https://discord.com/api'

    def get_user(self, username):
        req_users = requests.get(url=f'{self.base_url}/guilds/{self.guild}/members',
                                 headers=self.headers,
                                 params={"limit": 1000})

        if req_users.status_code == 200:
            for user in req_users.json():
                if username.split('#')[0] == user['user']['username']:
                    return user['user']['id']
            return username

        else:
            raise Exception(f'get_user() failed: {req_users.status_code}')