import re, logging, asyncio

from websockets import client, exceptions
import discord

logger = logging.getLogger("discord")


class DiscordConfig:
    def __init__(self, config: dict) -> None:
        self.token = config["bot_token"]

        self.maintainer = config["maintainer"]
        self.bridge_channel = config["bridge_channel"]
        self.log_channel = config["log_channel"]

        self.avatar = config["avatar"]
        self.color = config["color"]
        self.reply_color = config["reply_color"]


class Server:
    def __init__(self, server_config: dict) -> None:
        self.name = server_config["name"]
        self.ip = server_config["ip"]
        self.port = server_config["port"]
        self.ws_pass = server_config["ws_password"]

        self.display_name = server_config["display_name"]
        self.nickname = server_config["nickname"]
        self.color = server_config["color"]
        self.discord_color = discord.Color.from_str(self.color)
        self.creative = server_config["creative"]

        self.websocket: client.WebSocketClientProtocol | None = None


ServersDict = dict[str, Server]
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
            await tg.create_task(setup_connection(bridge_data, server, close_existing))


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
            message = response.split(maxsplit=2)[2]
            if chat_msg := re.search(r"<(.*?)> (.*)$", message):
                await handle_chat(bridge_data, server, chat_msg)
            elif join_msg := re.search(r".* (joined|left)", message):
                await handle_join_leave(bridge_data, server, join_msg)
            elif re.search(r"Average tick time|Top 10 counts", message):
                await bridge_data.profile_queue.put(response)
            else:
                logger.warn(f"Unhandled! {server} {message}")
        case "RCON":
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

    await bridge_data.webhook.send(
        message,
        username=username,
        avatar_url=f"https://mc-heads.net/head/{username}.png"
    )

    # TODO: Relay to other servers

async def handle_join_leave(bridge_data: BridgeData, source_server: Server, matches: re.Match):
    action = matches.group()

    bot_username = source_server.display_name
    location = source_server.nickname

    message = f"*{action} the {location}!*"
    await bridge_data.webhook.send(
        message,
        username=bot_username,
        avatar_url=bridge_data.config.avatar
    )

# async def process_chat_message(bot: PropertyBot, content: re.Match, webhook: Optional[discord.Webhook], server_config: ServerConfig):
#     username = content.group(1).replace("\\", "")
#     message = content.group(2)
#     avatar = f"https://mc-heads.net/head/{username}.png"
#
#     if webhook:
#         await webhook.send(message, username=username, avatar_url=avatar)
#
#     formatted = await format_message(bot, server_config.name, username, message )
#     await bridge_chat(bot, formatted, server_config.name)

# async def listen(bot: PropertyBot, server: MCServer):
#     webhook = bot.webhook
#     websocket = server.websocket
#     server_config = server.config
#
#     server_name = server_config.name
#     print(f"Setup listener for {server_name}!")
#
#     async for response in websocket:
#         response = str(response)
#
#         response_words = response.split()
#         logger.info(response)
#
#         resp_type = response_words[0]
#         match resp_type:
#                 else:
#                     # check only commands sent by the server
#                     if not re.search(r"MSG \[.*\] \[", response):
#                         print(repr(response))
#
#                         counter = [
#                             "No items have been",
#                             "No items for",
#                             "hasn't started counting",
#                             "Items for"
#                         ]
#
#                         warp_status = [
#                             "Estimated remaining time",
#                             "Tick warp has not started"
#                         ]
#
#                         if any(search in response for search in counter):
#                             await process_counter(bot, response)
#                         elif "Top 10 counts" in response:
#                             await process_tick_entities(bot, response)
#                         elif "The Rest, whatever" in response:
#                             await process_tick_health(bot, response)
#                         elif any(search in response for search in warp_status):
#                             await process_tick_warp_status(bot, response)
#             case "LIST" | "LIST_BACKUPS" | "BACKUP" | "CHECK" | "HEARTBEAT":
#                 await bot.old_messages.put(response)

