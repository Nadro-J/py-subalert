import sys
from pathlib import Path

file = Path(__file__).resolve()
package_root_directory = file.parents [1]
sys.path.append(str(package_root_directory))

from subalert.tips import *

tips = TipsSubscription()
tips.has_tips_updated()