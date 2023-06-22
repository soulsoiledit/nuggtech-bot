import tomllib
import re
import argparse
import random
from typing import Optional

import logging

import asyncio
from asyncio import Queue

from websockets import client

import discord
from discord import app_commands
from discord.ext.commands import Bot

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

class PropertyBot(Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=":", intents=intents)

        self.init_extensions = [ "server" ]
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
            await bot.load_extension('cogs.'+extension)
            print(f"Loaded extension {extension}!")

bot = PropertyBot()
regexs = {
    "join_messsage": re.compile(r"\[.*\] (.*) (left|joined) the game"),
    "chat_message": re.compile(r"<(.*)> (.*)"),
    "server_status": re.compile(r".* (\d+) .* (\d+)"),
    "backup_file": re.compile(r"(\S+\.tar\.gz) \((.*) (.*)\)")
}

@bot.tree.command()
@app_commands.checks.cooldown(rate=1, per=60)
async def pet(interaction: discord.Interaction):
    await interaction.response.send_message(f"Me{'o'*random.randint(1, 5)}w! ({bot.latency*1000:.1f} ms)")

@bot.tree.command()
@app_commands.checks.has_role(bot.discord_config.admin_role)
async def reload(interaction: discord.Interaction):
    if interaction.user.id == bot.discord_config.maintainer:
        for ext in bot.init_extensions:
            await bot.reload_extension('cogs.'+ext)
            await interaction.response.send_message(f"Reloaded {ext}")

        guild = discord.Object(bot.discord_config.guild)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await interaction.response.send_message("Don't touch this!", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingRole):
        await interaction.response.send_message("Missing permissions!", ephemeral=True)
    elif isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command on cooldown! Try again in {error.retry_after:.0f}s...", ephemeral=True)

@bot.event
async def on_ready():
    print("Ready!")
    await setup_bridges(bot)

@bot.event
async def on_message(msg: discord.Message):
    if msg.channel.id == bot.discord_config.bridge_channel and not msg.author.bot:
        user = msg.author.name
        message = str(msg.clean_content)

        if msg.attachments:
            message += " [IMG]"

        # Handle replies
        reply = msg.reference
        reply_user = None
        reply_message = None

        if reply is not None:
            reply = reply.resolved
            if isinstance(reply, discord.Message):
                reply_user = reply.author.name
                reply_message = reply.clean_content

                if reply.attachments:
                    reply_message += " [IMG]"

        formatted = await format_message(bot, "Discord", user, message, reply_user, reply_message)
        await bridge_chat(bot, formatted)

async def setup_connection(server_config: ServerConfig, servers: dict[str, MCServer]):
    server_name = server_config.name
    try:
        print("Attempting websocket connection to {}".format(server_name))

        url = "ws://{}:{}/taurus".format(server_config.ip, server_config.port)
        websocket = await client.connect(url)
        await websocket.send(server_config.ws_pass)

        servers[server_name] = MCServer(websocket, server_config)
        print(f"Connected to {server_name}!")

        return True
    except:
        print(f"Failed to connect to {server_name}!")
        return False

async def process_join_message(bot: PropertyBot, content: re.Match, server_config: ServerConfig):
    username = content.group(1)
    action = content.group(2)

    bot_username = server_config.display_name
    nickname = server_config.nickname

    discord_message = f"*{username} {action} the {nickname}!*"
    if bot.webhook:
        await bot.webhook.send(discord_message, username=bot_username, avatar_url=bot.discord_config.avatar)

async def process_chat_message(content: re.Match, webhook: discord.Webhook, server_config: ServerConfig):
    username = content.group(1).replace("\\", "")
    message = content.group(2)
    avatar = f"https://mc-heads.net/head/{username}.png"

    await webhook.send(message, username=username, avatar_url=avatar)

    source = server_config.display_name
    formatted = await format_message(bot, source, username, message )
    await bridge_chat(bot, formatted, server_config.name)

