import json
import os
import discord
import asyncio
from discord import app_commands
from extras import Utils, Checkers


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

    def get_email(self, user_id):
        wallet = self.get_wallet(user_id)["data"]["email"]
        if wallet == "":
            return None
        return wallet

    def get_wallet(self, user_id):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/wallets/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        self.make_wallet(user_id)
        user_data = json.load(open(filepath, 'r'))
        return {"data": user_data, "filepath": filepath}

    def add_balance(self, user_id, amount):
        # gets the wallet
        wallet = self.get_wallet(user_id)
        wallet["data"]["balance"] += amount  # adds the amount to the balance
        # Saves it in the users data
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)
        
    def remove_balance(self, user_id, amount):
        class TooMuchSpent(Exception):
            pass
        wallet = self.get_wallet(user_id)
        wallet["data"]["balance"] -= amount
        if wallet["data"]["balance"] < 0:
            raise TooMuchSpent("I see shenanigans")
        # Saves it in the users data
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)
        
    def get_transactions(self, user_id):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/transactions/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        if not os.path.isfile(filepath):
            user_file = {
                "user_id": str(user_id),
                "orders": {},
                "reloads": {},
            }
            json.dump(user_file, open(filepath, "w"), indent=4)
        user_data = json.load(open(filepath, 'r'))
        return {"data": user_data, "filepath": filepath}

    def add_order(self, user_id, order_id, amount, cart, instructions: None):
        transactions = self.get_transactions(user_id)
        transactions["data"]["orders"][order_id] = {
            "amount": amount,
            "cart": cart,
        }
        if instructions is not None:
            transactions["data"]["orders"][order_id]["instructions"] = instructions
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)

    def add_reload(self, user_id, reload_id, amount):
        transactions = self.get_transactions(user_id)
        transactions["data"]["reloads"][reload_id] = {
            "type": "reload",
            "amount": amount,
        }
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)

    def transaction_paginate(self, user_id, type: str, page):
        type = type.lower()
        if type != "orders" and type != "reloads":
            raise Exception("Transaction type must be orders or reloads")
        transactions = self.get_transactions(user_id)["data"][type]
        Utils.list_divider(transactions, 5)


