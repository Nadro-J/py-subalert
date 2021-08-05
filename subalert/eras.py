from subalert.base import Tweet, Configuration, Numbers, CoinGecko  # local library
from subalert.base import Configuration  # local library
import matplotlib.pyplot as plt
import matplotlib.image as image
import matplotlib.cbook as cbook
import os.path


class EraAnalysis:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.substrate = self.config.substrate
        self.hashtag = self.config.yaml_file['twitter']['hashtag']
        self.ticker = self.config.yaml_file['chain']['ticker']

    def era_total_stake(self):
        result = self.substrate.query_map(
            module='Staking',
            storage_function='ErasTotalStake',
            params=[])
        return result

    def circulating_supply(self):
        result = self.substrate.query(
            module='Balances',
            storage_function='TotalIssuance',
            params=[]
        )
        return Numbers(int(str(result)) / 10 ** self.substrate.token_decimals).large_to_dec()

    def era_84_graph(self):
        era_data, eras, values = {}, [], []

        for _era, _stake in self.era_total_stake():
            era_data.update({str(_era): str(_stake)})
        sort_orders = sorted(era_data.items(), key=lambda _era: _era[0], reverse=True)

        for era, value in sorted(sort_orders):
            eras.append(era), values.append(float(Numbers(int(value) / 10 ** self.substrate.token_decimals).large_to_dec()))

        with cbook.get_sample_data(os.path.abspath(f"logos/{self.hashtag}.png")) as file:
            img = image.imread(file)

        total_eras = len(eras) - 1
        price = CoinGecko(coin=self.hashtag, currency='usd').price()
        current_era_index = eras[total_eras]
        current_era_stake = Numbers(int(era_data[current_era_index]) / 10 ** self.substrate.token_decimals).human_format()
        current_era_stake_N = float(Numbers(int(era_data[current_era_index]) / 10 ** self.substrate.token_decimals).large_to_dec())
        previous_era_index = eras[total_eras - 1]
        usd_stake_value = int(era_data[current_era_index]) / 10 ** self.substrate.token_decimals * float(price.replace('$', ''))
        era_difference = int(era_data[current_era_index]) - int(era_data[previous_era_index])
        usd_era_difference = era_difference / 10 ** self.substrate.token_decimals * float(price.replace('$', ''))
        percentage_locked = current_era_stake_N / float(self.circulating_supply())

        era_diff_text = ""
        if era_difference < 0:
            era_diff_text = f"In the last 24hrs, ⬇️{Numbers(abs(era_difference) / 10 ** self.substrate.token_decimals).human_format()} (${Numbers(abs(usd_era_difference)).human_format()}) ${self.ticker} were unbonded."
        elif era_difference >= 0:
            era_diff_text = f"In the last 24hrs, ⬆️{Numbers(abs(era_difference) / 10 ** self.substrate.token_decimals).human_format()} (${Numbers(usd_era_difference).human_format()}) ${self.ticker} were bonded."

        fig, ax = plt.subplots()
        ax.plot_date(eras, values, marker='.', linestyle='-', color="#e6007a")
        ax.set_xticks(ax.get_xticks()[::5])

        plt.title(f"{self.hashtag} - total stake over 84 eras")
        plt.ylabel(f"Total stake (M{self.ticker})")
        plt.xlabel('Era(s)')
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.15)

        fig.figimage(img, 0, 10, zorder=3, alpha=.1, resize=False)
        plt.grid()
        plt.savefig('TotalStake84Eras.png')
        plt.close()

        tweet_body = (f"There are currently {current_era_stake} (${Numbers(usd_stake_value).human_format()}) {percentage_locked:.2%} ${self.ticker} locked on the network.\n\n"
                      f"{era_diff_text}")

        self.tweet.tweet_media(filename='TotalStake84Eras.png', message=tweet_body)


