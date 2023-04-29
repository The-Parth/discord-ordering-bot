import json
import os
import discord
from discord import app_commands
import os
import json
from extras import Utils


class Actions:
    def make_wallet(self, user_id):
        # Gets the user's wallet
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/wallets/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        if not os.path.isfile(filepath):
            user_file = {
                "user_id": str(user_id),
                "balance": 0,
                "email": "",
            }
            json.dump(user_file, open(filepath, "w"), indent=4)
        return
    
    def add_email(self, user_id, email):
        wallet = self.get_wallet(user_id)
        wallet["data"]["email"] = email
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)
        
        
    def get_wallet(self, user_id):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/wallets/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        self.make_wallet(user_id)
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


class WalletActions(app_commands.Group):

    def __init__(self, bot: discord.Client):
        super().__init__(name="wallet", description="Perform actions on your wallet")
        self.bot = bot
        
    @app_commands.command(name="view", description="View your wallet")
    async def view_wallet(self, interaction: discord.Interaction):
        bot = self.bot
        """Views the user's wallet"""
        # Gets the user's wallet
        wallet = Actions().get_wallet(interaction.user.id)["data"]
        embed = discord.Embed(title="Wallet",
                              description="**Balance**: ₹{0}".format(
                                  wallet["balance"])
                              )
        try:
            # Gets the user's accent color
            accent = await bot.fetch_user(interaction.user.id)
            accent = accent.accent_color
            if accent is not None:
                embed.color = accent
            else:
                # Might occur if the user has 10 dollar nitro
                embed.color = 0xc6be0f
        except:
            embed.color = 0xc6be0f

        # Sets the embed's thumbnail to the user's avatar
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        # Sets the embed's author to the user's name and discriminator
        embed.set_author(name=interaction.user.name+"#" +
                         interaction.user.discriminator)
        # Sets the embed's footer to the user's ID
        embed.set_footer(text="ID: {0}".format(wallet["user_id"]))

        # Sends the embed
        await interaction.response.send_message(embed=embed)

    async def view_transactions(self, interaction: discord.Interaction, bot: discord.Client):
        pass
