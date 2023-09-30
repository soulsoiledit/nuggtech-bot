import discord
from discord import app_commands
from discord.ext import commands

import bot
import random


class Pet(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="pet the nuggcat")
    # @app_commands.checks.cooldown(rate=1, per=60)
    async def pet(self, interaction: discord.Interaction):
        meowlen = random.randint(1, 69)
        meowchars = meowlen // 10
        meowsage = "Me{}w! ({:.1f} s)".format("o" * meowchars, meowlen / 10)

        meowrand = random.random()

        if meowrand < 0.01:
            meowsage = "Mw! (1 ns)"

        meowchance = 0.001
        if meowrand < meowchance:
            meowchars = random.randint(20, 30)
            meowsage = "Me{}w! ({}.0 s)".format("o" * meowchars, meowchars)

        await interaction.response.send_message(meowsage)

    @pet.error
    async def pet_error(self, interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            retry_period = round(error.retry_after)
            await interaction.response.send_message(
                f">w< try petting again after {retry_period}s...!", ephemeral=True
            )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Pet(bot))
