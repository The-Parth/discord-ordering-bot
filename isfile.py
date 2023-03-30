import os
import datetime

print(os.path.isfile(os.path.dirname(os.path.abspath(__file__))+"/data/carts/1.json"))

print(str(int(datetime.datetime.utcnow().timestamp()))[-1:-5:-1][::-1])
print(str(int(datetime.datetime.utcnow().timestamp())))