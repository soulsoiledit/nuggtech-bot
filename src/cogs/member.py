import logging
import json

import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from main import bot_
import bot
from bridge import bridge_send, check_servers

member_role = bot_.discord_config.member_role
admin_role = bot_.discord_config.admin_role
server_choices = [
    Choice(name=server.display_name, value=server.name)
    for server in bot_.server_config
]

class Member(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command(description="Lists servers and their online status")
    @app_commands.checks.has_any_role(*member_role)
    async def servers(self, interaction: discord.Interaction):
        embed = await check_servers(self.bot)
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

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Member(bot))
