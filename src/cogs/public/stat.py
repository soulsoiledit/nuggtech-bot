import json
from typing import Literal

from discord import Embed, Interaction
from discord.app_commands import Choice, choices, command, describe
from discord.ext import commands

from bot import NuggTechBot, Servers

type Stats = dict[str, dict[str, int]]

type Leaderboards = Literal["total", "pickaxe", "shovel", "axe", "hoe", "combined"]

TITLE = {
  "pickaxe": "Pickaxe",
  "shovel": "Shovel",
  "axe": "Axe",
  "hoe": "Hoe",
  "total": "Combined Tools",
  "combined": "Combined Digs",
}


class Statistics(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(description="show player stats")
  @describe(full="show all players")
  @choices(server=Servers)
  async def stat(
    self,
    inter: Interaction,
    server: Choice[str],
    stat: Leaderboards = "total",
    full: bool = False,
  ):
    _ = await inter.response.defer()

    bridge, server_ = self.bot.get_server(server)
    response = await bridge.sendr(
      f"SHELL python3 scripts/stat.py {server_} digs",
      lambda x: x.startswith(rf"MSG [{server_}] {{\"stats\":"),
    )

    response = response.strip().replace(f"[{server_}]", "").replace("<--[HERE]", "")

    stats: Stats = json.loads(response)["stats"]
    stat_ = {player: stats[player].get(stat, 0) for player in stats}
    sort = dict(
      sorted(
        stat_.items(),
        reverse=True,
        key=lambda x: x[1],
      )
    )

    total = sum(sort.values())
    ranks: list[str] = []
    players: list[str] = []
    counts: list[str] = []

    if not full:
      sort = dict(list(sort.items())[:15])
    for i, item in enumerate(sort.items(), start=1):
      player, value = item
      ranks.append(str(i))
      players.append(player.replace("_", "\\_"))
      counts.append(f"{value:,}")

    embed = (
      Embed(
        title=f"{TITLE[stat]}",
        description=f"**Total: {total:,}**",
        color=server_.color,
      )
      .add_field(name="", value="\n".join(ranks))
      .add_field(name="", value="\n".join(players))
      .add_field(name="", value="\n".join(counts))
      .set_footer(text=server_.display)
    )

    await inter.followup.send(embed=embed)


async def setup(bot: NuggTechBot):
  await bot.add_cog(Statistics(bot))
