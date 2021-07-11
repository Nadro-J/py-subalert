# run on an hourly basis using git-release.cache to check if a new release has been made.
from subalert.base import GitWatch, Tweet
import os.path
import json

tweet = Tweet()
git = GitWatch()
latest = git.latest_release()

print("🔍 checking for new release on github")

# cache data if it hasn't been done already
if not os.path.isfile('git-release.cache'):
    git.cache_release(latest)

# open cached data
with open('git-release.cache', 'r') as cache:
    cached_file = json.loads(cache.read())
    cache.close()

if git.has_updated(latest, cached_file):
    print("🔧 preparing tweet...")
    tweet_body = (
        f"""{latest['name']} has been released. #Polkadot\n
──────▄▀▄─────▄▀▄
─────▄█░░▀▀▀▀▀░░█▄
─▄▄──█░░░░░░░░░░░█──▄▄
█▄▄█─█░░▀░░┬░░▀░░█─█▄▄█

{latest['html_url']}
""")

    tweet.alert(tweet_body)
    git.cache_release(latest)
