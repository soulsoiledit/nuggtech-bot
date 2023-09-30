import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send


class Rcon(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(
        name="rcon",
        description="Sends an arbitrary rcon command to a creative-enabled server",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.creative_server_choices)
    @app_commands.describe(command="target server")
    async def rcon(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        command: str,
    ):
        await interaction.response.defer()

        target = server.value
        await bridge_send(self.bot.servers, target, f"RCON {target} {command}")
        result = await self.bot.response_queue.get()

        target_server = self.bot.servers[target]
        embed = discord.Embed(
            title=f"`/{command}`", description=result, color=target_server.discord_color
        )
        embed.set_footer(text=target_server.display_name)

        await interaction.followup.send(embed=embed)


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Rcon(bot))
