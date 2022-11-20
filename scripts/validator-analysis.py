from subalert.validator import ValidatorWatch
import subalert.base
import datetime

vw = ValidatorWatch()
print("Getting validator commission.. please wait")
data = vw.get_current_commission()
timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%I%M%S%p")

print("Writing data to directory")
subalert.base.Utils.cache_data(f'validator-analysis/snapshot-{timestamp}.json', data)

print("Complete!")
