import re
from typing import Callable, List, Tuple, Optional

import discord
from discord import Message, Member

import settings
import shared


def create_embed(title: str, description: str, color=settings.embed_color.get()):
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )


def create_error_embed(message: str, title: str = "Could Not Complete", color=settings.error_color.get()):
    return discord.Embed(
        title=title,
        description=message,
        color=color
    )


NOT_ALLOWED_EMBED = create_embed(
    "Not Allowed",
    "You are not allowed to use that command!",
    color=settings.error_color.get()
)

COMMAND_SUCCESS_EMBED = create_embed(
    "Success",
    "The command completed successfully."
)

MEMBER_NOT_FOUND_EMBED = create_error_embed("That member could not be found.")


def check_roles(member: Member, allowed_roles: List[int]) -> bool:
    if 0 in allowed_roles:
        # Role allows everybody
        return True

    for role in member.roles:
        if role.id in allowed_roles:
            return True

    return False


def get_member(name_or_mention: str) -> Optional[Member]:
    match = re.fullmatch(r'<@!?(\d{8,32})>', name_or_mention)
    if match:
        # They used a mention
        member: Optional[Member] = shared.guild.get_member(int(match.group(1)))
        if member:
            return member
    # They didn't use a valid mention, so now try finding the user by name
    return shared.guild.get_member_named(name_or_mention)


class CommandEntry(object):
    pattern: str
    handler: Callable
    require_prefix: bool
    role_groups: List[int]
    help_triggers: Tuple[str]
    command_help_syntax: str
    command_help_text: str

    def __init__(self,
                 pattern: str,
                 handler: Callable,
                 *,
                 role_groups: List[int],
                 require_prefix=True,
                 help_triggers: Tuple[str] = (),
                 command_help_syntax: str,
                 command_help_text: str):
        """
        An entry for a chat command.
        :param pattern: Regex pattern to match. Matching groups are passed to handler as args.
        :param handler: Callable handler.
        :param role_groups: Role groups that can use this command.
        :param require_prefix: Whether the command requires the use of the globally defined prefix.
        :param help_triggers: If the command is not matched, then these keywords or phrases will trigger the
        command syntax help message.
        :param command_help_syntax: A user-friendly string that should show the command's proper syntax.
        """

        # This is so we can use (@mention) in our patterns and it will still match
        self.pattern = pattern.replace('(@mention)', r'((?:[^#@:]+#\d{4})|(?:<@!?\d{8,32}>))')
        self.handler = handler
        self.require_prefix = require_prefix
        self.role_groups = role_groups
        self.help_triggers = help_triggers
        self.command_help_syntax = command_help_syntax
        self.command_help_text = command_help_text

    async def handle_message(self, message: Message):
        allowed = check_roles(message.author, self.role_groups)

        full_pattern = re.escape(settings.prefix.get()) + self.pattern if self.require_prefix else self.pattern
        match = re.fullmatch(full_pattern, message.content)

        if match:
            if not allowed:
                await message.channel.send(
                    embed=NOT_ALLOWED_EMBED
                )
                return

            groups = [group for group in match.groups() if group is not None]

            await self.handler(*groups, message=message)
        elif self.help_triggers:
            # Check if we are just missing args, and if so notify the user.
            matches_trigger = False
            for trigger in self.help_triggers:
                modified_trigger = trigger + r"\b"
                exp = (
                    re.escape(settings.prefix.get()) + modified_trigger
                    if self.require_prefix else
                    modified_trigger
                )
                if re.match(exp, message.content):
                    matches_trigger = True
                    break

            if matches_trigger:
                if allowed:
                    command_syntax = (settings.prefix.get() + self.command_help_syntax
                                      if self.require_prefix else
                                      self.command_help_syntax)
                    await message.channel.send(
                        embed=create_embed(
                            "Command Help",
                            f"**`{command_syntax}`** - {self.command_help_text}"
                        )
                    )
                else:
                    await message.channel.send(
                        embed=NOT_ALLOWED_EMBED
                    )
                    return


def create_help_embed(commands: List[CommandEntry]):
    from commands import role_groups

    commands_by_roles = {}
    for command in commands:
        groups_set = frozenset(command.role_groups)
        if groups_set not in commands_by_roles:
            commands_by_roles[groups_set] = [command]
        else:
            commands_by_roles[groups_set].append(command)

    prettify_name = lambda name: name.replace("_", " ").title()

    names_by_role = {
        frozenset(getattr(role_groups, name)): prettify_name(name) for name in dir(role_groups)
        if not name.startswith("__") and type(getattr(role_groups, name)) is list
    }

    role_sets = list(commands_by_roles.keys())

    # Sort role groups that contain everyone to the top, and then role groups that contain more roles to the top.
    role_sets.sort(key=lambda rs: (-(0 in rs), -len(rs)))

    result = ""

    for role_group_set in role_sets:
        commands_text = "\n".join([
            "**`" + (
                settings.prefix.get() + command.command_help_syntax
                if command.require_prefix else
                command.command_help_syntax
            ) + f"`** - {command.command_help_text}"
            for command in commands_by_roles[role_group_set]
        ])

        role_name = "Unknown Role"
        if role_group_set in names_by_role:
            role_name = names_by_role[role_group_set]

        result += f"\n\n__**Commands for {role_name}**__\n\n{commands_text}"

    return create_embed(
        "Command List",
        result
    )
