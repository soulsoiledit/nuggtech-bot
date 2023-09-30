import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send


def replace_map(string: str, map: dict) -> str:
    new_string = string
    for substring, replacement in map.items():
        new_string = new_string.replace(substring, replacement)
    return new_string


class TickWarp(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    async def handle_tick_warp_status(self, target: str) -> discord.Embed:
        status = await self.bot.response_queue.get()
        replace = {
            "Tick warp has not": "**Tick warp has not",
            "Starter:": "\nStarter:",
            "Average MSPT:": "\n**Average MSPT:",
            "Time elapsed:": "**\nTime elapsed:",
            "Estimated remaining time:": "\nEstimated remaining time:",
            "[": "\n**[",
        }
        status = replace_map(status, replace) + "**"

        embed = discord.Embed(title="`/tick warp status`")
        embed.description = status
        embed.set_footer(text=self.bot.servers[target].display_name)

        return embed

    @app_commands.command(name="tickwarpstatus", description="send /tick warp status")
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def tick_warp_status(
        self, interaction: discord.Interaction, server: app_commands.Choice[str]
    ):
        target = server.value
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"RCON {target} tick warp status")
        await interaction.followup.send(
            embed=await self.handle_tick_warp_status(target)
        )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(TickWarp(bot))
