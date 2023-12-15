import logging
import asyncio

import discord
from discord.ext import commands
from discord import app_commands

import bridge
import config

logger = logging.getLogger("discord")

server_choices = []
creative_server_choices = []

for server in config.servers.values():
    choice = app_commands.Choice(name=server.display_name, value=server.name)

    server_choices.append(choice)
    if server.creative:
        creative_server_choices.append(choice)


class PropertyBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="$$", intents=intents)

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
            "public.stats",
        ]

        self.webhook: discord.Webhook

        self.discord_config: bridge.DiscordConfig = config.discord_config
        self.servers: bridge.ServersDict = config.servers

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

        bridge_data = bridge.BridgeData(
            self.discord_config,
            self.webhook,
            self.servers,
            self.response_queue,
            self.profile_queue,
        )
        asyncio.create_task(bridge.setup_all_connections(bridge_data))

    async def on_message(self, msg: discord.Message):
        in_bridge_channel = msg.channel.id == self.discord_config.bridge_channel
        is_real_user = not msg.author.bot and isinstance(msg.author, discord.Member)
        if in_bridge_channel and is_real_user:
            username = msg.author.name
            message = msg.clean_content

            if msg.attachments:
                message += " [ATT]"

            # Handle replies
            reply = msg.reference
            reply_user = None
            reply_message = None

            reply_tuple = None
            if reply:
                reply = reply.resolved
                if isinstance(reply, discord.Message):
                    reply_user = reply.author.name
                    reply_message = reply.clean_content

                    if reply.attachments:
                        reply_message += " [ATT]"

                    reply_tuple = (reply_user, reply_message)

            tellraw_cmd = await bridge.create_tellraw(
                self.discord_config,
                self.servers,
                "Discord",
                username,
                message,
                reply_tuple,
            )
            await bridge.bridge_chat(self.servers, None, tellraw_cmd)

    async def load_cogs(self, reloading=False):
        for extension in self.init_extensions:
            if reloading:
                await self.reload_extension("cogs." + extension)
                logger.info(f"Reloaded {extension}!")
            else:
                await self.load_extension("cogs." + extension)
                logger.info(f"Loaded {extension}!")
