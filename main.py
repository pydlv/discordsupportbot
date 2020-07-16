#!venv/bin/python
import sys

import discord
from discord import Message

from commands.handlers.tickets import setup as setup_tickets_module
from commands.handlers.buyers import setup as setup_buyers_module
import settings
import shared
from client import client
from commands import handle_message


DISCORD_TOKEN = "Place your token here"


@client.event
async def on_ready():
    print(f"{client.user.name} Ready")
    print("-" * 10)

    # Initialize our shared variables
    for guild in client.guilds:
        if guild.id == settings.GUILD_ID:
            shared.guild = guild

    if shared.guild is None:
        print(f"Exiting because bot has not joined guild ID {settings.GUILD_ID}.")
        sys.exit(0)

    setup_tickets_module()
    setup_buyers_module()

    @client.event
    async def on_message(message: Message):
        if message.author == client.user:
            # Don't process our own messages
            return

        if message.channel.type == discord.ChannelType.private:
            await message.channel.send("Sorry, I can't help you in a private chat.")
            return

        if message.channel.type != discord.ChannelType.text:
            await message.channel.send("Sorry, I only respond to commands that are sent in a guild.")
            return

        # Verify message is in valid guild
        if message.guild.id != settings.GUILD_ID:
            return

        await handle_message(message)


client.run(DISCORD_TOKEN)
