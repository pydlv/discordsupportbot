from discord import Message

import shared
import settings
from commands.util import COMMAND_SUCCESS_EMBED, create_embed


async def print_help(*, message: Message):
    await message.channel.send(embed=shared.help_embed)


async def change_prefix(new_prefix: str, *, message: Message):
    settings.prefix.set(new_prefix)
    await message.channel.send(embed=COMMAND_SUCCESS_EMBED)


async def get_prefix(*, message: Message):
    await message.channel.send(
        embed=create_embed(
            "Result",
            f"The current prefix is: `{settings.prefix.get()}`."
        )
    )
