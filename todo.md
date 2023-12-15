- Write documentation

- Startup
  - Configuration
    - Load configuration from specified file
    - Set correct configuration to discord bot
    - Set correct parameters in cogs
  - Connections
    - Setup connections and set websockets
    - Setup listeners
      - Process messages
    - Use saved websocket to send new messages

- Chatbridge
  - Uses `taurus` as the backend
  - Send messages from MC to Discord channel
    - Send chat messages
    - Send player join, leave, and death messages
    - Broadcast messages to configured servers
    - Show output from commands send by the Discord bot
  - Send messages from Discord channel to MC
    - Send discord messages
    - Display when there's attached content such as images or files
    - Indicate reply messages and show the reply user and message
    - Properly format user mentions, channel names, message links, and emotes
  - Use RCON to send MC commands of any form

- Commands
  - Maintainer
    - Reload configuration
    - Reload modules
    - Sync commands
    - Restart taurus connections
  - Admin
    - **Log necessary commands to log channel**
    - Start server
    - Stop server
    - Restart server
    - Whitelist
      - Add players to the whitelist
      - Remove players from the whitelist
      - Add players to OP on creative servers
      - Remove players from OP on creative servers
    - List current backups
    - Create new backups
    - Arbitrary RCON commands to creative-enabled servers
  - Member
    - List servers
    - Check server health
    - List players on servers

    - Carpet integration
     - /player commands (pending approval)
     - /tick (pending approval)

     - /profile
      - health
      - entities

     - /spawn
      - spawn tracking
      - spawn tracking start
      - spawn tracking stop
      - spawn tracking restart
     - /counter
      - counter
      - counter wool
      - counter reset
      - counter wool reset

     - Carpet TIS integration
      - /lifetime
      - /raid
      - /scounter
      - /tick warp status
  - Public
    - Pet the NuggCat
    - Show player statistics from SMP
      - Use shell script and tmux to push input to taurus

# Todo
- Echo player join to other servers

- Add help command and readme documentation

- Separate queues into per server and per command
  - Use helper function to sort output type

- Improve text normalization
