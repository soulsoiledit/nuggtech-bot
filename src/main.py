import logging
from os import getenv

from bot import NuggTechBot


def main():
  logger = logging.getLogger("discord.nugg")
  level = getenv("LOG_LEVEL", default="info").upper()
  logger.setLevel(level)

  bot = NuggTechBot()
  bot.run(bot.config.token)


if __name__ == "__main__":
  main()
