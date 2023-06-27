import argparse
import random

import logging

import asyncio

import discord
from discord import app_commands

import bot, bridge

bot_ = bot.PropertyBot()

@bot_.tree.command()
@app_commands.checks.cooldown(rate=1, per=60)
async def pet(interaction: discord.Interaction):
    whole = random.randint(0, 5)
    dec = random.randint(0, 9) / 10

    should_long_chance = 0.01
    should_long = random.random()
    if should_long < should_long_chance:
        if should_long < should_long_chance / 2:
            whole = 15
            dec = 0
        else:
            whole = 0
            dec = 0.01

    if interaction.user.id == 1027880469926248458:
        whole = 1

    length = whole + dec
    await interaction.response.send_message(f"Me{'o'*whole}w! ({length:.1f} s)")

@bot_.tree.command()
@app_commands.checks.has_role(bot_.discord_config.admin_role)
async def reload(interaction: discord.Interaction):
    if interaction.user.id == bot_.discord_config.maintainer:
        for ext in bot_.init_extensions:
            await bot_.reload_extension('cogs.'+ext)
            await interaction.response.send_message(f"Reloaded {ext}", ephemeral=True)
    else:
        await interaction.response.send_message("Don't touch this!", ephemeral=True)

@bot_.tree.command()
@app_commands.checks.has_role(bot_.discord_config.admin_role)
async def sync(interaction: discord.Interaction):
    if interaction.user.id == bot_.discord_config.maintainer:
        guild = discord.Object(bot_.discord_config.guild)
        bot_.tree.copy_global_to(guild=guild)
        await bot_.tree.sync(guild=guild)
        # await bot.tree.sync()
        await interaction.response.send_message("Syncing...", ephemeral=True)
    else:
        await interaction.response.send_message("Don't touch this!", ephemeral=True)

@bot_.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingRole):
        await interaction.response.send_message("Missing permissions!", ephemeral=True)
    elif isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Command on cooldown! Try again in {error.retry_after:.0f}s...", ephemeral=True)

@bot_.event
async def on_ready():
    print("Ready!")
    await bridge.setup_bridges(bot_)

@bot_.event
async def on_message(msg: discord.Message):
    if msg.channel.id == bot_.discord_config.bridge_channel and not msg.author.bot:
        user = msg.author.name
        message = str(msg.clean_content)

        if msg.attachments:
            message += " [IMG]"

        # Handle replies
        reply = msg.reference
        reply_user = None
        reply_message = None

        if reply is not None:
            reply = reply.resolved
            if isinstance(reply, discord.Message):
                reply_user = reply.author.name
                reply_message = reply.clean_content

                if reply.attachments:
                    reply_message += " [IMG]"

        formatted = await bridge.format_message(bot_, "Discord", user, message, reply_user, reply_message)
        await bridge.bridge_chat(bot_, formatted)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--verbosity", help="set verbosity level")
    args = parser.parse_args()

    if args.verbosity:
        logging.basicConfig(level=getattr(logging, args.verbosity.upper()))

    asyncio.run(bot_.start(bot_.discord_config.token))

if __name__ == "__main__":
    main()
