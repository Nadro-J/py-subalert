from subalert.base import Tweet, Configuration, Numbers  # local library
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

    def era_84_graph(self):
        era_data, eras, values = {}, [], []

        for _era, _stake in self.era_total_stake():
            era_data.update({str(_era): str(_stake)})
        sort_orders = sorted(era_data.items(), key=lambda _era: _era[0], reverse=True)

        for era, value in sorted(sort_orders):
            eras.append(era), values.append(float(Numbers(int(value)).large_to_dec()))

        with cbook.get_sample_data(os.path.abspath(f"logos/{self.hashtag}.png")) as file:
            img = image.imread(file)

        fig, ax = plt.subplots()
        ax.plot_date(eras, values, marker='.', linestyle='-', color="#e6007a")
        ax.set_xticks(ax.get_xticks()[::5])

        fig.autofmt_xdate()
        plt.title(f"{self.hashtag} - Total stake over 84 eras")
        plt.ylabel(f"Total stake (M{self.ticker})")
        plt.xlabel('Era(s)')
        fig.figimage(img, 40, -40, zorder=3, alpha=.1, resize=False)
        plt.savefig('TotalStake84Eras.png')
