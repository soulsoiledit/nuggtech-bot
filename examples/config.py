from discord import Color

from bridge import Bridge, Config, Server

# this is what the current and very likely to change config format looks like
# the config format is written in python for ease of use and capabilities for advanced usage
# put this config next to main.py in the src/ directory

# this file may become outdated and not work with newer versions if I forget, please leave an issue or
# contact me on discord if this is the case

config = Config(
  # your discord bot's token
  token="MT...",
  # the channel ID where chat messages will be sent between discord and mc
  bridge_channel=1111111111111111111,
  # the channel ID where many admin actions are logged
  log_channel=1111111111111111111,
  # a url to the avatar you wish to use for your bot
  # use any format that discord supports
  avatar="awebsite.com/avatar.jpg",
  # the color of the [Discord] tag in discord messages
  # use 0x followed by the hex representation of the color
  name_color=Color(0x1E66F5),
  # the color of discord replies
  reply_color=Color(0x4C4F69),
)

bridges: list[Bridge] = [
  # for each instance of **taurus**, define a bridge
  Bridge(
    # a unique name from other instances
    name="taurus",
    # the ip address of the server hosting this taurus instance
    ip="0.0.0.0",
    # the ws_port from this taurus' config.json
    port=7500,
    # the ws_password from this taurus' config.json
    password="password",
    servers=[
      # for each **server** connected to this instance, define a server
      Server(
        # use the same name as in this servers' .json config
        name="server",
        # displayed for messages from this server
        # for example: [Server] username: message
        # or as the bot's name when sending join messages on this server
        display="Server",
        # the server name in join messages
        # for example: username joined server!
        joinname="server",
        # the color associated to this server
        color=Color(0xD20F39),
      ),
      # define additional servers
      # Server(
      #   ...
      # )
    ],
  ),
  # define additional bridges
  # Bridge(
  #   ...
  # )
]
