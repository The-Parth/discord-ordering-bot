import discord
import datetime
import os
import json


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
            if option in ["jesse","walter","walt","white"]:
                embed.color = 0x408044
                if option == "jesse":
                    embed.title = "Hey Mr. White, We need to cook"
                    embed.description = "Wireeee!!"
                else :
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

    async def get_help_options(self, interaction: discord.Interaction, option: str = None):
        options = ["help", "menu", "cart view", "cart build", "cart clear", "place_order", "menu", "tip", "tictactoe"]
        if option.lower() == "jesse":
            return [discord.app_commands.Choice(name="You found the hidden cook", value="jesse")]
        if option.lower() in ["walter", "walt", "white"]:
            return [discord.app_commands.Choice(name="You found the one who knocks", value=option.lower())]
        if option is None:
            return [discord.app_commands.Choice(name=i, value=i) for i in options]
        return [discord.app_commands.Choice(name=i, value=i) for i in options if option.lower() in i.lower()]
        

class Orders():
    pass


class Fun():
    class TicTacToeButton(discord.ui.Button['TicTacToe']):
        def __init__(self, x: int, y: int):
            super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
            self.x = x
            self.y = y

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            state = view.board[self.y][self.x]
            if state in (view.X, view.O):
                return

            if view.current_player == view.X:
                self.style = discord.ButtonStyle.danger
                self.label = 'X'
                self.disabled = True
                view.board[self.y][self.x] = view.X
                view.current_player = view.O
                content = "It is now O's turn"
            else:
                self.style = discord.ButtonStyle.success
                self.label = 'O'
                self.disabled = True
                view.board[self.y][self.x] = view.O
                view.current_player = view.X
                content = "It is now X's turn"

            winner = view.check_board_winner()
            if winner is not None:
                if winner == view.X:
                    content = 'X won!'
                elif winner == view.O:
                    content = 'O won!'
                else:
                    content = "It's a tie!"

                for child in view.children:
                    child.disabled = True

                view.stop()

            await interaction.response.edit_message(content=content, view=view)

    # This is our actual board View

    class TicTacToe(discord.ui.View):
        X = -1
        O = 1
        Tie = 2

        def __init__(self):
            super().__init__()
            self.current_player = self.X
            self.board = [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ]

            for x in range(3):
                for y in range(3):
                    self.add_item(Fun.TicTacToeButton(x, y))

        # This method checks for the board winner -- it is used by the TicTacToeButton
        def check_board_winner(self):
            for across in self.board:
                value = sum(across)
                if value == 3:
                    return self.O
                elif value == -3:
                    return self.X

            # Check vertical
            for line in range(3):
                value = self.board[0][line] + \
                    self.board[1][line] + self.board[2][line]
                if value == 3:
                    return self.O
                elif value == -3:
                    return self.X

            # Check diagonals
            diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
            if diag == 3:
                return self.O
            elif diag == -3:
                return self.X

            diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
            if diag == 3:
                return self.O
            elif diag == -3:
                return self.X

            # If we're here, we need to check if a tie was made
            if all(i != 0 for row in self.board for i in row):
                return self.Tie

            return None


