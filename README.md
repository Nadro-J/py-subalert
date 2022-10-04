```
 _______         __     _______ __              __   
|     __|.--.--.|  |--.|   _   |  |.-----.----.|  |_ 
|__     ||  |  ||  _  ||       |  ||  -__|   _||   _|
|_______||_____||_____||___|___|__||_____|__|  |____|
  1.0.0-alpha
```
### On-chain analytics delivered from substrate node to Twitter.

---

---
### **Current phase:** `Phase 1. B`

---
**Phase 1.**  
- a) Build several monitoring scripts
- b) Improve logging, error/exception handling
- c) Iron out any issues found from logging
- d) Improve queue system to mitigate API violations
- e) Clean up code

**Phase 2.**
- a) Experiment outside of Twitter by building classes specific to each platform
  - Discord
  - Telegram
  - Elements
  - Slack
- b) Capture information in DB to create KPI/Dashboard stats
- c) Modify extrinsic monitoring to parse through blocks from the past after creating a database connector for postgres
- d) Clean up code

**Phase 3.**
- a) Create standard scripts outside of py-subalert using py-substrate-interface to serve as examples for the community to use & experiment with
- b) Take snippets from the base file and create a separate library to make extrinsic calls returned in json format
  - Build lite UI Flask using library to perform basic wallet functionality



Kusama Bots
- [RMRK Interactions](https://twitter.com/NonFungibleTxs)
  - [AXC Sales](https://twitter.com/AXC_Sales)
- [Kusama Transactions](https://twitter.com/KusamaTxs)
- [Kusama Stake](https://twitter.com/KusamaStake)
- [Kusama Tips](https://twitter.com/KusamaTip)
- [Kusama Democracy](https://twitter.com/KusamaDemocracy)
- [Kusama Validators](https://twitter.com/KusamaValidator)