async def listen(bot: PropertyBot, server: MCServer):
    webhook = bot.webhook
    websocket = server.websocket
    server_config = server.config

    server_name = server_config.name
    print(f"Setup listener for {server_name}!")

    async for response in websocket:
        response = str(response)
        response_words = response.split()
        logging.info(response)

        resp_type = response_words[0]
        match resp_type:
            case "MSG":
                is_join_leave = regexs["join_messsage"].search(response)
                if is_join_leave:
                    await process_join_message(bot, is_join_leave, server_config)
                else:
                    content = regexs["chat_message"].search(response)
                    if content and webhook:
                        await process_chat_message(content, webhook, server_config)
            case "LIST" | "LIST_BACKUPS" | "BACKUP" | "CHECK" | "HEARTBEAT":
                await bot.old_messages.put(response)

async def process_backup_list(bot: PropertyBot):
    msg = await bot.old_messages.get()

    embed = discord.Embed(title="Backups", color=0x89b4fa)

    description = ""
    if msg == "LIST_BACKUPS ":
        description += "There are no backups! :3"
    else:
        total = 0
        count = 1

        for line in msg.split("\n"):
            matches = regexs["backup_file"].search(line)

            if matches:
                filename = matches.group(1)
                size = float(matches.group(2))
                unit = matches.group(3)

                match unit:
                    case "B":
                        total += size
                    case "MiB":
                        total += size * 1048576
                    case "GiB":
                        total += size * 1073741824

                if count <= 10:
                    description += "{} ({:.1f} {})\n".format(
                        filename,
                        size,
                        unit,
                    )

                count += 1

        total /= 1048576
        description += "\n**Total:** {:.2f} MiB".format(
            total,
        )

    embed.description = description
    embed.set_author(name="NuggTech", icon_url=bot.discord_config.avatar)

    return embed

async def format_message(bot: PropertyBot, source: str, user: str, message: str, reply_user: Optional[str] = None, reply_message: Optional[str] = None):
    server_message = ""
    if reply_user is not None:
        server_message = 'tellraw @a ["",{{"text":"{}: {}","color":"{}"}},{{"text":"\\n"}},{{"text":">[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
            reply_user,
            reply_message,
            bot.discord_config.reply_color,
            source,
            user,
            bot.discord_config.color,
            message
        )
    else:
        server_message = 'tellraw @a ["",{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
            source,
            user,
            bot.discord_config.color,
            message,
        )

    return server_message
   
async def bridge_chat(bot: PropertyBot, message: str, source_server: Optional[str] = None):
    for server in bot.servers.keys():
        if server != source_server:
            await bridge_send(bot, server, f"CMD {server} {message}")

async def bridge_send(bot: PropertyBot, target_server: str, command: str):
    server = bot.servers[target_server]
    ws = server.websocket

    await ws.send(command)

async def setup_bridges(bot: PropertyBot):
    if bot.listeners:
        task: asyncio.Task
        for task in bot.listeners:
            task.cancel()
        bot.listeners.clear()
        print("Stopped listeners!")

    for server in bot.server_config:
        bot.listeners.append(asyncio.create_task(setup_connection(server, bot.servers)))
    await asyncio.gather(*bot.listeners)

    bot.listeners.clear()
    for server in bot.servers.values():
        bot.listeners.append(asyncio.create_task(listen(bot, server)))

async def check_servers(bot: PropertyBot):
    online_servers = {}
    for server in bot.servers.keys():
        await bridge_send(bot, server, f"LIST {server}")
        status = await bot.old_messages.get()

        server_status = regexs["server_status"].search(status)
        if server_status:
            online = server_status.group(1)
            total = server_status.group(2)
            online_servers[server] = online, total

    desc = ""
    for server in bot.server_config:
        name = server.name
        display = server.display_name

        status = ""
        if name in online_servers.keys():
            status = ":white_check_mark: ({}/{})".format(
                online_servers[name][0],
                online_servers[name][1]
            )
        else:
            status = ":x:"

        desc += "**{}:** {}\n".format(display, status)


    embed = discord.Embed(title="Servers", color=0x89b4fa, description=desc)
    embed.set_author(name="NuggTech", icon_url=bot.discord_config.avatar)

    return embed

def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--verbosity", help="set verbosity level")
    args = parser.parse_args()

    if args.verbosity:
        logging.basicConfig(level=getattr(logging, args.verbosity.upper()))

    asyncio.run(bot.start(bot.discord_config.token))

if __name__ == "__main__":
    main()
