import datetime
import math
import time
from typing import List, Optional

import discord
from discord import Message, Role, TextChannel, Member

import settings
import shared
from commands import role_groups
from commands.util import create_error_embed, COMMAND_SUCCESS_EMBED, create_embed, get_member, MEMBER_NOT_FOUND_EMBED
from datastore import Property, root

CUSTOMER_SUPPORT_ROLE_GROUP = role_groups.SUPPORT
TICKET_CATEGORY_ID = 1234567890  # Place ID of the ticket category here
LOG_CHANNEL_ID = 1234567890  # Place the ID of the ticket log channel here
TROUBLESHOOTING_CHANNEL_ID = 1234567890  # Place the ID of the troubleshooting channel here

is_accepting_tickets = Property("is_accepting_tickets", False)

customer_support_roles: List[Role] = []
moderator_roles: List[Role] = []
ticket_category: Optional[TextChannel] = None
log_channel: Optional[TextChannel] = None
troubleshooting_channel: Optional[TextChannel] = None


def setup():
    global customer_support_roles, moderator_roles, ticket_category, log_channel, troubleshooting_channel

    for role_id in CUSTOMER_SUPPORT_ROLE_GROUP:
        found = False
        for role in shared.guild.roles:
            if role.id == role_id:
                customer_support_roles.append(role)
                found = True
                break
        if not found:
            print(f"Invalid role ID in customer support role group: {role_id}")

    for role_id in role_groups.MODERATORS:
        found = False
        for role in shared.guild.roles:
            if role.id == role_id:
                moderator_roles.append(role)
                found = True
                break
        if not found:
            print(f"Invalid role ID in moderator role group: {role_id}")

    for category in shared.guild.categories:
        if category.id == TICKET_CATEGORY_ID:
            ticket_category = category

    if TICKET_CATEGORY_ID and ticket_category is None:
        print(f"Channel category with ID {TICKET_CATEGORY_ID} was not found.")

    for channel in shared.guild.channels:
        if channel.id == LOG_CHANNEL_ID:
            log_channel = channel
        if channel.id == TROUBLESHOOTING_CHANNEL_ID:
            troubleshooting_channel = channel

    if LOG_CHANNEL_ID and log_channel is None:
        print(f"Text channel with ID {LOG_CHANNEL_ID} was not found.")

    if TROUBLESHOOTING_CHANNEL_ID and troubleshooting_channel is None:
        print(f"Text channel with ID {TROUBLESHOOTING_CHANNEL_ID} was not found.")


async def create_ticket(reason: str, *, message: Message, author: Member):
    # Make sure we are accepting tickets
    if not is_accepting_tickets.get():
        await message.channel.send(embed=create_error_embed("Sorry, we are not currently accepting new tickets."))
        return

    # Make sure we have a ticket category set
    if ticket_category is None:
        await message.channel.send(
            embed=create_error_embed(
                "Sorry, the command could not be completed because a ticket channel category "
                "has not been configured by the owner."
            )
        )
        return

    channel_already_exists = False
    existing_channel = None

    for channel in shared.guild.channels:
        if channel.name == str(author.id):
            channel_already_exists = True
            existing_channel = channel
            break

    if channel_already_exists:
        await message.channel.send(
            embed=create_error_embed(
                f"You already have a ticket open in {existing_channel.mention}!"
            )
        )
        return

    participant_perms = discord.PermissionOverwrite(
        read_messages=True,
        send_messages=True,
        read_message_history=True,
        attach_files=True,
        embed_links=True,
        mention_everyone=True,
        external_emojis=True,
        add_reactions=True
    )

    everyone_perms = discord.PermissionOverwrite(
        read_messages=False,
        read_message_history=False
    )

    channel_permission_overwrites = {
        author: participant_perms,
        message.guild.me: participant_perms,
        shared.guild.default_role: everyone_perms
    }

    # Add customer support and moderators to permissions
    for role in customer_support_roles + moderator_roles:
        channel_permission_overwrites[role] = participant_perms

    new_channel = await shared.guild.create_text_channel(
        author.id,
        category=ticket_category,
        overwrites=channel_permission_overwrites
    )

    author_name = f"{author.mention} ({author.name}#{author.discriminator})"

    key = f"ticket_{author.id}"
    new_value = {
        "open_time": math.floor(time.time()),
        "is_open": True,
        "reason": reason,
        "author_name": author_name,
        "author_id": str(author.id)
    }

    root[key] = new_value

    await message.channel.send(
        embed=create_embed("Ticket Opened", f"A ticket has been opened for you in {new_channel.mention}.")
    )

    troubleshooting_mention = troubleshooting_channel.mention if troubleshooting_channel else "troubleshooting"

    await new_channel.send(
        embed=create_embed(
            "Ticket Opened",
            f"A ticket has been opened for {author.mention}. "
            f"Customer support will be with you as soon as possible.\n\n"
            f"Reason: `{reason}`\n\nYou may close this ticket at any time by typing `{settings.prefix.get()}close`."
            f"\n\nIf you have any more information about the issue you are facing, please write it below."
            f"\n\nPlease be sure to review {troubleshooting_mention} since a solution "
            f"for most problems can be found there."
        )
    )

    if log_channel:
        await log_channel.send(
            embed=create_embed(
                "Ticket Opened",
                f"Channel: {new_channel.mention}\n"
                f"Author: {author_name}\n"
                f"Reason: {reason}"
            )
        )


