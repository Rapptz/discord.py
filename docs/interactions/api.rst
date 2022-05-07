.. currentmodule:: discord

Interactions API Reference
============================

The following section outlines the API of interactions, as implemented by the library.

For documentation about the rest of the library, check :doc:`/api`.

Models
--------

Similar to :ref:`discord_api_models`, these are not meant to be constructed by the user.

Interaction
~~~~~~~~~~~~

.. attributetable:: Interaction

.. autoclass:: Interaction()
    :members:

InteractionResponse
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: InteractionResponse

.. autoclass:: InteractionResponse()
    :members:

InteractionMessage
~~~~~~~~~~~~~~~~~~~

.. attributetable:: InteractionMessage

.. autoclass:: InteractionMessage()
    :members:
    :inherited-members:

MessageInteraction
~~~~~~~~~~~~~~~~~~~

.. attributetable:: MessageInteraction

.. autoclass:: MessageInteraction()
    :members:

Component
~~~~~~~~~~

.. attributetable:: Component

.. autoclass:: Component()
    :members:

ActionRow
~~~~~~~~~~

.. attributetable:: ActionRow

.. autoclass:: ActionRow()
    :members:

Button
~~~~~~~

.. attributetable:: Button

.. autoclass:: Button()
    :members:
    :inherited-members:

SelectMenu
~~~~~~~~~~~

.. attributetable:: SelectMenu

.. autoclass:: SelectMenu()
    :members:
    :inherited-members:


TextInput
~~~~~~~~~~

.. attributetable:: TextInput

.. autoclass:: TextInput()
    :members:
    :inherited-members:

AppCommand
~~~~~~~~~~~

.. attributetable:: discord.app_commands.AppCommand

.. autoclass:: discord.app_commands.AppCommand()
    :members:

AppCommandGroup
~~~~~~~~~~~~~~~~

.. attributetable:: discord.app_commands.AppCommandGroup

.. autoclass:: discord.app_commands.AppCommandGroup()
    :members:

AppCommandChannel
~~~~~~~~~~~~~~~~~~

.. attributetable:: discord.app_commands.AppCommandChannel

.. autoclass:: discord.app_commands.AppCommandChannel()
    :members:

AppCommandThread
~~~~~~~~~~~~~~~~~

.. attributetable:: discord.app_commands.AppCommandThread

.. autoclass:: discord.app_commands.AppCommandThread()
    :members:

Argument
~~~~~~~~~~

.. attributetable:: discord.app_commands.Argument

.. autoclass:: discord.app_commands.Argument()
    :members:

AllChannels
~~~~~~~~~~~~

.. attributetable:: discord.app_commands.AllChannels

.. autoclass:: discord.app_commands.AllChannels()
    :members:

Data Classes
--------------

Similar to :ref:`discord_api_data`, these can be received and constructed by users.

SelectOption
~~~~~~~~~~~~~

.. attributetable:: SelectOption

.. autoclass:: SelectOption
    :members:

Choice
~~~~~~~

.. attributetable:: discord.app_commands.Choice

.. autoclass:: discord.app_commands.Choice
    :members:


Enumerations
-------------

.. class:: InteractionType

    Specifies the type of :class:`Interaction`.

    .. versionadded:: 2.0

    .. attribute:: ping

        Represents Discord pinging to see if the interaction response server is alive.
    .. attribute:: application_command

        Represents a slash command interaction.
    .. attribute:: component

        Represents a component based interaction, i.e. using the Discord Bot UI Kit.
    .. attribute:: autocomplete

        Represents an auto complete interaction.
    .. attribute:: modal_submit

        Represents submission of a modal interaction.

.. class:: InteractionResponseType

    Specifies the response type for the interaction.

    .. versionadded:: 2.0

    .. attribute:: pong

        Pongs the interaction when given a ping.

        See also :meth:`InteractionResponse.pong`
    .. attribute:: channel_message

        Respond to the interaction with a message.

        See also :meth:`InteractionResponse.send_message`
    .. attribute:: deferred_channel_message

        Responds to the interaction with a message at a later time.

        See also :meth:`InteractionResponse.defer`
    .. attribute:: deferred_message_update

        Acknowledges the component interaction with a promise that
        the message will update later (though there is no need to actually update the message).

        See also :meth:`InteractionResponse.defer`
    .. attribute:: message_update

        Responds to the interaction by editing the message.

        See also :meth:`InteractionResponse.edit_message`
    .. attribute:: autocomplete_result

        Responds to the autocomplete interaction with suggested choices.

        See also :meth:`InteractionResponse.autocomplete`
    .. attribute:: modal

        Responds to the interaction with a modal.

        See also :meth:`InteractionResponse.send_modal`

