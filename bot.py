import discord
import os
import asyncio
import datetime
import json
import typing
from discord import app_commands
from extras import Checkers, Utils
from dotenv import load_dotenv
from mailer import Mailer
import pymongo

mongo_client = pymongo.MongoClient(os.environ.get("MONGO_URI"))


load_dotenv()
# Creates a mailer object
mailobj: Mailer = Mailer()

intents = discord.Intents.all()
bot = discord.AutoShardedClient(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owners = [354546286634074115]

order_channel = int(os.environ.get("ORDER_CHANNEL", 0))
feedback_channel = int(os.environ.get("FEEDBACK_CHANNEL", 0))

validity = {
    "coinbase": True,
    "razorpay": True,
}

bot_started = datetime.datetime.timestamp(datetime.datetime.now())


@bot.event
async def on_ready():
    """When the bot is ready"""
    print("Bot is ready, logged in as {0.user}".format(bot))
    # Initializes and logs in to the mailer object
    await mailobj.async__init__()
    try:
        from carts import CartActions
        from wallet import WalletActions
        from transactions import Transactions
        from recharge import Recharge
        # Creates the slash command tree
        cart = CartActions(bot)
        # Adds the cart command group to the tree
        tree.add_command(cart)
        # Creates the wallet command group
        wallet = WalletActions(bot)
        # Adds the wallet command group to the tree
        tree.add_command(wallet)
        # Creates the transactions command group
        transactions = Transactions(bot)
        # Adds the transactions command group to the tree
        tree.add_command(transactions)
        # Creates the recharge command group
        recharge = Recharge(bot)
        # Adds the recharge command group to the tree
        tree.add_command(recharge)


        # Syncs the tree globally
        await tree.sync()
    except Exception as e:
        print(e)
        pass

    print("Tree synced!")
    # Starts the status task forever
    while await status_task():
        continue


async def status_task():
    """Changes the bot's status every 150 seconds"""
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your Cart"))
    await asyncio.sleep(150)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your Orders"))
    await asyncio.sleep(150)
    return True


@tree.command(name="help", description="Helps you with the bot")
@app_commands.describe(
    command="The command you need help with"
)
@app_commands.autocomplete(command=Utils().get_help_options)
async def help(interaction: discord.Interaction, command: str = None):
    """Gets help for a command"""
    # The embed to be sent is generated using this.
    embed = Utils.help_embed(command)
    # Sends the embed.
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="place_order", description="Confirm and place your order! (DMs only)")
@Checkers.is_dm()
@app_commands.describe(
    instructions= "Special instructions for the order",
)
async def place_order(interaction: discord.Interaction, instructions: str = None):
    """Places the order"""
    # Imports the actions module from the wallet
    from wallet import Actions
    cartdb = mongo_client.DiscordCartDB.carts

    cart = cartdb.find_one({"_id": str(interaction.user.id)})
    print(cart)
    # Creates the cart if it doesn't exist
    if cart is None:
        cart = {
            "_id": str(interaction.user.id),
            "user_id": str(interaction.user.id),
            "cart": {}
        }
        cartdb.insert_one(cart)
    else:
        cart = Utils.to_json(cart)
    cart = cart["cart"]

    # Gets the user's email
    email = Actions().get_email(interaction.user.id)
    if email is None:
        # Sent if the user has no email set
        await interaction.response.send_message("You need to set your email first! Use `/email <email>`",
                                                ephemeral=True)
        return

    # If the cart is empty, sends an ephemeral message
    if cart == {}:
        print("Cart is empty")
        await interaction.response.send_message("Your cart is empty!", ephemeral=True)
        return

    class PlaceOrderView(discord.ui.View):
        def __init__(self):
            # Initializes the view
            super().__init__()

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Confirms the order"""
            # Checks if the cart is empty
            if cart == {}:
                # The message to be sent if the cart is empty
                embed = discord.Embed(title="Your Cart is Empty",
                                      description="Your cart is empty, add something to it!",
                                      color=0x57eac8)
                embed.set_footer(text="If you need help, use /help")

                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                """Now that we know the cart isn't empty, we can start formatting the menu string
                Menu string is a list of strings, each string is a page of the menu
                Pages are used so that the menu doesn't get too long and discord doesn't complain, 20 items per page"""
                menu_string = [""]*9
                item_count = 0 # The number of items in the cart
                total_items = 0 # The total number of items in the cart
                f = cart # The cart, used because I like it here
                amount = Utils.get_cart_total(cart) # Gets the total cart value
                if amount == 0:
                    # If the cart value is 0, sends an error message
                    await interaction.response.edit_message(embed=None, view=None, content="You cannot place an order for ₹0!")
                    #await interaction.response.edit_message(content="We do not accept orders for free items only!",view=None,embed=None)
                    return
                # Formats the menu string in the format of "Item(Price) x Quantity..........Total"
                for item in f:
                    # Adds the item to the menu string
                    item_count += 1
                    total_items += f[item]['quantity']
                    menu_string[int((item_count)/20.0001)] += "{4}. **{0}**(*₹{1}*) x **{2}**..........**₹{3}**\n".format(
                        item, f[item]['rate'], f[item]['quantity'], f[item]['rate'] * f[item]['quantity'], item_count)

                # Creates the embed
                embeds = []
                # Tells the linter that the embeds variable is a list of embeds
                embeds: typing.List[discord.Embed]
                rand_color = Utils.random_hex_color()
                for i in menu_string:
                    # Creates the embed list for each page by adding the menu string elemnts to the embed
                    if i == "":
                        # Breaks if the page is empty
                        break
                    embed = discord.Embed(description=i, color=rand_color)

                    # Adds the embed to the embed list
                    embeds.append(embed)

                # Sets the title of the first embed
                embeds[0].title = "Order for {0}".format(interaction.user.name)
                # Adds the total to the last embed

                # Adds the user's details to the last embed
                # Includes the user's ID, username, discriminator, email, and the number of items in the cart 
                # The instructions are also added to the last embed
                embeds.append(discord.Embed(title="Order Summary",
                                            color=rand_color))
                embeds[-1].description = "**User ID**: {0}\n".format(
                    interaction.user.id)
                embeds[-1].description += "**Username:** {0}#{1}\n".format(
                    interaction.user.name, interaction.user.discriminator)
                embeds[-1].description += "**Number of items:** {0}\n".format(
                    total_items)
                embeds[-1].description += "**Email:** {0}\n".format(email)
                embeds[-1].timestamp = datetime.datetime.now()
                embeds[-1].description += "\n**Total: ₹{0}**".format(
                    amount)
                embeds[-1].description += "\n**Instructions:** {0}".format(
                    instructions)
                if interaction.user.avatar is not None:
                    # Sets the thumbnail to the user's avatar if it exists
                    embeds[-1].set_thumbnail(url=interaction.user.avatar.url)
            # Sets the timestamp of them embed to the current time
            timestamp_of_order = int(datetime.datetime.utcnow().timestamp())
            # Limbopath for temporary storage of the cart
            limbo_path = os.path.dirname(os.path.abspath(
                __file__)) + "\data\carts\limbo\{0}".format(
                    Utils.filename_gen(str(timestamp_of_order)[-1:-5:-1][::-1],
                                       str(interaction.user.id),
                                       "json"))
            limbo_path = Utils.path_finder(limbo_path)
            json.dump(cart, open(limbo_path, "w"), indent=2)
            cartdb.delete_one({"_id": str(interaction.user.id)})
            balance = Actions().get_wallet(
                interaction.user.id)["data"]["balance"]
            if balance < amount:
                # If the user doesn't have enough balance, sends an ephemeral message
                embed = discord.Embed(title="Insufficient Balance!",
                                      description="You don't have enough balance to place this order!")
                embed.add_field(name="Your Balance", value="₹{0}".format(balance), inline=False)
                embed.add_field(name="Order Total", value="₹{0}".format(amount), inline=False)
                limbo_cart = json.load(open(limbo_path, "r"))
                cartdb.insert_one({"_id": str(interaction.user.id), "user_id": str(interaction.user.id), "cart": limbo_cart})
                os.remove(limbo_path)
                await interaction.response.edit_message(embed=embed, view=None)
                
                return
            # Gets the channel to which the order has to be sent for the restaurant
            channel = await bot.fetch_channel(os.getenv("ORDER_CHANNEL"))
            order_id = Utils.order_id_gen(interaction.user.id)+"_O" # Generates the order ID
            try:
                # Tries to remove the balance from the user's wallet and add the order to the database
                Actions().remove_balance(interaction.user.id, amount)
                Actions().add_order(interaction.user.id, order_id, amount, f, "Confirmed", instructions)
            except Exception as e:
                if str(e) == "I see shenanigans":
                    await interaction.response.edit_message(content="Don't try to cheat the system!", embed=None, view=None)
                else:
                    await interaction.response.edit_message(content="Something went wrong, please try again later!", embed=None, view=None)
                Actions().add_order(interaction.user.id, order_id, amount, f, "Cancelled", instructions)
            order_id = Utils.order_id_gen(interaction.user.id)+"_O"
        
            embeds[-1].description += "\n**Order ID:** {0}".format(order_id)
            await channel.send("Order for {0}".format(interaction.user.name), embeds=embeds)
            embed = discord.Embed(title="Order placed!",
                                  description="Please wait for a staff member to process your order!",
                                  timestamp=datetime.datetime.now(),
                                  color=0x05f569)
            # Shows the user their new balance
            embed.description += "\n**New Balance:** ₹{0}".format(round(balance-amount ,2))
            embed.set_footer(text="Order ID: {0}".format(order_id))
            os.remove(limbo_path)
            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(embeds=embeds)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Cancels the order"""
            embed = discord.Embed(title="Order cancelled!",
                                  description="Your order has been cancelled!",
                                  color=0xc6be0f)
            # Sends a message in the channel
            await interaction.response.edit_message(embed=embed, view=None)

    # Creates the embed
    amount = Utils.get_cart_total(cart)
    # Checks if the user has enough balance to place the order
    embed = discord.Embed(title="Confirm your order",
                          description="Please confirm your order by clicking the button below.\nThis will clear your cart." ,
                          color=0x05f569)
    # Adds the total to the embed
    embed.set_footer(text="Check your cart before confirming!")
    # Adds the total to the embed
    embed.add_field(name="Total", value="₹{0}".format(amount), inline=False)
    embed.add_field(name = "Your Balance", value = "₹{0}".format(Actions().get_wallet(interaction.user.id)["data"]["balance"]), inline=False)
    po_view = PlaceOrderView()
    await interaction.response.send_message(embed=embed, view=po_view)


