import subalert.base
import json


class PhragmenSubscription:
    def __init__(self):
        self.tweet = subalert.base.Tweet()
        self.config = subalert.base.Configuration()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def get_candidates(self):
        result = self.substrate.query(
            module='PhragmenElection',
            storage_function='Candidates',
            params=None
        )
        return result

    def voting_info(self):
        """
        :return: Information on all that vote council members
        """
        voters_list = {}
        result = self.substrate.query_map(
            module='PhragmenElection',
            storage_function='Voting',
            params=None)

        for voter, details in result:
            voters_list.update({voter.value: details.value})

        return json.dumps(voters_list, indent=4)
