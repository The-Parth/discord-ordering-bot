import json
import os
import discord
from extras import Utils


class UserManager:
    def get_wallet(self, user_id):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/wallets/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        if not os.path.isfile(filepath):
            user_file = {
                "user_id": str(user_id),
                "balance": 0,
            }
            json.dump(user_file, open(filepath, "w"), indent=4)
        user_data = json.load(open(filepath, 'r'))
        return {"data": user_data, "filepath": filepath}

    def change_balance(self, user_id, amount):
        # gets the wallet
        wallet = self.get_wallet(user_id)
        wallet["data"]["balance"] += amount  # adds the amount to the balance
        # Saves it in the users data
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)

    def get_transactions(self, user_id):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/transactions/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        if not os.path.isfile(filepath):
            user_file = {}
            json.dump(user_file, open(filepath, "w"), indent=4)
        user_data = json.load(open(filepath, 'r'))
        return {"data": user_data, "filepath": filepath}

    def add_order(self, user_id, order_id, amount, cart, instructions: None):
        transactions = self.get_transactions(user_id)
        transactions["data"][order_id] = {
            "type": "order",
            "amount": amount,
            "cart": cart,
        }
        if instructions is not None:
            transactions["data"][order_id]["instructions"] = instructions
        print(transactions)
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)

    def add_reload(self, user_id, reload_id, amount):
        transactions = self.get_transactions(user_id)
        transactions["data"][reload_id] = {
            "type": "reload",
            "amount": amount,
        }
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)


w = UserManager()
print(w.get_wallet(91))
print(w.get_transactions(91))
cart = {
}
w.change_balance(91, -100)
w.add_order(91, "order_1", 100, cart, instructions="Hello")
w.add_reload(91, "reload_1", 100)
