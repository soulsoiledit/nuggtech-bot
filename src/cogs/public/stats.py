from discord.ext import commands

import os
import json

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

if __name__ == "__main__":

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
        if not os.path.isfile("./whitelist.json"):
            return

        whitelist = json.load(open("./whitelist.json"))

        player_stats = {}
        for player in whitelist:
            name = player["name"]
            uuid = player["uuid"]
            stats_file = f"./world/stats/{uuid}.json"

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

        player_stats = json.dumps({"nuggcat-stats": player_stats})

        # send data to nuggcat...
        player_stats = json.loads(player_stats)["nuggcat-stats"]
        print(
            sorted(player_stats.items(), reverse=True, key=lambda x: x[1]["combined"])
        )
        print(sorted(player_stats.items(), reverse=True, key=lambda x: x[1]["total"]))
        print(sorted(player_stats.items(), reverse=True, key=lambda x: x[1]["pickaxe"]))

    push_server_stats()
else:
    import bot

    def func():
        pass
        # ...receive data from server
        # received_data = player_stats
        # received_data = json.loads(player_stats)["nuggcat-stats"]
        # mode = "total"
        #
        # data_sorted = sorted(
        #     received_data.items(), key=lambda data: data[1][mode], reverse=True
        # )
        #
        # # sorted list
        # for player, stats in data_sorted:
        #     print(f"{player}: {stats[mode]}")

    class Statistics(commands.Cog):
        def __init__(self, bot: bot.PropertyBot):
            self.bot = bot

        # @app_commands.command(description="show stats")
        # async def stats(self, interaction: discord.Interaction):
        #     await interaction.response.send_message(stats)

    async def setup(bot: bot.PropertyBot):
        await bot.add_cog(Statistics(bot))
