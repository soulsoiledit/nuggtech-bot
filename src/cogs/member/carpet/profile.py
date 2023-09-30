import re

import discord
from discord.ext import commands
from discord import app_commands

import bot
from bridge import bridge_send


class Profile(commands.Cog):
    def __init__(self, bot: bot.PropertyBot):
        self.bot = bot

    profile_commands = app_commands.Group(
        name="profile", description="Send profile command to server"
    )

    async def handle_profile_health(self, target: str):
        health = await self.bot.profile_queue.get()

        cleaned_health = ""
        for line in health.split("\n")[1:]:
            cleaned = re.sub(r"^.*Rcon: (.*)\]", r"\1", line)

            bolded = [
                "Average tick time",
                "overworld:",
                r"the\_nether:",
                r"the\_end:",
            ]
            if any(x in cleaned for x in bolded):
                cleaned_health += f"**{cleaned}**\n"
            elif "The Rest, whatever" in cleaned:
                cleaned_health += f"*{cleaned}*\n"
            else:
                cleaned_health += f"{cleaned}\n"

        server = self.bot.servers[target]

        embed = discord.Embed(title="`/profile health`")
        embed.color = server.discord_color
        embed.description = cleaned_health

        return embed

    async def handle_profile_entities(self, target: str):
        entities = await self.bot.profile_queue.get()

        cleaned_entities = ""
        for line in entities.split("\n")[1:]:
            cleaned = re.sub(r"^.*Rcon: (.*)\]", r"\1", line)

            bolded = ["Average tick time", "Top 10 counts:", "Top 10 CPU hogs:"]
            if any(x in line for x in bolded):
                cleaned_entities += "**" + cleaned + "**\n"
            else:
                cleaned_entities += f"{cleaned}\n"

        server = self.bot.servers[target]

        embed = discord.Embed(title="`/profile entities`")
        embed.color = server.discord_color
        embed.description = cleaned_entities

        return embed

    @profile_commands.command(
        description="Send /profile health command to specified server"
    )
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def health(
        self, interaction: discord.Interaction, server: app_commands.Choice[str]
    ):
        await interaction.response.defer()

        target = server.value
        await bridge_send(self.bot.servers, target, f"RCON {target} profile health")
        await interaction.followup.send(embed=await self.handle_profile_health(target))

    @profile_commands.command(
        description="Send /profile entities command to specified server"
    )
    @app_commands.describe(server="target server")
    @app_commands.choices(server=bot.server_choices)
    async def entities(
        self, interaction: discord.Interaction, server: app_commands.Choice[str]
    ):
        await interaction.response.defer()

        target = server.value
        await bridge_send(self.bot.servers, target, f"RCON {target} profile entities")
        await interaction.followup.send(
            embed=await self.handle_profile_entities(target)
        )


async def setup(bot: bot.PropertyBot):
    await bot.add_cog(Profile(bot))
