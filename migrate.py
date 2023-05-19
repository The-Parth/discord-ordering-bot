# Script can only be run from the root directory, otherwise it will not work
import pymongo
import os
import json
from dotenv import load_dotenv
import atexit

load_dotenv()

def path_finder(path):
    if os.name == "nt":
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")
"""
Migration tool for migrating user's old wallets and transactions
Moves them from the current data folder to the MongoDB database
Can be locally hosted or on a server like Atlas
This is a one time use tool, for existing users
Note that all wallets and transactions in the database, if any, will be deleted
Use with caution

We have not migrated carts, as they are usually temporary
Users can just re-add the items to their cart
"""

path = os.path.dirname(os.path.abspath(__file__)) + "/" + os.path.basename(__file__)
path = path_finder(path)
# We assume that the data is moved to the src folder
backpath = os.path.dirname(os.path.abspath(__file__)) + "/src/data/commands/"
backpath = path_finder(backpath)


client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
# The database name is DiscordDB
db = client.DiscordDB


def wallet_migrate():
    # Drops the existing collections, so fun to drop things
    db.drop_collection("wallets")
    print("Dropped wallets")    
    walletdb = db.wallets
    tpath = os.path.dirname(os.path.abspath(__file__)) + "/data/wallets/"
    tpath = path_finder(tpath)
    wallet =[i for i in os.listdir(tpath) if i.endswith(".json")]
    for i in wallet:
        data = json.load(open(tpath + i))
        data["_id"] = str(data["user_id"])
        walletdb.update_one({"_id": str(data["user_id"])}, {"$set": data}, upsert=True)
        print("Migrated wallets for " + i)

        
def transaction_migrate():
    db.drop_collection("transactions")
    print("Dropped transactions")
    orderdb = db.transactions
    tpath = os.path.dirname(os.path.abspath(__file__)) + "/data/transactions/"
    tpath = path_finder(tpath)
    transactions =[i for i in os.listdir(tpath) if i.endswith(".json")]
    for transaction in transactions: 
        i = json.load(open(tpath + transaction))
        i["_id"] = str(i["user_id"])
        orderdb.update_one({"_id": str(i["user_id"])}, {"$set": i}, upsert=True)
        print("Migrated Transactions for " + transaction)
    
        
def move():
    if os.name == "nt":
        os.system("move " + path + " " + backpath)
    else:
        os.system("mv " + path + " " + backpath)
    
if __name__ == "__main__":
    # Since this is a destructive script, we want to make sure the user knows what they are doing
    print("Please execute this scipt IF AND ONLY IF YOU KNOW WHAT YOU ARE DOING")
    print("This script will delete all existing wallets and transactions in the database")
    print("if you are sure you want to continue, type 'YES' (in all caps) and press enter")
    inp = input().strip()
    if inp != "YES":
        print("Aborted")
        exit(0)
    
    print("Confirmation 2: Are you sure (type 'I AM SURE' in all caps)")
    inp = input().strip()
    if inp != "I AM SURE":
        print("Aborted, you did not type 'I AM SURE'")
        exit(0)
    atexit.register(move)
    wallet_migrate()
    transaction_migrate()
    print("Done")
    print("Moved the script to " + backpath)
    print("This is to prevent accidental execution of the script again")
        