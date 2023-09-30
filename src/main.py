import logging, argparse
from bot import PropertyBot


def main():
    parser = argparse.ArgumentParser(
        description="Discord bot for the NuggTech server",
        epilog="uwu :3",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config", help="specify configuration file", default="./config.toml"
    )
    parser.add_argument("--verbosity", help="set verbosity level", default="warning")
    args = parser.parse_args()

    configfile = args.config

    bot = PropertyBot(configfile)

    log_level = getattr(logging, args.verbosity.upper())
    bot.run(bot.discord_config.token, log_level=log_level)


if __name__ == "__main__":
    main()
