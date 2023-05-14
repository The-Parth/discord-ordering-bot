import json
import os
from extras import Utils, Checkers
import pymongo

client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client.DiscordDB
walletdb = db.wallets


# Migration from Local Jsons under data/ to MongoDB
def carts():
    path = os.path.dirname(os.path.abspath(__file__)) + "/data/wallets"
    path = Utils.path_finder(path)
    for i in os.listdir(path):
        if i.endswith(".json"):
            filepath = path + "/" + i
            filepath = Utils.path_finder(filepath)
            print(filepath)
            data = json.load(open(filepath, 'r'))
            wallet = {
                "_id": str(data["user_id"]),
                "user_id": str(data["user_id"]),
                "balance": data["balance"]
            }
            print(wallet)
    

# pings pymongo to make sure it's connected
print(client.server_info())