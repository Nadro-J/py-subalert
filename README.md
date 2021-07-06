# py-subalert

#### Subscribe to transactions >= threshold set in .yaml
```python
txSub = TransactionSubscription()
txSub.substrate.subscribe_block_headers(txSub.new_block_sub, include_author=True)
```
