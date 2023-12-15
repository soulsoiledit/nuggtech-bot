from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send

colormap = {
    "white": 0xCFD5D6,
    "light_gray": 0x7D7D73,
    "gray": 0x373A3E,
    "black": 0x080A0F,
    "red": 0x8E2121,
    "orange": 0xE06101,
    "yellow": 0xF1AF15,
    "lime": 0x5EA918,
    "green": 0x495B24,
    "light_blue": 0x2489C7,
    "cyan": 0x157788,
    "blue": 0x2D2F8F,
    "purple": 0x64209C,
    "magenta": 0xA9309F,
    "pink": 0xF5C2E7,
    "brown": 0x603C20,
}

CounterArgs = (
    Literal[
        "white",
        "light_gray",
        "gray",
        "black",
        "red",
        "orange",
        "yellow",
        "lime",
        "green",
        "light_blue",
        "cyan",
        "blue",
        "purple",
        "magenta",
        "pink",
        "brown",
    ]
    | None
)


class SupplyCounter(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    scounter_commands = app_commands.Group(
        name="scounter", description="counter commands"
    )

    async def handle_scounter(
        self, target: str, color: str | None, reset: bool = False
    ) -> discord.Embed:
        counter = await self.bot.response_queue.get()
        counter = counter.replace("[X]", "")
        counter = counter.replace("/h)", "/h)\n").replace("/h)\n:", "/h):\n")

        colorcmd = f"`/scounter {color}" if color else "`/scounter"
        resetcmd = " reset`" if reset else "`"

        embed_color = 0
        desc = ""
        counterlines = counter.split("\n")
        for line in counterlines:
            if "Items for" in line:
                embed_color = colormap[line.split()[2]]
                desc += f"**{line}**\n"
            else:
                desc += f"{line}\n"

        if color:
            embed_color = colormap[color]

        server = self.bot.servers[target]
        embed = discord.Embed(
            title=f"{colorcmd}{resetcmd}", description=desc, color=embed_color
        )
        embed.set_footer(text=server.display_name)

        return embed

    @scounter_commands.command(name="list", description="send /scounter {counter}")
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def scounter_info(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        counter: CounterArgs,
    ):
        target = server.value
        await interaction.response.defer()
        if counter:
            await bridge_send(
                self.bot.servers, target, f"RCON {target} scounter {counter}"
            )
        else:
            await bridge_send(self.bot.servers, target, f"RCON {target} scounter")
        await interaction.followup.send(
            embed=await self.handle_scounter(target, counter)
        )

    @scounter_commands.command(
        name="reset", description="send /scounter {counter} reset"
    )
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def scounter_reset(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        counter: CounterArgs,
    ):
        target = server.value
        await interaction.response.defer()
        if counter:
            await bridge_send(
                self.bot.servers, target, f"RCON {target} scounter {counter} reset"
            )
        else:
            await bridge_send(self.bot.servers, target, f"RCON {target} scounter reset")
        await interaction.followup.send(
            embed=await self.handle_scounter(target, counter, True)
        )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(SupplyCounter(bot))
