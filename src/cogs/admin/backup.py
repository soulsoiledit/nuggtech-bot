import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice

from main import bot_
import bot
from bridge import bridge_send, process_backup_list

member_role = bot_.discord_config.member_role
admin_role = bot_.discord_config.admin_role
server_choices = [
    Choice(name=server.display_name, value=server.name)
    for server in bot_.server_config
]

class Backup(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    backup_commands = app_commands.Group(
        name="backup",
        description="backup commands"
    )

    @backup_commands.command(name="list", description="Lists backups of a server")
    @app_commands.describe(server="the server to list backups of")
    @app_commands.choices(server=server_choices)
    @app_commands.checks.has_role(admin_role)
    async def list_backups(self, interaction: discord.Interaction, server: Choice[str]):
        target = server.value
        await bridge_send(self.bot, target, "LIST_BACKUPS")
        embed: discord.Embed = await process_backup_list(self.bot)
        await interaction.response.send_message(embed=embed)

    @backup_commands.command(description="Creates a backup of a server")
    @app_commands.describe(server="the server to create a backup of")
    @app_commands.choices(server=server_choices)
    @app_commands.checks.has_role(admin_role)
    async def create(self, interaction: discord.Interaction, server: Choice[str]):
        await bridge_send(self.bot, server.value, f"BACKUP {server.value}")
        result = await self.bot.old_messages.get()

        embed = discord.Embed(title="Result", color=0x89b4fa)
        embed.set_author(name="NuggTech", icon_url=self.bot.discord_config.avatar)

        if result.find("aborted") >= 0:
            embed.description = f"Aborted {server.value} backup due to system constraints..."
            embed.color = 0xf38ba8
        elif result.find("starting") >= 0:
            embed.description = f"Starting backup for {server.value}..."
            embed.color = 0xa6e3a1

        await interaction.response.send_message(embed=embed)

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Backup(bot))
