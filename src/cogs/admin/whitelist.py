import discord
from discord.ext import commands
from discord import TextChannel, app_commands
from discord.app_commands import Choice

from main import bot_
import bot
from bridge import bridge_send

member_role = bot_.discord_config.member_role
admin_role = bot_.discord_config.admin_role
server_choices = [
    Choice(name=server.display_name, value=server.name)
    for server in bot_.server_config
]

class Whitelist(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    whitelist_commands = app_commands.Group(
        name="whitelist",
        description="Add and remove players from the whitelist"
    )

    @whitelist_commands.command(name="add", description="Adds a user to a server's whitelist")
    @app_commands.describe(server="the server to target")
    @app_commands.describe(server="the user to whitelist")
    @app_commands.choices(server=server_choices)
    @app_commands.checks.has_role(admin_role)
    async def whitelist_add(self, interaction: discord.Interaction, server: Choice[str], user: str):
        await bridge_send(self.bot, server.value, f"CMD {server.value} whitelist add {user}")
        log_channel = self.bot.get_channel(self.bot.discord_config.log_channel)
        if isinstance(log_channel, TextChannel):
            await log_channel.send(f"Added {user} to {server.value}")
        await interaction.response.send_message(f'Added {user} to {server.value}!', ephemeral=True)

    @whitelist_commands.command(name="remove", description="Removes a user from a server's whitelist")
    @app_commands.describe(server="the server to target")
    @app_commands.describe(server="the user to unwhitelist")
    @app_commands.choices(server=server_choices)
    @app_commands.checks.has_role(admin_role)
    async def whitelist_remove(self, interaction: discord.Interaction, server: Choice[str], user: str):
        await bridge_send(self.bot, server.value, f"CMD {server.value} whitelist remove {user}")
        log_channel = self.bot.get_channel(self.bot.discord_config.log_channel)
        if isinstance(log_channel, TextChannel):
            await log_channel.send(f"Removed {user} from {server.value}")
        await interaction.response.send_message(f'Removed {user} from {server.value}!', ephemeral=True)

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Whitelist(bot))
