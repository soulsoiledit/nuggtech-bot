import json
import typing

# change to name of the tmux session
SERVER_SHELL = "example"

# change to absolute path of server directory
SERVER_PATH = "/home/user/example"

TOOLS = [
    "pickaxe",
    "shovel",
    "axe",
    "hoe",
]

DEFAULT_STATS = {
    "pickaxe": 0,
    "shovel": 0,
    "axe": 0,
    "hoe": 0,
    "total": 0,
    "combined": 0,
}

LeaderboardChoices = typing.Literal[
    "pickaxe", "shovel", "axe", "hoe", "total", "combined"
]

STAT_MAPPING = {
    "pickaxe": "Pickaxe Uses",
    "shovel": "Shovel Uses",
    "axe": "Axe Uses",
    "hoe": "Hoe Uses",
    "total": "Total Tool Uses",
    "combined": "Combined Blocks",
}

if __name__ == "__main__":
    import os
    import subprocess

    def get_tool_stats(data, totals):
        for item, uses in data["minecraft:used"].items():
            for tool in TOOLS:
                if tool in item:
                    totals[tool] += uses
                    break

    # processes statistics data from a whitelisted server and sends it back to the bot
    # currently analyzes data for total blocks mined and tool uses
    # eventually, we want to be able to send arbitrary statistics back to the bot
    def push_server_stats():
        # check that the server is whitelisted
        whitelist_file = f"{SERVER_PATH}/whitelist.json"
        if not os.path.isfile(whitelist_file):
            return

        whitelist = json.load(open(whitelist_file))

        player_stats = {}
        for player in whitelist:
            name = player["name"]
            uuid = player["uuid"]
            stats_file = f"{SERVER_PATH}/world/stats/{uuid}.json"

            # check that player has a stats file
            if not os.path.isfile(stats_file):
                continue

            stat_data = json.load(open(stats_file))["stats"]
            stat_totals = DEFAULT_STATS.copy()

            # get number of tool uses by type
            if "minecraft:used" in stat_data:
                get_tool_stats(stat_data, stat_totals)

            # get total number of tool uses
            stat_totals["total"] = sum(stat_totals.values())

            # get total number of blocks mined
            if "minecraft:mined" in stat_data:
                stat_totals["combined"] = sum(stat_data["minecraft:mined"].values())

            player_stats[name] = stat_totals

        player_stats = json.dumps({"stats": player_stats})

        # send data to the tmux session...
        subprocess.run(
            [
                "tmux",
                "send-keys",
                "-t",
                SERVER_SHELL,
                player_stats,
                "Enter",
            ]
        )

    push_server_stats()
else:
    import discord
    from discord import app_commands
    from discord.ext import commands

    import bot
    from bridge import bridge_send

    class Statistics(commands.Cog):
        def __init__(self, bot: bot.PropertyBot):
            self.bot = bot

        async def handle_stats(
            self, target: str, statistic: str, full_leaderboard: bool
        ):
            stats = await self.bot.response_queue.get()
            stats = json.loads(stats.replace("\\", ""))["stats"]
            stats = sorted(stats.items(), reverse=True, key=lambda x: x[1][statistic])

            ranks = []
            players = []
            digs = []
            total_digs = sum([stat[1][statistic] for stat in stats])

            leaderboard_length = -1 if full_leaderboard else 15
            for i, (player, stat) in enumerate(stats[:leaderboard_length]):
                ranks.append(str(i + 1))
                players.append(str(player.replace("_", "\\_")))
                digs.append(f"{stat[statistic]:,}")

            server = self.bot.servers[target]
            embed = discord.Embed(
                title=f"{STAT_MAPPING[statistic]} Leaderboard",
                color=server.discord_color,
                description=f"**Total: {total_digs:,}**",
            )
            embed.set_footer(text=server.display_name)

            embed.add_field(name="Rank", value="\n".join(ranks))
            embed.add_field(name="Player", value="\n".join(players))
            embed.add_field(name="Digs", value="\n".join(digs))

            return embed

        @app_commands.command(
            name="stats", description="show scoreboard for a statistic"
        )
        @app_commands.describe(server="target server")
        @app_commands.choices(server=bot.server_choices)
        @app_commands.describe(leaderboard="leaderboard to display")
        @app_commands.describe(full="show all players")
        async def stats(
            self,
            interaction: discord.Interaction,
            server: app_commands.Choice[str],
            leaderboard: LeaderboardChoices = "total",
            full: bool = False,
        ):
            target = server.value
            await interaction.response.defer()

            await bridge_send(
                self.bot.servers,
                target,
                "SHELL python3 scripts/stats.py",
            )

            await interaction.followup.send(
                embed=await self.handle_stats(target, leaderboard, full)
            )

    async def setup(bot: bot.PropertyBot):
        await bot.add_cog(Statistics(bot))
