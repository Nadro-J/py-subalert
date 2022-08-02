from .config import Configuration
from .subtweet import Tweet
from subalert.base import SubQuery

class DemocracySubscription:
    def __init__(self):
        self.config = Configuration()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])
        self.subquery = SubQuery()

    def new_referendum(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from referendum_watch()
        :param update_nr: passed from subscription_handler
        :param subscription_id: passed from subscription_handler
        :return: return latest democracy referendum using referendum_info()
        """
        print(f"👂Listening for new democracy referendums.")

        if 'Finished' in self.subquery.referendum_info(obj.value):
            pass
        else:
            # democracy increased
            if update_nr > 0:
                # referendum info
                referendum = self.subquery.referendum_info(obj.value)['Ongoing']
                end = referendum['end']
                proposalHash = referendum['proposal_hash']
                threshold = referendum['threshold']
                delay = referendum['delay']
                votes = referendum['tally']
                ayes = votes['ayes']
                nays = votes['nays']

                tweet_body = (f"📜A proposal is ongoing.\n\n"
                              f"proposalHash: {proposalHash}\n\n"
                              f"end: {end} - delay: {delay}\n"
                              f"threshold: {threshold}\n"
                              f"✅AYE: {ayes / 10 ** self.substrate.token_decimals:,.2f} - ❌NAY: {nays / 10 ** self.substrate.token_decimals:,.2f}\n\n"
                              f"https://{self.hashtag.lower()}.polkassembly.io/referendum/{obj.value - 1}\n#{self.hashtag} #Governance")

                Tweet('KusamaDemocracy').alert(message=tweet_body)

            # The execution will block until an arbitrary value is returned, which will be the result of the `query`
            if update_nr > 1:
                return obj

    def referendum_watch(self):
        """
        :return: total number of referendums
        """

        return int(str(self.substrate.query(
            module='Democracy',
            storage_function='ReferendumCount',
            subscription_handler=self.new_referendum)))
