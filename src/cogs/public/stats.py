from discord.ext import commands

import bot


class Statistics(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    # @app_commands.command(description="show stats")
    # async def stats(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(stats)


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Statistics(bot))
