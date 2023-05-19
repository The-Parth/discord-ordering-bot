import discord
from discord import app_commands
from extras import Utils, Checkers
import os, json
import pymongo

client = pymongo.MongoClient(os.environ.get("MONGO_URI"))
db = client.DiscordCartDB
cartdb = db.carts


class CartActions(app_commands.Group):
    """Command group for cart actions, placed in the cart command group"""
    def __init__(self, bot: discord.Client):
        super().__init__(name="cart", description="Perform actions on your cart")
        self.bot = bot

    @app_commands.command(name="view", description="View your current cart")
    async def view(self, interaction: discord.Interaction):
        """View your current cart"""
        # Gets the cart from mongodb
        cart = cartdb.find_one({"_id": str(interaction.user.id)})

        # Creates the file if it doesn't exist
        if cart is None:
            cart = {
                "_id": str(interaction.user.id),
                "user_id": str(interaction.user.id),
                "cart": {},
            }
            cartdb.insert_one(cart)
            f = cart
        else:
            f = Utils.to_json(cart)
        
        f  = f["cart"]

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

        # Gets the filepath of the cart from mongodb and loads it
        cart = cartdb.find_one({"_id": str(interaction.user.id)})
        if cart is None:
            cart = {
                "_id": str(interaction.user.id),
                "user_id": str(interaction.user.id),
                "cart": {},
            }
            cartdb.insert_one(cart)
        else:
            cart = Utils.to_json(cart)
        cart = cart["cart"]
        
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
                cart = cartdb.find_one({"_id": str(interaction.user.id)})
                if cart is None:
                    cart = {
                        "_id": str(interaction.user.id),
                        "user_id": str(interaction.user.id),
                        "cart": {},
                    }
                    cartdb.insert_one(cart)
                else:
                    cart = Utils.to_json(cart)
                cart = cart["cart"]

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
                # Gets the cart from the database
                cart = cartdb.find_one({"_id": str(interaction.user.id)})
                if cart is None:
                    cart = {
                        "_id": str(interaction.user.id),
                        "user_id": str(interaction.user.id),
                        "cart": {},
                    }
                    cartdb.insert_one(cart)
                else:
                    cart = Utils.to_json(cart)
                cart = cart["cart"]

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
                        rate : float
                        rate = float(rate.strip())
                        cart[self.select_item.values[0]] = {
                            "rate": round(rate, 2),
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

                # Saves the cart to the database
                cartdb.update_one({"_id": str(interaction.user.id)}, {
                    "$set": {"cart": cart}})

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
                #print(interaction.user.id)
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
        #print(builder_view.og_author)

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
                # deletes the cart from mongo
                cartdb.delete_one({"_id": str(interaction.user.id)})
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
