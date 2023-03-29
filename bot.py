import discord
from discord import app_commands
import os
import asyncio
import csv
from extras import Checkers, Utils, Fun
from dotenv import load_dotenv
import datetime
import json


load_dotenv()


intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)
owners = [354546286634074115]


class CartActions(app_commands.Group):
    @app_commands.command(name="view", description="View your current cart")
    async def view(self, interaction: discord.Interaction):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + "\data\carts\{0}.json".format(interaction.user.id)
        filepath = Utils.path_finder(filepath)
        if not os.path.isfile(filepath):
            with open(filepath, "w") as f:
                json.dump({}, f, indent=2)
        f = json.load(open(filepath, "r"))
        if f == {}:
            embed = discord.Embed(title="Your Cart is Empty",
                                  description="Your cart is empty, add something to it!",
                                  color=0x57eac8)
            embed.set_footer(text="If you need help, use /help")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            menu_string = ""
            # Formats the menu string in the format of "Item(Price) x Quantity..........Total"
            for item in f:
                menu_string += "**{0}**(*₹{1}*) x **{2}**..........**₹{3}**\n".format(
                    item, f[item]['rate'], f[item]['quantity'], f[item]['rate'] * f[item]['quantity'])
            embed = discord.Embed(title="Your Cart",
                                  description=menu_string,
                                  color=0x57eac8)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    @view.error
    async def view_error(self, interaction: discord.Interaction, error):
        embed = discord.Embed(title="Error!",
                              description=str(error),
                              color=0xc6be0f)
        embed.set_footer(text="Please message staff")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="build", description="Build your cart!")
    async def build(
            self, interaction:
            discord.Interaction,
            page: app_commands.Range[int, 1, None] = 1):
        filepath = os.path.dirname(os.path.abspath(
            __file__)) + "/data/menus/newmenu.json"
        filepath = Utils.path_finder(filepath)
        with open(filepath, "r") as f:
            menu = json.load(f)
        menu_pages = Utils.list_divider(menu, 10)
        overflow_flag = False
        if page > len(menu_pages):
            page = len(menu_pages)
            overflow_flag = True
        embed = Utils.cartbuilder_paginate(menu_pages, page)

        class BuildView(discord.ui.View):
            current_page = page
            max_pages = len(menu_pages)

            def __init__(self):
                super().__init__(timeout=90)
                self.update_buttons()

            async def on_timeout(self) -> None:
                item: discord.ui.Item
                for item in self.children:
                    item.disabled = True
                self.message: discord.Message
                await self.message.edit(content="Menu Expired", view=self)

            def update_buttons(self):
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

                ls = []
                for i in menu_pages[self.current_page - 1]:
                    print(i)
                    ls.append(discord.SelectOption(
                        label=i['ITEM'] + " : ₹{0}".format(i['COST']), description="In Cart {0}".format(0), value=i['ITEM']))
                self.select1.options = ls

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.green, row=2)
            async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id is not self.og_author:
                    await interaction.response.send_message("You can't do that!", ephemeral=True)
                    return
                self.current_page -= 1
                self.update_buttons()
                embed = Utils.cartbuilder_paginate(
                    menu_pages, self.current_page)
                await interaction.response.edit_message(content=None, embed=embed, view=self)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.green, row=2)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                print(interaction.user)
                if interaction.user.id is not self.og_author:
                    await interaction.response.send_message("You can't do that!", ephemeral=True)
                    return
                self.current_page += 1
                self.update_buttons()
                embed = Utils.cartbuilder_paginate(
                    menu_pages, self.current_page)
                await interaction.response.edit_message(content=None, embed=embed, view=self)

            @discord.ui.select(placeholder="Select an option", max_values=1, min_values=1, row=0, options=[
                discord.SelectOption(
                    label="Option 1", emoji="👌", description="Placeholder 1"),
            ])
            async def select1(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id is not self.og_author:
                    await interaction.response.send_message("You can't do that!", ephemeral=True)
                    return
                await interaction.response.send_message(content=f"Your choice is {select.values[0]}!", ephemeral=True)

        builder_view = BuildView()
        if overflow_flag:
            await interaction.response.send_message("That page doesn't exist! Here's the last page instead.", embed=embed, view=builder_view)
        else:
            await interaction.response.send_message(embed=embed, view=builder_view)
        builder_view.message = await interaction.original_response()
        builder_view.og_author = interaction.user.id
        print(builder_view.og_author)


@bot.event
async def on_ready():
    print("Bot is ready, logged in as {0.user}".format(bot))
    try:
        cart = CartActions(name="cart", description="Views your cart")
        tree.add_command(cart)
        await tree.sync()
    except:
        pass
    while await status_task():
        continue


async def status_task():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your Cart"))
    await asyncio.sleep(150)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your Orders"))
    await asyncio.sleep(150)
    return True


@tree.command(name="order", description="Order your stuff")
async def order(interaction: discord.Interaction, name: str):
    embed = discord.Embed(title="Ordering {0}".format(name),
                          description="Ordering {0} for you".format(name),
                          color=0x74abc1)
    await interaction.response.send_message("Gotcha {0.user.mention}".format(interaction), embed=embed)


@tree.command(name="place_order", description="Confirm and place your order! (DMs only)")
@Checkers.is_dm()
async def place_order(interaction: discord.Interaction):
    await interaction.response.send_message("Gatorade me! Placing order")


@place_order.error
async def place_order_error(interaction: discord.Interaction, error):
    embed = discord.Embed(title="Works in DMs only!",
                          description="Please direct message the bot.",
                          color=0xc6be0f)
    view = discord.ui.View()
    dm = await interaction.user.create_dm()
    view.add_item(item=discord.ui.Button(label="Go to DMs", url=dm.jump_url))
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
    import re
    if (re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        pass
    else:
        await interaction.response.send_message("Invalid email address!", ephemeral=True)
        return
    # await interaction.response.send_message(f"A measly {amount}, sadge, sent invoice to {email},{interaction.user}")
    from payments import Payment
    memo = str(interaction.user.id) + \
        f": Tip from {str(interaction.user)} of INR {amount}"
    inv = Payment.invoice(str(interaction.user), email, amount, "INR", memo)
    embed = discord.Embed(title=f"Invoice {inv['code']} created!",
                          description=f"Payment link : {inv['url']}",
                          color=0xc6be0f)
    embed.add_field(name="Amount", value=f"INR {amount}", inline=True)
    embed.add_field(name="Order Code", value=inv['code'], inline=True)
    embed.add_field(name="Tx. ID", value=str(inv['id']), inline=True)
    view = discord.ui.View()
    view.add_item(item=discord.ui.Button(label="Make Payment", url=inv['url']))
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()
    count = 0
    flag_check_coming = False
    while True:
        stats = check_payments(inv)
        count += 1
        print(f"{count}. Payment Stats for {inv['code']} = {stats}")
        if stats == 'PAYMENT_PENDING' and flag_check_coming == False:
            flag_check_coming = True
            embed = discord.Embed(title=f"Payment for Invoice {inv['code']} Pending!",
                                  description=f"Check status here : {inv['url']}",
                                  color=0x3f7de0)
            embed.set_footer(
                text="We will notify you when the payment is complete.")
            await msg.reply(embed=embed)
        if stats == 'PAID':
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
            break
        if stats == 'VOID':
            embed = discord.Embed(title=f"Invoice {inv['code']} Voided!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} has been voided and can no longer be paid.",
                                  color=0xd62d2d)
            embed.set_footer(
                text="This is usually due to staff interruption.")
            await msg.reply(embed=embed)
            break
        if stats == 'EXPIRED':
            embed = discord.Embed(title=f"Invoice {inv['code']} Expired!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} has expired and can no longer be paid. Please make sure to pay within 60 minutes of placing the order.",
                                  color=0xd62d2d)
            embed.set_footer(text="You can try again with a new invoice.")
            await msg.reply(embed=embed)
        if stats == 'UNRESOLVED':
            embed = discord.Embed(title=f"Invoice {inv['code']} needs attention!",
                                  description=f"Your invoice with id {inv['id']} of INR {amount} is in an unresolved state. Please contact us for more information.",
                                  color=0xd62d2d)
            embed.set_footer("This may be due to underpayment or overpayment.")
            await msg.reply(embed=embed)
        await asyncio.sleep(10)


@tip.error
async def tip_error(interaction: discord.Interaction, error):
    embed = discord.Embed(title="Works in DMs only!",
                          description="Please direct message the bot.",
                          color=0xc6be0f)
    embed.set_footer(text="If this was in DMs, an inadvertent error occured.")
    view = discord.ui.View()
    dm = await interaction.user.create_dm()
    view.add_item(item=discord.ui.Button(label="Go to DMs", url=dm.jump_url))
    await interaction.response.send_message(embed=embed, ephemeral=True, view=view)


@tree.command(name="menu", description="Explore the delicious menu of Los Pollos Hermanos")
@app_commands.describe(
    page="[Optional] The page number of the menu you want to see"
)
async def new_menu(interaction: discord.Interaction,
                   page: app_commands.Range[int, 1, None] = 1):
    filepath = os.path.dirname(os.path.abspath(
        __file__)) + "/data/menus/newmenu.json"
    filepath = Utils.path_finder(filepath)
    menu = json.load(open(filepath, "r"))
    menu_pages = Utils.list_divider(menu, 5)
    overflow_flag = False
    if page > len(menu_pages):
        page = len(menu_pages)
        overflow_flag = True
    embed = Utils.menu_paginate(menu_pages, page)

    class NewView(discord.ui.View):
        current_page = page
        max_pages = len(menu_pages)

        def __init__(self):
            super().__init__(timeout=30)
            self.update_buttons()

        async def on_timeout(self) -> None:
            item: discord.ui.Item
            for item in self.children:
                item.disabled = True
            self.message: discord.Message
            await self.message.edit(content="Menu Expired", view=self)

        def update_buttons(self):
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
            self.current_page -= 1
            self.update_buttons()
            embed = Utils.menu_paginate(menu_pages, self.current_page)
            await interaction.response.edit_message(content=None, embed=embed, view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.green)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.current_page += 1
            self.update_buttons()
            embed = Utils.menu_paginate(menu_pages, self.current_page)
            await interaction.response.edit_message(content=None, embed=embed, view=self)
    view = NewView()
    if overflow_flag:
        await interaction.response.send_message("That page doesn't exist! Here's the last page instead.", embed=embed, view=view)
    else:
        await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()


def check_payments(inv):
    from payments import Payment
    status = Payment.check(inv['id'])
    return status.upper()


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.content.lower() == ";;jesse stop" and message.author.id in owners:
        await message.reply("Okay Mr. White, I'm out!")
        await bot.close()
    if message.content.lower().startswith(";;del") and message.author.id in owners:
        ls = message.content.split()
        if len(ls) >= 2:
            for i in ls[1:]:
                try:
                    msg = await message.channel.fetch_message(i)
                    await msg.delete()
                except:
                    pass
            try:
                await message.delete()
            except:
                pass


@tree.command(name="tictactoe", description="plays tictactoe")
async def tic(ctx: discord.Interaction):
    """Starts a tic-tac-toe game with yourself."""
    await ctx.response.send_message('Tic Tac Toe: X goes first', view=Fun.TicTacToe())
bot.run(os.getenv("TOKEN"))
