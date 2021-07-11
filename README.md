# py-subalert

#### Subscribe to transactions >= threshold set in .yaml
```python
from subalert.transact import *

txSub = TransactionSubscription()
txSub.substrate.subscribe_block_headers(txSub.new_block_sub, include_author=True)
```

#### Subscribe to referenda
```python 
from subalert.referenda import *

referendum = DemocracySubscription()
referendum.referendum_watch()
```

#### Currently tweets:  
- Large balance transfers
- Governance
    - Referenda
- Polkadot Binary Updates

#### In-progress:  
- Governance
    - Proposals
    - Tips.  



KSM tip address: `E5djM6u2p67C1LfkSyNDfRnvYwg6HAQxwPB8yK6Q5eAwdjn`
