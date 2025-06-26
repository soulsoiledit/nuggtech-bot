from collections import defaultdict
import glob
import json
import argparse
import subprocess

type Whitelist = list[dict[str, str]]
type Stat = dict[str, int]
type Stats = dict[str, Stat]


def get_server_dir(server: str) -> str | None:
  server_configs = glob.glob("servers/*.json")
  for file in server_configs:
    with open(file) as f:
      config = json.load(f)
      if config["name"] == server:
        return config["game"]["file_path"]


def get_whitelist(server_dir: str) -> Whitelist:
  with open(f"{server_dir}/whitelist.json") as wl:
    whitelist: Whitelist = json.load(wl)
    return whitelist


def get_player_stats(server_dir: str, uuid: str) -> Stats:
  try:
    with open(f"{server_dir}/world/stats/{uuid}.json") as st:
      stats: Stats = json.load(st)["stats"]
      return stats
  except Exception:
    return {}


def get_dig_stats(server_dir: str) -> Stats:
  TOOLS = [
    "pickaxe",
    "shovel",
    "axe",
    "hoe",
  ]

  whitelist = get_whitelist(server_dir)
  server_digs: Stats = {}
  for player in whitelist:
    name, uuid = player["name"], player["uuid"]
    stats = get_player_stats(server_dir, uuid)
    digs: Stat = defaultdict(int)

    # update tool uses
    for item, uses in stats.get("minecraft:used", {}).items():
      for tool in TOOLS:
        if item.endswith(tool):
          digs[tool] += uses
          digs["total"] += uses
          break

    # update digs
    digs["combined"] = sum(stats.get("minecraft:mined", {}).values())

    server_digs[name] = digs

  return server_digs


def main():
  parser = argparse.ArgumentParser()
  _ = parser.add_argument("session")
  _ = parser.add_argument("stat")
  args = parser.parse_args()
  session = str(args.session)
  stat = str(args.stat)

  server_dir = get_server_dir(session)
  if not server_dir:
    return

  if stat == "digs":
    stats = get_dig_stats(server_dir)
  else:
    # TODO: implement arbitrary stats
    print("Not implemented!")
    stats = {}

  _ = subprocess.run(
    ["tmux", "send-keys", "-t", session, json.dumps({"stats": stats}), "Enter"]
  )


if __name__ == "__main__":
  main()
