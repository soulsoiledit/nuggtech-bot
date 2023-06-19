import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

from main import PropertyBot
from main import config
from main import tr_command, check_servers, reset_bridges

server_choices = [
    Choice(name=server["chatbridge"]["username"], value=server["name"])
    for server in config["servers"]
]

member_role = config["discord"]["permissions"]["member_role"]
admin_role = config["discord"]["permissions"]["admin_role"]

class Taurus(commands.Cog):
    def __init__(self, bot: PropertyBot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def start(self, interaction: discord.Interaction, server: Choice[str]):
        await tr_command(self.bot, server.value, f"CMD {server.value} ./startup.sh")
        await interaction.response.send_message(f'Started {server.value}!')

    @app_commands.command()
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def stop(self, interaction: discord.Interaction, server: Choice[str]):
        await tr_command(self.bot, server.value, f"CMD {server.value} stop")
        await interaction.response.send_message(f'Shutdown {server.value}!')

    @app_commands.command()
    @app_commands.checks.has_role(admin_role)
    @app_commands.choices(server=server_choices)
    async def restart(self, interaction: discord.Interaction, server: Choice[str]):
        # holy this is cursed but thanks NC
        await tr_command(self.bot, server.value, f"CMD {server.value} C-c")
        await tr_command(self.bot, server.value, f"CMD {server.value} Up")
        await interaction.response.send_message(f'Restarted {server.value}!')

    @app_commands.command()
    @app_commands.checks.has_role(admin_role)
    async def reset_bridges(self, interaction: discord.Interaction):
        if interaction.user.id == 609957371279573003:
            await reset_bridges(self.bot)
            online = list(self.bot.sockets.keys())
            await interaction.response.send_message(f"Reset taurus connections! (Active: {online})")
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

    @app_commands.command()
    @app_commands.checks.has_role(admin_role)
    async def servers(self, interaction: discord.Interaction):
        embed = await check_servers(self.bot)
        await interaction.response.send_message(embed=embed)

    # @app_commands.command()
    # async def backup(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f'Backup command')
    #
    # @app_commands.command()
    # async def backup_list(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f'List backups command')
    #
    # @app_commands.command()
    # async def backup_prune(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f'Prune backups command')

    # @app_commands.command()
    # @app_commands.choices(choices=server_choices)
    # async def toggle_bridge(self, interaction: discord.Interaction, choices: Choice[str]):
    #     await tr_command(self.bot, choices.value, f"TOGGLE_BRIDGE {choices.value}")
    #     await interaction.response.send_message(f'Toggled chatbridge for {choices.value}!')
    #
    # @app_commands.command()
    # async def info_backups(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f'Backup size command')
    #
    # @app_commands.command()
    # async def info_world(self, interaction: discord.Interaction):
    #     await interaction.response.send_message(f'World size command')

async def setup(bot: PropertyBot):
    await bot.add_cog(Taurus(bot))
