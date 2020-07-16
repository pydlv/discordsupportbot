from typing import Optional

from discord import Role, Message, Member

import shared
from commands.util import create_error_embed, get_member, MEMBER_NOT_FOUND_EMBED, COMMAND_SUCCESS_EMBED

BUYER_ROLE_ID = 0  # Place the ID of the buyer role here

buyer_role: Optional[Role] = None


def setup():
    global buyer_role

    for role in shared.guild.roles:
        if role.id == BUYER_ROLE_ID:
            buyer_role = role

    if buyer_role is None:
        print(f"Unable to find role with ID {BUYER_ROLE_ID}.")


async def set_buyer_role(name_or_mention: str, new_value: str = "true", *, message: Message):
    if buyer_role is None:
        await message.channel.send(
            embed=create_error_embed("Could not complete because the buyer role has not been configured.")
        )
        return

    member: Optional[Member] = get_member(name_or_mention)

    if not member:
        await message.channel.send(
            embed=MEMBER_NOT_FOUND_EMBED
        )
        return

    if new_value == "true":
        await member.add_roles(buyer_role)
    else:
        await member.remove_roles(buyer_role)

    await message.channel.send(
        embed=COMMAND_SUCCESS_EMBED
    )
