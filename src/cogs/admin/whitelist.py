from typing import Literal

from discord import Interaction
from discord.app_commands import command, default_permissions
from discord.ext import commands

from bot import NuggTechBot, Servers


class Whitelist(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(description="whitelist players")
  @default_permissions()
  async def whitelist(
    self,
    inter: Interaction,
    server: Servers,
    action: Literal["add", "remove"],
    user: str,
  ):
    await inter.response.defer(ephemeral=True)

    bridge, server_ = server.value
    response = await bridge.sendr(f"RCON {server_} whitelist {action} {user}")

    if response.endswith("whitelist"):
      if response.startswith("Added"):
        verb = "Whitelisted"
      else:
        verb = "Unwhitelisted"

      await self.bot.log(
        f"`{inter.user}` {verb.lower()} `{user}` on {server_.display}",
      )

      response = f"{verb} {user} on {server_.display}"

    await inter.followup.send(response)

  @command(description="op players")
  @default_permissions()
  async def op(
    self,
    inter: Interaction,
    server: Servers,
    action: Literal["add", "remove"],
    user: str,
  ):
    await inter.response.defer(ephemeral=True)

    bridge, server_ = server.value
    command = "op" if action == "add" else "deop"
    response = await bridge.sendr(f"RCON {server_} {command} {user}")

    if response.startswith("Made"):
      if "no longer" in response:
        verb = "Deop'd"
      else:
        verb = "Op'd"

      await self.bot.log(
        f"`{inter.user}` {verb.lower()} `{user}` on {server_.display}",
      )

      response = f"{verb} {user} on {server_.display}"

    await inter.followup.send(response)


async def setup(bot: NuggTechBot):
  await bot.add_cog(Whitelist(bot))
