import discord
from discord import app_commands
import os
import asyncio
import csv
from extras import Checkers, Utils, Fun, Orders
from dotenv import load_dotenv
import typing
import datetime
import json


load_dotenv()


intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owners = [354546286634074115]


class CartActions(app_commands.Group):
    """Command group for cart actions, placed in the cart command group"""

    @app_commands.command(name="view", description="View your current cart")
    async def view(self, interaction: discord.Interaction):
        """View your current cart"""
        # Gets the filepath of the cart json file for the user, and creates it if it doesn't exist'
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)

        # Creates the file if it doesn't exist
        if not os.path.isfile(filepath):
            with open(filepath, "w") as f:
                json.dump({}, f, indent=2)
        # Loads the file
        f = json.load(open(filepath, "r"))

        # Checks if the cart is empty
        if f == {}:
            embed = discord.Embed(title="Your Cart is Empty",
                                  description="Your cart is empty, add something to it!",
                                  color=0x57eac8)
            embed.set_footer(text="If you need help, use /help")

            # Tells the user that their cart is empty
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            """Now that we know the cart isn't empty, we can start formatting the menu string"""
            """Menu string is a list of strings, each string is a page of the menu"""
            """Pages are used so that the menu doesn't get too long and discord doesn't complain, 12 items per page"""
            menu_string = [""]*9
            item_count = 0
            # Formats the menu string in the format of "Item(Price) x Quantity..........Total"
            for item in f:
                # Adds the item to the menu string
                item_count += 1
                menu_string[int((item_count)/12.0001)] += "{4}. **{0}**(*₹{1}*) x **{2}**..........**₹{3}**\n".format(
                    item, f[item]['rate'], f[item]['quantity'], f[item]['rate'] * f[item]['quantity'], item_count)

            # Creates the embed
            embeds = []
            for i in menu_string:
                # Creates the embed list for each page by adding the menu string elemnts to the embed
                if i == "":
                    # Breaks if the page is empty
                    break
                embed = discord.Embed(description=i, color=0x57eac8)

                # Adds the embed to the embed list
                embeds.append(embed)

            # Sets the title of the first embed
            embeds[0].title = "Your Cart"
            # Sets the footer of the last embed to
            embeds[-1].set_footer(text="Use /cart build to make changes to your cart")
            # Adds the total to the last embed
            embeds[-1].description += "\n**Total: ₹{0}**".format(
                Utils.get_cart_total(f))

            # Sends the cart
            await interaction.response.send_message(embeds=embeds, ephemeral=True)
            return

    @view.error
    async def view_error(self, interaction: discord.Interaction, error):
        """Error handler for the view command"""
        embed = discord.Embed(title="Error!",
                              description=str(error),
                              color=0xc6be0f)
        embed.set_footer(text="Please message staff")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="build", description="Build your cart!")
    async def build(self, interaction:
                    discord.Interaction,
                    page: app_commands.Range[int, 1, None] = 1):
        """Build your cart!"""
        """Took my beloved life to figure out how stuff works"""
        # Gets the filepath of the menu json file, and loads it
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + "/data/menus/newmenu.json"
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)
        with open(filepath, "r") as f:
            menu = json.load(f)

        # Gets the filepath of the cart json file for the user, and creates it if it doesn't exist
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
        # Makes it fit your OS
        filepath = Utils.path_finder(filepath)

        # Creates the cart if it doesn't exist
        if not os.path.isfile(filepath):
            json.dump({}, open(filepath, "w"), indent=2)
        menu_pages = Utils.list_divider(menu, 10)
        overflow_flag = False  # Flag to check if the page number is too high

        # Checks if the page number is too high
        if page > len(menu_pages):
            page = len(menu_pages)
            overflow_flag = True
        embed = Utils.cartbuilder_paginate(menu_pages, page)

        class BuildView(discord.ui.View):
            """Special view for the build command, super high level tactics"""
            current_page = page
            max_pages = len(menu_pages)
            initial_call = True  # Flag to check if it's the first time the view is called

            def __init__(self):
                super().__init__(timeout=90)
                if self.initial_call:
                    # Updates the buttons for the first time
                    self.update_pages()
                    self.initial_call = False

            async def on_timeout(self) -> None:
                """Called when the view times out"""
                item: discord.ui.Item  # type hinting

                # Disables all the buttons in the view
                for item in self.children:
                    item.disabled = True
                self.message: discord.Message

                # Edits the message to say that the cart has expired
                await self.message.edit(content="Cart Expired", view=self)

            def update_pages(self):
                """Updates the buttons in the view when the page is changed, also called when the view is initialized"""
                # Gets the filepath of the cart json file for the user, and creates it if it doesn't exist
                filepath = os.path.dirname(os.path.abspath(
                    __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
                # Makes it fit your OS
                filepath = Utils.path_finder(filepath)

                # Creates the cart if it doesn't exist
                if not os.path.isfile(filepath):
                    json.dump({}, open(filepath, "w"), indent=2)

                # Loads the cart
                cart = json.load(open(filepath, "r"))

                # Checks page number and updates the buttons accordingly
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

                # Options for the select menu, updates the description to show the quantity in the cart
                ls = []
                for i in menu_pages[self.current_page - 1]:
                    ls.append(discord.SelectOption(
                        label=i['ITEM'] + " : ₹{0}".format(i['COST']),
                        description="In Cart : {0}".format(
                            cart[i['ITEM']]['quantity'] if i['ITEM'] in cart else 0),
                        value=i['ITEM']
                    )
                    )

                # Updates the select menu options
                self.select_item.options = ls

                # Sets the selected option to None if the page is changed
                if len(self.select_item.values) != 0:
                    self.select_item.values[0] = None

                # Updates the label of the item in cart button if the page is changed
                self.in_cart.label = "Select an item"
                self.in_cart.disabled = True

            def update_carts(self, action):
                """Updates the cart when an item is added or removed, or the select menu option is changed"""
                # Gets the filepath of the cart json file for the user, and creates it if it doesn't exist
                filepath = os.path.dirname(os.path.abspath(
                    __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
                # Makes it fit your OS
                filepath = Utils.path_finder(filepath)

                # Creates the cart if it doesn't exist
                if not os.path.isfile(filepath):
                    json.dump({}, open(filepath, "w"), indent=2)

                # Loads the cart
                cart = json.load(open(filepath, "r"))

                if action == "ADD":
                    """Adds an item to the cart"""
                    if self.select_item.values[0] not in cart:
                        rate = None
                        item = None
                        for i in menu_pages[self.current_page - 1]:
                            # Gets the rate of the item
                            if i['ITEM'] == self.select_item.values[0]:
                                rate = i['COST']
                                item = i['ITEM']
                                break
                        # Adds the item to the cart
                        cart[self.select_item.values[0]] = {
                            "rate": int(rate.strip()),
                            "quantity": 1
                        }
                    else:
                        # If the item is already in the cart, increases the quantity
                        cart[self.select_item.values[0]]["quantity"] += 1

                    # Updates the label of the item in cart button
                    self.in_cart.label = "In Cart: {0}".format(
                        cart[self.select_item.values[0]]["quantity"])

                elif action == "REMOVE":
                    """Checks if the item is in the cart, and removes it if the quantity is 1, else decreases the quantity"""
                    if self.select_item.values[0] in cart:
                        if cart[self.select_item.values[0]]["quantity"] == 1:
                            del cart[self.select_item.values[0]]
                            self.in_cart.label = "In Cart: {0}".format(0)
                        else:
                            cart[self.select_item.values[0]]["quantity"] -= 1
                            self.in_cart.label = "In Cart: {0}".format(
                                cart[self.select_item.values[0]]["quantity"])

                elif action == "CLEAR":
                    """Clears the cart, not used yet"""
                    cart = {}

                elif action == "SELECT":
                    """Selects an item in the cart, updates the label of the item in cart button"""
                    if self.select_item.values[0] in cart:
                        self.in_cart.label = "In Cart: {0}".format(
                            cart[self.select_item.values[0]]["quantity"])
                    else:
                        self.in_cart.label = "In Cart: {0}".format(0)

                    self.in_cart.disabled = False
                for i in self.select_item.options:
                    # Updates the description of the select menu options for each item showing the quantity in the cart
                    i.description = "In Cart : {0}".format(cart[i.label.split(
                        " : ")[0]]['quantity'] if i.label.split(" : ")[0] in cart else 0)

                # Saves the cart
                json.dump(cart, open(filepath, "w+"), indent=2)

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.green, row=2)
            async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Previous button, goes to the previous page"""
                if not Checkers.is_dm_2(interaction):
                    if interaction.user.id is not self.og_author:
                        # Checks if the user is the original author of the message
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return
                self.current_page -= 1  # Decreases the page number
                self.update_pages()  # Updates the buttons

                # Gets the embed for the page
                embed = Utils.cartbuilder_paginate(
                    menu_pages, self.current_page)

                # Edits the message with the new embed and view
                await interaction.response.edit_message(content=None, embed=embed, view=self)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.green, row=2)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Next button, goes to the next page"""
                if not Checkers.is_dm_2(interaction):
                    if interaction.user.id is not self.og_author:
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return
                self.current_page += 1  # Increases the page number
                self.update_pages()  # Updates the buttons

                # Gets the embed for the page
                embed = Utils.cartbuilder_paginate(
                    menu_pages, self.current_page)

                # Edits the message with the new embed and view
                await interaction.response.edit_message(content=None, embed=embed, view=self)

            @discord.ui.select(placeholder="Select an option", max_values=1, min_values=1, row=0, options=[
                discord.SelectOption(
                    label="Option 1", emoji="👌", description="Placeholder 1", value=None, default=True),
            ])
            async def select_item(self, interaction: discord.Interaction, select: discord.ui.Select):
                """Select menu, selects an item"""
                print(interaction.user.id)
                if not (Checkers.is_dm_2(interaction)):
                    if (interaction.user.id is not self.og_author):
                        # Checks if the user is the original author of the message
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return

                # Resets the default value of the select menu options
                for i in self.select_item.options:
                    i.default = False

                # Sets the default value of the selected option to the newly selected option
                for i in self.select_item.options:
                    if i.value == self.select_item.values[0]:
                        i.default = True

                # Updates the label of the item in cart button
                self.update_carts("SELECT")

                # Edits the message with the new view
                await interaction.response.edit_message(view=self)

            @discord.ui.button(label="Remove item", style=discord.ButtonStyle.red, row=1)
            async def remove_item(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Remove item button, removes the selected item from the cart"""
                if not (Checkers.is_dm_2(interaction)):
                    if interaction.user.id is not self.og_author:
                        # Checks if the user is the original author of the message
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return

                # If no item is selected, sends an ephemeral message
                if len(self.select_item.values) == 0:
                    await interaction.response.send_message("Please select an item!", ephemeral=True)
                    return

                # If an item was selected before from a previous page, but the current page doesn't have that item, sends an ephemeral message
                if self.select_item.values[0] is None:
                    await interaction.response.send_message("Please select an item!", ephemeral=True)
                    return

                # Updates the cart
                self.update_carts("REMOVE")

                # Edits the message with the new view
                await interaction.response.edit_message(view=self)

            @discord.ui.button(label="Select an Item", style=discord.ButtonStyle.grey, row=1, disabled=True)
            async def in_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Shows the quantity of the selected item in the cart, can't be clicked"""
                # In the future, it might be possible to click this button to show the details of the currently selected item
                embed = Utils.item_describe(
                    menu_pages[self.current_page - 1], self.select_item.values[0])

                await interaction.response.send_message(embed=embed, ephemeral=True)

            @discord.ui.button(label="Add item", style=discord.ButtonStyle.green, row=1)
            async def add_item(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Add item button, adds the selected item to the cart"""
                if not (Checkers.is_dm_2(interaction)):
                    if interaction.user.id is not self.og_author:
                        # Checks if the user is the original author of the message
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return

                # If no item is selected, sends an ephemeral message
                if len(self.select_item.values) == 0:
                    await interaction.response.send_message("Please select an item!", ephemeral=True)
                    return

                # If an item was selected before from a previous page, but the current page doesn't have that item, sends an ephemeral message
                if self.select_item.values[0] is None:
                    await interaction.response.send_message("Please select an item!", ephemeral=True)
                    return

                # Updates the cart
                self.update_carts("ADD")

                # Edits the message with the new view
                await interaction.response.edit_message(view=self)

        # Creates the view
        builder_view = BuildView()
        # If the page number is greater than the number of pages, sends a message saying that
        # the page doesn't exist and the last page is shown instead
        if overflow_flag:
            await interaction.response.send_message("That page doesn't exist! Here's the last page instead.", embed=embed, view=builder_view)
        else:
            await interaction.response.send_message(embed=embed, view=builder_view)

        # Sets the message attribute of the view to the original response
        builder_view.message = await interaction.original_response()
        # Sets the original author of the view to the user who sent the command
        builder_view.og_author = interaction.user.id

        # Debugging purposes
        print(builder_view.og_author)

    @build.error
    async def build_error(self, interaction: discord.Interaction, error):
        """Error handler for the view command"""
        embed = discord.Embed(title="Error!",
                              description=str(error),
                              color=0xc6be0f)
        embed.set_footer(text="Please message staff")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear", description="Clears your cart")
    async def clear_cart(self, interaction: discord.Interaction):
        """Clears the user's cart"""
        class ConfirmView(discord.ui.View):
            """Confirmation view for clearing the cart"""

            def __init__(self):
                super().__init__(timeout=30.0)

            async def on_timeout(self):
                for i in self.children:
                    i.disabled = True
                    await self.message.edit(view=self)

            @discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
            async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                """Yes button, clears the cart"""
                # Clears the cart
                if not (Checkers.is_dm_2(interaction)):
                    if interaction.user.id is not self.og_author:
                        # Checks if the user is the original author of the message
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return
                filepath = os.path.dirname(os.path.abspath(
                    __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
                # Makes it fit your OS
                filepath = Utils.path_finder(filepath)
                # Edits the message with the new view
                if os.path.exists(filepath):
                    os.remove(filepath)
                embed = discord.Embed(title="Cart cleared!",
                                      description="Your cart has been cleared!",
                                      color=0xc6be0f)
                for i in self.children:
                    i.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="No", style=discord.ButtonStyle.green)
            async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                """No button, cancels the operation"""
                # Cancels the operation
                if not (Checkers.is_dm_2(interaction)):
                    if interaction.user.id is not self.og_author:
                        await interaction.response.send_message("You can't do that!", ephemeral=True)
                        return
                embed = discord.Embed(title="Cart not cleared!",
                                      description="Your cart has not been cleared!",
                                      color=0xc6be0f)
                for i in self.children:
                    i.disabled = True
                await interaction.response.edit_message(embed=embed, view=self)

        embed = discord.Embed(title="Are you sure?",
                              description="Are you sure you want to clear your cart?",
                              color=0xc6be0f)
        embed.set_footer(text="This action cannot be undone!")
        confirmv = ConfirmView()
        await interaction.response.send_message(embed=embed, view=confirmv, ephemeral=True)
        confirmv.message = await interaction.original_response()
        confirmv.og_author = interaction.user.id


@bot.event
async def on_ready():
    """When the bot is ready"""
    print("Bot is ready, logged in as {0.user}".format(bot))
    try:
        # Creates the slash command tree
        cart = CartActions(name="cart", description="Views your cart")
        # Adds the cart command group to the tree
        tree.add_command(cart)
        # Syncs the tree globally
        await tree.sync()
    except:
        pass

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
    embed = Utils.help_embed(command)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="place_order", description="Confirm and place your order! (DMs only)")
@Checkers.is_dm()
@app_commands.describe(
    email="Your email address to which the invoice must be sent!"
)
async def place_order(interaction: discord.Interaction, email: str):
    """Places the order"""
    filepath = os.path.dirname(os.path.abspath(
        __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
    # Makes it fit your OS
    filepath = Utils.path_finder(filepath)

    # Creates the cart if it doesn't exist
    if not os.path.isfile(filepath):
        json.dump({}, open(filepath, "w"), indent=2)

    # Opens the cart
    cart = json.load(open(filepath, "r"))

    import re
    if (re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        pass
    else:
        # Error message if email is invalid
        await interaction.response.send_message("Invalid email address!", ephemeral=True)
        return

    # If the cart is empty, sends an ephemeral message
    if cart == {}:
        await interaction.response.send_message("Your cart is empty!", ephemeral=True)
        return

    class PlaceOrderView(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Confirms the order"""
            order_channel = bot.get_channel(1090984464261320724)
            # Checks if the cart is empty
            if cart == {}:
                embed = discord.Embed(title="Your Cart is Empty",
                                      description="Your cart is empty, add something to it!",
                                      color=0x57eac8)
                embed.set_footer(text="If you need help, use /help")

                await order_channel.send(embed=embed)
                return
            else:
                """Now that we know the cart isn't empty, we can start formatting the menu string"""
                """Menu string is a list of strings, each string is a page of the menu"""
                """Pages are used so that the menu doesn't get too long and discord doesn't complain, 20 items per page"""
                menu_string = [""]*9
                item_count = 0
                total_items = 0
                f = cart
                # Formats the menu string in the format of "Item(Price) x Quantity..........Total"
                for item in f:
                    # Adds the item to the menu string
                    item_count += 1
                    total_items += f[item]['quantity']
                    menu_string[int((item_count)/20.0001)] += "{4}. **{0}**(*₹{1}*) x **{2}**..........**₹{3}**\n".format(
                        item, f[item]['rate'], f[item]['quantity'], f[item]['rate'] * f[item]['quantity'], item_count)

                # Creates the embed
                embeds = []
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
                    Utils.get_cart_total(f))
            timestamp_of_order = int(datetime.datetime.utcnow().timestamp())
            limbo_path = os.path.dirname(os.path.abspath(
                __file__)) + "\data\carts\limbo\{0}".format(
                    Utils.filename_gen(str(timestamp_of_order)[-1:-5:-1][::-1],
                                       str(interaction.user.id),
                                       "json"))
            limbo_path = Utils.path_finder(limbo_path)
            json.dump(cart, open(limbo_path, "w"), indent=2)
            os.remove(filepath)
            int_channel = interaction.channel
            from payments import Payment
            amount = Utils.get_cart_total(cart)/100
            memo = str(interaction.user.id) + \
                f": Order from {str(interaction.user)} of INR {amount} at {timestamp_of_order}"
            # Create the invoice using the Coinbase Commerce API in payments.py
            inv: dict
            if amount == 0:
                await interaction.response.send_message("We do not accept orders for free items only!", ephemeral=True)
                return
            try:
                inv = Payment.invoice(str(interaction.user),
                                      email, amount, "INR", memo)
            except Exception as e:
                await interaction.response.send_message("Error creating invoice, please try again later!", ephemeral=True)
                json.dump(json.load(open(limbo_path, "r")),
                          open(filepath, "w"), indent=2)
                os.remove(limbo_path)
                return

            # Make an invoice with a button to pay the invoice
            embed = discord.Embed(title=f"Invoice {inv['code']} created!",
                                  description=f"Payment link : {inv['url']}",
                                  color=0xc6be0f)
            embed.add_field(name="Amount", value=f"INR {amount}", inline=True)
            embed.add_field(name="Order Code", value=inv['code'], inline=True)
            embed.add_field(name="Tx. ID", value=str(inv['id']), inline=True)
            view = discord.ui.View()
            view.add_item(item=discord.ui.Button(
                label="Make Payment", url=inv['url']))

            # Send the invoice to the user
            await interaction.response.edit_message(embed=embed, view=view)
            msg = await interaction.original_response()
            count = 0
            flag_check_coming = False
            while True:
                """Checks if the invoice has been paid every 10 seconds"""
                stats = check_payments(inv)
                count += 1
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
                    await msg.reply(embed=embed)

                if stats == 'PAID':
                    """Case when the payment is complete, and the user hasn't been notified yet"""
                    embed = discord.Embed(title=f"Invoice {inv['code']} Paid Successfully!",
                                          description=f"View Charge : {inv['url']}",
                                          color=0x20e364)
                    embed.add_field(
                        name="Amount", value=f"INR {amount}", inline=True)
                    embed.add_field(name="Order Code",
                                    value=inv['code'], inline=True)
                    embed.add_field(name="Tx. ID", value=str(
                        inv['id']), inline=True)
                    embed.set_footer(
                        text="Thank you for shopping with us! See you soon!")
                    view = discord.ui.View()
                    view.add_item(item=discord.ui.Button(
                        label="View Charge", url=inv['url']))
                    await msg.reply(embed=embed, view=view)
                    await order_channel.send(embeds=embeds)
                    await int_channel.send(embed=discord.Embed(
                        title="Order Placed!",
                        description=f"Your order has been placed successfully!",
                        color=0x20e364)
                    )

                    break  # break out of the loop

                if stats == 'VOID':
                    """Case when the invoice is voided, and the user hasn't been notified yet"""
                    embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                          description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                          color=0xd62d2d)
                    embed.set_footer(
                        text="This is usually due to staff interruption.")
                    await msg.reply(embed=embed)
                    json.dump(json.load(open(limbo_path, "r")),
                              open(filepath, "w"), indent=2)
                    break  # break out of the loop

                if stats == 'EXPIRED':
                    """Case when the invoice is expired, and the user hasn't been notified yet"""
                    embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                          description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                          color=0xd62d2d)
                    embed.set_footer(
                        text="You can try again with a new invoice.")
                    await msg.reply(embed=embed)
                    json.dump(json.load(open(limbo_path, "r")),
                              open(filepath, "w"), indent=2)
                    break  # break out of the loop

                if stats == 'UNRESOLVED':
                    """Case when the invoice is in an unresolved state, and the user hasn't been notified yet"""
                    embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                          description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                          color=0xd62d2d)
                    embed.set_footer(
                        "This may be due to underpayment or overpayment.")
                    json.dump(json.load(open(limbo_path, "r")),
                              open(filepath, "w"), indent=2)
                    await msg.reply(embed=embed)
                    break  # break out of the loop

                # sleep for 10 seconds before checking again
                await asyncio.sleep(10)

            # Sends a message in the channel
            os.remove(limbo_path)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Cancels the order"""
            embed = discord.Embed(title="Order cancelled!",
                                  description="Your order has been cancelled!",
                                  color=0xc6be0f)
            # Sends a message in the channel
            await interaction.response.edit_message(embed=embed, view=None)

    # Creates the embed
    embed = discord.Embed(title="Confirm your order",
                          description="Please confirm your order by clicking the button below.\nThis will clear your cart.",
                          color=0x05f569)
    embed.set_footer(text="Check your cart before confirming!")
    po_view = PlaceOrderView()
    await interaction.response.send_message(embed=embed, view=po_view)


@place_order.error
async def place_order_error(interaction: discord.Interaction, error):
    """ Custom error handler for the place_order command."""
    # Embed to send in the response
    embed = discord.Embed(title="Works in DMs only!",
                          description="Please direct message the bot.",
                          color=0xc6be0f)

    # Create a view with a button that links to the DM channel
    view = discord.ui.View()
    dm = await interaction.user.create_dm()
    view.add_item(item=discord.ui.Button(label="Go to DMs", url=dm.jump_url))

    # Send the response
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


@tree.command(name="tip", description="Send us your tips")
@Checkers.is_dm()
@app_commands.describe(
    amount="The amount you want to tip us! We accept payments in INR",
    email="Your email address to which the invoice must be sent!"
)
async def tip(interaction: discord.Interaction,
              amount: app_commands.Range[int, 1, None],
              email: str):
    """Function to send tips to the restaurant (bot owner) using invoices (powered by Coinbase Commerce)"""
    """To be used in DMs only, and real money is involved, so be careful"""

    # check if email is valid using regex
    import re
    if (re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        pass
    else:
        # Error message if email is invalid
        await interaction.response.send_message("Invalid email address!", ephemeral=True)
        return

    # Commented out for testing purposes
    # await interaction.response.send_message(f"A measly {amount}, sadge, sent invoice to {email},{interaction.user}")
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
    embed.add_field(name="Amount", value=f"INR {amount}", inline=True)
    embed.add_field(name="Order Code", value=inv['code'], inline=True)
    embed.add_field(name="Tx. ID", value=str(inv['id']), inline=True)
    view = discord.ui.View()
    view.add_item(item=discord.ui.Button(label="Make Payment", url=inv['url']))

    # Send the invoice to the user
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    count = 0
    flag_check_coming = False
    while True:
        """
        Check for payment status every 10 seconds, and notify the user when the payment is complete
        done using the Coinbase Commerce API in payments.py
        this function below is a coroutine, so it can be awaited
        this makes sure that the bot doesn't get blocked while waiting for the payment to complete
        """
        stats = check_payments(inv)
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
            await msg.reply(embed=embed)

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
            await msg.reply(embed=embed, view=view)
            break  # break out of the loop

        if stats == 'VOID':
            """Case when the invoice is voided, and the user hasn't been notified yet"""
            embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                  color=0xd62d2d)
            embed.set_footer(
                text="This is usually due to staff interruption.")
            await msg.reply(embed=embed)
            break  # break out of the loop

        if stats == 'EXPIRED':
            """Case when the invoice is expired, and the user hasn't been notified yet"""
            embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                  color=0xd62d2d)
            embed.set_footer(text="You can try again with a new invoice.")
            await msg.reply(embed=embed)
            break  # break out of the loop

        if stats == 'UNRESOLVED':
            """Case when the invoice is in an unresolved state, and the user hasn't been notified yet"""
            embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                  color=0xd62d2d)
            embed.set_footer("This may be due to underpayment or overpayment.")
            await msg.reply(embed=embed)
            break  # break out of the loop

        # sleep for 10 seconds before checking again
        await asyncio.sleep(10)


@tip.error
async def tip_error(interaction: discord.Interaction, error):
    """If the user is not in DMs, send them a message to go to DMs."""
    # Embed to send to the user
    embed = discord.Embed(title="Works in DMs only!",
                          description="Please direct message the bot.",
                          color=0xc6be0f)
    embed.set_footer(text="If this was in DMs, an inadvertent error occured.")
    # View to send to the user containing a button to go to DMs
    view = discord.ui.View()
    dm = await interaction.user.create_dm()
    view.add_item(item=discord.ui.Button(label="Go to DMs", url=dm.jump_url))
    # Send the message with the embed and view
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


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
            super().__init__(timeout=30)
            # update the buttons on first load
            self.update_buttons()

        async def on_timeout(self) -> None:
            """Disables all buttons when the view times out"""
            item: discord.ui.Item  # type hinting
            for item in self.children:
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


@tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    """Command to check the bot's latency"""
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Pong!",
            description=f"**Latency:** {round(bot.latency * 1000)}ms",
            color=discord.Color.blurple()
        )
    )
    msg = await interaction.original_response()
    msg.add_reaction("🏓")


