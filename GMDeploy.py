from datetime import datetime
from subalert.subtweet import Tweet
import datetime as dt
import pytz
import time

country__zones = pytz.all_timezones
country_time_zones = []


def isNowInTimePeriod(startTime, endTime, nowTime):
    if startTime < endTime:
        return nowTime >= startTime and nowTime <= endTime
    else:
        return nowTime >= startTime or nowTime <= endTime


for country_time_zone in country__zones:
    country_time_zones.append(pytz.timezone(country_time_zone))
for i in range(len(country_time_zones)):
    country_time = datetime.now(country_time_zones[i])
    if isNowInTimePeriod(dt.time(5, 30), dt.time(11, 59), country_time.time()):
        #  SENT IT
        tweet = f"#GM {country__zones[i]}!\nCurrent time: {country_time.strftime('%H:%M:%S')}"
        Tweet('GMDeploy').alert(message=tweet, verbose=True)
        time.sleep(10)