import discord
import datetime
import os
import json
from abc import ABC, abstractmethod


class Checkers():

    def is_dm_2(interaction: discord.Interaction):
        if interaction.guild is None:
            return True
        return False

    def is_dm():
        def predicate(interaction: discord.Interaction):
            if interaction.guild is None:
                return True
            return False
        return discord.app_commands.check(predicate)

    def is_owner():
        def predicate(interaction: discord.Interaction):
            if interaction.guild is None:
                return True
        return discord.app_commands.check(predicate)


class Utils():

    def list_divider(ls: list, n: int):
        newlist = []
        for i in range(0, len(ls), n):
            newlist.append(ls[i:i+n])
        return newlist
    
    def to_json(data):
        import bson.json_util as json_util
        return json_util.loads(json_util.dumps(data))

    def menu_paginate(menu_pages, page) -> discord.Embed:
        embed = discord.Embed(title="Menu",
                              description="The delicious menu of Los Pollos Hermanos",
                              color=0x74abc1,
                              timestamp=datetime.datetime.now())

        for i in menu_pages[page-1]:
            f1 = ''+i["ITEM"] + ": Rs "+i["COST"]+"."
            f2 = '*'+i["DESC"].strip() + \
                ',\nPreparation Time:* ***'+i["TIME"]+'***'
            embed.add_field(name=f1, value=f2, inline=False)

        embed.set_footer(text=f"Page {page} of {len(menu_pages)}")
        return embed

    def cartbuilder_paginate(menu_pages, page) -> discord.Embed:
        embed = discord.Embed(title="Cart",
                              description="Add or remove items from your cart here",
                              color=0xf7b51d,
                              timestamp=datetime.datetime.now())
        for i in menu_pages[page-1]:
            f1 = ''+i["ITEM"] + ": Rs "+i["COST"]+"."
            f2 = i["DESC"].strip()
            embed.add_field(name=f1, value=f2, inline=False)

        embed.set_footer(text=f"Page {page} of {len(menu_pages)}")
        return embed

    def path_finder(path):
        if os.name == "nt":
            return path.replace("/", "\\")
        else:
            return path.replace("\\", "/")

    def get_cart_total(cart):
        total = 0
        for i in cart:
            total += cart[i]["quantity"]*cart[i]["rate"]
        return total

    def filename_gen(name: str, id: str, ext: str):
        return (name.strip())+"_"+(str(id))+"."+(ext.strip())

    def random_hex_color():
        import random
        return discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def help_embed(option: str):
        embed = discord.Embed(color=Utils.random_hex_color())
        if option == None:
            embed.title = "Help"
            embed.set_footer(
                text="Use `/help <command>` to get more info on a command")
            embed.description = "Here are the commands you can use : `/help`, `/menu`, `/cart view`, `/cart build`, `/cart clear`, `/place_order`, `/tip`, `/tictactoe`"
        else:
            filepath = os.path.dirname(os.path.abspath(
                __file__)) + "/data/commands/help.json"
            # Makes it fit your OS
            option = option.lower()
            filepath = Utils.path_finder(filepath)
            to_show = json.load(open(filepath, "r"))
            if option in ["jesse", "walter", "walt", "white"]:
                embed.color = 0x408044
                if option == "jesse":
                    embed.title = "Hey Mr. White, We need to cook"
                    embed.description = "Ahh, Wireeee!!"
                else:
                    embed.title = "I am the one who knocks"
                    embed.description = "So, Say my name"
                return embed
            if option not in to_show:
                embed.title = "This command doesn't exist"
                embed.description = "Use `/help` to get a list of commands"
                embed.set_footer(text="<> = required, [] = optional")
                return embed
            embed.title = "/"+option
            embed.description = to_show[option]["desc"] + \
                "\n\n**Usage:** `/"+to_show[option]["usage"]+"`"
            embed.set_footer(text="<> = required, [] = optional")

        return embed

    def item_describe(menu, item) -> discord.Embed():
        embed = discord.Embed(color=discord.Color.green())
        embed.title = item
        for i in menu:
            if i["ITEM"] == item:
                embed.description = i["DESC"]
                embed.add_field(name="Cost", value="₹" + i["COST"])
                embed.add_field(name="Preparation Time", value=i["TIME"])
                if "IMAG" in i:
                    embed.set_image(url=i["IMAG"])
                break
        return embed

    def generate_otp(length: int, has_letters: bool = False) -> str:
        """Returns a random OTP of given length"""
        import random
        valid_characters = [str(i) for i in range(10)]
        if has_letters:
            valid_characters.extend([chr(i) for i in range(65, 91)])
        otp = ""
        l = len(valid_characters)
        for i in range(length):
            otp += random.choice(valid_characters)
        return otp

    async def get_help_options(self, interaction: discord.Interaction, option: str = None):
        options = ["help", "menu", "cart view", "cart build",
                   "cart clear", "place_order", "tip", "email", "feedback", 
                   "wallet view", "wallet refresh", "recharge fiat", "recharge crypto",
                   "transactions recharge", "transactions orders", "bot_info"]
        if option.lower() == "jesse":
            return [discord.app_commands.Choice(name="You found the hidden cook", value="jesse")]
        if option.lower() in ["walter", "walt", "white"]:
            return [discord.app_commands.Choice(name="You found the one who knocks", value=option.lower())]
        if option is None:
            return [discord.app_commands.Choice(name=i, value=i) for i in options]
        return [discord.app_commands.Choice(name=i, value=i) for i in options if option.lower() in i.lower()]

    def order_id_gen(user_id):
        """Generates an order ID based on the TIME and USER_ID"""
        user_id = int(user_id)
        from external_modules import Numpy as np
        b36 = np.base_repr(user_id, base=36)
        time = np.base_repr(int(datetime.datetime.timestamp(
            (datetime.datetime.utcnow()))), base=36)
        order_id = f"{time}_{b36}"
        return order_id

    def time_to_dhms(time: int):
        time = int(time)
        """converts time in seconds to days, hours, minutes and seconds"""
        days = time//86400
        hours = (time % 86400)//3600
        minutes = (time % 3600)//60
        seconds = time % 60
        str = ""
        if days:
            str += f"{days} days, "
        if hours:
            str += f"{hours} hours, "
        str += f"{minutes} minutes "
        str += f"and {seconds} seconds."
        return str

    class OTPView(discord.ui.View):
        """View for OTP modal, which displays the Enter button and has a button to retry in case of failure"""
        email = "your mail"

        def __init__(self, sent_otp: int, tries_left: int):
            """Initializes the view with the sent OTP and the number of tries left"""
            super().__init__(timeout=600)
            self.sent_otp = sent_otp
            self.tries_left = tries_left

        async def on_timeout(self):
            """Disables the view after timeout"""
            try:
                for child in self.children:
                    child.disabled = True
                self.message: discord.Message
                await self.message.edit(view=self)
            except Exception as e:
                pass

        @discord.ui.button(label="Retry", style=discord.ButtonStyle.red)
        async def retry(self,  interaction: discord.Interaction, button: discord.ui.Button):
            """Retries the OTP verification, if first try, displays the green ENTER button"""
            # Modals for OTP entry
            modal = Utils.OTPModal()
            modal.tries_left = self.tries_left
            modal.sent_otp = self.sent_otp
            modal.email = self.email
            modal.otp.placeholder = f"Enter OTP sent to {self.email}"

            # Send the modal
            await interaction.response.send_modal(modal)

    class OTPModal(discord.ui.Modal, title="Enter OTP"):
        """Modal to enter OTP, which is sent to the user's email"""

        def __init__(self):
            super().__init__(timeout=600)
            
        email = "your mail"

        otp = discord.ui.TextInput(
            style=discord.TextStyle.short,
            required=True,
            min_length=5,
            max_length=5,
            placeholder=f"Enter OTP sent to {email}",
            label="OTP")
        sent_otp: int
        tries_left: int

        async def on_submit(self, interaction: discord.Interaction):
            # Check if the OTP is correct
            self.tries_left -= 1
            if self.otp.value.upper() == self.sent_otp:
                from wallet import Actions
                Actions().add_email(interaction.user.id, self.email)
                await interaction.response.edit_message(content=f"Email Verified! The email **{self.email}** is now associated with your account!", view=None)
            else:
                if self.tries_left == 0:
                    await interaction.response.edit_message(content="Out of Tries. Please try sending a new OTP.", view=None)
                else:
                    # We need to send a new modal with the updated tries_left
                    # We are generously giving 3 tries to the user
                    OTPView = Utils.OTPView(self.sent_otp, self.tries_left)
                    OTPView.email = self.email
                    OTPView.message = interaction.original_response()
                    await interaction.response.edit_message(content=f"Invalid OTP, You have {self.tries_left} tries left", view=OTPView)

