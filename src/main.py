import argparse
import logging

from bot import PropertyBot


def main():
    parser = argparse.ArgumentParser(
        description="Discord bot for the NuggTech server",
        allow_abbrev=False,
    )
    parser.add_argument("--verbosity", help="set verbosity level", default="warning")

    args = parser.parse_args()
    log_level = getattr(logging, args.verbosity.upper())

    bot = PropertyBot()
    bot.run(bot.discord_config.token, log_level=log_level)


if __name__ == "__main__":
    main()
