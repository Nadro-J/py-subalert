from subalert.base import Tweet  # local library
from subalert.base import Configuration  # local library


class EraAnalysis:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.substrate = self.config.substrate

    def era_total_stake(self):
        result = self.substrate.query_map(
            module='Staking',
            storage_function='ErasTotalStake',
            params=[])
        return result
