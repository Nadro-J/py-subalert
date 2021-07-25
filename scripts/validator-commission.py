# 0 */12 * * * cd /root/py-subalert && /usr/bin/python3 /root/py-subalert/commission.py >> /root/py-subalert/validator_commission.log 2>&1
from subalert.validator import *

validators = ValidatorWatch()
validators.has_commission_updated()