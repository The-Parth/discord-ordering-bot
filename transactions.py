import discord
import json
import os
import asyncio
import datetime
import typing
from discord import app_commands
from wallet import Actions
from extras import Utils, Checkers


class Transactions(app_commands.Group):

    def __init__(self, bot):
        super().__init__(name="transactions", description="Commands for managing transactions")
        self.bot = bot
        self.actions_obj = Actions()

    def transactions_paginate(self, transactions: dict, order_list: list) -> discord.Embed:
        embed = discord.Embed(
            title="Recharge History",
            description="",
            color=0x5481e8,
            timestamp=datetime.datetime.now()
        )
        for order_id in order_list:
            order = transactions[order_id]
            data = self.get_idbased_transaction_data(order_id)
            embed.description += f"**{order_id}** -- **Rs. {order['amount']}**\n"
            embed.description += f"Status: *{order['status']}*\nTime: *{data['time']}*\n\n"

        return embed

    class Autocompletes:
        async def get_reload_ids(self, interaction: discord.Interaction, id: str = None):
            transactions = Actions().get_transactions(interaction.user.id)[
                "data"]["reloads"]
            transactions: typing.Dict[str, str]
            keys = transactions.keys()
            if id is None:
                return [discord.app_commands.Choice(name=i, value=i) for i in keys][::-1][:25]
            return [discord.app_commands.Choice(name=i, value=i) for i in keys if id.lower() in i.lower()][::-1][:25]

        async def get_order_ids(self, interaction: discord.Interaction, id: str = None):
            transactions = Actions().get_transactions(interaction.user.id)[
                "data"]["orders"]
            transactions: typing.Dict[str, str]
            keys = transactions.keys()
            if id is None:
                return [discord.app_commands.Choice(name=i, value=i) for i in keys][::-1][:25]
            return [discord.app_commands.Choice(name=i, value=i) for i in keys if id.lower() in i.lower()][::-1][:25]

    def get_idbased_transaction_data(self, id: str):
        import time
        ls = id.split('_')
        t = ""
        if ls[2].upper() == 'O':
            t = 'ORDER'
        elif ls[2].upper() == 'R':
            t = 'RELOAD'
        elif ls[2].upper() == 'RC':
            t = 'RELOAD_COINBASE'
        elif ls[2].upper() == 'RR':
            t = 'RELOAD_RAZORPAY'
        timestamp = int(ls[0], 36)

        data = {
            "user": int(ls[1], 36),
            "type": t,
            "timestamp": timestamp,
            "time": datetime.datetime.fromtimestamp(timestamp - time.timezone).strftime('%A, %d %B, %Y at %H:%M:%S'),
            "timezone": time.timezone
        }
        return data

    def embed_for_reloads(self, transactions: dict, id: str) -> discord.Embed:
        embed = discord.Embed(
            title="Recharge Details",
            color=0x5481e8
        )
        data = self.get_idbased_transaction_data(id)
        embed.description = f"**ID:** {id}\n**Type:** "+data['type']
        embed.add_field(name="Amount", value=str(
            transactions[id]['amount']), inline=True)
        embed.add_field(name="Status", value=str(
            transactions[id]['status']), inline=True)
        embed.add_field(name="Invoice", value=str(
            transactions[id]['invoice']), inline=True)
        embed.set_footer(text=f"User ID: {data['user']}")
        embed.timestamp = datetime.datetime.fromtimestamp(
            data['timestamp'] - data['timezone'])
        view = discord.ui.View()
        payment_url = ""
        if data['type'] == "RELOAD_COINBASE":
            payment_url = f"https://commerce.coinbase.com/invoices/{transactions[id]['invoice']}"
        elif data['type'] == "RELOAD_RAZORPAY":
            from razorpay_custom import Razorpay
            payment_url = Razorpay.get_link(transactions[id]['invoice'])
        if transactions[id]['status'] == "OPEN" or transactions[id]['status'] == "VIEWED":
            embed.color = 0x2fe466
            button = discord.ui.Button(
                label="Pay", url=payment_url)
            view.add_item(button)
        elif transactions[id]['status'] != "VOID":
            button = discord.ui.Button(
                label="View Invoice", url=payment_url)
            view.add_item(button)

        return embed, view

    async def embed_for_orders(self, transactions: dict, id: str) -> discord.Embed:
        embed = discord.Embed(
            title="Order Details",
            color=0x44f3f3
        )
        cart = transactions[id]['cart']
        menu_string = [""]*9
        item_count = 0
        total_items = 0
        amount = Utils.get_cart_total(cart)
        data = self.get_idbased_transaction_data(id)
        embed.description = f"**ID:** {id}\n**Type:** "+data['type']
        embed.add_field(name="Amount", value=str(
            transactions[id]['amount']), inline=True)
        embed.add_field(name="Status", value=str(
            transactions[id]['status']), inline=True)
        embed.set_footer(text=f"User ID: {data['user']}")
        for item in cart:
            # Adds the item to the menu string
            item_count += 1
            total_items += cart[item]['quantity']
            menu_string[int((item_count)/20.0001)] += "{4}. **{0}**(*₹{1}*) x **{2}**..........**₹{3}**\n".format(
                item, cart[item]['rate'], cart[item]['quantity'], cart[item]['rate'] * cart[item]['quantity'], item_count)
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
        bot = self.bot
        bot: discord.Client
        user = await bot.fetch_user(data['user'])

        embeds[0].title = "Order for {0}".format(user.name)
        # Adds the total to the last embed

        embeds.append(discord.Embed(title="Order Summary",
                                    color=rand_color))
        embeds[-1].description = "**User ID**: {0}\n".format(
            user.id)
        embeds[-1].description += "**Username:** {0}#{1}\n".format(
            user.name, user.discriminator)
        embeds[-1].description += "**Number of items:** {0}\n".format(
            total_items)
        embeds[-1].description += "**Email:** {0}\n".format(
            Actions().get_email(data['user']))
        embeds[-1].timestamp = datetime.datetime.fromtimestamp(
            data['timestamp']-data['timezone'])
        embeds[-1].description += "\n**Total: ₹{0}**".format(
            amount)
        if "instructions" in transactions[id]:
            embeds[-1].description += "\n**Instructions:** {0}".format(
                transactions[id]['instructions'])
        embeds[-1].description += "\n**Status:** {0}".format(
            transactions[id]['status'])
        embeds[-1].description += "\n**ID:** {0}".format(id)

        return embeds

    @app_commands.command(name="recharge", description="View your recharge history")
    @app_commands.describe(id="The ID of the transaction to view")
    @Checkers.is_dm()
    @app_commands.autocomplete(id=Autocompletes.get_reload_ids)
    async def recharge(self, interaction: discord.Interaction, id: str = None, page_number: int = 1):
        transactions = self.actions_obj.get_transactions(interaction.user.id)[
            "data"]["reloads"]
        if id is not None:
            view = None
            if id in transactions:
                embed, view = self.embed_for_reloads(transactions, id)
            else:
                embed = discord.Embed(
                    title="Transaction not found",
                    color=0xff0a0c,
                    description="The transaction you are looking for does not exist on your account or the transaction is of a different type"
                )

            await interaction.response.send_message(embed=embed, view=view)
            return

        if transactions == {}:
            embed = discord.Embed(
                title="Recharge History",
                description="Your recharge history is empty",
                color=0x9fcb6c
            )
            embed.description += "\n\nUse `/wallet recharge` to recharge your wallet"
            embed = embed
        else:
            transactions: dict
            order_list = list(transactions.keys())[::-1]
            pages = Utils.list_divider(order_list, 7)
            overflow_flag = False
            if page_number > len(pages):
                page_number = len(pages)
                overflow_flag = True

            class TransactionView(discord.ui.View):
                """Special view for the build command, super high level tactics"""
                current_page = page_number
                max_pages = len(pages)
                initial_call = True  # Flag to check if it's the first time the view is called

                def __init__(self):
                    super().__init__(timeout=20)
                    if self.initial_call:
                        # Updates the buttons for the first time
                        self.update_pages()
                        self.initial_call = False
                        self.select_updates()

                def select_updates(self):
                    """Updates the buttons when a button is pressed"""
                    ls = pages[self.current_page - 1]
                    option_list = []
                    for i in ls:
                        option_list.append(
                            discord.SelectOption(label=i, value=i))
                    self.select_menu.options = option_list

                async def on_timeout(self) -> None:
                    """Called when the view times out"""
                    item: discord.ui.Item  # type hinting

                    # Disables all the buttons in the view
                    for item in self.children:
                        item.disabled = True
                    self.message: discord.Message

                    # Edits the message to say that the cart has expired
                    await self.message.edit(content="View Expired", view=self)

                def update_pages(self):
                    """Updates the buttons in the view"""
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
                    self.select_updates()

                @discord.ui.button(label="Previous", style=discord.ButtonStyle.green, row=1)
                async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.current_page -= 1
                    self.update_pages()

                    embed = Transactions(None).transactions_paginate(
                        transactions, pages[self.current_page-1])
                    embed.set_footer(
                        text=f"Page {self.current_page} of {len(pages)}")
                    await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.button(label="Next", style=discord.ButtonStyle.green, row=1)
                async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.current_page += 1
                    self.update_pages()

                    embed = Transactions(None).transactions_paginate(
                        transactions, pages[self.current_page-1])
                    embed.set_footer(
                        text=f"Page {self.current_page} of {len(pages)}")

                    await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.select(placeholder="Select your transaction", min_values=1, max_values=1, row=0,
                                   options=[
                                       discord.SelectOption(
                                           label="Ok", value="ok"),
                                   ])
                async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
                    """Called when the user selects an option"""
                    embed, new_view = Transactions(None).embed_for_reloads(
                        transactions, self.select_menu.values[0])
                    await interaction.response.send_message(embed=embed, view=new_view, ephemeral=True)

            embed = self.transactions_paginate(
                transactions, pages[page_number-1])
            embed.set_footer(text=f"Page {page_number} of {len(pages)}")
            view = TransactionView()
            nmsg = None
            if overflow_flag:
                nmsg = "Page number overflowed, redirecting to last page"
            await interaction.response.send_message(content=nmsg, embed=embed, view=view)
            view.message = await interaction.original_response()
            return

        await interaction.response.send_message("Recharge History", embed=embed)

    @recharge.error
    async def recharge_error(self, interaction: discord.Interaction, error):
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

    @app_commands.command(name="orders", description="View your order history")
    @app_commands.describe(id="The ID of the transaction to view")
    @Checkers.is_dm()
    @app_commands.autocomplete(id=Autocompletes.get_order_ids)
    async def orders(self, interaction: discord.Interaction, id: str = None, page_number: int = 1):
        transactions = self.actions_obj.get_transactions(interaction.user.id)[
            "data"]["orders"]
        if id is not None:
            view = None
            embeds = []
            if id in transactions:
                embeds = await self.embed_for_orders(transactions, id)
            else:
                embeds[0] = discord.Embed(
                    title="Transaction not found",
                    color=0xff0a0c,
                    description="The transaction you are looking for does not exist on your account or the transaction is of a different type"
                )

            await interaction.response.send_message(embeds=embeds)
            return

        if transactions == {}:
            embed = discord.Embed(
                title="Order History",
                description="Your order history is empty",
                color=0x9fcb6c
            )
            embed.description += "\n\nUse `/wallet order` to order a product"
            embed = embed
        else:
            transactions: dict
            order_list = list(transactions.keys())[::-1]
            pages = Utils.list_divider(order_list, 7)
            overflow_flag = False
            if page_number > len(pages):
                page_number = len(pages)
                overflow_flag = True

            class TransactionView(discord.ui.View):
                """Special view for the build command, super high level tactics"""
                current_page = page_number
                max_pages = len(pages)
                initial_call = True

                def __init__(self, bot):
                    super().__init__(timeout=20)
                    if self.initial_call:
                        # Updates the buttons for the first time
                        self.update_pages()
                        self.initial_call = False
                        self.select_updates()
                        self.bot = bot

                def select_updates(self):
                    """Updates the buttons when a button is pressed"""
                    ls = pages[self.current_page - 1]
                    option_list = []
                    for i in ls:
                        option_list.append(
                            discord.SelectOption(label=i, value=i))
                    self.select_menu.options = option_list

                async def on_timeout(self) -> None:
                    """Called when the view times out"""
                    item: discord.ui.Item  # type hinting

                    # Disables all the buttons in the view
                    for item in self.children:
                        item.disabled = True
                    self.message: discord.Message

                    # Edits the message to say that the cart has expired
                    await self.message.edit(content="View Expired", view=self)

                def update_pages(self):
                    """Updates the buttons in the view"""
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
                    self.select_updates()

                @discord.ui.button(label="Previous", style=discord.ButtonStyle.green, row=1)
                async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.current_page -= 1
                    self.update_pages()

                    embed = Transactions(self.bot).transactions_paginate(
                        transactions, pages[self.current_page-1])
                    embed.set_footer(
                        text=f"Page {self.current_page} of {len(pages)}")
                    await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.button(label="Next", style=discord.ButtonStyle.green, row=1)
                async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.current_page += 1
                    self.update_pages()

                    embed = Transactions(None).transactions_paginate(
                        transactions, pages[self.current_page-1])
                    embed.set_footer(
                        text=f"Page {self.current_page} of {len(pages)}")

                    await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.select(placeholder="Select your transaction", min_values=1, max_values=1, row=0,
                                   options=[
                                       discord.SelectOption(
                                           label="Ok", value="ok"),
                                   ])
                async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
                    """Called when the user selects an option"""
                    embed = await Transactions(self.bot).embed_for_orders(
                        transactions, self.select_menu.values[0])
                    await interaction.response.send_message(embeds=embed, ephemeral=True)

            embed = self.transactions_paginate(
                transactions, pages[page_number-1])
            embed.set_footer(text=f"Page {page_number} of {len(pages)}")
            view = TransactionView(bot=self.bot)
            nmsg = None
            if overflow_flag:
                nmsg = "Page number overflowed, redirecting to last page"
            await interaction.response.send_message(content=nmsg, embed=embed, view=view)
            view.message = await interaction.original_response()
            return

        await interaction.response.send_message("Recharge History", embed=embed)

    @orders.error
    async def orders_error(self, interaction: discord.Interaction, error):
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