@place_order.error
async def place_order_error(interaction: discord.Interaction, error):
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



@tree.command(name="tip", description="Send us your tips")
@Checkers.is_dm()
@app_commands.describe(
    amount="The amount you want to tip us! We accept payments in INR",
)
async def tip(interaction: discord.Interaction,
              amount: app_commands.Range[float, 1, None]):
    """Function to send tips to the restaurant (bot owner) using invoices (powered by Coinbase Commerce)"""
    """To be used in DMs only, and real money is involved, so be careful"""
    class TipView(discord.ui.View):
        color = None

        def __init__(self):
            # Initializes the view
            super().__init__(timeout=30)
            self.value = None

        async def on_timeout(self):
            # Disables the buttons on timeout
            for child in self.children:
                child.disabled = True
            await self.message.edit(view=None)

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            from wallet import Actions
            embed = discord.Embed()
            wallet = Actions().get_wallet(interaction.user.id)
            # Checks if the user has enough balance to tip
            if wallet["data"]["balance"] < amount:
                embed.title = "Insufficient Balance!"
                embed.description = "You don't have enough balance in your wallet to send this tip!"
                embed.set_footer(
                    text="Please use /wallet reload to recharge your wallet.")
                embed.color = self.color
                await interaction.response.edit_message(embed=embed, view=None)
                return
            else:
                try:
                    # Tries to send the tip
                    Actions().remove_balance(interaction.user.id, amount)
                except Exception as e:
                    await interaction.response.edit_message(content=f"Error: {e}", embed=None, view=None)
                    return

                embed.title = "Tip sent!"
                # Shows the user their new balance
                new_bal = Actions().get_wallet(
                    interaction.user.id)['data']['balance']
                # Shows the user their new balance and the tip amount
                embed.description = f"Your tip of **₹ {amount}** has been sent to the restaurant!" + \
                    f"\nYour new balance is **₹ {new_bal}**"
                # Yeah THANKS for the support
                embed.set_footer(text="Thank you for your support!")
                embed.color = self.color
                await interaction.response.edit_message(embed=embed, view=None)
                channel = bot.get_channel(feedback_channel)
                # Sends a message in the feedback channel to show how much a user loves us
                fe = discord.Embed(
                    title="New Tip from {0}#{1}".format(
                        interaction.user.name, interaction.user.discriminator),
                    description=f"**Amount:** ₹ {amount}\n",
                    timestamp=datetime.datetime.now(),
                    color=self.color
                )
                if interaction.user.avatar is not None:
                    fe.set_thumbnail(url=interaction.user.avatar.url)
                # Sets the footer to the user's ID
                fe.set_footer(text="User ID: {0}".format(interaction.user.id))
                # I love you too, random patron
                await channel.send(embed=fe)

                return

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Cancels the tip
            embed = discord.Embed(title="Tip cancelled!",
                                  description="Your tip has been cancelled!",
                                  color=self.color)
            await interaction.response.edit_message(embed=embed, view=None)

    # Sends the tip confirmation message
    embed = discord.Embed(title="Confirm your tip",
                          description=f"Please confirm your tip of **₹ {amount}** by clicking the **Confirm** button below.",
                          color=Utils.random_hex_color())
    embed.set_footer(text="This will be deducted from your wallet balance.")
    view = TipView()
    view.color = embed.color
    await interaction.response.send_message(embed=embed, view=view)
    # Sets the message attribute of the view to the message sent
    view.message = await interaction.original_response()


