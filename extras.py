import discord
import datetime


class Checkers():

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
            f1 = ''+i[0] + ": Rs "+i[1]+"."
            f2 = '*'+i[2].strip().replace(';', ',') + \
                ',\nPreparation Time:* ***'+i[3]+'***'
            embed.add_field(name=f1, value=f2, inline=False)

        embed.set_footer(text=f"Page {page} of {len(menu_pages)}")
        return embed
