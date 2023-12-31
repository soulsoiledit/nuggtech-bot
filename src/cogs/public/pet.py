import discord
from discord import app_commands
from discord.ext import commands

import math
import bot
import random


class Pet(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="pet the nuggcat")
    async def pet(self, interaction: discord.Interaction):
        meowlen = -1
        meowchars = -1

        if random.random() < 0.01:
            meowlen = random.gauss(10, 10)
            if meowlen <= 10:
                meowlen = 0
                meowchars = -1
            else:
                meowchars = round(meowlen)
                meowlen = round(meowlen, 1)
        else:
            meowlen = round(random.randint(1, 69) / 10, 1)
            meowchars = math.floor(meowlen)

        meowsage = ""
        if meowlen == 0:
            meowsage = "Mw! (1 ns)"
        else:
            meowsage = "Me{}w! ({} s)".format("o" * meowchars, meowlen)

        await interaction.response.send_message(meowsage)


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Pet(bot))