class PaymentClass(ABC):
    """
    Abstract class for payment gateways class
    In our case, we have 2 payment gateways, Razorpay and Coinbase Commerce
    """
    @abstractmethod
    def invoice(name: str, email: str, price: float, denomination: str, desc: str) -> dict:
        """
        Generates an invoice for the user to pay, which is a link to the payment gateway
        
        Args:
            name (str): name of the user
            email (str): email of the user
            price (float): amount to be paid
            denomination (str): currency of the amount, usually INR or USD
            desc (str): description of the invoice

        Returns:
            dict: invoice object, a dictionary containing the invoice id, code and the link to the payment gateway
            form : {"id": str, "code": str, "link": str}
        """
        pass
    
    @abstractmethod
    def check(id: str) -> str:
        """
        Checks the status of the transaction

        Args:
            id (str): Transaction or invoice id

        Returns:
            str: Status of the transaction
        """
        pass
    
    @abstractmethod
    def void_payment(invoice_id: str, id_pass=False):
        """_
        Voids the payment
        
        Args:
            invoice_id (str): The invoice id to be voided
            id_pass (bool, optional): Switch to be used if id is passed instead of inv. Defaults to False.
        """
        pass
    
    @abstractmethod
    def get_link(inv_id) -> str:
        """
        Returns the link to the payment gateway
        
        Args:
            inv_id (_type_): Invoice id

        Returns:
            str: Link to the payment gateway
        """
        pass
    
    @abstractmethod
    def check_payments(inv, id_pass=False):
        """
        Checks the payments for the invoice

        Args:
            inv (_type_): _description_
            id_pass (bool, optional): _description_. Defaults to False.
        """
        pass
    
    
class Orders():
    pass
