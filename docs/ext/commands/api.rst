.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py's command extension module.

.. _ext_commands_api_bot:

Bots
------

Bot
~~~~

.. attributetable:: discord.ext.commands.Bot

.. autoclass:: discord.ext.commands.Bot
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, listen

    .. automethod:: Bot.after_invoke()
        :decorator:

    .. automethod:: Bot.before_invoke()
        :decorator:

    .. automethod:: Bot.check()
        :decorator:

    .. automethod:: Bot.check_once()
        :decorator:

    .. automethod:: Bot.command(*args, **kwargs)
        :decorator:

    .. automethod:: Bot.event()
        :decorator:

    .. automethod:: Bot.group(*args, **kwargs)
        :decorator:

    .. automethod:: Bot.listen(name=None)
        :decorator:

AutoShardedBot
~~~~~~~~~~~~~~~~

.. attributetable:: discord.ext.commands.AutoShardedBot

.. autoclass:: discord.ext.commands.AutoShardedBot
    :members:

Prefix Helpers
----------------

.. autofunction:: discord.ext.commands.when_mentioned

.. autofunction:: discord.ext.commands.when_mentioned_or

.. _ext_commands_api_events:

Event Reference
-----------------

These events function similar to :ref:`the regular events <discord-api-events>`, except they
are custom to the command extension module.

