import logging
from discord import Interaction, app_commands
from discord.app_commands import check, command, default_permissions
from discord.ext import commands

from bot import NuggTechBot

logger = logging.getLogger("discord.nugg")


async def is_owner(inter: Interaction[NuggTechBot]) -> bool:
  return await inter.client.is_owner(inter.user)


class Debug(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(description="reload bot")
  @default_permissions()
  async def reload(self, inter: Interaction):
    _ = await inter.response.defer(ephemeral=True)

    await self.bot.load_cogs()
    await self.bot.close_bridges()

    logger.info("Reloaded bot")
    await inter.followup.send("Reloaded bot and bridges")

  async def sync_commands(self):
    # set all commands to guild only
    for cmd in self.bot.tree.walk_commands():
      cmd.guild_only = True
    _ = await self.bot.tree.sync()
    logger.info("Synced commands")

  @commands.command(name="sync")
  @commands.is_owner()
  async def text_sync(self, ctx: commands.Context[NuggTechBot]):
    await self.sync_commands()
    _ = await ctx.send("Synced commands", reference=ctx.message, mention_author=False)

  @command(description="sync bot commands")
  @check(is_owner)
  @default_permissions()
  async def sync(self, inter: Interaction):
    _ = await inter.response.defer(ephemeral=True)
    await self.sync_commands()
    await inter.followup.send("Synced commands")

  @sync.error
  async def is_owner_error(
    self, inter: Interaction, error: app_commands.AppCommandError
  ):
    if isinstance(error, app_commands.CheckFailure):
      _ = await inter.response.send_message("Permission denied", ephemeral=True)

  @text_sync.error
  async def text_sync_error(
    self, ctx: commands.Context[NuggTechBot], error: commands.CommandError
  ):
    if isinstance(error, commands.CheckFailure):
      _ = await ctx.send(
        "Permission denied", reference=ctx.message, mention_author=False
      )


async def setup(bot: NuggTechBot):
  await bot.add_cog(Debug(bot))
