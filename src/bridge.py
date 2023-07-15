import re
from typing import Optional

import logging

import asyncio

from websockets import client

import discord

from bot import PropertyBot, ServerConfig, MCServer

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

async def process_chat_message(bot: PropertyBot, content: re.Match, webhook: Optional[discord.Webhook], server_config: ServerConfig):
    username = content.group(1).replace("\\", "")
    message = content.group(2)
    avatar = f"https://mc-heads.net/head/{username}.png"

    if webhook:
        await webhook.send(message, username=username, avatar_url=avatar)

    formatted = await format_message(bot, server_config.name, username, message )
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
                if is_join_leave := re.search(r"\[.*\] (.*) (left|joined) the game", response):
                    await process_join_message(bot, is_join_leave, server_config)
                elif content := re.search(r"<(.*)> (.*)", response):
                    await process_chat_message(bot, content, webhook, server_config)
                else:
                    # check only commands sent by the server
                    if not re.search(r"MSG \[.*\] \[", response):
                        print(repr(response))

                        counter = [
                            "No items have been",
                            "No items for",
                            "hasn't started counting",
                            "Items for"
                        ]

                        warp_status = [
                            "Estimated remaining time",
                            "Tick warp has not started"
                        ]

                        if any(search in response for search in counter):
                            await process_counter(bot, response)
                        elif "Top 10 counts" in response:
                            await process_tick_entities(bot, response)
                        elif "The Rest, whatever" in response:
                            await process_tick_health(bot, response)
                        elif any(search in response for search in warp_status):
                            await process_tick_warp_status(bot, response)

            case "LIST" | "LIST_BACKUPS" | "BACKUP" | "CHECK" | "HEARTBEAT":
                await bot.old_messages.put(response)

async def process_tick_entities(bot: PropertyBot, message: str):
    infolines = message.split("\n")[1:]
    embed = discord.Embed(title="/tick entities", color=0xa6e3a1)
    desc = ""
    for line in infolines:
        cleaned = re.sub(r"^\[.*?\] ", "", line)
        bolded = [
            "Average tick time",
            "Top 10 counts:",
            "Top 10 CPU hogs:"
        ]
        if any(x in line for x in bolded):
            desc += "**"+cleaned+"**\n"
        else:
            desc += cleaned+"\n"
    embed.description = desc

    if bot.webhook:
        await bot.webhook.send(embed=embed)

async def process_tick_health(bot: PropertyBot, message: str):
    infolines = message.split("\n")[1:]
    embed = discord.Embed(title="/tick health", color=0xa6e3a1)
    desc = ""
    for line in infolines:
        cleaned = re.sub(r"^\[.*?\] ", "", line)
        bolded = [
            "Average tick time",
            "overworld:",
            r"the\_nether:",
            r"the\_end:",
        ]
        if any(x in cleaned for x in bolded):
            desc += f"**{cleaned}**\n"
        elif "The Rest, whatever" in cleaned:
            desc += f"*{cleaned}*\n"
        else:
            desc += f"{cleaned}\n"
    embed.description = desc

    if bot.webhook:
        await bot.webhook.send(embed=embed)

async def process_counter(bot: PropertyBot, message: str):
    infolines = message.split("\n")
    embed = discord.Embed(title="/counter", color=0xa6e3a1)
    desc = ""

    colormap = {
        "white": 0xe4e4e4,
        "light_gray": 0xa0a7a7,
        "gray": 0x414141,
        "black": 0x181414,
        "red": 0x9e2b27,
        "orange": 0xea7e35,
        "yellow": 0xc2b51c,
        "lime": 0x39ba2e,
        "green": 0x364b18,
        "light_blue": 0x6387d2,
        "cyan": 0x267191,
        "blue": 0x253193,
        "purple": 0x7e34bf,
        "magenta": 0xbe49c9,
        "pink": 0xd98199,
        "brown": 0x56331c,
    }

    for line in infolines:
        cleaned = re.sub(r"(^[(MSG )]*\[.*?\] |\[X\])", "", line).strip()

        if "Items for" in cleaned:
            embed.color = colormap[cleaned.replace("\\_", "_").split()[2]]
            desc += f"**{cleaned}**\n"
        else:
            desc += f"{cleaned}\n"

    embed.description = desc

    if bot.webhook:
        await bot.webhook.send(embed=embed)

async def process_tick_warp_status(bot: PropertyBot, message: str):
    infolines = message.split("\n")[1:]
    embed = discord.Embed(title="/tick warp status", color=0xa6e3a1)
    desc = ""
    for line in infolines:
        cleaned = re.sub(r"^\[.*?\] ", "", line)
        bolded = [
            "Average MSPT",
            "[",
        ]
        if any(x in cleaned for x in bolded):
            desc += f"**{cleaned}**\n"
        else:
            desc += f"{cleaned}\n"
    embed.description = desc

    if bot.webhook:
        await bot.webhook.send(embed=embed)

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
            matches = re.search(r"(\S+\.tar\.gz) \((.*) (.*)\)", line)

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
        server_message = 'tellraw @a ["",{{"text":"┌─ {}: {}","color":"{}"}},{{"text":"\\n"}},{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
            reply_user,
            reply_message,
            bot.discord_config.reply_color,
            source,
            user,
            bot.discord_config.color,
            message
        )
    else:
        name = None
        color = None
        if source == "Discord":
            name = source
            color = bot.discord_config.color
        else:
            name = bot.servers[source].config.display_name
            color = bot.servers[source].config.color

        server_message = 'tellraw @a ["",{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
            name,
            user,
            color,
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

        server_status = re.search(r".* (\d+) .* (\d+)", status)
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