.. function:: discord.ext.commands.on_command_error(ctx, error)

    An error handler that is called when an error is raised
    inside a command either through user input error, check
    failure, or an error in your own code.

    A default one is provided (:meth:`.Bot.on_command_error`).

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`
    :param error: The error that was raised.
    :type error: :class:`.CommandError` derived

.. function:: discord.ext.commands.on_command(ctx)

    An event that is called when a command is found and is about to be invoked.

    This event is called regardless of whether the command itself succeeds via
    error or completes.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. function:: discord.ext.commands.on_command_completion(ctx)

    An event that is called when a command has completed its invocation.

    This event is called only if the command succeeded, i.e. all checks have
    passed and the user input it correctly.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. _ext_commands_api_command:

Commands
----------

Decorators
~~~~~~~~~~~~

.. autofunction:: discord.ext.commands.command
    :decorator:

.. autofunction:: discord.ext.commands.group
    :decorator:

Command
~~~~~~~~~

.. attributetable:: discord.ext.commands.Command

.. autoclass:: discord.ext.commands.Command
    :members:
    :special-members: __call__
    :exclude-members: after_invoke, before_invoke, error

    .. automethod:: Command.after_invoke()
        :decorator:

    .. automethod:: Command.before_invoke()
        :decorator:

    .. automethod:: Command.error()
        :decorator:

Group
~~~~~~

.. attributetable:: discord.ext.commands.Group

.. autoclass:: discord.ext.commands.Group
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, command, error, group

    .. automethod:: Group.after_invoke()
        :decorator:

    .. automethod:: Group.before_invoke()
        :decorator:

    .. automethod:: Group.command(*args, **kwargs)
        :decorator:

    .. automethod:: Group.error()
        :decorator:

    .. automethod:: Group.group(*args, **kwargs)
        :decorator:

GroupMixin
~~~~~~~~~~~

.. attributetable:: discord.ext.commands.GroupMixin

.. autoclass:: discord.ext.commands.GroupMixin
    :members:
    :exclude-members: command, group

    .. automethod:: GroupMixin.command(*args, **kwargs)
        :decorator:

    .. automethod:: GroupMixin.group(*args, **kwargs)
        :decorator:

.. _ext_commands_api_cogs:

Cogs
------

Cog
~~~~

.. attributetable:: discord.ext.commands.Cog

.. autoclass:: discord.ext.commands.Cog
    :members:

CogMeta
~~~~~~~~

.. attributetable:: discord.ext.commands.CogMeta

.. autoclass:: discord.ext.commands.CogMeta
    :members:

.. _ext_commands_help_command:

Help Commands
---------------

HelpCommand
~~~~~~~~~~~~

.. attributetable:: discord.ext.commands.HelpCommand

.. autoclass:: discord.ext.commands.HelpCommand
    :members:

DefaultHelpCommand
~~~~~~~~~~~~~~~~~~~

.. attributetable:: discord.ext.commands.DefaultHelpCommand

.. autoclass:: discord.ext.commands.DefaultHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

MinimalHelpCommand
~~~~~~~~~~~~~~~~~~~

.. attributetable:: discord.ext.commands.MinimalHelpCommand

.. autoclass:: discord.ext.commands.MinimalHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

Paginator
~~~~~~~~~~

.. attributetable:: discord.ext.commands.Paginator

.. autoclass:: discord.ext.commands.Paginator
    :members:

Enums
------

.. class:: BucketType
    :module: discord.ext.commands

    Specifies a type of bucket for, e.g. a cooldown.

    .. attribute:: default

        The default bucket operates on a global basis.
    .. attribute:: user

        The user bucket operates on a per-user basis.
    .. attribute:: guild

        The guild bucket operates on a per-guild basis.
    .. attribute:: channel

        The channel bucket operates on a per-channel basis.
    .. attribute:: member

        The member bucket operates on a per-member basis.
    .. attribute:: category

        The category bucket operates on a per-category basis.
    .. attribute:: role

        The role bucket operates on a per-role basis.

        .. versionadded:: 1.3


.. _ext_commands_api_checks:

Checks
-------

.. autofunction:: discord.ext.commands.check(predicate)
    :decorator:

.. autofunction:: discord.ext.commands.check_any(*checks)
    :decorator:

.. autofunction:: discord.ext.commands.has_role(item)
    :decorator:

.. autofunction:: discord.ext.commands.has_permissions(**perms)
    :decorator:

.. autofunction:: discord.ext.commands.has_guild_permissions(**perms)
    :decorator:

.. autofunction:: discord.ext.commands.has_any_role(*items)
    :decorator:

.. autofunction:: discord.ext.commands.bot_has_role(item)
    :decorator:

.. autofunction:: discord.ext.commands.bot_has_permissions(**perms)
    :decorator:

.. autofunction:: discord.ext.commands.bot_has_guild_permissions(**perms)
    :decorator:

.. autofunction:: discord.ext.commands.bot_has_any_role(*items)
    :decorator:

.. autofunction:: discord.ext.commands.cooldown(rate, per, type=discord.ext.commands.BucketType.default)
    :decorator:

.. autofunction:: discord.ext.commands.dynamic_cooldown(cooldown, type=BucketType.default)
    :decorator:

.. autofunction:: discord.ext.commands.max_concurrency(number, per=discord.ext.commands.BucketType.default, *, wait=False)
    :decorator:

.. autofunction:: discord.ext.commands.before_invoke(coro)
    :decorator:

.. autofunction:: discord.ext.commands.after_invoke(coro)
    :decorator:

.. autofunction:: discord.ext.commands.guild_only(,)
    :decorator:

.. autofunction:: discord.ext.commands.dm_only(,)
    :decorator:

.. autofunction:: discord.ext.commands.is_owner(,)
    :decorator:

.. autofunction:: discord.ext.commands.is_nsfw(,)
    :decorator:

.. _ext_commands_api_context:

Context
--------

.. attributetable:: discord.ext.commands.Context

.. autoclass:: discord.ext.commands.Context
    :members:
    :inherited-members:
    :exclude-members: typing

    .. automethod:: discord.ext.commands.Context.typing
        :async-with:

.. _ext_commands_api_converters:

Converters
------------

.. autoclass:: discord.ext.commands.Converter
    :members:

.. autoclass:: discord.ext.commands.ObjectConverter
    :members:

.. autoclass:: discord.ext.commands.MemberConverter
    :members:

.. autoclass:: discord.ext.commands.UserConverter
    :members:

.. autoclass:: discord.ext.commands.MessageConverter
    :members:

.. autoclass:: discord.ext.commands.PartialMessageConverter
    :members:

.. autoclass:: discord.ext.commands.GuildChannelConverter
    :members:

.. autoclass:: discord.ext.commands.TextChannelConverter
    :members:

.. autoclass:: discord.ext.commands.VoiceChannelConverter
    :members:

.. autoclass:: discord.ext.commands.StageChannelConverter
    :members:

.. autoclass:: discord.ext.commands.CategoryChannelConverter
    :members:

.. autoclass:: discord.ext.commands.InviteConverter
    :members:

.. autoclass:: discord.ext.commands.GuildConverter
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

.. autoclass:: discord.ext.commands.ThreadConverter
    :members:

.. autoclass:: discord.ext.commands.GuildStickerConverter
    :members:

.. autoclass:: discord.ext.commands.ScheduledEventConverter
    :members:

.. autoclass:: discord.ext.commands.clean_content
    :members:

.. autoclass:: discord.ext.commands.Greedy()

.. autofunction:: discord.ext.commands.run_converters

Flag Converter
~~~~~~~~~~~~~~~

.. autoclass:: discord.ext.commands.FlagConverter
    :members:

.. autoclass:: discord.ext.commands.Flag()
    :members:

.. autofunction:: discord.ext.commands.flag


Defaults
--------

.. autoclass:: discord.ext.commands.Parameter()
    :members:

.. autofunction:: discord.ext.commands.parameter

.. autofunction:: discord.ext.commands.param

.. data:: discord.ext.commands.Author

    A default :class:`.Parameter` which returns the :attr:`~.Context.author` for this context.

    .. versionadded:: 2.0

.. data:: discord.ext.commands.CurrentChannel

    A default :class:`.Parameter` which returns the :attr:`~.Context.channel` for this context.

    .. versionadded:: 2.0

.. data:: discord.ext.commands.CurrentGuild

    A default :class:`.Parameter` which returns the :attr:`~.Context.guild` for this context. This will never be ``None``. If the command is called in a DM context then :exc:`~discord.ext.commands.NoPrivateMessage` is raised to the error handlers.

    .. versionadded:: 2.0

.. _ext_commands_api_errors:

Exceptions
-----------

.. autoexception:: discord.ext.commands.CommandError
    :members:

.. autoexception:: discord.ext.commands.ConversionError
    :members:

.. autoexception:: discord.ext.commands.MissingRequiredArgument
    :members:

.. autoexception:: discord.ext.commands.ArgumentParsingError
    :members:

.. autoexception:: discord.ext.commands.UnexpectedQuoteError
    :members:

.. autoexception:: discord.ext.commands.InvalidEndOfQuotedStringError
    :members:

.. autoexception:: discord.ext.commands.ExpectedClosingQuoteError
    :members:

.. autoexception:: discord.ext.commands.BadArgument
    :members:

.. autoexception:: discord.ext.commands.BadUnionArgument
    :members:

.. autoexception:: discord.ext.commands.BadLiteralArgument
    :members:

.. autoexception:: discord.ext.commands.PrivateMessageOnly
    :members:

.. autoexception:: discord.ext.commands.NoPrivateMessage
    :members:

.. autoexception:: discord.ext.commands.CheckFailure
    :members:

.. autoexception:: discord.ext.commands.CheckAnyFailure
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

.. autoexception:: discord.ext.commands.MaxConcurrencyReached
    :members:

.. autoexception:: discord.ext.commands.NotOwner
    :members:

.. autoexception:: discord.ext.commands.MessageNotFound
    :members:

.. autoexception:: discord.ext.commands.MemberNotFound
    :members:

.. autoexception:: discord.ext.commands.GuildNotFound
    :members:

.. autoexception:: discord.ext.commands.UserNotFound
    :members:

.. autoexception:: discord.ext.commands.ChannelNotFound
    :members:

.. autoexception:: discord.ext.commands.ChannelNotReadable
    :members:

.. autoexception:: discord.ext.commands.ThreadNotFound
    :members:

.. autoexception:: discord.ext.commands.BadColourArgument
    :members:

.. autoexception:: discord.ext.commands.RoleNotFound
    :members:

.. autoexception:: discord.ext.commands.BadInviteArgument
    :members:

.. autoexception:: discord.ext.commands.EmojiNotFound
    :members:

.. autoexception:: discord.ext.commands.PartialEmojiConversionFailure
    :members:

.. autoexception:: discord.ext.commands.GuildStickerNotFound
    :members:

.. autoexception:: discord.ext.commands.ScheduledEventNotFound
    :members:

.. autoexception:: discord.ext.commands.BadBoolArgument
    :members:

.. autoexception:: discord.ext.commands.MissingPermissions
    :members:

.. autoexception:: discord.ext.commands.BotMissingPermissions
    :members:

.. autoexception:: discord.ext.commands.MissingRole
    :members:

.. autoexception:: discord.ext.commands.BotMissingRole
    :members:

.. autoexception:: discord.ext.commands.MissingAnyRole
    :members:

.. autoexception:: discord.ext.commands.BotMissingAnyRole
    :members:

.. autoexception:: discord.ext.commands.NSFWChannelRequired
    :members:

.. autoexception:: discord.ext.commands.FlagError
    :members:

.. autoexception:: discord.ext.commands.BadFlagArgument
    :members:

.. autoexception:: discord.ext.commands.MissingFlagArgument
    :members:

.. autoexception:: discord.ext.commands.TooManyFlags
    :members:

.. autoexception:: discord.ext.commands.MissingRequiredFlag
    :members:

.. autoexception:: discord.ext.commands.ExtensionError
    :members:

.. autoexception:: discord.ext.commands.ExtensionAlreadyLoaded
    :members:

.. autoexception:: discord.ext.commands.ExtensionNotLoaded
    :members:

.. autoexception:: discord.ext.commands.NoEntryPointError
    :members:

.. autoexception:: discord.ext.commands.ExtensionFailed
    :members:

.. autoexception:: discord.ext.commands.ExtensionNotFound
    :members:

.. autoexception:: discord.ext.commands.CommandRegistrationError
    :members:


Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`~.DiscordException`
        - :exc:`~.commands.CommandError`
            - :exc:`~.commands.ConversionError`
            - :exc:`~.commands.UserInputError`
                - :exc:`~.commands.MissingRequiredArgument`
                - :exc:`~.commands.TooManyArguments`
                - :exc:`~.commands.BadArgument`
                    - :exc:`~.commands.MessageNotFound`
                    - :exc:`~.commands.MemberNotFound`
                    - :exc:`~.commands.GuildNotFound`
                    - :exc:`~.commands.UserNotFound`
                    - :exc:`~.commands.ChannelNotFound`
                    - :exc:`~.commands.ChannelNotReadable`
                    - :exc:`~.commands.BadColourArgument`
                    - :exc:`~.commands.RoleNotFound`
                    - :exc:`~.commands.BadInviteArgument`
                    - :exc:`~.commands.EmojiNotFound`
                    - :exc:`~.commands.GuildStickerNotFound`
                    - :exc:`~.commands.ScheduledEventNotFound`
                    - :exc:`~.commands.PartialEmojiConversionFailure`
                    - :exc:`~.commands.BadBoolArgument`
                    - :exc:`~.commands.ThreadNotFound`
                    - :exc:`~.commands.FlagError`
                        - :exc:`~.commands.BadFlagArgument`
                        - :exc:`~.commands.MissingFlagArgument`
                        - :exc:`~.commands.TooManyFlags`
                        - :exc:`~.commands.MissingRequiredFlag`
                - :exc:`~.commands.BadUnionArgument`
                - :exc:`~.commands.BadLiteralArgument`
                - :exc:`~.commands.ArgumentParsingError`
                    - :exc:`~.commands.UnexpectedQuoteError`
                    - :exc:`~.commands.InvalidEndOfQuotedStringError`
                    - :exc:`~.commands.ExpectedClosingQuoteError`
            - :exc:`~.commands.CommandNotFound`
            - :exc:`~.commands.CheckFailure`
                - :exc:`~.commands.CheckAnyFailure`
                - :exc:`~.commands.PrivateMessageOnly`
                - :exc:`~.commands.NoPrivateMessage`
                - :exc:`~.commands.NotOwner`
                - :exc:`~.commands.MissingPermissions`
                - :exc:`~.commands.BotMissingPermissions`
                - :exc:`~.commands.MissingRole`
                - :exc:`~.commands.BotMissingRole`
                - :exc:`~.commands.MissingAnyRole`
                - :exc:`~.commands.BotMissingAnyRole`
                - :exc:`~.commands.NSFWChannelRequired`
            - :exc:`~.commands.DisabledCommand`
            - :exc:`~.commands.CommandInvokeError`
            - :exc:`~.commands.CommandOnCooldown`
            - :exc:`~.commands.MaxConcurrencyReached`
        - :exc:`~.commands.ExtensionError`
            - :exc:`~.commands.ExtensionAlreadyLoaded`
            - :exc:`~.commands.ExtensionNotLoaded`
            - :exc:`~.commands.NoEntryPointError`
            - :exc:`~.commands.ExtensionFailed`
            - :exc:`~.commands.ExtensionNotFound`
    - :exc:`~.ClientException`
        - :exc:`~.commands.CommandRegistrationError`
