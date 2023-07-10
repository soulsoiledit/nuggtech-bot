import tomllib
from typing import Optional

from asyncio import Queue

from websockets import client

import discord
from discord.ext import commands

class DiscordConfig:
    def __init__(self, config: dict) -> None:
        self.token = config["bot_token"]
        self.avatar = config["avatar"]
        self.color = config["color"]
        self.reply_color = config["reply_color"]

        self.guild = config["guild"]
        self.webhook = config["webhook_id"]
        self.bridge_channel = config["bridge_channel_id"]
        self.log_channel = config["log_channel_id"]

        self.member_role = config["member_role"]
        self.admin_role = config["admin_role"]
        self.maintainer = config["maintainer"]

class ServerConfig:
    def __init__(self, server_config: dict) -> None:
        self.name = server_config["name"]
        self.ip = server_config["ip"]
        self.port = server_config["port"]
        self.ws_pass = server_config["ws_password"]

        self.display_name = server_config["display_name"]
        self.nickname = server_config["nickname"]
        self.color = server_config["color"]

class MCServer:
    def __init__(self, websocket: client.WebSocketClientProtocol, config: ServerConfig) -> None:
        self.websocket = websocket
        self.config = config

class PropertyBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="$", intents=intents)

        self.init_extensions = [
            "admin.manage",
            "admin.whitelist",
            "admin.backup",
            "member",
            "public"
        ]
        self.webhook: Optional[discord.Webhook] = None

        with open("./config.toml", "rb") as f:
            config = tomllib.load(f)
            self.discord_config: DiscordConfig = DiscordConfig(config["discord"])
            self.server_config: list[ServerConfig] = [ 
                ServerConfig(server_config) for server_config in config["servers"]
            ]

        self.servers: dict[str, MCServer] = {}
        self.listeners = []
        self.old_messages: Queue = Queue(maxsize=1)

    async def setup_hook(self):
        self.webhook = await self.fetch_webhook(self.discord_config.webhook)

        for extension in self.init_extensions:
            await self.load_extension('cogs.'+extension)
            print(f"Loaded extension {extension}!")
