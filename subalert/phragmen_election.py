import subalert.base
from subalert.base import Tweet, Configuration, SubQuery, Imagify, Queue, Utils
import datetime
import time
import json, os
import deepdiff


class PhragmenSubscription:
    def __init__(self):
        self.config = Configuration()
        self.subquery = SubQuery()
        self.queue = Queue()
        self.utils = Utils()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def get_all_participants(self):
        participants = {}
        members = self.substrate.query(
            module='PhragmenElection',
            storage_function='Members',
            params=[]
        )

        runnersup = self.substrate.query(
            module='PhragmenElection',
            storage_function='RunnersUp',
            params=[]
        )

        for member in members.serialize():
            participants.update({member['who']: {'backing': member['stake']}})

        for runner_up in runnersup.serialize():
            participants.update({runner_up['who']: {'backing': runner_up['stake']}})

        return participants

    def get_candidates(self):
        result = self.substrate.query(
            module='PhragmenElection',
            storage_function='Candidates',
            params=[]
        )

        return result

    def voting_info(self, address=None):
        """
        :return: Information on all that vote council members
        """
        voters_list = {}

        if address is None:
            result = self.substrate.query_map(
                module='PhragmenElection',
                storage_function='Voting',
                params=address)

            for voter, details in result:
                voters_list.update({voter.value: details.value})

            return voters_list
        else:
            result = self.substrate.query(
                module='PhragmenElection',
                storage_function='Voting',
                params=[address])

            return result.serialize()

    def has_voting_updated(self):
        voting_data = self.voting_info()

        if not os.path.isfile('data-cache/council-voters.cache'):
            self.utils.cache_data('data-cache/council-voters.cache', voting_data)

        cached_voting_data = self.utils.open_cache('data-cache/council-voters.cache')

        # use DeepDiff to check if any values have changed since we ran has_commission_updated().
        difference = deepdiff.DeepDiff(cached_voting_data, voting_data, ignore_order=True).to_json()
        result = json.loads(difference)

        if len(result) == 0:
            print("🔧 No changes to commission have been found since the last execution")
            exit(1)

        print("🔧 changes have been found since the last time has_voting_updated was invoked")
        for key, value in result.items():
            if key == 'dictionary_item_added':
                for new_candidate in value:
                    voter_address = new_candidate.replace("root['", "").replace("']", "")
                    candidate_info = self.voting_info(voter_address)
                    candidates = ""

                    for voting in candidate_info['votes']:
                        candidates += f"{self.subquery.check_identity(address=voting).replace(' ', '')}\n"

                    identity = self.subquery.check_identity(address=voter_address)
                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y")
                    image_path = Imagify(title=f"{identity} voted for",
                                         text=candidates,
                                         footer=f"{timestamp} - @PolkadotTxs").create()

                    Tweet().alert(message=f"New #{self.hashtag} council votes!", filename=image_path, verbose=True)
        self.utils.cache_data('data-cache/council-voters.cache', voting_data)