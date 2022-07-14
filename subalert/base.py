import json
import uuid, random
import socket
import urllib.request
from urllib.request import urlopen
import urllib.error
import time

import tweepy
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps
from substrateinterface import SubstrateInterface
from pathlib import Path
import uuid
from .config import Configuration


config = Configuration()
hashtag = config.yaml_file['twitter']['hashtag']
substrate = config.substrate


class SubQuery:
    @staticmethod
    def short_address(address):
        start, end = address[:6], address[-6:]
        return f"{start}...{end}"

    @staticmethod
    def system_account(address):
        """
        :param address: On-chain address to lookup.
        :return: Information regarding a specific address on the network
        """
        result = substrate.query(
            module='System',
            storage_function='Account',
            params=[address]
        )
        return json.loads(str(result).replace("\'", "\""))

    def check_identity(self, address):
        """
        :param address:
        :return: Information that is pertinent to identify the entity behind an account.
        """
        substrate.connect_websocket()
        result = substrate.query(
            module='Identity',
            storage_function='IdentityOf',
            params=[address]
        )
        result = result.value
        #substrate.close()

        # return short address if result contains nothing
        if result is None:
            return self.short_address(address)
        else:
            display = result['info']['display']
            twitter = result['info']['twitter']

        if 'Raw' in twitter:
            if len(twitter['Raw']) > 0:
                return twitter['Raw']

        if 'Raw' in display:
            if len(display['Raw']) > 0:
                return display['Raw']

        return self.short_address(address)

    @staticmethod
    def tips_info():
        """
        :return: A list of all proposed tips
        """
        tips_list = {}
        result = substrate.query_map(
            module='Tips',
            storage_function='Tips',
            params=None
        )

        for tip_hash, attributes in result.records:
            tips_list.update({tip_hash.value: attributes.value})
        return tips_list

    @staticmethod
    def tip_info(tip_hash):
        """
        :param tip_hash:
        :return: Details of a specific proposed tip.
        """
        result = substrate.query(
            module='Tips',
            storage_function='Tips',
            params=[tip_hash])

        return result.serialize()

    @staticmethod
    def tip_reason(reason_hash):
        """
        :param reason_hash:
        :return: Short description on why the tip was proposed.
        """
        result = substrate.query(
            module='Tips',
            storage_function='Reasons',
            params=[reason_hash]
        )
        return result


class Imagify:
    def __init__(self, title, text: str, footer: str):
        self.title = title
        self.text = text.encode("ascii", errors="ignore").decode()
        self.footer = footer

    def create(self):
        watermark = Image.open(f'logos/{hashtag}_White.png')
        new_watermark = watermark.resize((50, 50), Image.ANTIALIAS)
        guid = uuid.uuid4()

        Path("imagify/").mkdir(exist_ok=True)
        imagify_path = f"imagify/images/{guid}.png"

        # background
        new_image = Image.new('RGBA', (400, 300), color='#36393f')
        new_image_draw = ImageDraw.Draw(new_image)

        # text font settings
        text_font = ImageFont.truetype(font="imagify/fonts/SourceCodePro-Regular.ttf", size=16)
        text_w, text_h = new_image_draw.textsize(self.text, text_font)

        # title font settings
        title_font = ImageFont.truetype(font="imagify/fonts/SourceCodePro-Bold.ttf", size=22)
        title_w, title_h = new_image_draw.textsize(self.title, title_font)

        # footer font settings
        footer_font = ImageFont.truetype(font="imagify/fonts/SourceCodePro-Bold.ttf", size=10)
        footer_w, footer_h = new_image_draw.textsize(self.footer, title_font)

        # If the footer is the biggest element by width, adjust the box.
        # footer_w > text_w and title_w
        if title_w > footer_w or title_w > text_w:
            modified_image = new_image.resize(size=(title_w + 75, text_h + 85))
            modified_image_draw = ImageDraw.Draw(modified_image)

        elif text_w > title_w or text_w > footer_w:
            modified_image = new_image.resize(size=(text_w + 75, text_h + 85))
            modified_image_draw = ImageDraw.Draw(modified_image)

        elif footer_w > title_w or title_w < footer_w:
            modified_image = new_image.resize(size=(footer_w + 90, text_h + 85))
            modified_image_draw = ImageDraw.Draw(modified_image)

        modified_image.paste(new_watermark, (modified_image.width - 50, text_h + 35), mask=new_watermark)
        modified_image_draw.text(xy=((modified_image.width - title_w) / 2, 10), text=self.title, fill='#d1d0b0',
                                 font=title_font)
        modified_image_draw.text(xy=(10, 65), text=self.text, fill='#d1d0b0', font=text_font)
        modified_image_draw.text(xy=(10, modified_image.height - 20), text=f"{self.footer}", fill='#d1d0b0',
                                 font=footer_font)

        bordered = ImageOps.expand(modified_image, border=2, fill='#E6007A')
        bordered.save(imagify_path)

        return imagify_path


