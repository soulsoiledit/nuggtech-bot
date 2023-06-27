import re
from typing import Optional

import logging

import asyncio

from websockets import client

import discord

from bot import PropertyBot, ServerConfig, MCServer

regexs = {
    "join_messsage": re.compile(r"\[.*\] (.*) (left|joined) the game"),
    "chat_message": re.compile(r"<(.*)> (.*)"),
    "server_status": re.compile(r".* (\d+) .* (\d+)"),
    "backup_file": re.compile(r"(\S+\.tar\.gz) \((.*) (.*)\)")
}

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

async def process_chat_message(bot: PropertyBot, content: re.Match, webhook: discord.Webhook, server_config: ServerConfig):
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
                        await process_chat_message(bot, content, webhook, server_config)
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
