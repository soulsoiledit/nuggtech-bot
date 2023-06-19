import tomllib
import re
import asyncio
from websockets import client

import discord
from discord import Webhook
from discord.ext import commands

class PropertyBot(commands.Bot):
    def __init__(self, command_prefix, intents) -> None:
        super().__init__(command_prefix, intents=intents)
        self.config = {}
        self.sockets = {}
        self.webhook = None
        self.tasks = []

class SocketServer:
    def __init__(self, socket, server: dict, online: bool = False) -> None:
        self.socket = socket
        self.server = server
        self.online = online

class DiscordConfig:
    pass

class ServerConfig:
    pass

filepath = "./secrets.toml"
with open(filepath, "rb") as f:
    config = tomllib.load(f)
discord_config = config["discord"]

extensions = [ 'server' ]

bot_token = discord_config["bot_token"]
bridge_channel_id = discord_config["bridge_channel_id"]
webhook_id = discord_config["webhook_id"]
default_avatar = discord_config["default_avatar"]
default_color = discord_config["color"]

intents = discord.Intents.default()
intents.message_content = True

bot = PropertyBot(command_prefix='/', intents=intents)
bot.config = config

regexs = {
    "join_messsage": re.compile(r"\[.*\] (.*) (left|joined) the game"),
    "chat_message": re.compile(r"<(.*)> (.*)"),
    "server_status": re.compile(r"LIST(.*)"),
}

@bot.tree.command()
async def echo(interaction: discord.Interaction, arg: str):
    webhook: Webhook = await bot.fetch_webhook(webhook_id)
    for server in config["servers"]:
        name = server["name"]
        await interaction.response.send_message(f"I said {arg} to {name}!")
        await webhook.send(f"I said {arg} to {name} in a webhook!", username="soiledit_", avatar_url=default_avatar)

@bot.tree.command()
async def reload(interaction: discord.Interaction):
    for ext in extensions:
        await bot.reload_extension('commands.'+ext)
        await interaction.response.send_message(f"Reloaded {ext}")

@bot.event
async def setup_hook():
    pass

@bot.event
async def on_ready():
    print("Ready!")

    bot.webhook = await bot.fetch_webhook(webhook_id)

    for ext in extensions:
        await bot.load_extension('commands.'+ext)
        print(f"Loaded extension {ext}!")

    # await bot.tree.sync()

    await reset_bridges(bot)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingRole):
        await interaction.response.send_message("Missing permissions!", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    username = message.author.name
    if message.channel.id == bridge_channel_id and not message.author.bot:

        if message.author.nick:
            username = message.author.nick

        final_message = str(message.clean_content)

        if message.attachments:
            final_message = f"{final_message} [Image]"

        #TODO: handle replies better
        if message.reference:
            final_message = f"{final_message} [Reply]"

        await tr_message(bot, username, final_message, None)

async def setup_connection(server_config: dict, sockets: dict):
    server_name = server_config["name"]
    try:
        print("Attempting websocket connection to {}".format(server_name))

        url = "ws://{}:{}/taurus".format(server_config["ip"], server_config["port"])
        websocket = await client.connect(url)
        await websocket.send(server_config["ws_password"])

        sockets[server_name] = SocketServer(websocket, server_config)
        print(f"Connected to {server_name}!")

        return True
    except:
        print(f"Failed to connect to {server_name}!")
        return False

async def process_join_message(content: re.Match, webhook: Webhook, chatbridge_config):
    username = content.group(1)
    action = content.group(2)

    bot_username = chatbridge_config["username"]
    nickname = chatbridge_config["nickname"]

    discord_message = f"*{username} {action} the {nickname}!*"
    await webhook.send(discord_message, username=bot_username, avatar_url=default_avatar)

async def process_chat_message(content: re.Match, webhook, server_config):
    username = content.group(1).replace("\\", "")
    message = content.group(2)
    avatar = f"https://mc-heads.net/head/{username}.png"

    await webhook.send(message, username=username, avatar_url=avatar)
    await tr_message(bot, username, message,server_config)

async def listen(socketserver: SocketServer, webhook: Webhook):
    websocket = socketserver.socket
    server_config = socketserver.server

    server_name = server_config["name"]
    print(f"Setup listener for {server_name}!")

    async for mc_message in websocket:
        mc_message: str
        # print(mc_message)

        server_status = regexs["server_status"].search(mc_message)
        if server_status:
            socketserver.online = len(server_status.group(1).strip()) > 0

        is_join_leave = regexs["join_messsage"].search(mc_message)
        if is_join_leave:
            await process_join_message(is_join_leave, webhook, server_config["chatbridge"])
        else:
            content = regexs["chat_message"].search(mc_message)
            if content:
                await process_chat_message(content, webhook, server_config)

async def tr_message(bot, user, message, sending_server):
    for socket in bot.sockets.values():
        websocket = socket.socket
        receiving_server = socket.server

        if receiving_server != sending_server:
            target_server = receiving_server["name"]
            source_name = "Discord"
            color = default_color

            if sending_server:
                source_name = sending_server["chatbridge"]["username"]
                color = sending_server["chatbridge"]["color"]

            server_message = 'RCON {} tellraw @a ["", {{"text": "[{}] {}:", "color": "{}"}}, {{"text": " {}"}}]'.format(
                target_server,
                source_name,
                user,
                color,
                message
            )

            await websocket.send(server_message)

async def tr_command(bot, target_server, command):
    socket = bot.sockets[target_server]
    websocket = socket.socket
    receiving_server = socket.server

    if receiving_server["name"] == target_server:
        await websocket.send(command)

async def reset_bridges(bot: PropertyBot):
    if bot.tasks:
        task: asyncio.Task
        for task in bot.tasks:
            task.cancel()
        bot.tasks.clear()
        print("Stopped listeners!")

    for server in config["servers"]:
        bot.tasks.append(asyncio.create_task(setup_connection(server, bot.sockets)))
    await asyncio.gather(*bot.tasks)

    await check_server_status(bot)

    bot.tasks.clear()
    for socket in bot.sockets.values():
        bot.tasks.append(asyncio.create_task(listen(socket, bot.webhook)))

async def check_server_status(bot: PropertyBot):
    for socket in bot.sockets.values():
        socket: SocketServer

        ws = socket.socket
        name = socket.server["name"]

        await ws.send(f"LIST {name}")

async def check_servers(bot):
    await check_server_status(bot)
    await asyncio.sleep(1)

    online_servers = []
    for socket in bot.sockets.values():
        socket: SocketServer
        if socket.online:
            name = socket.server["name"]
            online_servers.append(name)

    description = ""

    for server in bot.config["servers"]:
        active = ""
        if server["name"] in online_servers:
            active = ":white_check_mark:"
        else:
            active = ":x:"

        description += "**{}:** {}\n".format(server["chatbridge"]["username"], active)

    embed = discord.Embed(title="Servers", color=0xff0000, description=description)
    embed.set_author(name="NuggTech", icon_url=default_avatar)

    return embed

if __name__ == "__main__":
    asyncio.run(bot.start(bot_token))
