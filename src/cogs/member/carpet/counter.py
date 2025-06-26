from enum import Enum
from typing import Literal

from discord import Color, Embed, Interaction
from discord.app_commands import Choice, choices, command
from discord.ext import commands

from bot import NuggTechBot, Servers


class Counters(Enum):
  white = Color(0xCFD5D6)
  light_gray = Color(0x7D7D73)
  gray = Color(0x373A3E)
  black = Color(0x080A0F)
  red = Color(0x8E2121)
  orange = Color(0xE06101)
  yellow = Color(0xF1AF15)
  lime = Color(0x5EA918)
  green = Color(0x495B24)
  light_blue = Color(0x2489C7)
  cyan = Color(0x157788)
  blue = Color(0x2D2F8F)
  purple = Color(0x64209C)
  magenta = Color(0xA9309F)
  pink = Color(0xF5C2E7)
  brown = Color(0x603C20)
  all = None


type Actions = Literal["list", "reset"]


class Counter(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  async def generic(
    self,
    base_command: str,
    inter: Interaction,
    server: Choice[str],
    counter: Counters = Counters.all,
    action: Actions = "list",
  ):
    pass
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)

    command_ = base_command
    color = None
    if counter.value:
      command_ += f" {counter.name}"
      color = counter.value
    if action == "reset":
      command_ += " reset"

    response = await bridge.sendr(f"RCON {server_} {command_}")

    response = (
      response.replace("[X]", "")
      .replace("- ", "\n- ")
      .replace("Items for", "\nItems for")
      .strip()
    )

    if color is None and response.startswith("Items for"):
      color = Counters[response.split(maxsplit=3)[2]].value

    response = [
      f"**{line}**" if line.startswith("Items for") else line
      for line in response.splitlines()
    ]

    embed = Embed(
      title=f"`/{command_}`",
      description="\n".join(response),
      color=color,
    ).set_footer(text=server_.display)

    await inter.followup.send(embed=embed)

  @command(description="/counter")
  @choices(server=Servers)
  async def counter(
    self,
    inter: Interaction,
    server: Choice[str],
    counter: Counters = Counters.all,
    action: Actions = "list",
  ):
    await self.generic("counter", inter, server, counter, action)

  @command(description="/scounter")
  @choices(server=Servers)
  async def scounter(
    self,
    inter: Interaction,
    server: Choice[str],
    counter: Counters = Counters.all,
    action: Actions = "list",
  ):
    await self.generic("scounter", inter, server, counter, action)


async def setup(bot: NuggTechBot):
  await bot.add_cog(Counter(bot))
