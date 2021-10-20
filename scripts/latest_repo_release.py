# run every 59 minutes past the hour (path may vary on system):
#   * * * * * cd /root/py-subalert && /usr/bin/python3 /root/py-subalert/latest_repo_release.py >> /root/py-subalert/latest_repo_release.log 2>&1
#
# Use git-release.cache to check if a new release has been made.
from subalert.base import GitWatch, Tweet
import os.path
import json

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

    Tweet(message=tweet_body).alert()
    git.cache_release(latest)
