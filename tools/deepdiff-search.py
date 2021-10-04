import os
import json
import time
import deepdiff
import subalert.base
from pathlib import Path

paths = sorted(Path('../validator-analysis').iterdir(), key=os.path.getmtime)
_1kv_candidates = subalert.base.Utils.get_1kv_candidates()
subquery = subalert.base.SubQuery()

for i in range(0, len(paths)):
    x = i
    y = i - 1

    if y > 0:
        y_path = subalert.base.Utils.open_cache(paths[y])
        x_path = subalert.base.Utils.open_cache(paths[x])

        print(f"\nComparing: '{paths[y]}'\n"
              f"Against: '{paths[x]}'")

        difference = deepdiff.DeepDiff(y_path, x_path, ignore_order=True).to_json()
        result = json.loads(difference)
        validators_list = {}

        if len(result) == 0:
            continue

        for key, value in result.items():
            if key == 'values_changed':
                for obj, attributes in result['values_changed'].items():
                    if 'blocked' in obj:
                        pass
                    elif 'commission' in obj:
                        address = obj.replace("root['", "").replace("']", "").replace("['commission", "")
                        validators_list.update({address: attributes})

                for validator_address, changed_attributes in validators_list.items():
                    _1kv = False
                    validators_list[validator_address]['old_value'] = float(f"{100 * float(changed_attributes['old_value']) / float(1000000000):,.2f}")
                    validators_list[validator_address]['new_value'] = float(f"{100 * float(changed_attributes['new_value']) / float(1000000000):,.2f}")

                    if validator_address in _1kv_candidates:
                        _1kv = True
                        validators_list[validator_address]['is1kv'] = _1kv

                    identity = subquery.check_identity(validator_address)
                    if identity:
                        validators_list[validator_address]['identity'] = identity

                    print("----------------")
                    print(validator_address)
                    print(changed_attributes)
                print(f"================")
