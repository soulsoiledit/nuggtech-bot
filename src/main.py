import logging, argparse
import discord
from bot import PropertyBot

def main():
    parser = argparse.ArgumentParser(
        description="Discord bot for the NuggTech server",
        epilog="uwu :3",
        allow_abbrev=False
    )
    parser.add_argument("--config", help="specify configuration file", default="./config.toml")
    parser.add_argument("--verbosity", help="set verbosity level")
    args = parser.parse_args()

    configfile = args.config

    if args.verbosity:
        logger = logging.getLogger("nuggtech-bot")
        logger.setLevel(level=getattr(logging, args.verbosity.upper()))
        handler = logging.StreamHandler()
        handler.setFormatter(discord.utils._ColourFormatter())
        logger.addHandler(handler)

    bot = PropertyBot(configfile)

    bot.run(bot.discord_config.token)

if __name__ == "__main__":
    main()
