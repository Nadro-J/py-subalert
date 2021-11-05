# py-subalert

On-chain analytics delivered from substrate based blockchains to Twitter.

Note: This library will mature over time and certain areas may be re-developed to further improve alerts. The current scope is Twitter, but with the eventual plan of creating a web interface displaying real-time data once the library has matured enough.

KSM tip address: `E5djM6u2p67C1LfkSyNDfRnvYwg6HAQxwPB8yK6Q5eAwdjn`  

Twitter bots (more to follow):
- [Polkadot](https://twitter.com/PolkadotTxs)   
- [Kusama](https://twitter.com/KusamaTxs)

---

##### Task list 
* [ ] block events
    * [x] transactions
    * [ ] RMRK NFT mints
* [x] referenda
* [x] phragmen election
    * [x] votes
* [x] tips
    * [x] proposed
    * [x] successfully closed
* [ ] validator
    * [x] commission monitoring
        * [ ] attach graph giving more detail to validators updating commission over X amount of eras
            * [ ] era points
            * [ ] elected stake
            * [ ] rewards & slashes
            * [ ] commission
* [ ] produce detailed graphs of the eco system
    * [x] bonded/unbonded in the last 24hrs
    * [ ] amount locked in crowdloans over X period
* [x] latest github binary release
---
##### subalert config
```yaml 
twitter:
  hashtag: Polkadot
  OAuthHandler:
    consumer_key: 
    consumer_secret: 
  access_token:
    key: 
    secret: 
chain:
  url: wss://polkadot.api.onfinality.io/public-ws
  ss58_format: 0
  type_registry_preset: polkadot
  ticker: DOT
  eras: 1
alert:
  transact_usd_threshold: 250000
  whale_threshold: 500000
  validator_change: 0
github:
  repository: https://api.github.com/repos/paritytech/polkadot/releases/latest
validator_programme_url: https://polkadot.w3f.community/candidates
```

---

### Examples
##### Block events monitoring
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

##### Stake on the network over 84 Eras
```python
from subalert.eras import *

era = EraAnalysis()
era.era_84_graph()
```

##### Monitor incoming/closing tips
```python
from subalert.tips import *

tips = TipsSubscription()
tips.has_tips_updated()
```

##### PhragmenElection council votes
```python
from subalert.phragmen_election import *

council_votes = PhragmenSubscription()
council_votes.has_voting_updated()
```