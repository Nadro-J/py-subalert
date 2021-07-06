from subalert.transact import *

#
txSub = TransactionSubscription()
txSub.substrate.subscribe_block_headers(txSub.new_block_sub, include_author=True)