@tip.error
async def tip_error(interaction: discord.Interaction, error):
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



@tree.command(name="menu", description="Explore the delicious menu of Los Pollos Hermanos")
@app_commands.describe(
    page="[Optional] The page number of the menu you want to see"
)
async def new_menu(interaction: discord.Interaction,
                   page: app_commands.Range[int, 1, None] = 1):
    """
    Displays the menu, paginated by 5 items per page.
    Also has a view for navigating the menu.
    """
    filepath = os.path.dirname(os.path.abspath(
        __file__)) + "/data/menus/newmenu.json"  # open the menu file
    # change the path to the one for your system
    filepath = Utils.path_finder(filepath)
    # load the menu
    menu = json.load(open(filepath, "r"))
    # divide the menu into pages of 5 items each
    menu_pages = Utils.list_divider(menu, 5)
    # flag to check if the page number is greater than the number of pages
    overflow_flag = False
    if page > len(menu_pages):  # if the page number is greater than the number of pages
        page = len(menu_pages)
        overflow_flag = True
    # get the embed for the page of the menu
    embed = Utils.menu_paginate(menu_pages, page)

    class NewView(discord.ui.View):
        """View for navigating the menu"""
        current_page = page
        max_pages = len(menu_pages)

        def __init__(self):
            super().__init__(timeout=120)
            # update the buttons on first load
            self.update_buttons()

        async def on_timeout(self) -> None:
            """Disables all buttons when the view times out"""
            item: discord.ui.Item  # type hinting
            for item in self.children:
                # disable all buttons if the view times out
                item.disabled = True
            self.message: discord.Message
            # edit the message to show that the menu has expired
            await self.message.edit(content="Menu Expired", view=self)

        def update_buttons(self):
            """Function to update the buttons when the page changes or the view is loaded"""
            if self.current_page == 1:
                self.prev.disabled = True
                self.prev.style = discord.ButtonStyle.grey
            else:
                self.prev.disabled = False
                self.prev.style = discord.ButtonStyle.green
            if self.current_page == self.max_pages:
                self.next.disabled = True
                self.next.style = discord.ButtonStyle.grey
            else:
                self.next.disabled = False
                self.next.style = discord.ButtonStyle.green

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.green)
        async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Previous button"""
            self.current_page -= 1  # decrement the current page
            self.update_buttons()
            embed = Utils.menu_paginate(menu_pages, self.current_page)
            # edit the message to show the previous page
            await interaction.response.edit_message(content=None, embed=embed, view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.green)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Next button"""
            self.current_page += 1  # increment the current page
            self.update_buttons()
            embed = Utils.menu_paginate(menu_pages, self.current_page)
            # edit the message to show the next page
            await interaction.response.edit_message(content=None, embed=embed, view=self)
    view = NewView()
    # Check if overflow_flag is True, if it is, send a message saying that the page doesn't exist and send the last page instead
    if overflow_flag:
        await interaction.response.send_message("That page doesn't exist! Here's the last page instead.", embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)
    # set the message attribute of the view to the message sent by the bot
    view.message = await interaction.original_response()
    # set the og_author attribute of the view to the user who sent the command
    view.og_author = interaction.user.id