class Numbers:
    def __init__(self, number):
        self.number = number
        self.magnitude = int()

    def human_format(self):
        magnitude = 0
        while abs(self.number) >= 1000:
            magnitude += 1
            self.number /= 1000.0
        # add more suffixes if you need them
        return '%.2f%s' % (self.number, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])

    def large_to_dec(self):
        magnitude = 0
        while abs(self.number) >= 1000:
            magnitude += 1
            self.number /= 1000.0
        return '%.2f' % self.number


class Utils:
    @staticmethod
    def cache_data(filename, data):
        with open(f"{filename}", 'w') as cache:
            cache.write(json.dumps(data, indent=4))
        cache.close()

    @staticmethod
    def open_cache(filename):
        with open(filename, 'r') as cache:
            cached_file = json.loads(cache.read())
            cache.close()
        return cached_file

    @staticmethod
    def get_1kv_candidates():
        candidates = []
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
        request = urllib.request.Request(config.yaml_file['validator_programme_url'], headers=header)
        response = json.loads(urlopen(request).read())

        for candidate in response:
            candidates.append(candidate['stash'])

        return candidates


class Public_API:
    def __init__(self, url):
        self.url = url
        self.opener = urllib.request.build_opener()
        self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)')]

        urllib.request.install_opener(self.opener)
        socket.setdefaulttimeout(60)

    def connect(self):
        try:
            request = urllib.request.Request(self.url)
            try:
                connect = urlopen(url=request).read()
                return json.loads(connect)
            except ValueError:
                return False

        except urllib.error.HTTPError as http_error:
            return http_error

    def retrieve_image(self, filepath):
        full_filepath = f"{filepath}/{uuid.uuid4()}.tmp"
        response = urllib.request.urlretrieve(self.url, full_filepath)
        content_type = response[1].get_content_type().split("/")[1]

        fullpath = Path(full_filepath)
        new_path = str(fullpath.rename(fullpath.with_suffix(f".{content_type}")))
        return new_path

    def IPFS_RMRK(self, rmrk_version):
        IPFS_data = self.connect()

        if rmrk_version == '1.0.0':
            if 'metadata' in IPFS_data[0].keys():
                metadata = IPFS_data[0]['metadata'].replace('ipfs://', 'https://rmrk.mypinata.cloud/')
                self.url = metadata  # update URL with the one found in ['metadata']

                IPFS_data = self.connect()
                if 'animation_url' in IPFS_data:
                    NFT_image_URL = IPFS_data['animation_url'].replace('ipfs://', 'https://rmrk.mypinata.cloud/').replace(' ', '%20')
                    self.url = NFT_image_URL # update URL with the one found in ['image']
                    return self.retrieve_image("NFT")

                if 'image' in IPFS_data:
                    NFT_image_URL = IPFS_data['image'].replace('ipfs://', 'https://rmrk.mypinata.cloud/').replace(' ', '%20')
                    self.url = NFT_image_URL # update URL with the one found in ['image']
                    return self.retrieve_image("NFT")

        elif rmrk_version == '2.0.0':
            if 'metadata' in IPFS_data[0].keys():
                metadata = IPFS_data[0]['metadata'].replace('ipfs://', 'https://rmrk.mypinata.cloud/').replace(' ', '%20')
                self.url = metadata

                print(f"1# - RMRK 2.0.0 Metadata: {metadata}") #log

                IPFS_data = self.connect()

                if 'mediaUri' in IPFS_data:
                    metadata = IPFS_data['mediaUri'].replace('ipfs://', 'https://rmrk.mypinata.cloud/').replace(' ', '%20')
                    print(f"2# - RMRK 2.0.0 Metadata: {metadata}") #log
                    self.url = metadata
                    return self.retrieve_image("NFT")


# change coingecko to use public API.
class CoinGecko:
    def __init__(self, coin: str, currency):
        self.coin = coin.lower()
        self.currency = currency
        self.url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&C{currency}"

    def price(self):
        try:
            api_response = json.loads(urlopen(url=self.url, timeout=30).read())
            return '{:,.2f}'.format(api_response[self.coin][self.currency])
        except urllib.error.HTTPError as http_error:
            return 0


class GitWatch:
    @staticmethod
    def latest_release():
        with urllib.request.urlopen(config.yaml_file['github']['repository']) as repository:
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
