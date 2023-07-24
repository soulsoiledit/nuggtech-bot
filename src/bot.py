import logging, tomllib
from typing import Dict, Optional

import asyncio

import discord
from discord.app_commands import Choice, command
from discord.ext import commands
from discord.member import Member

from bridge import BridgeData, DiscordConfig, QueuedMessage, Server, bridge_send, setup_all_connections

logger = logging.getLogger("nuggtech-bot")

def member_check(interaction: discord.Interaction) -> bool:
    bot = interaction.client
    user = interaction.user
    if isinstance(bot, PropertyBot) and isinstance(user, Member):
        roles = bot.discord_config.member_roles
        return any(
            user.get_role(role)
            for role in roles
        )
    else:
        return False

server_choices = []

class ServerTransformer(discord.app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> str | None:
        bot = interaction.client
        if isinstance(bot, PropertyBot):
            if value in bot.servers.keys():
                return value
            else:
                await interaction.response.send_message("Invalid server selected!", ephemeral=True) 

class PropertyBot(commands.Bot):
    def __init__(self, configfile: str) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="$$", intents=intents)

        self.configfile = configfile
        self.init_extensions = [
            "maintainer.debug",
            "admin.manage",
            "admin.whitelist",
            "admin.backup",
            # "member.info",
            # "member.carpet",
            "public.pet",
            # "public.stats"
        ]

        self.webhook: Optional[discord.Webhook] = None

        with open(configfile, "rb") as f:
            server_config = tomllib.load(f)
            self.discord_config: DiscordConfig = DiscordConfig(server_config["discord"])

            self.servers: Dict[str, Server] = {}
            for server_config in server_config["servers"]:
                server = Server(server_config)
                self.servers[server.name] = server
                server_choices.append(
                    Choice(name=server.display_name, value=server.name)
                )

        self.response_queue: asyncio.Queue[QueuedMessage] = asyncio.Queue(maxsize=1)

    async def setup_hook(self):
        await self.load_cogs()
        logger.info("Loaded cogs...")

        bridge_channel = await self.fetch_channel(self.discord_config.bridge_channel)
        if bridge_channel and isinstance(bridge_channel, discord.TextChannel):
            if len(await bridge_channel.webhooks()) == 0:
                await bridge_channel.create_webhook(name="chatbridge")
            self.webhook = (await bridge_channel.webhooks())[0]

        logger.info("Webhook setup!")


        if self.webhook:
            bridge_data = BridgeData(self.discord_config, self.webhook, self.servers, self.response_queue)
            asyncio.create_task(setup_all_connections(bridge_data))

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingRole) or isinstance(error, discord.app_commands.MissingAnyRole):
            await interaction.response.send_message("Missing role!", ephemeral=True)
        else:
            raise

    async def reload_config(self):
        with open(self.configfile, "rb") as f:
            config = tomllib.load(f)
            self.discord_config: DiscordConfig = DiscordConfig(config["discord"])
            # TODO: Reload other things
            #
            # server configuration
            # self.server_config: list[ServerConfig] = [ 
            #     ServerConfig(server_config) for server_config in config["servers"]
            # ]

    async def load_cogs(self, reloading=False):
        for extension in self.init_extensions:
            if reloading:
                await self.reload_extension('cogs.'+extension)
                logger.info(f"Reloaded {extension}!")
            else:
                await self.load_extension('cogs.'+extension)
                logger.info(f"Loaded {extension}!")
