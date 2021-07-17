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

#### Monitor validator commission
```python
from subalert.validator import *

validators = ValidatorWatch()
validators.has_commission_updated()
```

#### Roadmap  
- Large balance transfers ✅
- Governance
    - Referenda 🔄✅ (complete, but pending testing for when live referenda proposals come in)
    - Council
    - Proposals 
    - Tips
    - Bounties
- Staking
    - Total stake per era (report the difference from the previous era)
    - Monitor changes to Validator commission 🔄
- Polkadot Binary Updates ✅



KSM tip address: `E5djM6u2p67C1LfkSyNDfRnvYwg6HAQxwPB8yK6Q5eAwdjn`  
DOT tip address: `5GLSSnXaukoyf7ZYRWJoJnX9n9cHwCUyEDD8FK58oSPVVJBW`
