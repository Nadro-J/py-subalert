from subalert.base import Tweet  # local library
from subalert.base import Configuration  # local library


class DemocracySubscription:
    def __init__(self):
        self.tweet = Tweet()
        self.config = Configuration()
        self.substrate = self.config.substrate

    def new_referendum(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from referendum_watch()
        :param update_nr: passed from subscription_handler
        :param subscription_id: passed from subscription_handler
        :return: return latest democracy referendum using referendum_info()
        """
        print(f"-------[ DEBUGGING: Initial data ] --------\n"
              f"update_nr: {update_nr} - subscription_id: {subscription_id}\n"
              f"democracy count: {obj}\ndata: {self.referendum_info(obj.value)}\n"
              f"---------------------------------------------")

        if update_nr > 0:
            # Do something with the update
            print("referendum_count increased")
            print('referendum count now:', obj.value)

            return self.referendum_info(obj.value)

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

    def referendum_info(self, index):
        """
        :param index: index of referendum
        :return: data: {'Ongoing': {
                            'end': 6048000,
                            'proposalHash': '0x397985b75154982117611d75751dd4453877fd65e714c54d251f5e771351e07d',
                            'threshold': 'Super majority approval', #
                            'delay': 403200,
                            'tally': {
                                'ayes': 100942195000000,
                                'nays': 1502819115000000,
                                'turnout': 2388275096100000
                            }
                       }}
        """

        # index - 1 since democracy referendum starts at zero
        result = self.substrate.query(
            module='Democracy',
            storage_function='ReferendumInfoOf',
            params=[index - 3])  # increase to go back; original: 1
        return result
