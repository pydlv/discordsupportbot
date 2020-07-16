from discord import Message
from .commands import commands
from .util import CommandEntry


async def handle_message(message: Message):
    for command in commands:
        await command.handle_message(message)