# async def process_tick_entities(bot: PropertyBot, message: str):
#     infolines = message.split("\n")[1:]
#     embed = discord.Embed(title="/tick entities", color=0xa6e3a1)
#     desc = ""
#     for line in infolines:
#         cleaned = re.sub(r"^\[.*?\] ", "", line)
#         bolded = [
#             "Average tick time",
#             "Top 10 counts:",
#             "Top 10 CPU hogs:"
#         ]
#         if any(x in line for x in bolded):
#             desc += "**"+cleaned+"**\n"
#         else:
#             desc += cleaned+"\n"
#     embed.description = desc
#
#     if bot.webhook:
#         await bot.webhook.send(embed=embed)
#
# async def process_tick_health(bot: PropertyBot, message: str):
#     infolines = message.split("\n")[1:]
#     embed = discord.Embed(title="/tick health", color=0xa6e3a1)
#     desc = ""
#     for line in infolines:
#         cleaned = re.sub(r"^\[.*?\] ", "", line)
#         bolded = [
#             "Average tick time",
#             "overworld:",
#             r"the\_nether:",
#             r"the\_end:",
#         ]
#         if any(x in cleaned for x in bolded):
#             desc += f"**{cleaned}**\n"
#         elif "The Rest, whatever" in cleaned:
#             desc += f"*{cleaned}*\n"
#         else:
#             desc += f"{cleaned}\n"
#     embed.description = desc
#
#     if bot.webhook:
#         await bot.webhook.send(embed=embed)
#
# async def process_counter(bot: PropertyBot, message: str):
#     infolines = message.split("\n")
#     embed = discord.Embed(title="/counter", color=0xa6e3a1)
#     desc = ""
#
#     colormap = {
#         "white": 0xe4e4e4,
#         "light_gray": 0xa0a7a7,
#         "gray": 0x414141,
#         "black": 0x181414,
#         "red": 0x9e2b27,
#         "orange": 0xea7e35,
#         "yellow": 0xc2b51c,
#         "lime": 0x39ba2e,
#         "green": 0x364b18,
#         "light_blue": 0x6387d2,
#         "cyan": 0x267191,
#         "blue": 0x253193,
#         "purple": 0x7e34bf,
#         "magenta": 0xbe49c9,
#         "pink": 0xd98199,
#         "brown": 0x56331c,
#     }
#
#     for line in infolines:
#         cleaned = re.sub(r"(^[(MSG )]*\[.*?\] |\[X\])", "", line).strip()
#
#         if "Items for" in cleaned:
#             embed.color = colormap[cleaned.replace("\\_", "_").split()[2]]
#             desc += f"**{cleaned}**\n"
#         else:
#             desc += f"{cleaned}\n"
#
#     embed.description = desc
#
#     if bot.webhook:
#         await bot.webhook.send(embed=embed)
#
# async def process_tick_warp_status(bot: PropertyBot, message: str):
#     infolines = message.split("\n")[1:]
#     embed = discord.Embed(title="/tick warp status", color=0xa6e3a1)
#     desc = ""
#     for line in infolines:
#         cleaned = re.sub(r"^\[.*?\] ", "", line)
#         bolded = [
#             "Average MSPT",
#             "[",
#         ]
#         if any(x in cleaned for x in bolded):
#             desc += f"**{cleaned}**\n"
#         else:
#             desc += f"{cleaned}\n"
#     embed.description = desc
#
#     if bot.webhook:
#         await bot.webhook.send(embed=embed)
#
#
# async def format_message(bot: PropertyBot, source: str, user: str, message: str, reply_user: Optional[str] = None, reply_message: Optional[str] = None):
#     server_message = ""
#
#     if reply_user is not None:
#         server_message = 'tellraw @a ["",{{"text":"┌─ {}: {}","color":"{}"}},{{"text":"\\n"}},{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
#             reply_user,
#             reply_message,
#             bot.discord_config.reply_color,
#             source,
#             user,
#             bot.discord_config.color,
#             message
#         )
#     else:
#         name = None
#         color = None
#         if source == "Discord":
#             name = source
#             color = bot.discord_config.color
#         else:
#             name = bot.servers[source].config.display_name
#             color = bot.servers[source].config.color
#
#         server_message = 'tellraw @a ["",{{"text":"[{}] {}:","color":"{}"}},{{"text":" {}"}}]'.format(
#             name,
#             user,
#             color,
#             message,
#         )
#
#     return server_message
