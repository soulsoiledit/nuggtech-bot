from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send

TrackingSubcommand = Literal["start", "stop", "restart"] | None


class SpawnTracking(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    async def handle_spawn_tracking(
        self, target: str, subcommand: TrackingSubcommand
    ) -> discord.Embed:
        spawn = await self.bot.response_queue.get()
        # bold the first line
        spawn = spawn.replace("--------------------", "**").replace("min", "min**", 1)
        # format into bulleted list
        spawn = (
            spawn.replace(" > ", "\n- **")
            .replace("s/att", "s/att**")
            .replace("   - ", "\n - ")
        )
        # bold when spawn tracking stops or starts
        spawn = spawn.replace("Spawning tracking", "\n**Spawning tracking")
        spawn = spawn.replace("started.", "started.**").replace(
            "stopped.", "stopped.**"
        )

        server = self.bot.servers[target]
        embed = discord.Embed(
            title="`spawn tracking{}`".format(" " + subcommand if subcommand else ""),
            description=spawn,
            color=server.discord_color,
        )
        embed.set_footer(text=server.display_name)

        return embed

    @app_commands.command(
        name="spawntracking", description="send /spawn tracking {option}"
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
                self.bot.servers, target, f"RCON {target} spawn tracking {subcommand}"
            )
        else:
            await bridge_send(self.bot.servers, target, f"RCON {target} spawn tracking")
        await interaction.followup.send(
            embed=await self.handle_spawn_tracking(target, subcommand)
        )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(SpawnTracking(bot))
