# py-subalert

On-chain analytics delivered from substrate based eco-systems to Twitter.  

Note: This library will mature over time and certain areas may be re-developed to further improve alerts. The current scope is Twitter, but with the eventual plan of creating a web interface displaying real-time data once the library has matured enough.

[PolkadotTxs](https://twitter.com/PolkadotTxs) 
```yaml 
chain:
  url: wss://polkadot.api.onfinality.io/public-ws
  ss58_format: 0
  type_registry_preset: polkadot
  ticker: DOT
alert:
  transact_threshold: 25000
  whale_threshold: 500000
github:
  repository: https://api.github.com/repos/paritytech/polkadot/releases/latest
validator_programme_url: https://polkadot.w3f.community/candidates
```
---

[KusamaTxs](https://twitter.com/KusamaTxs)
```yaml
chain:
  url: wss://kusama-rpc.polkadot.io/
  ss58_format: 0
  type_registry_preset: kusama
  ticker: KSM
alert:
  transact_threshold: 250
  whale_threshold: 250000
github:
  repository: https://api.github.com/repos/paritytech/polkadot/releases/latest
validator_programme_url: https://kusama.w3f.community/candidates
```

### Examples

##### Subscribe to transactions >= threshold set in .yaml
```python
from subalert.transact import *

txSub = TransactionSubscription()
txSub.substrate.subscribe_block_headers(txSub.new_block_sub, include_author=True)
```

##### Subscribe to referenda
```python 
from subalert.referenda import *

referendum = DemocracySubscription()
referendum.referendum_watch()
```

##### Monitor validator commission
```python
from subalert.validator import *

validators = ValidatorWatch()
validators.has_commission_updated()
```

---

### Roadmap  
- Large balance transfers ✅  
![](https://i.imgur.com/UK79bb8.png)
- Governance  
    - Referenda ✅   
    ![](https://i.imgur.com/7wdmhyg.png)
    - Council
    - Proposals 
    - Tips 🔄
    - Bounties
- Staking
    - Total stake per era (report the difference from the previous era)
    - Monitor changes to Validator commission ✅  
    ![](https://i.imgur.com/JY67kkv.png)
- Polkadot Binary Updates ✅  
![](https://i.imgur.com/lOVP4D5.png)



KSM tip address: `E5djM6u2p67C1LfkSyNDfRnvYwg6HAQxwPB8yK6Q5eAwdjn`  
DOT tip address: `5GLSSnXaukoyf7ZYRWJoJnX9n9cHwCUyEDD8FK58oSPVVJBW`
