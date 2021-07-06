from subalert.transact import *

# subscribe to transactions > transact_threshold : specified in config.local.yaml
txSub = TransactionSubscription()
txSub.substrate.subscribe_block_headers(txSub.new_block, include_author=True)