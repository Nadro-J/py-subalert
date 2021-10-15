import subalert.base
from subalert.base import Tweet, Configuration, SubQuery
import datetime
import json, os
import deepdiff


class PhragmenSubscription:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.subquery = SubQuery()
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
        stake_change = {}
        change = ''

        if not os.path.isfile('data-cache/council-voters.cache'):
            subalert.base.Utils.cache_data('data-cache/council-voters.cache', voting_data)

        cached_voting_data = subalert.base.Utils.open_cache('data-cache/council-voters.cache')

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
                        candidates += f"{self.subquery.check_identity(address=voting)}\n"

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %I:%M:%S%p")
                    image_path = subalert.base.Imagify(title=f"{self.subquery.check_identity(address=voter_address)} voted for",
                                          text=candidates, footer=f"{timestamp}").create()



                    #print(f"Info: {self.voting_info(candidate_address)}")
            elif key == 'values_changed':
                for obj, attributes in result['values_changed'].items():
                    if 'stake' in obj:
                        address = obj.replace("root['", "").replace("']", "").replace("['stake", "")
                        stake_change.update({address: attributes})

                for voter, changed_attributes in stake_change.items():
                    old_value = int(changed_attributes['old_value']) / 10 ** self.substrate.token_decimals
                    new_value = int(changed_attributes['new_value']) / 10 ** self.substrate.token_decimals

                    if new_value > old_value:
                        change = f"has increased their stake from {old_value} to {new_value} $DOT"

                    if new_value < old_value:
                        change = f"has decreased their stake from {old_value} to {new_value} $DOT"

                    print(f"{self.subquery.check_identity(voter)} {change}")
