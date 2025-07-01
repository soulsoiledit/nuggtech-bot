import asyncio
import json
import logging
import re
from asyncio import Task, create_task
from typing import NamedTuple, override

import discord
from discord.app_commands import Choice
from discord.ext import commands

from bridge import MSG, Bridge, Config, Server
from config import bridges, config

logger = logging.getLogger("discord.nugg")

_servers: dict[tuple[str, str], tuple[Bridge, Server]] = {}
Servers: list[Choice[str]] = []

for bridge in bridges:
  for server in bridge.servers:
    _servers[(server.display, bridge.name)] = (bridge, server)
    Servers.append(Choice[str](name=server.display, value=bridge.name))

extensions = [
  "admin.debug",
  "admin.manage",
  "admin.rcon",
  "admin.whitelist",
  "admin.backup",
  "member.info",
  "member.carpet.counter",
  # TODO: "member.carpet.player",
  "member.carpet.profile",
  "member.carpet.raid",
  "member.carpet.spawn",
  "member.carpet.tick",
  "public.pet",
  "public.stat",
]


class Message(NamedTuple):
  author: str
  content: str


class NuggTechBot(commands.Bot):
  def __init__(self) -> None:
    intents = discord.Intents.default()
    intents.message_content = True
    super().__init__(command_prefix="$$", intents=intents)

    self.webhook: discord.Webhook

    self.config: Config = config
    self.bridges: list[Bridge] = bridges
    self.connect_task: Task[None]

  @override
  async def setup_hook(self) -> None:
    await super().setup_hook()
    await self.load_cogs()
    await self.set_webhook()

    # start all bridges
    self.connect_task = create_task(self.connect_bridges())

  def get_server(self, choice: Choice[str]) -> tuple[Bridge, Server]:
    return _servers[(choice.name, choice.value)]

  # TODO: investigate having a more central processor
  # currently has 1 for each bridge
  async def process(self, bridge: Bridge):
    async for resp in bridge.connect():
      msg = resp.message
      if chat := re.search(r"<(.*?)> (.*)$", msg):
        logger.info(msg)
        await self.handle_chat(resp, chat)
      elif join := re.search(r"(.*) (joined|left)", msg):
        logger.info(msg)
        await self.handle_join_leave(resp.server, join)

  async def connect_bridges(self):
    async with asyncio.TaskGroup() as tg:
      for bridge in self.bridges:
        _ = tg.create_task(self.process(bridge))

  async def close_bridges(self):
    async with asyncio.TaskGroup() as tg:
      for bridge in self.bridges:
        _ = tg.create_task(bridge.close())

  async def relay(self, target: Server | None, msg: str):
    async with asyncio.TaskGroup() as tg:
      for bridge in self.bridges:
        for server in bridge.servers:
          if server is not target:
            _ = tg.create_task(bridge.send(f"RCON {server.name} tellraw @a {msg}"))

  async def handle_chat(self, response: MSG, chat: re.Match[str]):
    author, message = chat.groups()

    author = author.replace(r"\_", "_")
    if " " in author:
      avatar = "https://mc-heads.net/head/steve"
    else:
      avatar = f"https://mc-heads.net/head/{author}"

    await self.webhook.send(message, username=author, avatar_url=avatar)

    tellraw = json.dumps(
      [
        "",
        {
          "text": f"[{response.server.display}]",
          "color": str(response.server.color),
        },
        f" {author}: {message}",
      ]
    )

    await self.relay(response.server, tellraw)

  async def handle_join_leave(self, source: Server, matches: re.Match[str]):
    user, action = matches.groups()

    await self.webhook.send(
      f"*{user} {action} {source.joinname}!*",
      username=source.display,
      avatar_url=self.config.avatar,
    )

    tellraw = json.dumps(
      [
        f"{user} {action} ",
        {
          "text": source.joinname,
          "color": str(source.color),
        },
        "!",
      ]
    )

    await self.relay(source, tellraw)

  @override
  async def on_message(self, message: discord.Message):
    await super().on_message(message)

    if message.channel.id != self.config.bridge_channel:
      return

    if message.author.bot:
      return

    message_ = self.create_message(message)
    reply = self.create_reply(message)
    if reply is None:
      tellraw = (
        [
          "",
          {
            "text": "[Discord]",
            "color": str(self.config.name_color),
          },
          f" {message_.author}: {message_.content}",
        ],
      )
    else:
      tellraw = [
        "",
        {
          "text": f"┌─{reply.author}: {reply.content}\n",
          "color": str(self.config.reply_color),
        },
        {
          "text": "[Discord]",
          "color": str(self.config.name_color),
        },
        f" {message_.author}: {message_.content}",
      ]

    await self.relay(None, json.dumps(tellraw))

  async def load_cogs(self):
    for ext in extensions:
      name = f"cogs.{ext}"
      try:
        await self.load_extension(name)
      except commands.ExtensionAlreadyLoaded:
        await self.reload_extension(name)
      logger.debug(f"Loaded {ext}")

    logger.info("Loaded extensions")

  async def set_webhook(self):
    channel = await self.fetch_channel(self.config.bridge_channel)
    if not isinstance(channel, discord.TextChannel):
      raise TypeError("Bridge channel incorrectly configured")

    webhooks = await channel.webhooks()
    for webhook in webhooks:
      if webhook.name == "ngb-chatbridge":
        self.webhook = webhook
        break
    else:
      self.webhook = await channel.create_webhook(name="ngb-chatbridge")

    logger.info("Webhook setup!")

  async def log(self, message: str):
    channel = await self.fetch_channel(self.config.log_channel)
    if not isinstance(channel, discord.TextChannel):
      raise TypeError("Log channel incorrectly configured")
    _ = await channel.send(message)

  def create_message(self, message: discord.Message) -> Message:
    author = message.author.display_name
    content = message.clean_content
    if message.attachments:
      content += " [ATT]"
    return Message(author, content)

  def create_reply(self, message: discord.Message) -> Message | None:
    if not isinstance(message.reference, discord.MessageReference):
      return None

    reply = message.reference.resolved
    if not isinstance(reply, discord.Message):
      return None
