import json
import os
import discord
import asyncio
import datetime
from discord import app_commands
from extras import Utils, Checkers


class Actions:
    def make_wallet(self, user_id):
        # Gets the user's wallet
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/wallets/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        # Makes the wallet if it doesn't exist
        if not os.path.isfile(filepath):
            user_file = {
                "user_id": str(user_id),
                "balance": 0,
                "email": "",
            }
            # Saves the wallet
            json.dump(user_file, open(filepath, "w"), indent=4)
        return filepath

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
        # Gets the user's wallet from the make_wallet function
        filepath = self.make_wallet(user_id)
        # Loads the wallet
        user_data = json.load(open(filepath, 'r'))
        # Returns the wallet
        return {"data": user_data, "filepath": filepath}

    def add_balance(self, user_id, amount):
        # gets the wallet
        wallet = self.get_wallet(user_id)
        # Adds the amount to the balance
        wallet["data"]["balance"] += amount  # adds the amount to the balance
        wallet["data"]["balance"] = round(wallet["data"]["balance"], 2)
        # Saves it in the users data
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)

    def remove_balance(self, user_id, amount):
        class TooMuchSpent(Exception):
            pass
        # gets the wallet
        wallet = self.get_wallet(user_id)
        # Spends the amount from the balance
        wallet["data"]["balance"] -= amount
        wallet["data"]["balance"] = round(wallet["data"]["balance"], 2)
        # Error if the balance is less than 0
        if wallet["data"]["balance"] < 0:
            raise TooMuchSpent("I see shenanigans")
        # Saves it in the users data, if the balance is greater than 0
        json.dump(wallet["data"], open(wallet["filepath"], "w"), indent=4)

    def get_transactions(self, user_id):
        # Gets the user's transactions
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + f"/data/transactions/{str(user_id)}.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        # Makes the transactions if it doesn't exist
        if not os.path.isfile(filepath):
            user_file = {
                "user_id": str(user_id),
                "orders": {},
                "reloads": {},
            }
            # Saves the transactions
            json.dump(user_file, open(filepath, "w"), indent=4)
        # Loads the transactions
        user_data = json.load(open(filepath, 'r'))
        # Returns the transactions
        return {"data": user_data, "filepath": filepath}

    def add_order(self, user_id, order_id, amount, cart, status, instructions: None):
        # Gets the user's transactions
        transactions = self.get_transactions(user_id)
        # Adds the order to the transactions
        transactions["data"]["orders"][order_id] = {
            "amount": amount,
            "status": status,
            "cart": cart,
        }
        # Adds the instructions if there are any
        if instructions is not None:
            transactions["data"]["orders"][order_id]["instructions"] = instructions
        # Saves the transactions
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)

    def add_reload(self, user_id, reload_id, amount, status, invoice=None):
        # Gets the user's transactions
        transactions = self.get_transactions(user_id)
        # Adds the reload to the transactions
        transactions["data"]["reloads"][reload_id] = {
            "amount": amount,
            "status": status,
            "invoice": invoice,
        }
        # Saves the transactions
        json.dump(transactions["data"], open(
            transactions["filepath"], "w"), indent=4)


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

    @app_commands.command(name="recharge", description="Recharge your wallet")
    @app_commands.describe(
        amount="The amount you want to recharge your wallet with in INR"
    )
    @Checkers.is_dm()
    async def reload_wallet(self, interaction: discord.Interaction, amount: app_commands.Range[float, 1, 10000]):
        email = self.action_object.get_email(interaction.user.id)
        if email is None:
            await interaction.response.send_message("You need to set your email before you can recharge your wallet. Use `/email <email>` to set your email")
            return
        await interaction.response.send_message("Okay, generating an invoice...")
        msg = await interaction.original_response()
        from payments import Payment
        # Generate a unique memo for the invoice using the user's name and the amount
        order_id = str(Utils.order_id_gen(interaction.user.id))+"_R"
        memo = str(order_id) + \
            f": Recharge for {str(interaction.user)} of INR {amount}"
        # Create the invoice using the Coinbase Commerce API in payments.py
        inv = Payment.invoice(str(interaction.user),
                              email, amount, "INR", memo)
        self.action_object.add_reload(
            interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
        # Make an the invoice with a button to pay the invoice
        embed = discord.Embed(title=f"Invoice {inv['code']} created!",
                              description=f"Payment link : {inv['url']}",
                              color=0xc6be0f)
        embed.add_field(name="Recharge Amount",
                        value=f"INR {amount}", inline=True)
        embed.add_field(name="Order Code", value=inv['code'], inline=True)
        embed.add_field(name="Order ID", value=order_id, inline=True)
        embed.set_footer(text="Tx. ID: {0}".format(inv['id']))
        view = discord.ui.View()
        view.add_item(item=discord.ui.Button(
            label="Make Payment", url=inv['url']))

        # Send the invoice to the user
        await interaction.followup.edit_message(message_id=msg.id, content=None, embed=embed, view=view)
        # await interaction.followup.send(embed=embed, view=view)
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
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Payment for Invoice {inv['code']} Pending!",
                                      description=f"Check status here : {inv['url']}",
                                      color=0x3f7de0)
                embed.set_footer(
                    text="We will notify you when the payment is complete.")
                await interaction.followup.send(embed=embed)

            if stats == 'PAID':
                """Case when the payment is complete, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Paid Successfully!",
                                      description=f"View Charge : {inv['url']}",
                                      color=0x20e364)
                embed.add_field(
                    name="Amount", value=f"INR {amount}", inline=True)
                embed.add_field(name="Order Code",
                                value=inv['code'], inline=True)
                embed.add_field(name="Order ID", value=order_id, inline=True)
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
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                      color=0xd62d2d)
                embed.set_footer(
                    text="This happens if the invoice is not paid within 60 minutes or if the invoice is cancelled.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'EXPIRED':
                """Case when the invoice is expired, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                      color=0xd62d2d)
                embed.set_footer(text="You can try again with a new invoice.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'UNRESOLVED':
                """Case when the invoice is in an unresolved state, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                      color=0xd62d2d)
                embed.set_footer(
                    "This may be due to underpayment or overpayment.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if count == 30 and (stats == 'VIEWED' or stats == 'OPEN'):
                Payment.void_payment(inv['code'])

            # sleep for 10 seconds before checking again
            await asyncio.sleep(10)

        self.action_object.add_reload(
            interaction.user.id, order_id, amount, Payment.check_payments(inv), inv["code"])
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

    @app_commands.command(name="refresh", description="Refreshes all unpaid invoices. Also cancels any unpaid invoices")
    @app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild, i.user.id))
    async def refresh_invoices(self, interaction: discord.Interaction):
        """Refreshes the invoices for the user."""
        # Get the user's invoices
        from payments import Payment
        await interaction.response.send_message("Refreshing your invoices...")
        transactions_obj = self.action_object.get_transactions(
            interaction.user.id)
        transactions = transactions_obj["data"]
        for t in transactions["reloads"]:
            i = transactions["reloads"][t]
            stat = i["status"]
            if stat == "PAID" or stat == "VOID":
                continue
            else:
                new_stat = Payment.check_payments(i['invoice'], id_pass=True)
                if new_stat == "PAID":
                    transactions["reloads"][t]["status"] = "PAID"
                    self.action_object.add_balance(
                        interaction.user.id, i["amount"])
                    await interaction.followup.send(f"Invoice {i['invoice']}: Your wallet has been recharged with INR {i['amount']}")
                elif new_stat == "OPEN" or new_stat == "VIEWED":
                    Payment.void_payment(i['invoice'])
                    await interaction.followup.send(f"Invoice {i['invoice']}: Your invoice has been voided.")
                    transactions["reloads"][t]["status"] = "VOID"
                elif new_stat != stat:
                    transactions["reloads"][t]["status"] = new_stat
                    await interaction.followup.send(f"Invoice {i['invoice']}: Your invoice status is {new_stat}")
                else:
                    continue
        json.dump(transactions, open(
            transactions_obj["filepath"], "w"), indent=4)
        await interaction.followup.send("Your invoices have been refreshed.")

    @refresh_invoices.error
    async def refresh_invoices_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Please wait for {error.retry_after} seconds before using this command again.", ephemeral=True)
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("Works in DMs only!", ephemeral=True)
        else:
            await interaction.response.send_message("An unknown error occured, please try again later.", ephemeral=True)
