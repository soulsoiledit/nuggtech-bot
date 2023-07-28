import logging
from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands

import bot, bridge

logger = logging.getLogger("nuggtech-bot")

class Debug(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def reload(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await interaction.response.send_message(f"Reloaded modules!", ephemeral=True)
            await self.bot.load_cogs(reloading=True)
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def reload_config(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await interaction.response.send_message(f"Reloaded config!", ephemeral=True)
            await self.bot.reload_config()
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def text_sync(self, ctx: commands.Context, operation: Literal["quick", "copy", "clear", "global"]):
        if ctx.author.id == self.bot.discord_config.maintainer:
            await ctx.message.delete()
            if ctx.guild:
                output: str | None
                match operation:
                    case "quick":
                        await self.bot.tree.sync(guild=ctx.guild)
                        output = "Synced guild commands"
                    case "copy":
                        self.bot.tree.copy_global_to(guild=ctx.guild)
                        await self.bot.tree.sync(guild=ctx.guild)
                        output = "Copied and synced commands"
                    case "clear":
                        self.bot.tree.clear_commands(guild=ctx.guild)
                        await self.bot.tree.sync(guild=ctx.guild)
                        output = "Cleared and synced commands"
                    case "global":
                        await self.bot.tree.sync()
                        output = "Synced global commands"
                logger.info(output)

    @app_commands.command(name="sync")
    @app_commands.default_permissions(administrator=True)
    async def slash_sync(self, interaction: discord.Interaction, operation: Literal["guild", "copy", "clear", "global"]):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await interaction.response.defer(ephemeral=True)
            if interaction.guild:
                output: str | None
                match operation:
                    case "guild":
                        await self.bot.tree.sync(guild=interaction.guild)
                        output = "Synced guild commands"
                    case "copy":
                        self.bot.tree.copy_global_to(guild=interaction.guild)
                        await self.bot.tree.sync(guild=interaction.guild)
                        output = "Copied and synced commands"
                    case "clear":
                        self.bot.tree.clear_commands(guild=interaction.guild)
                        await self.bot.tree.sync(guild=interaction.guild)
                        output = "Cleared and synced commands"
                    case "global":
                        await self.bot.tree.sync()
                        output = "Synced global commands"
                logger.info(output)
                await interaction.followup.send(output, ephemeral=True)
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def fix_bridges(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await interaction.response.send_message("Restarted missing bridges...", ephemeral=True)
            if self.bot.webhook:
                bridge_data = bridge.BridgeData(self.bot.discord_config, self.bot.webhook, self.bot.servers, self.bot.response_queue)
                await bridge.setup_all_connections(bridge_data)
            logger.info("Restarted missing bridges")
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

    @app_commands.command()
    @app_commands.default_permissions(administrator=True)
    async def reset_bridges(self, interaction: discord.Interaction):
        if interaction.user.id == self.bot.discord_config.maintainer:
            await interaction.response.send_message("Restarted all bridges...", ephemeral=True)
            if self.bot.webhook:
                bridge_data = bridge.BridgeData(self.bot.discord_config, self.bot.webhook, self.bot.servers, self.bot.response_queue)
                await bridge.setup_all_connections(bridge_data, close_existing=True)
            logger.info("Restarted all bridges")
        else:
            await interaction.response.send_message("Don't touch this!", ephemeral=True)

async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Debug(bot))
