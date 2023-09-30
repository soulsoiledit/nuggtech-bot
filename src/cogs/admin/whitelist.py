import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send


class Whitelist(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    whitelist_commands = app_commands.Group(
        name="whitelist", description="Add and remove players from the whitelist"
    )

    async def handle_whitelist(self) -> tuple[bool, str]:
        response = await self.bot.response_queue.get()
        success = response.split()[0]
        success = success == "Added" or success == "Removed"
        return (success, response)

    @whitelist_commands.command(
        name="add", description="Adds a user to a server's whitelist"
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    @app_commands.describe(user="target user")
    async def whitelist_add(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        user: str,
    ):
        target = server.value
        await interaction.response.defer(ephemeral=True)
        await bridge_send(
            self.bot.servers, target, f"RCON {target} whitelist add {user}"
        )
        result = await self.handle_whitelist()
        if result[0]:
            await interaction.followup.send(f"Added `{user}` to {target}!")
            log_channel = await self.bot.fetch_channel(
                self.bot.discord_config.log_channel
            )
            if isinstance(log_channel, discord.TextChannel):
                await log_channel.send(
                    f"`{interaction.user.name}` added `{user}` to {target}"
                )
        else:
            await interaction.followup.send(result[1])

    @whitelist_commands.command(
        name="remove", description="Removes a user from a server's whitelist"
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    @app_commands.describe(user="target user")
    async def whitelist_remove(
        self,
        interaction: discord.Interaction,
        server: app_commands.Choice[str],
        user: str,
    ):
        target = server.value
        await interaction.response.defer(ephemeral=True)
        await bridge_send(
            self.bot.servers, target, f"RCON {target} whitelist remove {user}"
        )
        result = await self.handle_whitelist()
        if result[0]:
            await interaction.followup.send(f"Removed `{user}` from {target}!")
            log_channel = await self.bot.fetch_channel(
                self.bot.discord_config.log_channel
            )
            if isinstance(log_channel, discord.TextChannel):
                await log_channel.send(
                    f"`{interaction.user.name}` removed `{user}` from {target}"
                )
        else:
            await interaction.followup.send(result[1])

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Whitelist(bot))
