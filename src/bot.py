import logging, tomllib, asyncio

import discord
from discord.ext import commands
from discord import app_commands

import bridge

logger = logging.getLogger("discord")
server_choices = []
creative_server_choices = []


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
            "admin.rcon",
            "admin.backup",
            "member.info",
            "member.carpet.counter",
            # "member.carpet.lifetime",
            # "member.carpet.player",
            # "member.carpet.tick",
            "member.carpet.profile",
            "member.carpet.raid",
            "member.carpet.scounter",
            "member.carpet.spawn",
            "member.carpet.warp",
            "public.pet",
            # "public.stats"
        ]

        self.webhook: discord.Webhook | None = None

        with open(configfile, "rb") as f:
            server_config = tomllib.load(f)
            self.discord_config: bridge.DiscordConfig = bridge.DiscordConfig(server_config["discord"])

            self.servers: bridge.ServersDict = {}
            for server_config in server_config["servers"]:
                server = bridge.Server(server_config)
                self.servers[server.name] = server
                choice = app_commands.Choice(
                    name=server.display_name, value=server.name
                )
                server_choices.append(choice)
                if server.creative:
                    creative_server_choices.append(choice)

        self.response_queue: bridge.ResponseQueue = asyncio.Queue(maxsize=1)
        self.profile_queue: bridge.ResponseQueue = asyncio.Queue(maxsize=1)

    async def setup_hook(self) -> None:
        await super().setup_hook()
        await self.load_cogs()

        bridge_channel = await self.fetch_channel(self.discord_config.bridge_channel)
        if bridge_channel and isinstance(bridge_channel, discord.TextChannel):
            if len(await bridge_channel.webhooks()) == 0:
                await bridge_channel.create_webhook(name="chatbridge")
            self.webhook = (await bridge_channel.webhooks())[0]

        logger.info("Webhook setup!")

        if self.webhook:
            bridge_data = bridge.BridgeData(self.discord_config, self.webhook, self.servers, self.response_queue)
            asyncio.create_task(bridge.setup_all_connections(bridge_data))

    # async def on_ready(self):

    # async def on_message(msg: discord.Message):
    #     if msg.channel.id == bot_.discord_config.bridge_channel and not msg.author.bot:
    #         user = msg.author.name
    #         message = str(msg.clean_content)
    #
    #         if msg.attachments:
    #             message += " [IMG]"
    #
    #         # Handle replies
    #         reply = msg.reference
    #         reply_user = None
    #         reply_message = None
    #
    #         if reply is not None:
    #             reply = reply.resolved
    #             if isinstance(reply, discord.Message):
    #                 reply_user = reply.author.name
    #                 reply_message = reply.clean_content
    #
    #                 if reply.attachments:
    #                     reply_message += " [IMG]"
    #
    #         formatted = await bridge.format_message(bot_, "Discord", user, message, reply_user, reply_message)
    #         await bridge.bridge_chat(bot_, formatted)

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingRole) or isinstance(error, discord.app_commands.MissingAnyRole):
            await interaction.response.send_message("Missing role!", ephemeral=True)
        else:
            raise

    async def reload_config(self):
        with open(self.configfile, "rb") as f:
            config = tomllib.load(f)
            self.discord_config: bridge.DiscordConfig = bridge.DiscordConfig(
                config["discord"]
            )
            # TODO: Reload other things
            #
            # server configuration
            # self.server_config: list[ServerConfig] = [
            #     ServerConfig(server_config) for server_config in config["servers"]
            # ]

    async def load_cogs(self, reloading=False):
        for extension in self.init_extensions:
            if reloading:
                await self.reload_extension("cogs." + extension)
                logger.info(f"Reloaded {extension}!")
            else:
                await self.load_extension("cogs." + extension)
                logger.info(f"Loaded {extension}!")