def check_payments(inv):
    """checks the status of the invoice by calling the check method of the Payment class"""
    from payments import Payment
    # calls the check method of the Payment class
    status = Payment.check(inv['id'])
    return status.upper()  # returns the status in uppercase


@bot.event
async def on_message(message: discord.Message):
    """Event handler for messages, detects all messages and responds to ones that satisfy the conditions
    Most of this is for basic bot admin commands, you can remove this if you want, although I would recommend keeping it"""
    if message.author == bot.user:
        """If the message is sent by the bot, ignore it"""
        return
    if message.content.lower() == ";;jesse stop" and message.author.id in owners:
        """closes the bot if the message is ;;jesse stop and the author is in the owners list"""
        await message.reply("Okay Mr. White, I'm out!")
        print("Bot closed by", message.author)
        await bot.close()  # closes the bot

    if message.content.lower().startswith(";;void") and ((message.author.id in owners)):
        # Void the payments. Only for admins
        ls = message.content.split()
        for i in ls[1:]:
            try:
                # Manages to void for both Razorpay and Coinbase, so nice!
                from payments import Payment
                from razorpay_custom import Razorpay
                if len(i) < 10:
                    temp_s = Payment.void_payment(i)
                    await message.reply(f"{i} : {temp_s}")
                else:
                    temp_s = Razorpay.void_payment(i, True)
                    await message.reply(f"{i} : {temp_s}")
            except Exception as e:
                await message.reply("Error in **{0}**".format(i))
                print(e)
                pass
    
    if message.content.lower() == ";;jesse restart" and message.author.id in owners:
        # Restarts the bot. Only for admins. NOT RECOMMENDED TO USE UNLESS NECESSARY
        await message.reply("Okay Mr. White, I'm restarting!")
        print("Bot restarted by", message.author)
        await restart_program()

    if message.content.lower().startswith(";;del") and ((message.author.id in owners) or (message.guild is None)):
        """deletes messages with ids given after ;;del if the author is in the owners list"""
        ls = message.content.split()  # splits the message into a list, getting all the ids
        if len(ls) >= 2:
            for i in ls[1:]:
                try:
                    # fetches the message with the id
                    msg = await message.channel.fetch_message(i)
                    await msg.delete()  # deletes the message
                except:
                    pass
            try:
                await message.delete()
            except:
                pass