.. class:: ComponentType

    Represents the component type of a component.

    .. versionadded:: 2.0

    .. attribute:: action_row

        Represents the group component which holds different components in a row.
    .. attribute:: button

        Represents a button component.
    .. attribute:: select

        Represents a select component.

    .. attribute:: text_input

        Represents a text box component.

.. class:: ButtonStyle

    Represents the style of the button component.

    .. versionadded:: 2.0

    .. attribute:: primary

        Represents a blurple button for the primary action.
    .. attribute:: secondary

        Represents a grey button for the secondary action.
    .. attribute:: success

        Represents a green button for a successful action.
    .. attribute:: danger

        Represents a red button for a dangerous action.
    .. attribute:: link

        Represents a link button.

    .. attribute:: blurple

        An alias for :attr:`primary`.
    .. attribute:: grey

        An alias for :attr:`secondary`.
    .. attribute:: gray

        An alias for :attr:`secondary`.
    .. attribute:: green

        An alias for :attr:`success`.
    .. attribute:: red

        An alias for :attr:`danger`.
    .. attribute:: url

        An alias for :attr:`link`.

.. class:: TextStyle

    Represents the style of the text box component.

    .. versionadded:: 2.0

    .. attribute:: short

        Represents a short text box.
    .. attribute:: paragraph

        Represents a long form text box.
    .. attribute:: long

        An alias for :attr:`paragraph`.

.. class:: AppCommandOptionType

    The application command's option type. This is usually the type of parameter an application command takes.

    .. versionadded:: 2.0

    .. attribute:: subcommand

        A subcommand.
    .. attribute:: subcommand_group

        A subcommand group.
    .. attribute:: string

        A string parameter.
    .. attribute:: integer

        A integer parameter.
    .. attribute:: boolean

        A boolean parameter.
    .. attribute:: user

        A user parameter.
    .. attribute:: channel

        A channel parameter.
    .. attribute:: role

        A role parameter.
    .. attribute:: mentionable

        A mentionable parameter.
    .. attribute:: number

        A number parameter.
    .. attribute:: attachment

        An attachment parameter.

.. class:: AppCommandType

    The type of application command.

    .. versionadded:: 2.0

    .. attribute:: chat_input

        A slash command.
    .. attribute:: user

        A user context menu command.
    .. attribute:: message

        A message context menu command.

.. _discord_ui_kit:

Bot UI Kit
-------------

The library has helpers to aid create component-based UIs. These are all in the ``discord.ui`` package.


View
~~~~~~~

.. attributetable:: discord.ui.View

.. autoclass:: discord.ui.View
    :members:

Modal
~~~~~~

.. attributetable:: discord.ui.Modal

.. autoclass:: discord.ui.Modal
    :members:
    :inherited-members:

Item
~~~~~~~

.. attributetable:: discord.ui.Item

.. autoclass:: discord.ui.Item
    :members:

Button
~~~~~~~

.. attributetable:: discord.ui.Button

.. autoclass:: discord.ui.Button
    :members:
    :inherited-members:

.. autofunction:: discord.ui.button

Select
~~~~~~~

.. attributetable:: discord.ui.Select

.. autoclass:: discord.ui.Select
    :members:
    :inherited-members:

.. autofunction:: discord.ui.select

TextInput
~~~~~~~~~~

.. attributetable:: discord.ui.TextInput

.. autoclass:: discord.ui.TextInput
    :members:
    :inherited-members:

.. _discord_app_commands:

Application Commands
----------------------

The library has helpers to aid in creation of application commands. These are all in the ``discord.app_commands`` package.

CommandTree
~~~~~~~~~~~~

.. attributetable:: discord.app_commands.CommandTree

.. autoclass:: discord.app_commands.CommandTree
    :members:

Commands
~~~~~~~~~

Command
++++++++

.. attributetable:: discord.app_commands.Command

.. autoclass:: discord.app_commands.Command
    :members:

ContextMenu
++++++++++++

.. attributetable:: discord.app_commands.ContextMenu

.. autoclass:: discord.app_commands.ContextMenu
    :members:

