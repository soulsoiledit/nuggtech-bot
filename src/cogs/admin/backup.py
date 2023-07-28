import discord
from discord import app_commands
from discord.ext import commands

import bot
from bridge import bridge_send

class Backup(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    backup_commands = app_commands.Group(
        name="backup",
        description="backup commands"
    )

    async def handle_backup_list(self, target: str) -> discord.Embed:
        backup_list = await self.bot.response_queue.get()
        server = self.bot.servers[target]

        desc: str = ""
        if backup_list == "LIST_BACKUPS ":
            desc = "There are no backups!"
        else:
            total = 0
            lines = 0

            for line in backup_list.replace("LIST_BACKUPS ", "").split("\n"):
                name, size, unit = line.split()
                size = float(size[1:])
                unit = unit[:-1]

                match unit:
                    case "B":
                        total += size
                    case "MiB":
                        total += size * 1048576
                    case "GiB":
                        total += size * 1073741824

                lines += 1
                if lines < 11:
                    desc += f"{name} ({size:.1f} {unit})\n"

            if total < 1048576:
                desc += f"\n**Total:** {total:.2f} B"
            elif total < 1073741824:
                total /= 1048576
                desc += f"\n**Total:** {total:.2f} MiB"
            else:
                total /= 1073741824
                desc += f"\n**Total:** {total:.2f} GiB"

        embed = discord.Embed(
            title=f"Backups for {server.display_name}:",
            color=int(server.color[1:], base=16),
            description=desc
        )
        embed.set_footer(text="NuggTech", icon_url=self.bot.discord_config.avatar)

        return embed

    async def handle_backup_create(self, target: str) -> discord.Embed:
        result = await self.bot.response_queue.get()
        server = self.bot.servers[target]

        if result == "starting new backup":
            color = int(server.color[1:], base=16)
        else:
            color = 0xf38ba8

        embed = discord.Embed(
            title=f"Backup result for {server.display_name}:",
            color=color,
            description=result.capitalize()
        )
        embed.set_footer(text="NuggTech", icon_url=self.bot.discord_config.avatar)

        return embed

    @backup_commands.command(name="list", description="Lists backups of a server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def list_backups(self, interaction: discord.Interaction, server: app_commands.Choice[str]):
        target = server.value
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"LIST_BACKUPS")
        await interaction.followup.send(embed=await self.handle_backup_list(target))

    @backup_commands.command(name="create", description="Creates a backups for a server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def create_backup(self, interaction: discord.Interaction, server: app_commands.Choice[str]):
        target = server.value
        await interaction.response.defer()
        await bridge_send(self.bot.servers, target, f"BACKUP {target}")
        await interaction.followup.send(embed=await self.handle_backup_create(target))

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Backup(bot))
