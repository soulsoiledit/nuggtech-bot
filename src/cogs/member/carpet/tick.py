import re
from discord import Embed, Interaction
from discord.app_commands import Choice, choices, command
from discord.ext import commands

from bot import NuggTechBot, Servers


class Tick(commands.GroupCog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot
    self.description: str = "/tick commands"

  @command(name="warpstatus", description="get tick warp status")
  @choices(server=Servers)
  async def tick_warp_status(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)

    response = await bridge.sendr(f"RCON {server_} tick warp status")
    response = re.sub(r"(Starter|Average|Time|Estimated|\[)", r"\n\1", response)

    await inter.followup.send(
      embed=Embed(
        title="`/tick warp status`",
        description=response,
        color=server_.color,
      ).set_footer(text=server_.display)
    )


async def setup(bot: NuggTechBot):
  await bot.add_cog(Tick(bot))