Group
++++++

.. attributetable:: discord.app_commands.Group

.. autoclass:: discord.app_commands.Group
    :members:

Decorators
~~~~~~~~~~~

.. autofunction:: discord.app_commands.command
    :decorator:

.. autofunction:: discord.app_commands.context_menu
    :decorator:

.. autofunction:: discord.app_commands.describe
    :decorator:

.. autofunction:: discord.app_commands.rename
    :decorator:

.. autofunction:: discord.app_commands.choices
    :decorator:

.. autofunction:: discord.app_commands.autocomplete
    :decorator:

.. autofunction:: discord.app_commands.guilds
    :decorator:

.. autofunction:: discord.app_commands.guild_only
    :decorator:

.. autofunction:: discord.app_commands.default_permissions
    :decorator:

Checks
~~~~~~~

.. autofunction:: discord.app_commands.check
    :decorator:

.. autofunction:: discord.app_commands.checks.has_role
    :decorator:

.. autofunction:: discord.app_commands.checks.has_any_role
    :decorator:

.. autofunction:: discord.app_commands.checks.has_permissions
    :decorator:

.. autofunction:: discord.app_commands.checks.bot_has_permissions
    :decorator:

.. autofunction:: discord.app_commands.checks.cooldown
    :decorator:

.. autofunction:: discord.app_commands.checks.dynamic_cooldown
    :decorator:

Cooldown
~~~~~~~~~

.. attributetable:: discord.app_commands.Cooldown

.. autoclass:: discord.app_commands.Cooldown
    :members:


Namespace
~~~~~~~~~~

.. attributetable:: discord.app_commands.Namespace

.. autoclass:: discord.app_commands.Namespace()
    :members:

Transformers
~~~~~~~~~~~~~

Transformer
++++++++++++

.. attributetable:: discord.app_commands.Transformer

.. autoclass:: discord.app_commands.Transformer
    :members:

Transform
++++++++++

.. attributetable:: discord.app_commands.Transform

.. autoclass:: discord.app_commands.Transform
    :members:

Range
++++++

.. attributetable:: discord.app_commands.Range

.. autoclass:: discord.app_commands.Range
    :members:

Exceptions
~~~~~~~~~~~

.. autoexception:: discord.app_commands.AppCommandError
    :members:

.. autoexception:: discord.app_commands.CommandInvokeError
    :members:

.. autoexception:: discord.app_commands.TransformerError
    :members:

.. autoexception:: discord.app_commands.CheckFailure
    :members:

.. autoexception:: discord.app_commands.NoPrivateMessage
    :members:

.. autoexception:: discord.app_commands.MissingRole
    :members:

.. autoexception:: discord.app_commands.MissingAnyRole
    :members:

.. autoexception:: discord.app_commands.MissingPermissions
    :members:

.. autoexception:: discord.app_commands.BotMissingPermissions
    :members:

.. autoexception:: discord.app_commands.CommandOnCooldown
    :members:

.. autoexception:: discord.app_commands.CommandLimitReached
    :members:

.. autoexception:: discord.app_commands.CommandAlreadyRegistered
    :members:

.. autoexception:: discord.app_commands.CommandSignatureMismatch
    :members:

.. autoexception:: discord.app_commands.CommandNotFound
    :members:

.. autoexception:: discord.app_commands.MissingApplicationID
    :members:

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`~discord.DiscordException`
        - :exc:`~discord.app_commands.AppCommandError`
            - :exc:`~discord.app_commands.CommandInvokeError`
            - :exc:`~discord.app_commands.TransformerError`
            - :exc:`~discord.app_commands.CheckFailure`
                - :exc:`~discord.app_commands.NoPrivateMessage`
                - :exc:`~discord.app_commands.MissingRole`
                - :exc:`~discord.app_commands.MissingAnyRole`
                - :exc:`~discord.app_commands.MissingPermissions`
                - :exc:`~discord.app_commands.BotMissingPermissions`
                - :exc:`~discord.app_commands.CommandOnCooldown`
            - :exc:`~discord.app_commands.CommandLimitReached`
            - :exc:`~discord.app_commands.CommandAlreadyRegistered`
            - :exc:`~discord.app_commands.CommandSignatureMismatch`
            - :exc:`~discord.app_commands.CommandNotFound`
            - :exc:`~discord.app_commands.MissingApplicationID`