@bot.event
async def on_message(message: discord.Message):
    """Event handler for messages, detects all messages and responds to ones that satisfy the conditions"""
    if message.author == bot.user:
        """If the message is sent by the bot, ignore it"""
        return
    if message.content.lower() == ";;jesse stop" and message.author.id in owners:
        """closes the bot if the message is ;;jesse stop and the author is in the owners list"""
        await message.reply("Okay Mr. White, I'm out!")
        await bot.close()  # closes the bot
    if message.content.lower().startswith(";;del") and ((message.author.id in owners) or (message.guild is None)):
        print(message.guild)
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


@tree.command(name="email", description="Your email address")
async def email(interaction: discord.Interaction):
    """sends the email to the user"""
    await interaction.response.send_message("k:", ephemeral=True)
    print((interaction.user.email))


@tree.command(name="feedback", description="Send feedback to the owner")
async def feedback(interaction: discord.Interaction):
    #await interaction.response.defer()
    class FeedbackModal(discord.ui.Modal, title="Submit Feedback"):
        fb_title = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label="Feedback Title",
            required= True,
            placeholder="Please give a title to your feedback"
        )

        content = discord.ui.TextInput(
            style= discord.TextStyle.long,
            label="Details",
            required=False,
            max_length=1200,
            placeholder="Give a description of your feedback if you please"
        )
        
        order = discord.ui.TextInput(
            style = discord.TextStyle.short,
            label = "Order ID",
            required = False,
            max_length = 20,
            placeholder = "Order ID if this is order related feedback"
        )

        async def on_submit(self, interaction: discord.Interaction):
            channel = bot.get_channel(1100058856119345303)
            embeds = []
            embeds : typing.List[discord.Embed]
            self.user : discord.User
            user = self.user
            embeds.append(discord.Embed(
                title = "Feedback from " + user.name + "#" + user.discriminator,
                description= f"UID : {user.id}",
                timestamp= datetime.datetime.now(),
                color= Utils.random_hex_color()
            ))
            embeds.append(discord.Embed(
                title= self.fb_title.value,
                description= self.content.value,
                color = embeds[0].color
            ))
            if self.order.value is not "":
                embeds[1].set_footer(text=f"Order ID : {self.order.value}")
            await channel.send(embeds=embeds)
            await interaction.response.send_message(f"Thank you for your feedback, {self.user.mention}!", ephemeral=True)

    modal = FeedbackModal()
    modal.user = interaction.user
    await interaction.response.send_modal(modal)

    pass


@tree.command(name="tictactoe", description="plays tictactoe")
async def tic(ctx: discord.Interaction):
    """plays tictactoe with the user in a view"""
    await ctx.response.send_message('Tic Tac Toe: X goes first', view=Fun.TicTacToe())
bot.run(os.getenv("TOKEN"))
