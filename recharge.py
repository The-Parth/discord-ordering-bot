import discord
from discord import app_commands
from extras import Utils, Checkers
import asyncio
from wallet import Actions


class Recharge(app_commands.Group):
    bot: discord.Client
    action_object = Actions()

    def __init__(self, bot):
        super().__init__(name="recharge", description="Recharge your wallet")
        self.bot = bot

    async def payments_manager(self, interaction: discord.Interaction, amount: float, type: str):
        """Handle all payments"""
        PAYMENT_CLASS = None
        order_id = str(Utils.order_id_gen(interaction.user.id))
        from payments import Payment
        from razorpay_custom import Razorpay
        if type == "razorpay":
            PAYMENT_CLASS = Razorpay
            order_id += "_RR"
        elif type == "coinbase":
            PAYMENT_CLASS = Payment
            order_id += "_RC"

        email = self.action_object.get_email(interaction.user.id)
        if email is None:
            await interaction.response.send_message("You need to set your email before you can recharge your wallet. Use `/email <email>` to set your email")
            return
        await interaction.response.send_message("Okay, generating an invoice...")
        msg = await interaction.original_response()
        # Generate a unique memo for the invoice using the user's name and the amount

        memo = str(order_id) + \
            f": Recharge for {str(interaction.user)} of INR {amount}"
        # Create the invoice using the Coinbase Commerce API in payments.py
        inv = PAYMENT_CLASS.invoice(str(interaction.user),
                                    email, amount, "INR", memo)
        self.action_object.add_reload(
            interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
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

            stats = PAYMENT_CLASS.check_payments(inv)
            count += 1

            # print every 10 seconds for debugging purposes
            print(f"{count}. Payment Stats for {inv['code']} = {stats}")

            # check status every 10 seconds
            if stats == 'PAYMENT_PENDING' and flag_check_coming == False:
                """Case when the payment is marked as pending, and the user hasn't been notified yet"""
                flag_check_coming = True
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Payment for Invoice {inv['code']} Pending!",
                                      description=f"Check status here : {inv['url']}",
                                      color=0x3f7de0)
                embed.set_footer(
                    text="We will notify you when the payment is complete.")
                await interaction.followup.send(embed=embed)

            if stats == 'PAID':
                """Case when the payment is complete, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
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
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                      color=0xd62d2d)
                embed.set_footer(
                    text="This happens if the invoice is not paid within 60 minutes or if the invoice is cancelled.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'CANCELLED':
                """Case when the invoice is cancelled, and the user hasn't been notified yet"""
                """For Razorpay"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Cancelled!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} has been cancelled and can no longer be paid.",
                                      color=0xd62d2d)
                embed.set_footer(
                    text="This happens if the invoice is not paid within 60 minutes or if the invoice is cancelled.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'EXPIRED':
                """Case when the invoice is expired, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                      color=0xd62d2d)
                embed.set_footer(
                    text="This happens if the invoice is not paid within 60 minutes.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if stats == 'UNRESOLVED':
                """Case when the invoice is in an unresolved state, and the user hasn't been notified yet"""
                self.action_object.add_reload(
                    interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
                embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                      description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                      color=0xd62d2d)
                embed.set_footer(
                    "This may be due to underpayment or overpayment.")
                await interaction.followup.send(embed=embed)
                break  # break out of the loop

            if count == 30 and (stats == 'VIEWED' or stats == 'OPEN'):
                PAYMENT_CLASS.void_payment(inv['code'])

            # sleep for 10 seconds before checking again
            await asyncio.sleep(10)

        self.action_object.add_reload(
            interaction.user.id, order_id, amount, PAYMENT_CLASS.check_payments(inv), inv["code"])
        await interaction.followup.send("Your wallet recharge was unsuccessful. Please try again later.")

    @app_commands.command(name="crypto", description="Recharge your wallet")
    @app_commands.describe(
        amount="The amount you want to recharge your wallet with in INR"
    )
    @Checkers.is_dm()
    async def reload_wallet(self, interaction: discord.Interaction, amount: app_commands.Range[float, 1, 10000]):
        await self.payments_manager(interaction, amount, "coinbase")

    @reload_wallet.error
    async def reload_wallet_error(self, interaction: discord.Interaction, error):
        """If the user is not in DMs, send them a message to go to DMs."""
        # Embed to send to the user
        dm = await interaction.user.create_dm()
        try:
            msg = await dm.send("Use the command in DMs only.")
        except:
            pass
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(title="Works in DMs only!",
                                  description="Please direct message the bot.",
                                  color=0xc6be0f)
            embed.set_footer(
                text="If this was in DMs, an inadvertent error occured.")
            # View to send to the user containing a button to go to DMs
            view = discord.ui.View()
            view.add_item(item=discord.ui.Button(
                label="Go to DMs", url=dm.jump_url))
            # Send the message with the embed and view
            await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
            await msg.delete()
        else:
            await interaction.response.send_message("An unknown error occured, please try again later.")
            print(error)

    @app_commands.command(name="fiat", description="Recharge your wallet with fiat currency.")
    @app_commands.describe(
        amount="The amount of fiat currency to recharge your wallet with.",
    )
    @Checkers.is_dm()
    async def fiat(self, interaction: discord.Interaction, amount: app_commands.Range[float, 30, 10000]):
        await self.payments_manager(interaction, amount, "razorpay")

    @reload_wallet.error
    async def reload_wallet_error(self, interaction: discord.Interaction, error):
        """If the user is not in DMs, send them a message to go to DMs."""
        # Embed to send to the user
        dm = await interaction.user.create_dm()
        try:
            msg = await dm.send("Use the command in DMs only.")
        except:
            pass
        if isinstance(error, app_commands.CheckFailure):
            print("Not in DMs")
            embed = discord.Embed(title="Works in DMs only!",
                                  description="Please direct message the bot.",
                                  color=0xc6be0f)
            embed.set_footer(
                text="If this was in DMs, an inadvertent error occured.")
            # View to send to the user containing a button to go to DMs
            view = discord.ui.View()
            view.add_item(item=discord.ui.Button(
                label="Go to DMs", url=dm.jump_url))
            # Send the message with the embed and view
            await interaction.response.send_message(embed=embed, ephemeral=True, view=view)
            await msg.delete()

        else:
            await interaction.response.send_message("An unknown error occured, please try again later.")
            print(error)
