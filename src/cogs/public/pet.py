import math
import random

import discord
from discord import app_commands
from discord.ext import commands

from bot import NuggTechBot


class Pet(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  def meow(self, maximum, mean, stdev) -> str:
    length = round(random.uniform(0, maximum), 1)
    if length == 0:
      return "Mw! (1 ns)"
    else:
      if length == maximum:
        length += abs(random.gauss(mean, stdev))
      chars = math.ceil(length)
      meowsage = "Me{}w! ({} s)".format("o" * chars, length)
      return meowsage

  @app_commands.command(description="pet nuggcat")
  async def pet(self, inter: discord.Interaction):
    await inter.response.send_message(self.meow(7, 0, 1))

  @app_commands.command(description="boop nuggcat")
  async def boop(self, inter: discord.Interaction):
    await inter.response.send_message(self.meow(2, 0, 0))


async def setup(bot: NuggTechBot):
  await bot.add_cog(Pet(bot))
