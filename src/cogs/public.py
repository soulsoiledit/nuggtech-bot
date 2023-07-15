import discord
from discord.ext import commands
from discord import app_commands

import bot
import random

class Public(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="pet the cat")
    @app_commands.checks.cooldown(rate=1, per=60)
    async def pet(self, interaction: discord.Interaction):
        meowlen = random.randint(1, 69)
        meowtime = meowlen / 10
        meowchars = round(meowtime)
        meowsage = "Me{}w! ({} s)".format("o" * meowchars, meowtime)

        meowchance = 0.001
        meowrand = random.random()

        if meowrand < 0.01:
            meowsage = "Mw! (1 ns)"

        if meowrand < meowchance: 
            meowchars = 30
            meowsage = "Me{}w! ({} s)".format("o" * meowchars, meowchars)

        await interaction.response.send_message(meowsage)

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Public(bot))
