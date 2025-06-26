from typing import Literal
from discord import Embed, Interaction
from discord.app_commands import command
from discord.ext import commands

from bot import NuggTechBot, Servers


class RaidTracking(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(name="raidtracking", description="/raid tracking")
  async def spawn_tracking(
    self,
    inter: Interaction,
    server: Servers,
    action: Literal["start", "stop", "restart"] | None,
  ):
    await inter.response.defer()

    bridge, server_ = server.value

    command_ = f"RCON {server_} raid tracking"
    if action:
      command_ += " {subcommand}"

    raid = await bridge.sendr(command_)

    # TODO: update formatting
    raid = (
      # Remove unnecessary break
      raid.replace("----------- Raid Tracker -----------\n", "")
      # Format into bulleted list
      .replace("- ", "\n- ")
      .replace("/h)Raiders", "/h)\nRaiders")
      # Bold important text
      .replace("Tracked", "**Tracked")
      .replace("(in game)", "(in game)**\n")
      .replace("Reasons for invalidation:", "\n**Reasons for invalidation:**")
      .replace("\nRaid gen", "\n**Raid gen")
      .replace("\nRaiders:", "\n**Raiders:")
      .replace("/h)\n", "/h)**\n")
      # Bold when spawn tracking stops or starts
      .replace("Raid Tracker", "\n**Raid Tracker")
      .replace("started", "started**")
      .replace("stopped", "stopped**")
      .replace("running", "running**")
    )

    await inter.followup.send(
      embed=Embed(
        title=f"`/{command_}`",
        description=raid,
        color=server_.color,
      ).set_footer(text=server_.display)
    )


async def setup(bot: NuggTechBot):
  await bot.add_cog(RaidTracking(bot))
