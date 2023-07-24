import discord
from discord.ext import commands
from discord import TextChannel, app_commands
from discord.app_commands import Choice

import bot
from bridge import bridge_send, handle_whitelist

class Whitelist(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    whitelist_commands = app_commands.Group(
        name="whitelist",
        description="Add and remove players from the whitelist"
    )

    @whitelist_commands.command(name="add", description="Adds a user to a server's whitelist")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.describe(user="target user")
    @app_commands.choices(server=bot.server_choices)
    async def whitelist_add(self, interaction: discord.Interaction, server: Choice[str], user: str):
        target = server.value
        await interaction.response.defer(ephemeral=True)
        await bridge_send(self.bot.servers, target, f"RCON {target} whitelist add {user}")
        result = await handle_whitelist(self.bot.response_queue)
        if result[0]:
            await interaction.followup.send(f"Added `{user}` to `{target}`")
            log_channel = self.bot.get_channel(self.bot.discord_config.log_channel)
            if isinstance(log_channel, TextChannel):
                await log_channel.send(f"`{interaction.user.name}` added `{user}` to `{target}`")
        else:
            await interaction.followup.send(result[1])

    @whitelist_commands.command(name="remove", description="Removes a user from a server's whitelist")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.describe(user="target user")
    @app_commands.choices(server=bot.server_choices)
    async def whitelist_remove(self, interaction: discord.Interaction, server: Choice[str], user: str):
        target = server.value
        await interaction.response.defer(ephemeral=True)
        await bridge_send(self.bot.servers, target, f"RCON {target} whitelist remove {user}")
        result = await handle_whitelist(self.bot.response_queue)
        if result[0]:
            await interaction.followup.send(f"Removed `{user}` from `{target}`")
            log_channel = self.bot.get_channel(self.bot.discord_config.log_channel)
            if isinstance(log_channel, TextChannel):
                await log_channel.send(f"`{interaction.user.name}` removed `{user}` from `{target}`")
        else:
            await interaction.followup.send(result[1])

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Whitelist(bot))