@tree.command(name="feedback", description="Send feedback to the owner")
async def feedback(interaction: discord.Interaction):
    # await interaction.response.defer()
    class FeedbackModal(discord.ui.Modal, title="Submit Feedback"):
        """The feedback modal"""
        fb_title = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Feedback Title",
            required=True,
            placeholder="Please give a title to your feedback"
        )

        content = discord.ui.TextInput(
            style=discord.TextStyle.long,
            label="Details",
            required=False,
            max_length=1200,
            placeholder="Give a description of your feedback if you please"
        )

        order = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Order ID",
            required=False,
            max_length=20,
            placeholder="Order ID if this is order related feedback"
        )

        async def on_submit(self, interaction: discord.Interaction):
            """When the user submits the feedback"""
            channel = bot.get_channel(feedback_channel)
            embeds = []
            embeds: typing.List[discord.Embed]  # type hinting
            self.user: discord.User
            user = self.user
            # First embed, contains the user's avatar, name, discriminator and id
            embeds.append(discord.Embed(
                title="Feedback from " + user.name + "#" + user.discriminator,
                description=f"UID : {user.id}",
                timestamp=datetime.datetime.now(),
                color=Utils.random_hex_color()
            ))
            if user.avatar is not None:
                embeds[0].set_thumbnail(url=user.avatar.url)

            # Second embed, contains the feedback title and description
            embeds.append(discord.Embed(
                title=self.fb_title.value,
                description=self.content.value,
                color=embeds[0].color
            ))

            # If the user has provided an order id, add it to the footer of the second embed
            if self.order.value != "":
                embeds[1].set_footer(text=f"Order ID : {self.order.value}")
            await channel.send(embeds=embeds)
            await interaction.response.send_message(f"Thank you for your feedback, {self.user.mention}!", ephemeral=True)

    modal = FeedbackModal()
    modal.user = interaction.user
    await interaction.response.send_modal(modal)

    pass


@feedback.error
async def feedback_error(interaction: discord.Interaction, error):
    await interaction.response.send_message("Something went wrong, please try again", ephemeral=True)


