import json

import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send


class ServerInfo(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    async def handle_server_status(self) -> discord.Embed:
        embed = discord.Embed(title="Servers:", color=0xA6E3A1)

        for server in self.bot.servers.values():
            target = server.name
            await bridge_send(self.bot.servers, target, f"RCON {target} list")
            status = await self.bot.response_queue.get()

            state = ""
            if status:
                split_status = status.split()
                online, max = split_status[2], split_status[7]
                state = f":white_check_mark: ({online}/{max})"
            else:
                state = ":x:"

            embed.add_field(
                name="", value=f"**{server.display_name}:** {state}\n", inline=False
            )

        return embed

    async def handle_playerlist(self, target: str) -> discord.Embed:
        server = self.bot.servers[target]
        await bridge_send(self.bot.servers, target, f"RCON {target} list")
        playerlist = await self.bot.response_queue.get()

        desc = ""
        if playerlist:
            if int(playerlist.split()[2]):
                desc += playerlist.split(": ", maxsplit=1)[1].replace(", ", "\n")
            else:
                desc = "**No players are online!**"
        else:
            desc = "**The server is offline!**"

        server = self.bot.servers[target]
        embed = discord.Embed(
            title=f"Player list for {server.display_name}:",
            description=desc,
            color=server.discord_color,
        )

        return embed

    async def handle_server_check(self, target: str) -> discord.Embed:
        await bridge_send(self.bot.servers, target, "CHECK")
        health = await self.bot.response_queue.get()
        health_dict = json.loads(health)

        await bridge_send(self.bot.servers, target, "HEARTBEAT")
        heartbeat = (await self.bot.response_queue.get()) == "true"

        cpu_avg = health_dict["cpu_avg"][1]
        if cpu_avg is None:
            cpu_avg = health_dict["cpu_avg"][0]
        cpu_avg = float(cpu_avg) * 100

        ram_used = float(health_dict["ram"][0])
        ram_total = float(health_dict["ram"][1])
        ram_perc = ram_used / ram_total * 100

        disk_perc = float(health_dict["disk_info"][0][2]) * 100

        uptime = int(health_dict["uptime"])
        days = uptime / 86400
        uptime_msg = f":arrow_up: Server has been up for {days:.1f} days"

        server = self.bot.servers[target]

        embed = discord.Embed(
            title=f"NuggTech {server.display_name}",
            description=uptime_msg,
            color=server.discord_color,
        )

        embed.add_field(name=":brain: CPU Avg", value=f"{cpu_avg:.1f}%")
        embed.add_field(name="", value="\u200b")
        embed.add_field(name=":ram: RAM Usage", value=f"{ram_perc:.1f}%")

        embed.add_field(name=":cd: Disk Usage", value=f"{disk_perc:.1f}%")
        embed.add_field(name="", value="\u200b")
        embed.add_field(name=":two_hearts: Struggling?", value=heartbeat)

        return embed

    @app_commands.command(description="lists servers' online status")
    async def servers(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(embed=await self.handle_server_status())

    @app_commands.command(description="lists online players")
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def playerlist(
        self, interaction: discord.Interaction, server: app_commands.Choice[str]
    ):
        target = server.value
        await interaction.response.defer()
        await interaction.followup.send(embed=await self.handle_playerlist(target))

    @app_commands.command(description="check servers health")
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def check(
        self, interaction: discord.Interaction, server: app_commands.Choice[str]
    ):
        target = server.value
        await interaction.response.defer()
        await interaction.followup.send(embed=await self.handle_server_check(target))


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(ServerInfo(bot))
