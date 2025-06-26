from discord import Embed, Interaction
from discord.app_commands import Choice, choices, command, default_permissions
from discord.ext import commands

import bot
from bot import NuggTechBot, Servers

# taurus has awful conversions...
KB = 1000.0
MB = 1000000.0
MiB = 1048576.0
GiB = 1073741824.0


@default_permissions()
class Backup(commands.GroupCog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot
    self.description: str = "manage backups"

  @command(description="manage backups")
  @default_permissions()
  @choices(server=Servers)
  async def create(self, inter: Interaction, server: Choice[str]):
    _ = await inter.response.defer()
    bridge, server_ = self.bot.get_server(server)
    response = await bridge.sendr(f"BACKUP {server_}")
    await inter.followup.send(response.capitalize())

  @command(description="list backups")
  @choices(server=Servers)
  async def list(self, inter: Interaction, server: Choice[str], full: bool = False):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    bridge, server_ = self.bot.get_server(server)
    response = await bridge.sendr("LIST_BACKUPS")

    desc: list[str] = []
    backups: list[float] = []
    count = 0
    for line in response.splitlines():
      if not (full or line.startswith(server_.name)):
        continue

      _, size, unit = line.split()
      size = float(size[1:])
      unit = unit[:-1]

      match unit:
        case "KiB":
          mult = KB
        case "MiB":
          mult = MB
        case "GiB":
          mult = GiB
        case _:
          # if you have TiB, please seek help
          mult = 1.0

      backups.append(size * mult)
      count += 1

      if full or count <= 10:
        desc.append(line)

    total = sum(backups)
    if total < GiB:
      total /= MiB
      desc.append(f"\n**Total:** {total:.2f} MiB")
    else:
      total /= GiB
      desc.append(f"\n**Total:** {total:.2f} GiB")

    if not desc:
      desc.append("No backups found")

    embed = Embed(
      description="\n".join(desc),
      color=server_.color,
    ).set_footer(text=server_.display)

    await inter.followup.send(embed=embed)


async def setup(bot: bot.NuggTechBot):
  await bot.add_cog(Backup(bot))
