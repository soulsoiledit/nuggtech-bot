import asyncio

from discord import Interaction
from discord.app_commands import Choice, choices, command, default_permissions
from discord.ext import commands

from bot import NuggTechBot, Servers


class Management(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(description="start server")
  @default_permissions()
  @choices(server=Servers)
  async def start(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()
    bridge, server_ = self.bot.get_server(server)
    await bridge.send(f"CMD {server_} ./startup.sh")
    await inter.followup.send(f"Started {server_.display}")

  @command(description="stop server")
  @default_permissions()
  @choices(server=Servers)
  async def stop(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()
    bridge, server_ = self.bot.get_server(server)
    await bridge.send(f"RCON {server_} stop")
    await inter.followup.send(f"Stopped {server_.display}")

  @command(description="restart server")
  @default_permissions()
  @choices(server=Servers)
  async def restart(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    await bridge.send(f"RCON {server_} stop")
    # arbitrary wait
    await asyncio.sleep(10)
    await bridge.send(f"CMD {server_} ./startup.sh")

    await inter.followup.send(f"Restarted {server_.display}")


async def setup(bot: NuggTechBot):
  await bot.add_cog(Management(bot))
