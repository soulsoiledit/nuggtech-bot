import asyncio
import logging
import re

import discord
from websockets import client, exceptions


class DiscordConfig:
    def __init__(
        self,
        token,
        maintainer,
        bridge_channel,
        log_channel,
        avatar,
        name_color,
        reply_color,
    ) -> None:
        self.token = token

        self.maintainer = maintainer
        self.bridge_channel = bridge_channel
        self.log_channel = log_channel

        self.avatar = avatar
        self.name_color = name_color
        self.reply_color = reply_color


class Server:
    def __init__(
        self, name, ip, port, ws_password, display_name, nickname, color, creative
    ) -> None:
        self.name = name
        self.ip = ip
        self.port = port
        self.ws_pass = ws_password

        self.display_name = display_name
        self.nickname = nickname
        self.color = color
        self.discord_color = discord.Color.from_str(self.color)
        self.creative = creative

        self.websocket: client.WebSocketClientProtocol | None = None


ServersDict = dict[str, Server]

logger = logging.getLogger("discord")

ResponseQueue = asyncio.Queue[str]


class BridgeData:
    def __init__(
        self,
        config: DiscordConfig,
        webhook: discord.Webhook,
        servers: ServersDict,
        response_queue: ResponseQueue,
        profile_queue: ResponseQueue,
    ) -> None:
        self.config = config
        self.webhook = webhook
        self.servers = servers
        self.response_queue = response_queue
        self.profile_queue = profile_queue


# Setup connections to all configured servers
async def setup_all_connections(bridge_data: BridgeData, close_existing=False):
    async with asyncio.TaskGroup() as tg:
        for server in bridge_data.servers.values():
            tg.create_task(setup_connection(bridge_data, server, close_existing))


# Setup connection to single server websocket and start listener
async def setup_connection(
    bridge_data: BridgeData, server: Server, close_existing=False
) -> None:
    try:
        if server.websocket:
            logger.info(f"Websocket already setup for {server.name}")
            if close_existing:
                await server.websocket.close()
                logger.info(f"Existing connection for {server.name} closed!")
            else:
                return

        logger.info(f"Attempting connection to {server.name}...")
        url = "ws://{}:{}/taurus".format(server.ip, server.port)
        websocket = await client.connect(url, ping_timeout=30)
        await websocket.send(server.ws_pass)
        server.websocket = websocket
        logger.info(f"Connected to {server.name}!")

        await bridge_listen(bridge_data, server)
    except ConnectionRefusedError:
        logger.warn(f"Failed to connect to {server.name}")


# Listen for messages from websocket and handle closed connections
async def bridge_listen(bridge_data: BridgeData, server: Server):
    try:
        if server.websocket:
            logger.info(f"Starting listener for {server.name}...")
            async for response in server.websocket:
                if isinstance(response, str):
                    await process_response(bridge_data, server, response)
    except exceptions.ConnectionClosedError as e:
        server.websocket = None
        logger.warn(f"Lost connection with {server.name} due to {e}")
    except exceptions.ConnectionClosedOK:
        server.websocket = None
        logger.info(f"Closed connection with {server.name}")


async def bridge_send(servers: ServersDict, target: str, command: str):
    websocket = servers[target].websocket
    if websocket:
        await websocket.send(command)


async def bridge_rcon(servers: ServersDict, target: str, command: str):
    websocket = servers[target].websocket
    if websocket:
        await websocket.send(command)


async def bridge_chat(servers: ServersDict, source: str | None, message):
    for server in servers.keys():
        if server != source:
            await bridge_send(servers, server, f"RCON {server} {message}")


async def process_response(bridge_data: BridgeData, server: Server, response: str):
    logger.info(f"RESPONSE: {response}")
    split_response = response.split(maxsplit=1)

    match split_response[0]:
        case "MSG":
            # Differentiate chat messages, join/leave, etc
            message = response
            if chat_msg := re.search(r"<(.*?)> (.*)$", message):
                await handle_chat(bridge_data, server, chat_msg)
            elif join_msg := re.search(r"\[.*\] (.*) (joined|left)", message):
                await handle_join_leave(bridge_data, server, join_msg)
            elif re.search(r"Average tick time|Top 10 counts", message):
                await bridge_data.profile_queue.put(response)
            elif stats_msg := re.search(r"({\\\"stats\\\".*)<--.*", message):
                await bridge_data.response_queue.put(stats_msg.group(1))
            else:
                logger.warn(f"Unhandled! {server.name} {message}")
        case "RCON":
            if "No player was found" in response:
                return
            if len(split_response) > 1:
                await bridge_data.response_queue.put(response.split(maxsplit=1)[1])
            logger.info(f"RCON response from {server.name}!: {response}")
        case "LIST_BACKUPS" | "BACKUP" | "LIST" | "CHECK" | "HEARTBEAT":
            if len(split_response) == 1:
                await bridge_data.response_queue.put("")
            else:
                await bridge_data.response_queue.put(response.split(maxsplit=1)[1])
        case _:
            logger.warn(f"Unhandled message type: {response}")


async def handle_chat(bridge_data: BridgeData, source: Server, matches: re.Match):
    username = matches.group(1).replace("\\", "")
    message = matches.group(2).replace("\\", "")

    if " " in username:
        avatar = "https://mc-heads.net/head/steve.png"
    else:
        avatar = f"https://mc-heads.net/head/{username}.png"

    await bridge_data.webhook.send(message, username=username, avatar_url=avatar)

    tellraw_cmd = await create_tellraw(
        bridge_data.config, bridge_data.servers, source.name, username, message, None
    )
    await bridge_chat(bridge_data.servers, source.name, tellraw_cmd)


async def handle_join_leave(
    bridge_data: BridgeData, source_server: Server, matches: re.Match
):
    username = matches.group(1)
    action = matches.group(2)

    bot_username = source_server.display_name
    location = source_server.nickname

    message = f"{username} {action} the {location}!"
    await bridge_data.webhook.send(
        f"*{message}*", username=bot_username, avatar_url=bridge_data.config.avatar
    )

    tellraw_cmd = 'tellraw @a {{"text":"{}","color":"{}"}}'.format(
        await clear_formatting(message), source_server.color
    )
    await bridge_chat(bridge_data.servers, source_server.name, tellraw_cmd)


async def clear_formatting(message):
    # Returns repr version of the string with quotes escaped properly
    return repr(message)[1:-1].replace('"', '\\"')


async def create_tellraw(
    discord_config: DiscordConfig,
    servers: ServersDict,
    source: str,
    username: str,
    message: str,
    reply: tuple[str, str] | None,
):
    tellraw_cmd = ""

    source_name = None
    color = None
    if source == "Discord":
        source_name = source
        color = discord_config.name_color
    else:
        source_name = servers[source].display_name
        color = servers[source].color

    if reply is not None:
        tellraw_cmd = 'tellraw @a ["",{{"text":"┌─ {}: {}","color":"{}"}},{{"text":"\\n"}},{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
            reply[0],
            await clear_formatting(reply[1]),
            discord_config.reply_color,
            source_name,
            username,
            color,
            await clear_formatting(message),
        )
    else:
        tellraw_cmd = 'tellraw @a ["",{{"text":"[{}] {}: ","color":"{}"}},{{"text":"{}"}}]'.format(
            source_name,
            username,
            color,
            await clear_formatting(message),
        )

    return tellraw_cmd
