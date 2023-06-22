import logging
import json

import discord
from discord.ext import commands
from discord import TextChannel, app_commands
from discord.app_commands import Choice

from main import PropertyBot, bot
from main import bridge_send, check_servers, setup_bridges, process_backup_list

member_role = bot.discord_config.member_role
admin_role = bot.discord_config.admin_role
server_choices = [
    Choice(name=server.display_name, value=server.name)
    for server in bot.server_config
]

class Taurus(commands.Cog):
    def __init__(self, bot: PropertyBot):
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

    @app_commands.command(description="Lists servers and their online status")
    @app_commands.checks.has_any_role(*member_role)
    async def servers(self, interaction: discord.Interaction):
        embed = await check_servers(self.bot)
        await interaction.response.send_message(embed=embed)

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

    @app_commands.command(description="Shows info about the target server")
    @app_commands.describe(server="the server to check")
    @app_commands.choices(server=server_choices)
    @app_commands.checks.has_any_role(*member_role)
    async def check(self, interaction: discord.Interaction, server: Choice[str]):
        target = server.value
        targetName = server.name

        await bridge_send(self.bot, target, "CHECK")
        check = await self.bot.old_messages.get()
        check_dict = json.loads((check[6:]))

        await bridge_send(self.bot, target, "HEARTBEAT")
        heartbeat: str = await self.bot.old_messages.get()

        try:
            embed = discord.Embed()
            embed.title = f"NuggTech {targetName}"
            embed.color = 0xa6e3a1

            # cpu
            cpu_avg = check_dict["cpu_avg"][1]
            if cpu_avg is None:
                cpu_avg = check_dict["cpu_avg"][0]
            cpu_avg = float(cpu_avg) * 100

            embed.add_field(name=":brain: CPU Avg", value=f"{cpu_avg:.1f}%")
            embed.add_field(name="", value="\u200b")

            # ram
            ram_used = float(check_dict["ram"][0])
            ram_total = float(check_dict["ram"][1])
            ram_perc = ram_used / ram_total * 100
            embed.add_field(name=":ram: RAM Usage", value=f"{ram_perc:.1f}%")
            
            # disk
            disk_perc = float(check_dict["disk_info"][0][2]) * 100
            embed.add_field(name=":cd: Disk Usage", value=f"{disk_perc:.1f}%")
            embed.add_field(name="", value="\u200b")

            # heartbeat
            under_load = heartbeat.split()[1] == "true"
            if under_load:
                embed.color = 0xfab387
            under_load = "Yes" if under_load else "No"
            embed.add_field(name=":two_hearts: Under load?", value=under_load)

            # uptime
            uptime = int(check_dict["uptime"])
            days = uptime / 86400
            embed.set_footer(text=f"Server has been up for {days:.1f} days",
                icon_url="https://em-content.zobj.net/thumbs/320/twitter/351/up-arrow_2b06-fe0f.png")

            await interaction.response.send_message(embed=embed)
        except:
            logging.error(f"Failed to create embed")
            await interaction.response.send_message(f'Check command failed!', ephemeral=True)

async def setup(bot: PropertyBot):
    await bot.add_cog(Taurus(bot))