class WalletActions(app_commands.Group):
    
    action_object = Actions()

    def __init__(self, bot: discord.Client):
        super().__init__(name="wallet", description="Perform actions on your wallet")
        self.bot = bot

    @app_commands.command(name="view", description="View your wallet")
    async def view_wallet(self, interaction: discord.Interaction):
        bot = self.bot
        """Views the user's wallet"""
        # Gets the user's wallet
        wallet = self.action_object.get_wallet(interaction.user.id)["data"]
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

    @app_commands.command(name="transactions", description="View your transactions")
    @app_commands.describe(
        type="The type of transactions you want to view"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="orders", value="orders"),
        app_commands.Choice(name="reloads", value="reloads")]
    )
    async def view_transactions(self, interaction: discord.Interaction, type: str):
        await interaction.response.send_message("This command is not yet implemented, you chose {0}".format(type))

    @app_commands.command(name="reload", description="Recharge your wallet")
    @app_commands.describe(
        amount="The amount you want to recharge your wallet with in INR"
    )
    @Checkers.is_dm()
    async def reload_wallet(self, interaction: discord.Interaction, amount: app_commands.Range[float, 1, 10000]):
        email = self.action_object.get_email(interaction.user.id)
        if email is None:
            await interaction.response.send_message("You need to set your email before you can recharge your wallet. Use `/email <email>` to set your email")
            return
        
        from payments import Payment
        # Generate a unique memo for the invoice using the user's name and the amount
        memo = str(interaction.user.id) + \
            f": Tip from {str(interaction.user)} of INR {amount}"
        # Create the invoice using the Coinbase Commerce API in payments.py
        inv = Payment.invoice(str(interaction.user), email, amount, "INR", memo)

        # Make an the invoice with a button to pay the invoice
        embed = discord.Embed(title=f"Invoice {inv['code']} created!",
                            description=f"Payment link : {inv['url']}",
                            color=0xc6be0f)
        embed.add_field(name="Recharge Amount", value=f"INR {amount}", inline=True)
        embed.add_field(name="Order Code", value=inv['code'], inline=True)
        embed.add_field(name="Tx. ID", value=str(inv['id']), inline=True)
        view = discord.ui.View()
        view.add_item(item=discord.ui.Button(label="Make Payment", url=inv['url']))

        # Send the invoice to the user
        await interaction.response.send_message(embed=embed, view=view)
        count = 0
        flag_check_coming = False
        while True:
            """
            Check for payment status every 10 seconds, and notify the user when the payment is complete
            done using the Coinbase Commerce API in payments.py
            this function below is a coroutine, so it can be awaited
            this makes sure that the bot doesn't get blocked while waiting for the payment to complete
            """
            
            stats = Payment.check_payments(inv)
            count += 1

            # print every 10 seconds for debugging purposes
            print(f"{count}. Payment Stats for {inv['code']} = {stats}")

            # check status every 10 seconds
            if stats == 'PAYMENT_PENDING' and flag_check_coming == False:
                """Case when the payment is marked as pending, and the user hasn't been notified yet"""
                flag_check_coming = True
                embed = discord.Embed(title=f"Payment for Invoice {inv['code']} Pending!",
                                    description=f"Check status here : {inv['url']}",
                                    color=0x3f7de0)
                embed.set_footer(
                    text="We will notify you when the payment is complete.")
                await interaction.followup.send(embed=embed)

            if stats == 'PAID':
                """Case when the payment is complete, and the user hasn't been notified yet"""
                embed = discord.Embed(title=f"Invoice {inv['code']} Paid Successfully!",
                                    description=f"View Charge : {inv['url']}",
                                    color=0x20e364)
                embed.add_field(name="Amount", value=f"INR {amount}", inline=True)
                embed.add_field(name="Order Code", value=inv['code'], inline=True)
                embed.add_field(name="Tx. ID", value=str(inv['id']), inline=True)
                embed.set_footer(
                    text="Thank you for shopping with us! See you soon!")
                view = discord.ui.View()
                view.add_item(item=discord.ui.Button(
                    label="View Charge", url=inv['url']))
                await interaction.followup.send(embed=embed, view=view)
                self.action_object.add_balance(interaction.user.id, amount)
                await interaction.followup.send("Your wallet has been recharged with INR {0}".format(amount))
                return
                # Add the amount to the user's balance

            if stats == 'VOID':
                """Case when the invoice is voided, and the user hasn't been notified yet"""
                embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                    description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                    color=0xd62d2d)
                embed.set_footer(
                    text="This is usually due to staff interruption.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'EXPIRED':
                """Case when the invoice is expired, and the user hasn't been notified yet"""
                embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                    description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                    color=0xd62d2d)
                embed.set_footer(text="You can try again with a new invoice.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'UNRESOLVED':
                """Case when the invoice is in an unresolved state, and the user hasn't been notified yet"""
                embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                    description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                    color=0xd62d2d)
                embed.set_footer("This may be due to underpayment or overpayment.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            # sleep for 10 seconds before checking again
            await asyncio.sleep(10)
        
        await interaction.followup.send("Your wallet recharge was unsuccessful. Please try again later.")

    @reload_wallet.error
    async def reload_wallet_error(self, interaction: discord.Interaction, error):
        """If the user is not in DMs, send them a message to go to DMs."""
        # Embed to send to the user
        if isinstance(error, app_commands.CheckFailure):
            print("Not in DMs")
            embed = discord.Embed(title="Works in DMs only!",
                                  description="Please direct message the bot.",
                                  color=0xc6be0f)
            embed.set_footer(
                text="If this was in DMs, an inadvertent error occured.")
            # View to send to the user containing a button to go to DMs
            view = discord.ui.View()
            dm = await interaction.user.create_dm()
            view.add_item(item=discord.ui.Button(
                label="Go to DMs", url=dm.jump_url))
            # Send the message with the embed and view
            await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
        else:
            await interaction.response.send_message("An unknown error occured, please try again later.")
            print(error)
