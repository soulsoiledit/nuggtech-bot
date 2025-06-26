import json
from random import choice

from discord import Color, Embed, Interaction
from discord.app_commands import command
from discord.ext import commands

from bot import NuggTechBot, Servers


class ServerInfo(commands.Cog):
  def __init__(self, bot: NuggTechBot):
    self.bot: NuggTechBot = bot

  @command(description="list servers")
  async def servers(self, inter: Interaction):
    await inter.response.defer()

    embed = Embed(title="Servers:")
    colors: list[Color] = []
    for bridge in self.bot.bridges:
      response = await bridge.sendr("LIST")
      states: dict[str, str] = {server.name: ":x:" for server in bridge.servers}

      for line in response.splitlines():
        name, state = line.split(maxsplit=1)
        state = state.split()
        online, max_players = state[2], state[7]
        states[name] = f":white_check_mark: ({online}/{max_players})"

      for server in bridge.servers:
        colors.append(server.color)
        state = states[server.name]
        _ = embed.add_field(
          name="",
          value=f"**{server.display}**: {state}",
          inline=False,
        )
    embed.color = choice(colors)

    await inter.followup.send(embed=embed)

  @command(description="list online players")
  async def players(self, inter: Interaction, server: Servers):
    await inter.response.defer()

    bridge, server_ = server.value
    online = await bridge.sendr(f"RCON {server_} list")

    desc = "The server is offline"
    if online:
      desc = "No players are online"
      if not online.startswith("There are 0"):
        players = online.partition(": ")[2].split(",")
        desc = "\n".join(players)

    await inter.followup.send(
      embed=Embed(
        title=f"{server_.display} Players:",
        description=desc,
        color=server_.color,
      )
    )

  @command(description="check server health")
  async def check(self, inter: Interaction, server: Servers):
    await inter.response.defer()

    bridge, server_ = server.value
    health = json.loads(await bridge.sendr("CHECK"))

    pain = "No"
    if await bridge.sendr("HEARTBEAT") == "true":
      pain = "Yes"

    cpu_usage = 100.0 * float(health["cpu_avg"][1])

    ram_used = float(health["ram"][0])
    ram_total = float(health["ram"][1])
    ram_usage = 100.0 * ram_used / ram_total

    disk_usage = 100.0 * float(health["disk_info"][0][2])
    uptime = float(health["uptime"]) / 86400.0

    await inter.followup.send(
      embed=(
        Embed(
          title=f"{server_.display}:",
          description=f":arrow_up: {uptime:.1f} days",
          color=server_.color,
        )
        .add_field(name=":brain: CPU", value=f"{cpu_usage:.1f}%")
        .add_field(name="\t", value="\t")
        .add_field(name=":ram: RAM", value=f"{ram_usage:.1f}%")
        .add_field(name=":cd: Disk", value=f"{disk_usage:.1f}%")
        .add_field(name="\t", value="\t")
        .add_field(name=":two_hearts: Pain?", value=pain)
      )
    )


async def setup(bot: NuggTechBot):
  await bot.add_cog(ServerInfo(bot))
