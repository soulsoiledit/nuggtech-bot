import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

import bot

from bridge import bridge_send

class Management(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="Starts a server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def start(self, interaction: discord.Interaction, server: Choice[str]):
        target = server.value
        # holy this is cursed but thanks NC
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"CMD {target} ")
        await bridge_send(self.bot.servers, target, f"CMD {target} ./startup.sh")
        await interaction.followup.send(f'Started {target}!')

    @app_commands.command(description="Stops a server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def stop(self, interaction: discord.Interaction, server: Choice[str]):
        target = server.value
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"RCON {server.value} stop")
        await interaction.followup.send(f'Stopped {target}!')

    @app_commands.command(description="Restarts a server (Use with caution!)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def restart(self, interaction: discord.Interaction, server: Choice[str]):
        target = server.value
        # holy this is cursed but thanks NC
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"CMD {target} ")
        await bridge_send(self.bot.servers, target, f"CMD {target} C-c")
        await bridge_send(self.bot.servers, target, f"CMD {target} ./startup.sh")
        await interaction.followup.send(f'Restarted {target}!')

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Management(bot))
