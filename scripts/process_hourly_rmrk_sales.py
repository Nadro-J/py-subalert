import json
import pandas as pd
import sys
from pathlib import Path

file = Path(__file__).resolve()
package_root_directory = file.parents [1]
sys.path.append(str(package_root_directory))

from subalert.base import Imagify, Utils
from subalert.subtweet import Tweet

# Pandas settings
pd.set_option("display.max_rows", None, "display.max_columns", None)  # display full table


class Table:
    def __init__(self):
        self.df = pd.DataFrame()

    def add(self, data):
        self.df = pd.concat([self.df, pd.DataFrame.from_records(data)])
        self.df['serial'] = self.df['nft'].str.split('-', expand=True)[0]
        self.df['identifier'] = self.df['nft'].str.split('-', expand=True)[1]
        self.df['name'] = self.df['nft'].str.split('-', expand=True)[2]

    def sales(self):
        sales = self.df.groupby(
            ['identifier', 'name']).agg(
            volume=('nft-price', 'sum'),
            sales=('nft-price', 'count'),
        ).reset_index(level='identifier', drop=True)

        return sales.sort_values(['sales'], ascending=False)

    def fetch(self):
        return self.df

    @staticmethod
    def check_ascii(string):
        return len(string) == len(string.encode())


# initialize Table() class
table = Table()

# process hourly data captured from extrinsics_monitor.py into pandas table
hourly_nft_data = Utils().open_cache(f'data-cache/hourly-rmrk-sales.json')

if len(hourly_nft_data) > 0:
    # iterate through each json record and add it to the table
    for record in hourly_nft_data:
        json_record = json.loads(json.dumps(list(record.values()), indent=4))

        # avoid collection(s) that use non-ascii characters
        if table.check_ascii(json_record[0]['nft']) is False:
            continue
        table.add(data=json_record)

    filename = Imagify(title=f"RMRK sales", text=str(table.sales()), footer=f"hourly sales").create()
    Tweet(account='NonFungibleTxs').alert(message='#RMRK sale(s) caught in the last hour.', filename=filename)
    Utils.cache_data('data-cache/hourly-rmrk-sales.json', [])
