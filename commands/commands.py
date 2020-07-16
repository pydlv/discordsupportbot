import shared
from .handlers import tickets, buyers
from .util import CommandEntry as Entry, create_help_embed
from . import handlers
from .role_groups import *

commands = [
    # Commands for everyone
    Entry(
        r'help',
        handlers.print_help,
        role_groups=EVERYONE,
        command_help_syntax="help",
        command_help_text="Displays a list of commands."
    ),
    Entry(
        r'new ((?:.|\n){10,})',
        tickets.new_ticket,
        role_groups=EVERYONE,
        help_triggers=("new",),
        command_help_syntax="new <reason>",
        command_help_text="Creates a new ticket with the specified reason. "
                          "The reason must be at least 10 characters long."
    ),
    Entry(
        r'close(?: (.+))?',
        tickets.close_ticket,
        role_groups=EVERYONE,
        command_help_syntax="close [message]",
        command_help_text="Closes the current ticket with an optional message."
    ),
    Entry(
        r'getopen',
        tickets.get_accepting_tickets,
        role_groups=EVERYONE,
        help_triggers=("getopen",),
        command_help_syntax="getopen",
        command_help_text="Returns whether we are currently accepting new tickets."
    ),
    Entry(
        r'prefix',
        handlers.get_prefix,
        require_prefix=False,
        role_groups=EVERYONE,
        command_help_syntax="prefix",
        command_help_text="Returns the current prefix for support bot commands."
    ),

    # Commands for staff
    Entry(
        r'setopen ((?:true)|(?:false))',
        tickets.set_accepting_tickets,
        role_groups=ALL_STAFF,
        help_triggers=("setopen",),
        command_help_syntax="setopen <true|false>",
        command_help_text="Sets whether new tickets will be accepted."
    ),
    Entry(
        r'newfor (@mention)(?: ((?:.|\n)+))?',
        tickets.newfor_ticket,
        role_groups=ALL_STAFF,
        help_triggers=('newfor',),
        command_help_syntax="newfor <user> [reason]",
        command_help_text="Creates a new ticket for the provided user. Use full name with discriminator or @mention."
    ),
    Entry(
        r'buyer (@mention)(?: ((?:true)|(?:false)))?',
        buyers.set_buyer_role,
        role_groups=ALL_STAFF,
        help_triggers=('buyer',),
        command_help_syntax="buyer <user> [true|false]",
        command_help_text="Sets whether the provided user has the Buyer role. Defaults to true."
    ),

    # Commands for admin
    Entry(
        r'prefix (.+)',
        handlers.change_prefix,
        role_groups=ADMIN,
        help_triggers=('prefix',),
        command_help_syntax="prefix <value>",
        command_help_text="Updates the prefix for all subsequent commands."
    )
]

shared.help_embed = create_help_embed(commands)
