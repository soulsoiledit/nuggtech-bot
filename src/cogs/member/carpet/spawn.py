from typing import Literal

from discord import Embed, Interaction
from discord.app_commands import Choice, choices, command
from discord.ext import commands

from bot import NuggTechBot, Servers


class SpawnTracking(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(name="spawntracking", description="/spawn tracking")
  @choices(server=Servers)
  async def spawn_tracking(
    self,
    inter: Interaction,
    server: Choice[str],
    action: Literal["start", "stop", "restart"] | None,
  ):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    command_ = "spawn tracking"
    if action:
      command_ += f" {action}"

    spawn = await bridge.sendr(f"RCON {server_} {command_}")

    # TODO: update formatting
    spawn = (
      # bold the first line
      spawn.replace("--------------------", "**")
      .replace("min", "min**", 1)
      # format into bulleted list
      .replace(" > ", "\n- **")
      .replace("s/att", "s/att**")
      .replace("   - ", "\n - ")
      # bold when start and stop
      .replace("Spawning tracking started.", "\n**Spawning tracking started.**")
      .replace("Spawning tracking stopped.", "\n**Spawning tracking stopped.**")
    )

    await inter.followup.send(
      embed=Embed(
        title=f"`/{command_}`",
        description=spawn,
        color=server_.color,
      ).set_footer(text=server_.display)
    )


async def setup(bot: NuggTechBot):
  await bot.add_cog(SpawnTracking(bot))