@tree.command(name="email", description="Add/change the email address associated with your account")
@app_commands.describe(
    email="The email address to be added"
)
@app_commands.checks.cooldown(1, 300, key=lambda i: i.user.id)
async def verify(interaction: discord.Interaction, email: str):
    """verifies the user's email address"""
    """if the user has a pre-existing email address, it will be replaced with the new one"""
    import re
    # Check if the email is valid by Regex
    if (re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        pass
    else:
        # Error message if email is invalid
        await interaction.response.send_message("Invalid email address", ephemeral=True)
        return

    # Generates a 6 character OTP
    otp = Utils.generate_otp(5, has_letters=True)

    # Location of the HTML file to be sent via email
    filepath = os.path.dirname(os.path.abspath(
        __file__)) + "/data/commands/otp.html"
    # Makes it fit your OS
    filepath = Utils.path_finder(filepath)
    # Saves it to a string and replaces the placeholders with the user's name and the OTP
    content = open(filepath, "r").read().format(interaction.user.name,
                                                interaction.user.name+"#"+interaction.user.discriminator, otp)
    await interaction.response.send_message(f"Sending OTP to your email address ({email})", ephemeral=True)
    msg = await interaction.original_response()
    #  Sends the email
    await mailobj.async_send_mail(email, interaction.user.name, "Your OTP for The-Parth", content)
    tries_left = 3
    # Creates a view to send in the message
    OTPView = Utils.OTPView(otp, tries_left)
    # Sets the label of the button to "Enter OTP" and the color to green
    OTPView.retry.label = "Enter OTP"
    OTPView.retry.style = discord.ButtonStyle.green
    OTPView.email = email
    OTPView.message = await interaction.original_response()
    # Sends the message
    await interaction.followup.edit_message(msg.id, content=f"Enter the OTP sent to {email}", view=OTPView)


@verify.error
async def verify_error(interaction: discord.Interaction, error):
    await interaction.response.send_message(str(error), ephemeral=True)


@tree.command(name="bot_info", description="Get basic information about the bot")
async def bot_info(interaction: discord.Interaction):
    """Command to check the bot's latency"""
    embed = discord.Embed(
        title="Pong!",
        description=f"**Latency:** {round(bot.latency * 1000)}ms" +
        f"\n**Guilds:** {len(bot.guilds)}",
        color=discord.Color.blurple()
    )

    time = datetime.datetime.timestamp(datetime.datetime.now()) - bot_started
    await interaction.response.send_message(
        "Bot is up and running for " + str(Utils.time_to_dhms(time)),
        embed=embed
    )
    msg = await interaction.original_response()
    await msg.add_reaction("🏓")
    
async def restart_program():
    """Restarts the current program, with file objects and descriptors"""
    import psutil
    try:
        p = psutil.Process(os.getpid())
        await bot.close()
        print ("Restarting", p.name(), p.pid)
        print ("Process has been killed")
        os.kill(p.pid, 9)
    except Exception as e:
        print(e)
    

    
def check_env():
    # Check set 1
    if os.getenv("TOKEN") == None:
        print("No discord bot token (TOKEN) is set in the .env file")
        exit(0)
    if os.getenv("CB_TOKEN") == None:
        print("No Coinbase token (CB_TOKEN) is set in the .env file")
        print("Bot starting, but will cause errors")
        validity["coinbase"] = False
        
    # Check set 2
    if os.getenv("ORDER_CHANNEL") == None:
        print("No order channel (ORDER_CHANNEL) is set in the .env file")
        exit(0)
    if os.getenv("FEEDBACK_CHANNEL") == None:
        print("No feedback channel (FEEDBACK_CHANNEL) is set in the .env file")
        exit(0)
        
    # Check set 3 : Email
    if os.getenv("EMAIL_SENDER") == None:
        print("No email sender (EMAIL_SENDER) is set in the .env file")
        exit(0)
    if os.getenv("EMAIL_PASSWORD") == None:
        print("No email password (EMAIL_PASSWORD) is set in the .env file")
        exit(0)
    if os.getenv("EMAIL_SMTP") == None:
        print("No email smtp (EMAIL_SMTP) is set in the .env file")
        exit(0)
    if os.getenv("EMAIL_PORT") == None:
        print("No email port (EMAIL_PORT) is set in the .env file")
        print("Defaulting to port 587")
        os.environ["EMAIL_PORT"] = "587"
        
    if os.getenv("EMAIL_SENDER_NAME") == None:
        print("No email sender (EMAIL_SENDER_NAME) is set in the .env file")
        print("Bot starting with default name")
        os.environ["EMAIL_SENDER_NAME"] = "OTP Bot"
    
    # Check set 4 : Razorpay
    if os.getenv("RPAY_KEY_ID") == None:
        print("No razorpay key id (RPAY_KEY_ID) is set in the .env file")
        print("Bot starting, but will cause errors")
        validity["razorpay"] = False
    if os.getenv("RPAY_KEY_SECRET") == None:
        print("No razorpay key secret (RPAY_KEY_SECRET) is set in the .env file")
        print("Bot starting, but will cause errors")
        validity["razorpay"] = False

check_env()
bot.run(os.getenv("TOKEN"))
