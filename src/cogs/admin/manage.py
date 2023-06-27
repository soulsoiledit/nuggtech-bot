import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from main import bot_
import bot
from bridge import bridge_send, setup_bridges 

member_role = bot_.discord_config.member_role
admin_role = bot_.discord_config.admin_role
server_choices = [
    Choice(name=server.display_name, value=server.name)
    for server in bot_.server_config
]

class Management(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="Starts a server")
    @app_commands.describe(server="the server to start")
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def start(self, interaction: discord.Interaction, server: Choice[str]):
        await bridge_send(self.bot, server.value, f"CMD {server.value} ./startup.sh")
        await interaction.response.send_message(f'Started {server.value}!')

    @app_commands.command(description="Stops a server")
    @app_commands.describe(server="the server to stop")
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def stop(self, interaction: discord.Interaction, server: Choice[str]):
        await bridge_send(self.bot, server.value, f"CMD {server.value} stop")
        await interaction.response.send_message(f'Shutdown {server.value}!')

    @app_commands.command(description="Restarts a server (WARN: Use with caution!)")
    @app_commands.describe(server="the server to restart")
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def restart(self, interaction: discord.Interaction, server: Choice[str]):
        # holy this is cursed but thanks NC
        await bridge_send(self.bot, server.value, f"CMD {server.value} C-c")
        await bridge_send(self.bot, server.value, f"CMD {server.value} Up")
        await interaction.response.send_message(f'Restarted {server.value}!')

    @app_commands.command(description="Restarts all websocket connections to taurus")
    @app_commands.checks.has_role(admin_role)
    async def reset_bridges(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await setup_bridges(self.bot)
            online = list(self.bot.servers.keys())
            await interaction.response.send_message(f"Reset taurus connections! (Active: {online})")
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Management(bot))
