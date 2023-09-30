from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send

TrackingSubcommand = Literal["start", "stop", "restart"] | None


class RaidTracking(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    async def handle_raid_tracking(
        self, target: str, subcommand: TrackingSubcommand
    ) -> discord.Embed:
        raid = await self.bot.response_queue.get()
        # Remove unnecessary break
        raid = raid.replace("----------- Raid Tracker -----------\n", "")
        # Format into bulleted list
        raid = raid.replace("- ", "\n- ").replace("/h)Raiders", "/h)\nRaiders")
        # Bold important text
        raid = raid.replace("Tracked", "**Tracked").replace(
            "(in game)", "(in game)**\n"
        )
        raid = raid.replace(
            "Reasons for invalidation:", "\n**Reasons for invalidation:**"
        )
        raid = raid.replace("\nRaid gen", "\n**Raid gen").replace(
            "\nRaiders:", "\n**Raiders:"
        )
        raid = raid.replace("/h)\n", "/h)**\n")
        # Bold when spawn tracking stops or starts
        raid = raid.replace("Raid Tracker", "\n**Raid Tracker")
        raid = (
            raid.replace("started", "started**")
            .replace("stopped", "stopped**")
            .replace("running", "running**")
        )

        server = self.bot.servers[target]
        embed = discord.Embed()
        embed.title = "`/raid tracking{}`".format(
            " " + subcommand if subcommand else ""
        )
        embed.description = raid
        # embed.description = f"`{repr(raid)}`"
        embed.color = server.discord_color
        embed.set_footer(text=server.display_name)

        return embed

    @app_commands.command(
        name="raidtracking", description="send /raid tracking {option}"
    )
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def spawn_tracking(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        subcommand: TrackingSubcommand,
    ):
        target = server.value
        await interaction.response.defer()
        if subcommand:
            await bridge_send(
                self.bot.servers, target, f"RCON {target} raid tracking {subcommand}"
            )
        else:
            await bridge_send(self.bot.servers, target, f"RCON {target} raid tracking")
        await interaction.followup.send(
            embed=await self.handle_raid_tracking(target, subcommand)
        )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(RaidTracking(bot))