async def new_ticket(reason: str, *, message: Message):
    await create_ticket(reason, message=message, author=message.author)


async def newfor_ticket(member_name: str, reason: str = None, *, message: Message):
    member = get_member(member_name)

    if member is not None:
        await create_ticket(reason, message=message, author=member)
    else:
        await message.channel.send(
            embed=MEMBER_NOT_FOUND_EMBED
        )


async def close_ticket(reason=None, *, message: Message):
    if not message.channel.name.isnumeric() or int(message.channel.category_id) != ticket_category.id:
        await message.channel.send(
            embed=create_error_embed("That command can only be used inside an open ticket.")
        )
        return

    ticket_author_id = int(message.channel.name)
    key = f"ticket_{ticket_author_id}"
    if key in root:
        ticket_data = root[key]

        open_dt = datetime.datetime.fromtimestamp(ticket_data["open_time"])
        close_time = datetime.datetime.now()

        diff = close_time - open_dt

        days, seconds = diff.days, diff.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        time_open_display = f"{days} day(s) " \
                            f"{hours} hour(s) " \
                            f"{minutes} minute(s) " \
                            f"{seconds} second(s)"

        closed_by_display = f"{message.author.mention} ({message.author.name}#{message.author.discriminator})"

        ticket_info_embed = create_embed(
                "Ticket Closed",
                f"Author: {ticket_data['author_name']}\n"
                f"Reason: {ticket_data['reason']}\n"
                f"Time open: {time_open_display}\n"
                f"Closed by: {closed_by_display}\n"
                f"Close message: {None if not reason else reason}"
            )

        await log_channel.send(
            embed=ticket_info_embed
        )

        member = shared.guild.get_member(int(ticket_data["author_id"]))
        if member:
            try:
                await member.send(embed=ticket_info_embed)
                await member.send(
                    f"Thank you for using the {shared.guild.name} support system. "
                    "We hope you are satisfied with the support that you received.\n"
                    "Please fill out the customer support satisfaction survey. "
                    "It is only a few questions and helps us improve our customer support. "
                )
            except (discord.errors.Forbidden,):
                # The user probably has DMs turned off.
                pass

        del root[key]

        await message.channel.delete(reason=f"Closed by: {message.author}. Reason: {reason}")
    else:
        print("Could  not find ticket data when closing it. Deleting channel without.")

        await message.channel.delete(reason=f"Closed by: {message.author}. Reason: {reason}")


async def set_accepting_tickets(str_value: str, *, message: Message):
    if str_value == "true":
        is_accepting_tickets.set(True)
    else:
        is_accepting_tickets.set(False)

    await message.channel.send(
        embed=COMMAND_SUCCESS_EMBED
    )


async def get_accepting_tickets(*, message: Message):
    await message.channel.send(
        embed=create_embed(
            "Result",
            "Yes" if is_accepting_tickets.get() else "No"
        )
    )
