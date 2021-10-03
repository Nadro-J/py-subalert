import os
import json
import time
import deepdiff
import subalert.base
from pathlib import Path

paths = sorted(Path('../validator-analysis').iterdir(), key=os.path.getmtime)

for i in range(0, len(paths)):
    x = i
    y = i - 1

    if y > 0:
        y_path = subalert.base.Utils.open_cache(paths[y])
        x_path = subalert.base.Utils.open_cache(paths[x])

        print(f"================\n"
              f"Comparing: '{paths[y]}'\n"
              f"Against: '{paths[x]}'\n"
              f"----------------")

        difference = deepdiff.DeepDiff(y_path, x_path, ignore_order=True).to_json()
        result = json.loads(difference)

        if len(result) == 0:
            print(f"No changes made during this time period.\n"
                  f"================\n\n")
            continue

        for key, value in result.items():
            print(f"key: {key}\n"
                  f"values_changed: {value}")
        print(f"================\n\n")
        time.sleep(3.14)
