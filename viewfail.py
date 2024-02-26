from datetime import datetime
import sys
import os
import json

MONTH = datetime.now().strftime('%Y%m')
job = sys.argv[-1].split('/')[-1]
fail_path = f'data/{MONTH}/{job}/fail.json'
if not os.path.exists(fail_path):
	print("No Failure")
with open(fail_path, 'r') as file:
	last_fail = json.load(file)
if len(last_fail['car_series']) + len(last_fail['car_type']) == 0:
	print("No Failure")
else:
	if len(last_fail['car_series']) != 0:
		print("car_series:")
		for v in last_fail['car_series'].values:
			print(v['url'])
	if len(last_fail['car_type']) != 0:
		print("car_type:")
		for v in last_fail['car_type'].values:
			print(v['url'])
	# print(json.dumps(last_fail, indent=4))
