from functools import partial

from discord import Embed, Interaction
from discord.app_commands import Choice, choices, command
from discord.ext import commands

from bot import NuggTechBot, Servers


class Profile(commands.GroupCog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot
    self.description: str = "/profile commands"

  def filter_profile(self, server: str, response: str) -> bool:
    return response.startswith(f"MSG [{server}] [Rcon: ]\n")

  @command(description="tick/profile health")
  @choices(server=Servers)
  async def health(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)

    health = await bridge.sendr(
      f"RCON {server_} profile health 20",
      partial(self.filter_profile, server_.name),
      True,
    )

    health = (
      health.replace(f"[{server_}] [Rcon: ", "").replace("]", "").strip().splitlines()
    )

    desc: list[str] = []
    for line in health:
      if not line.startswith(("- ", "Carpet:", "Scarpet", "The Rest,")):
        line = f"**{line}**"
      if line.startswith("The Rest,"):
        line = f"*{line}*"
      desc.append(line)

    await inter.followup.send(
      embed=Embed(
        title="`/profile health`",
        description="\n".join(desc),
        color=server_.color,
      ).set_footer(text=server_.display)
    )

  @command(description="tick/profile entities")
  @choices(server=Servers)
  async def entities(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    entities = await bridge.sendr(
      f"RCON {server_} profile entities",
      partial(self.filter_profile, server_.name),
      True,
    )

    entities = (
      entities.replace(f"[{server_}] [Rcon: ", "").replace("]", "").strip().splitlines()
    )

    desc: list[str] = []
    for line in entities:
      if not line.startswith("- "):
        line = f"**{line}**"
      desc.append(line)

    await inter.followup.send(
      embed=Embed(
        title="`/profile entities`",
        description="\n".join(desc),
        color=server_.color,
      ).set_footer(text=server_.display)
    )


async def setup(bot: NuggTechBot):
  await bot.add_cog(Profile(bot))
