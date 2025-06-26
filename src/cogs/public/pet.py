import math
import random

import discord
from discord import app_commands
from discord.ext import commands

from bot import NuggTechBot


class Pet(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @app_commands.command(description="pet nuggcat")
  async def pet(self, inter: discord.Interaction):
    length = round(random.uniform(0, 7.0), 1)
    if length == 0.0:
      meowsage = "Mw! (1 ns)"
      pass
    else:
      if length == 7.0:
        length = 7.0 + abs(random.gauss(0, 10))
      chars = math.ceil(length)
      meowsage = "Me{}w! ({} s)".format("o" * chars, length)

    _ = await inter.response.send_message(meowsage)


async def setup(bot: NuggTechBot):
  await bot.add_cog(Pet(bot))
