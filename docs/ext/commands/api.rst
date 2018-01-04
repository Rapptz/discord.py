.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py's command extension module.

.. _ext_commands_api_bot:

Bot
----

.. autoclass:: discord.ext.commands.Bot
    :members:
    :inherited-members:

.. autoclass:: discord.ext.commands.AutoShardedBot
    :members:

.. autofunction:: discord.ext.commands.when_mentioned

.. autofunction:: discord.ext.commands.when_mentioned_or

.. _ext_commands_api_events:

Event Reference
-----------------

These events function similar to :ref:`the regular events <discord-api-events>`, except they
are custom to the command extension module.

.. function:: on_command_error(ctx, error)

    An error handler that is called when an error is raised
    inside a command either through user input error, check
    failure, or an error in your own code.

    A default one is provided (:meth:`.Bot.on_command_error`).

    :param ctx: The invocation context.
    :type ctx: :class:`Context`
    :param error: The error that was raised.
    :type error: :class:`CommandError` derived

.. function:: on_command(ctx)

    An event that is called when a command is found and is about to be invoked.

    This event is called regardless of whether the command itself succeeds via
    error or completes.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

.. function:: on_command_completion(ctx)

    An event that is called when a command has completed its invocation.

    This event is called only if the command succeeded, i.e. all checks have
    passed and the user input it correctly.

    :param ctx: The invocation context.
    :type ctx: :class:`Context`

.. _ext_commands_api_command:

Command
--------

.. autofunction:: discord.ext.commands.command

.. autofunction:: discord.ext.commands.group

.. autoclass:: discord.ext.commands.Command
    :members:

.. autoclass:: discord.ext.commands.Group
    :members:
    :inherited-members:

.. autoclass:: discord.ext.commands.GroupMixin
    :members:

.. _ext_commands_api_formatters:

Formatters
-----------

.. autoclass:: discord.ext.commands.Paginator
    :members:

.. autoclass:: discord.ext.commands.HelpFormatter
    :members:

.. _ext_commands_api_checks:

Checks
-------

.. autofunction:: discord.ext.commands.check

.. autofunction:: discord.ext.commands.has_role

.. autofunction:: discord.ext.commands.has_permissions

.. autofunction:: discord.ext.commands.has_any_role

.. autofunction:: discord.ext.commands.bot_has_role

.. autofunction:: discord.ext.commands.bot_has_permissions

.. autofunction:: discord.ext.commands.bot_has_any_role

.. autofunction:: discord.ext.commands.cooldown

.. autofunction:: discord.ext.commands.guild_only

.. autofunction:: discord.ext.commands.is_owner

.. autofunction:: discord.ext.commands.is_nsfw

.. _ext_commands_api_context:

Context
--------

.. autoclass:: discord.ext.commands.Context
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: discord.ext.commands.Context.history
        :async-for:

    .. autocomethod:: discord.ext.commands.Context.typing
        :async-with:

.. _ext_commands_api_converters:

Converters
------------

.. autoclass:: discord.ext.commands.Converter
    :members:

.. autoclass:: discord.ext.commands.MemberConverter
    :members:

.. autoclass:: discord.ext.commands.UserConverter
    :members:

.. autoclass:: discord.ext.commands.TextChannelConverter
    :members:

.. autoclass:: discord.ext.commands.VoiceChannelConverter
    :members:

.. autoclass:: discord.ext.commands.CategoryChannelConverter
    :members:

.. autoclass:: discord.ext.commands.InviteConverter
    :members:

.. autoclass:: discord.ext.commands.RoleConverter
    :members:

.. autoclass:: discord.ext.commands.GameConverter
    :members:

.. autoclass:: discord.ext.commands.ColourConverter
    :members:

.. autoclass:: discord.ext.commands.EmojiConverter
    :members:

.. autoclass:: discord.ext.commands.PartialEmojiConverter
    :members:

.. autoclass:: discord.ext.commands.clean_content
    :members:

.. _ext_commands_api_errors:

Errors
-------

.. autoexception:: discord.ext.commands.CommandError
    :members:

.. autoexception:: discord.ext.commands.MissingRequiredArgument
    :members:

.. autoexception:: discord.ext.commands.BadArgument
    :members:

.. autoexception:: discord.ext.commands.NoPrivateMessage
    :members:

.. autoexception:: discord.ext.commands.CheckFailure
    :members:

.. autoexception:: discord.ext.commands.CommandNotFound
    :members:

.. autoexception:: discord.ext.commands.DisabledCommand
    :members:

.. autoexception:: discord.ext.commands.CommandInvokeError
    :members:

.. autoexception:: discord.ext.commands.TooManyArguments
    :members:

.. autoexception:: discord.ext.commands.UserInputError
    :members:

.. autoexception:: discord.ext.commands.CommandOnCooldown
    :members:

.. autoexception:: discord.ext.commands.NotOwner
    :members:

.. autoexception:: discord.ext.commands.MissingPermissions
    :members:

.. autoexception:: discord.ext.commands.BotMissingPermissions
    :members:

