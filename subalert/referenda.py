import subalert.base


class DemocracySubscription:
    def __init__(self):
        self.tweet = subalert.base.Tweet()
        self.config = subalert.base.Configuration()
        self.substrate = self.config.substrate
        self.hashtag = str(self.config.yaml_file['twitter']['hashtag'])

    def referendum_info(self, index):
        """
        :param index: index of referendum
        :return: Information regarding a specific referendum
        """

        # index - 1 since democracy referendum starts at zero
        result = self.substrate.query(
            module='Democracy',
            storage_function='ReferendumInfoOf',
            params=[index - 1])  # increase to go back; original: 1
        return result.serialize()

    def new_referendum(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from referendum_watch()
        :param update_nr: passed from subscription_handler
        :param subscription_id: passed from subscription_handler
        :return: return latest democracy referendum using referendum_info()
        """
        print(f"👂Listening for new democracy referendums.")

        if 'Finished' in self.referendum_info(obj.value):
            pass
        else:

            # democracy increased
            if update_nr > 0:
                # referendum info
                referendum = self.referendum_info(obj.value)['Ongoing']
                end = referendum['end']
                proposalHash = referendum['proposalHash']
                threshold = referendum['threshold']
                delay = referendum['delay']
                votes = referendum['tally']
                ayes = votes['ayes']
                nays = votes['nays']

                tweet_body = (f"📜A new proposal has been submitted.\n\n"
                              f"proposalHash: {proposalHash}\n\n"
                              f"end: {end} - delay: {delay}\n"
                              f"threshold: {threshold}\n"
                              f"✅AYE: {ayes / 10 ** self.substrate.token_decimals:,.2f} - ❌NAY: {nays / 10 ** self.substrate.token_decimals:,.2f}\n\n"
                              f"https://{self.hashtag.lower()}.polkassembly.io/referendum/{obj.value - 1}")

                self.tweet.alert(tweet_body)

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
