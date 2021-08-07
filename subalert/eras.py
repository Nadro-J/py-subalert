from subalert.base import Tweet, Configuration, Numbers, CoinGecko
from subalert.base import Configuration
import matplotlib.pyplot as plt
import matplotlib.image as image
import matplotlib.cbook as cbook
import os.path


class EraAnalysis:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.substrate = self.config.substrate
        self.token_decimal = self.substrate.token_decimals
        self.hashtag = self.config.yaml_file['twitter']['hashtag']
        self.ticker = self.config.yaml_file['chain']['ticker']

    def era_total_stake(self):
        """
        :return: A list including the total stake over the last 84 eras.
        """
        result = self.substrate.query_map(
            module='Staking',
            storage_function='ErasTotalStake',
            params=[])
        return result

    def circulating_supply(self):
        """
        :return: Total issuance circulating the network
        """
        result = self.substrate.query(
            module='Balances',
            storage_function='TotalIssuance',
            params=[]
        )
        return int(str(result))

    def era_84_graph(self):
        """
        :return: Generate a graph using matplotlib showing the total stake over 84 eras
        """
        era_data, eras, values = {}, [], []

        # Add data into era_data
        for _era, _stake in self.era_total_stake():
            era_data.update({str(_era): str(_stake)})

        sort_orders = sorted(era_data.items(), key=lambda _era: _era[0], reverse=True)

        # Iterate through sort_orders and append to eras/values.
        # This is used to plot the graph in matplotlib.
        for era, value in sorted(sort_orders):
            eras.append(era), values.append(float(Numbers(int(value) / 10 ** self.substrate.token_decimals).large_to_dec()))

        with cbook.get_sample_data(os.path.abspath(f"logos/{self.hashtag}.png")) as file:
            img = image.imread(file)

        price = CoinGecko(coin=self.hashtag, currency='usd').price()
        era_diff_text = ""
        total_eras = len(eras) - 1
        current_index = eras[total_eras]
        previous_index = eras[total_eras - 1]
        era_difference = int(era_data[current_index]) - int(era_data[previous_index])
        usd_difference = era_difference / 10 ** self.substrate.token_decimals * float(price.replace('$', ''))
        current_stake = Numbers(int(era_data[current_index]) / 10 ** self.substrate.token_decimals).human_format()
        current_stake_usd = int(era_data[current_index]) / 10 ** self.substrate.token_decimals * float(price.replace('$', ''))
        percentage_locked = int(era_data[current_index]) / self.circulating_supply()

        # Change icon depending if more or less has been bonded.
        if era_difference < 0:
            era_diff_text = f"In the last 24hrs, ⬇️{Numbers(abs(era_difference) / 10 ** self.substrate.token_decimals).human_format()} ${self.ticker} (${Numbers(abs(usd_difference)).human_format()}) were unbonded."
        elif era_difference >= 0:
            era_diff_text = f"In the last 24hrs, ⬆️{Numbers(abs(era_difference) / 10 ** self.substrate.token_decimals).human_format()} ${self.ticker} (${Numbers(usd_difference).human_format()}) were bonded."

        # Create graph using eras/values
        fig, ax = plt.subplots()
        ax.plot_date(eras, values, marker='.', linestyle='-', color="#e6007a")
        ax.set_xticks(ax.get_xticks()[::5])

        plt.title(f"{self.hashtag} - total stake over 84 eras")
        plt.ylabel(f"Total stake (M{self.ticker})")
        plt.xlabel('Era(s)')
        plt.xticks(rotation=45)
        plt.subplots_adjust(bottom=0.15)

        fig.figimage(img, zorder=3, alpha=.1, resize=False)
        plt.grid()

        plt.savefig('TotalStake84Eras.png', bbox_inches='tight')
        plt.close()

        tweet_body = (
            f"There are currently {current_stake} ${self.ticker} "
            f"(${Numbers(current_stake_usd).human_format()} - {percentage_locked:.2%}) locked on the network.\n\n"
            f"{era_diff_text}")

        self.tweet.tweet_media(filename='TotalStake84Eras.png', message=tweet_body)


