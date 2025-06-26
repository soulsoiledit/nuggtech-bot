import discord
from discord import app_commands
from discord.ext import commands

from bot import NuggTechBot, Servers


class Rcon(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @app_commands.command(description="send rcon command")
  @app_commands.default_permissions()
  @app_commands.choices(server=Servers)
  async def rcon(
    self, inter: discord.Interaction, server: app_commands.Choice[str], command: str
  ):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    response = await bridge.sendr(f"RCON {server_} {command}")

    embed = discord.Embed(
      title=f"`/{command}`",
      description=response,
      color=server_.color,
    ).set_footer(text=server_.display)

    await inter.followup.send(embed=embed)


async def setup(bot: NuggTechBot):
  await bot.add_cog(Rcon(bot))
