:orphan:

.. _discord_slash_commands:

Slash commands
===============

Slash commands are one of Discord's primary methods of implementing a user-interface for bots.
Analogous to their name, they're previewed and invoked in the Discord client by beginning your message with a forward-slash.

.. image:: /images/guide/app_commands/meow_command_preview.png
    :width: 400

Application commands are implemented within the :ref:`discord.app_commands <discord_app_commands>` package.
Code examples in this page will always assume the following two imports:

.. code-block:: python

    import discord
    from discord import app_commands

Setting up
-----------

To work with app commands, bots need the ``applications.commands`` scope.

You can enable this scope when generating an OAuth2 URL for your bot, shown :ref:`here <discord_invite_bot>`.

Defining a Tree
++++++++++++++++

First, an :class:`.app_commands.CommandTree` needs to be created
- which acts as a container holding all of the bot's application commands.

This class contains a few dedicated methods for managing and viewing app commands:

- :meth:`.CommandTree.add_command` to add a command
- :meth:`.CommandTree.remove_command` to remove a command
- :meth:`.CommandTree.get_command` to find a specific command
- :meth:`.CommandTree.get_commands` to return all commands

Preferably, this tree should be attached to the client instance to
play well with type checkers and to allow for easy access from anywhere in the code:

.. code-block:: python

    import discord
    from discord import app_commands

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

    client = MyClient()

.. note::

    If your project instead uses :class:`.ext.commands.Bot` as the client instance,
    a :class:`~discord.app_commands.CommandTree` has already been defined at :attr:`.Bot.tree`,
    so this step is largely skipped.

Creating a command
-------------------

Slash commands are created by decorating an async function.
This function is then called whenever the slash command is invoked.

For example, the following code responds with "meow" on invocation:

.. code-block:: python

    @client.tree.command()
    async def meow(interaction: discord.Interaction):
        """Meow meow meow"""

        await interaction.response.send_message("meow")

Functions of this pattern are called callbacks, since their execution is
left to the library to be called later.

There are two main decorators to use when creating a command:

1. :meth:`tree.command() <.CommandTree.command>` (as seen above)
2. :func:`.app_commands.command`

Both decorators wrap an async function into a :class:`~.app_commands.Command`, however,
the former also adds the command to the tree,
which skips the step of having to add it manually using :meth:`.CommandTree.add_command()`.

For example, these two are functionally equivalent:

.. code-block:: python

    @app_commands.command()
    async def meow(interaction: discord.Interaction):
        pass

    client.tree.add_command(meow)

    # versus.

    @client.tree.command()
    async def meow(interaction: discord.Interaction):
        pass

Since ``tree.command()`` is more concise and easier to understand,
it'll be the main method used to create slash commands in this guide.

Some information is logically inferred from the function to populate the slash command's fields:

- The :attr:`~.app_commands.Command.name` takes after the function name "meow"
- The :attr:`~.app_commands.Command.description` takes after the docstring "Meow meow meow"

To change them to something else, ``tree.command()`` takes ``name`` and ``description`` keyword-arguments:

.. code-block:: python

    @client.tree.command(name="woof", description="Woof woof woof")
    async def meow(interaction: discord.Interaction):
        pass

    # or...
    @client.tree.command(name="list")
    async def list_(interaction: discord.Interaction):
        # prevent shadowing the "list" builtin

If a description isn't provided through ``description`` or by the docstring, an ellipsis "..." is used instead.

Interaction
++++++++++++

As shown above, app commands always keep the first parameter for an :class:`~discord.Interaction`,
a Discord model used for both app commands and UI message components.

When an interaction is created on command invoke, some information about the surrounding context is given, such as:

- :class:`discord.Interaction.channel` - the channel it was invoked in
- :class:`discord.Interaction.guild` - the guild it was invoked in, if any
- :class:`discord.Interaction.user` - the user or member who invoked the command

Attributes like these and others are a given, however when it comes to responding to an interaction,
by sending a message or otherwise, the methods from :attr:`.Interaction.response` need to be used.

A response needs to occur within 3 seconds, otherwise this message pops up on Discord in red:

.. image:: /images/guide/app_commands/interaction_failed.png

In practice, it's common to use either of the following two methods:

- :meth:`.InteractionResponse.send_message` to send a message
- :meth:`.InteractionResponse.defer` to defer a response

In the case of deferring, a follow-up message needs to be sent within 15 minutes for app commands.

For example, to send a deferred ephemeral message:

.. code-block:: python

    import asyncio
    import random

    @client.tree.command()
    async def weather(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # indicates the follow-up message will be ephemeral

        weathers = ["clear", "cloudy", "rainy", "stormy"]
        await asyncio.sleep(5) # an expensive operation... (no more than 15 minutes!)
        forecast = random.choice(weathers)

        await interaction.followup.send(f"the weather today is {forecast}!")

Syncing
++++++++

In order for this command to show up on Discord, the API needs some information regarding it, namely:

- The name and description
- Any :ref:`parameter names, types, descriptions <parameters>`
- Any :ref:`checks <checks>` attached
- Whether this command is a :ref:`group <command_groups>`
- Whether this is a :ref:`global or guild command <guild_commands>`
- Any :ref:`localisations <translating>` for the above

Syncing is the process of sending this information, which is done by
calling the :meth:`.CommandTree.sync` method, typically in :meth:`.Client.setup_hook`:

.. code-block:: python

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
            await self.tree.sync()

Commands need to be synced again each time a new command is added or removed, or if any of the above properties change.

Reloading your own client is sometimes also needed for new changes to be visible -
old commands tend to linger in the command preview if a client hasn't yet refreshed, but Discord
blocks invocation with this message in red:

.. image:: /images/guide/app_commands/outdated_command.png

As another measure, discord.py will log warnings if there's a mismatch with what Discord provides and
what the bot defines in code during invocation.

.. _parameters:

Parameters
-----------

Since slash commands are defined by making Python functions, parameters are similarly defined with function parameters.

Each parameter must have an assiociated type. This restricts what type of value a user can and cannot input.
Types are specified in code through :pep:`526` function annotations.

For example, the following code implements a repeat command that repeats text a
certain number of times using a ``content`` and an ``n_times`` parameter:

.. code-block:: python

    import textwrap

    @client.tree.command()
    async def repeat(interaction: discord.Interaction, content: str, n_times: int):
        to_send = textwrap.shorten(f"{content} " * n_times, width=2000)
        await interaction.response.send_message(to_send)

On the client, these parameters show up as "black boxes" that need to be filled out during invocation:

.. image:: /images/guide/app_commands/repeat_command_preview.png
    :width: 300

Parameters cannot have a value that doesn't match their type; trying to enter a non-numeric character for ``n_times`` will result in an error:

.. image:: /images/guide/app_commands/repeat_command_wrong_type.png
    :width: 300

Some types of parameters require different modes of input. For example,
annotating to :class:`discord.Member` will show a selection of members to pick from in the current guild.

.. image:: /images/guide/app_commands/avatar_command_preview.png
    :width: 300

A full list of available parameter types can be seen in the :ref:`type conversion table <type_conversion>`.

typing.Optional
++++++++++++++++

Discord supports optional parameters, wherein a user doesn't need to provide a value during invocation.

A parameter is considered optional if its assigned a default value and/or annotated
to :obj:`~typing.Optional`.

For example, this command displays a given user's avatar, or the current user's avatar:

.. code-block:: python

    from typing import Optional

    @client.tree.command()
    async def avatar(interaction: discord.Interaction, user: Optional[discord.User] = None):
        avatar = (user or interaction.user).display_avatar
        await interaction.response.send_message(avatar.url)

On Discord:

.. image:: /images/guide/app_commands/avatar_command_optional_preview.png

`Python version 3.10+ union types <https://peps.python.org/pep-0604/>`_ are also supported instead of :obj:`typing.Optional`.

typing.Union
+++++++++++++

Some types comprise of multiple other types. For example, a ``MENTIONABLE`` type parameter can point to any of these:

- :class:`discord.User`
- :class:`discord.Member`
- :class:`discord.Role`

To specify in code, a parameter should annotate to a :obj:`typing.Union` with all the different models:

.. code-block:: python

    from typing import Union

    @client.tree.command()
    async def something(
        interaction: discord.Interaction,
        mentionable: Union[discord.User, discord.Member, discord.Role]
    ):
        await interaction.response.send_message(
            f"i got: {mentionable}, of type: {mentionable.__class__.__name__}"
        )

Types that point to other types also don't have to include everything.
For example, a ``CHANNEL`` type parameter can point to any channel in a guild,
but can be narrowed down to a specific set of channels:

.. code-block:: python

    from typing import Union

    @client.tree.command()
    async def channel_info(interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        # Everything except threads
        pass

    @client.tree.command()
    async def channel_info(interaction: discord.Interaction, channel: discord.TextChannel):
        # Only text channels
        pass

    @client.tree.command()
    async def channel_info(interaction: discord.Interaction, channel: Union[discord.Thread, discord.VoiceChannel]):
        # Threads and voice channels only
        pass

.. note::

    Union types can't mix Discord types.

    Something like ``Union[discord.Member, discord.TextChannel]`` isn't possible.

Refer to the :ref:`type conversion table <type_conversion>` for full information on sub-types.

Describing
+++++++++++

Descriptions are added to parameters using the :func:`.app_commands.describe` decorator,
where each keyword is treated as a parameter name.

.. code-block:: python
    :emphasize-lines: 2-5

    @client.tree.command()
    @app_commands.describe(
        content="the text to repeat",
        n_times="the number of times to repeat the text"
    )
    async def repeat(interaction: discord.Interaction, content: str, n_times: int):
        to_send = textwrap.shorten(f"{content} " * n_times, width=2000)
        await interaction.response.send_message(to_send)

These show up on Discord just beside the parameter's name:

.. image:: /images/guide/app_commands/repeat_command_described.png

In addition to the decorator, parameter descriptions can also be added using
Google, Sphinx or Numpy style docstrings.

Examples using a command to add 2 numbers together:

.. code-block:: python

    @client.tree.command() # numpy
    async def addition(interaction: discord.Interaction, a: int, b: int):
        """adds 2 numbers together.

        Parameters
        -----------
        a: int
            left operand
        b: int
            right operand
        """

        await interaction.response.send_message(f"{a} + {b} is {a + b}!")

    @client.tree.command() # google
    async def addition(interaction: discord.Interaction, a: int, b: int):
        """adds 2 numbers together.

        Args:
            a (int): left operand
            b (int): right operand
        """

    @client.tree.command() # sphinx
    async def addition(interaction: discord.Interaction, a: int, b: int):
        """adds 2 numbers together.

        :param a: left operand
        :param b: right operand
        """

If both are used, :func:`.app_commands.describe` always takes precedence.

Naming
^^^^^^^

Since parameter names are confined to the rules of Python's syntax,
the library offers a method to rename them with the :func:`.app_commands.rename` decorator.

In use:

.. code-block:: python
    :emphasize-lines: 2

    @client.tree.command()
    @app_commands.rename(n_times="number-of-times")
    async def repeat(interaction: discord.Interaction, content: str, n_times: int):
        to_send = textwrap.shorten(f"{content} " * n_times, width=2000)
        await interaction.response.send_message(to_send)

When referring to a renamed parameter in other decorators, the original parameter name should be used.
For example, to use :func:`~.app_commands.describe` and :func:`~.app_commands.rename` together:

.. code-block:: python

    @client.tree.command()
    @app_commands.describe(
        content="the text to repeat",
        n_times="the number of times to repeat the text"
    )
    @app_commands.rename(n_times="number-of-times")
    async def repeat(interaction: discord.Interaction, content: str, n_times: int):
        to_send = textwrap.shorten(f"{content} " * n_times, width=2000)
        await interaction.response.send_message(to_send)

Choices
++++++++

:class:`str`, :class:`int` and :class:`float` type parameters can optionally set a list of choices for an argument
using the :func:`.app_commands.choices` decorator.

During invocation, a user is restricted to picking one choice and can't type anything else.

Each individual choice contains 2 fields:

- A name, which is what the user sees in their client
- A value, which is hidden to the user and only visible to the bot and API.

  Typically, this is either the same as the name or something else more developer-friendly.

  Value types are limited to either a :class:`str`, :class:`int` or :class:`float`.

To illustrate, the following command has a selection of 3 colours with each value being the colour code:

.. code-block:: python

    @client.tree.command()
    @app_commands.describe(colour="pick your favourite colour")
    @app_commands.choices(colour=[
        app_commands.Choice(name="Red", value=0xFF0000),
        app_commands.Choice(name="Green", value=0x00FF00),
        app_commands.Choice(name="Blue", value=0x0000FF)
    ])
    async def colour(interaction: discord.Interaction, colour: app_commands.Choice[int]):
        """show a colour"""

        embed = discord.Embed(title=colour.name, colour=colour.value)
        await interaction.response.send_message(embed=embed)

On the client:

.. image:: /images/guide/app_commands/colour_command_preview.png
    :width: 400

discord.py also supports 2 other pythonic ways of adding choices to a command,
shown :func:`here <discord.app_commands.choices>` in the reference.

Autocompletion
+++++++++++++++

Autocomplete callbacks allow the bot to dynamically return up to 25 choices
to a user as they type a parameter.

In short:

- User starts typing.

- After a brief debounced pause from typing, Discord requests a list of choices from the bot.

- An autocomplete callback is called with the current user input.

- Returned choices are sent back to Discord and shown in the user's client.

  - An empty list can be returned to denote no choices.

Attaching an autocomplete function to a parameter can be done in 2 main ways:

1. From the command, with the :meth:`~.app_commands.Command.autocomplete` decorator
2. With a separate decorator, :func:`.app_commands.autocomplete`

Code examples for either method can be found in the corresponding reference page.

.. note::

    Unlike :func:`.app_commands.choices`, a user can still submit any value instead of
    being limited to the bot's suggestions.

.. warning::

    Since exceptions raised from within an autocomplete callback are not considered handleable,
    they're silently ignored and discarded.

    Instead, an empty list is returned to the user.

Range
++++++

:class:`str`, :class:`int` and :class:`float` type parameters can optionally set a minimum and maximum value.
For strings, this limits the character count, whereas for numeric types this limits the magnitude.

To set a range, a parameter should annotate to :class:`.app_commands.Range`.

Transformers
+++++++++++++

Sometimes additional logic for parsing arguments is wanted.
For instance, to parse a date string into a :class:`datetime.datetime` we might do:

.. code-block:: python

    import datetime

    @client.tree.command()
    async def date(interaction: discord.Interaction, date: str):
        when = datetime.datetime.strptime(date, "%d/%m/%Y") # dd/mm/yyyy format
        when = when.replace(tzinfo=datetime.timezone.utc) # attach timezone information

        # do something with 'when'...

However, this can get verbose pretty quickly if the parsing is more complex or we need to do this parsing in multiple commands.
It helps to isolate this code into it's own place, which we can do with transformers.

Transformers are effectively classes containing a ``transform`` method that "transforms" a raw argument value into a new value.
Making one is done by inherting from :class:`.app_commands.Transformer` and overriding the :meth:`~.Transformer.transform` method.

.. code-block:: python

    # the above example adapted to a transformer

    class DateTransformer(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, value: str) -> datetime.datetime:
            when = datetime.datetime.strptime(date, "%d/%m/%Y")
            when = when.replace(tzinfo=datetime.timezone.utc)
            return when

If you're familar with the commands extension :ref:`ext.commands <discord_ext_commands>`, a lot of similarities can be drawn between transformers and converters.

To use this transformer in a command, a paramater needs to annotate to :class:`.app_commands.Transform`,
passing the transformed type and transformer respectively.

.. code-block:: python

    @client.tree.command()
    async def date(interaction: discord.Interaction, when: app_commands.Transform[datetime.datetime, DateTransformer]):
        # do something with 'when'...

It's also possible to instead pass an instance of the transformer instead of the class directly,
which opens up the possibility of setting up some state in :meth:`~object.__init__`.

Since the parameter's type annotation is replaced with :class:`~.app_commands.Transform`,
the underlying type and other information must now be provided through the :class:`~.app_commands.Transformer` itself.

These can be provided by overriding the following properties:

- :attr:`~.Transformer.type`
- :attr:`~.Transformer.min_value`
- :attr:`~.Transformer.max_value`
- :attr:`~.Transformer.choices`
- :attr:`~.Transformer.channel_types`

Since these are properties, they must be decorated with :class:`property`:

.. code-block:: python

    class UserAvatar(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, user: discord.User) -> discord.Asset:
            return user.display_avatar

        # changes the underlying type to discord.User
        @property
        def type(self) -> discord.AppCommandOptionType:
            return discord.AppCommandOptionType.user

:meth:`~.Transformer.autocomplete` callbacks can also be defined in-line.

.. _type_conversion:

Type conversion
++++++++++++++++

The table below outlines the relationship between Discord and Python types.

+-----------------+------------------------------------------------------------------------------------+
|   Discord Type  |                                Python Type                                         |
+=================+====================================================================================+
| ``STRING``      | :class:`str`                                                                       |
+-----------------+------------------------------------------------------------------------------------+
| ``INTEGER``     | :class:`int`                                                                       |
+-----------------+------------------------------------------------------------------------------------+
| ``BOOLEAN``     | :class:`bool`                                                                      |
+-----------------+------------------------------------------------------------------------------------+
| ``NUMBER``      | :class:`float`                                                                     |
+-----------------+------------------------------------------------------------------------------------+
| ``USER``        | :class:`~discord.User` or :class:`~discord.Member`                                 |
+-----------------+------------------------------------------------------------------------------------+
| ``CHANNEL``     | :class:`~discord.abc.GuildChannel` and all subclasses, or :class:`~discord.Thread` |
+-----------------+------------------------------------------------------------------------------------+
| ``ROLE``        | :class:`~discord.Role`                                                             |
+-----------------+------------------------------------------------------------------------------------+
| ``MENTIONABLE`` | :class:`~discord.User` or :class:`~discord.Member`, or :class:`~discord.Role`      |
+-----------------+------------------------------------------------------------------------------------+
| ``ATTACHMENT``  | :class:`~discord.Attachment`                                                       |
+-----------------+------------------------------------------------------------------------------------+

:ddocs:`Application command option types <interactions/application-commands#application-command-object-application-command-option-type>` as documented by Discord.

User parameter
^^^^^^^^^^^^^^^

Annotating to either :class:`discord.User` or :class:`discord.Member` both point to a ``USER`` Discord-type.

The actual type given by Discord is dependent on whether the command was invoked in DM-messages or in a guild.

For example, if a parameter annotates to :class:`~discord.Member`, and the command is invoked in direct-messages,
discord.py will raise an error since the actual type given by Discord,
:class:`~discord.User`, is incompatible with :class:`~discord.Member`.

discord.py doesn't raise an error for the other way around, ie. a parameter annotated to :class:`~discord.User` invoked in a guild -
this is because :class:`~discord.Member` is compatible with :class:`~discord.User`.

To accept member and user, regardless of where the command was invoked, place both types in a :obj:`~typing.Union`:

.. code-block:: python

    from typing import Union

    @client.tree.command()
    async def userinfo(
        interaction: discord.Interaction,
        user: Union[discord.User, discord.Member]
    ):
        info = user.name

        # add some extra info if this command was invoked in a guild
        if isinstance(user, discord.Member):
            joined = user.joined_at
            if joined:
                relative = discord.utils.format_dt(joined, "R")
                info = f"{info} (joined this server {relative})"

        await interaction.response.send_message(info)

.. _command_groups:

Command groups
---------------

To make a more organised and complex tree of commands, Discord implements command groups and subcommands.
A group can contain up to 25 subcommands or subgroups, with up to 1 level of nesting supported.

Meaning, a structure like this is possible:

.. code-block::

    todo
    ├── lists
    │   ├── /todo lists create
    │   └── /todo lists switch
    ├── /todo add
    └── /todo delete

Command groups **are not invocable** on their own.

Therefore, instead of creating a command the standard way by decorating an async function,
groups are created by using :class:`.app_commands.Group`.

This class is customisable by subclassing and passing in any relevant fields at inheritance:

.. code-block:: python

    class Todo(app_commands.Group, name="todo", description="manages a todolist"):
        ...

    client.tree.add_command(Todo()) # required!

.. note::

    Groups need to be added to the command tree manually with :meth:`.CommandTree.add_command`,
    since we lose the shortcut decorator :meth:`.CommandTree.command` with this class approach.

If ``name`` or ``description`` are omitted, the class defaults to using a lower-case kebab-case
version of the class name, and the class's docstring shortened to 100 characters for the description.

Subcommands can be made in-line by decorating bound methods in the class:

.. code-block:: python

    class Todo(app_commands.Group, name="todo", description="manages a todolist"):
        @app_commands.command(name="add", description="add a todo")
        async def todo_add(self, interaction: discord.Interaction):
            await interaction.response.send_message("added something to your todolist...!")

    client.tree.add_command(Todo())

After syncing:

.. image:: /images/guide/app_commands/todo_group_preview.png
    :width: 400

To add 1-level of nesting, create another :class:`~.app_commands.Group` in the class:

.. code-block:: python

    class Todo(app_commands.Group, name="todo", description="manages a todolist"):
        @app_commands.command(name="add", description="add a todo")
        async def todo_add(self, interaction: discord.Interaction):
            await interaction.response.send_message("added something to your todolist...!")

        todo_lists = app_commands.Group(
            name="lists",
            description="commands for managing different todolists for different purposes"
        )

        @todo_lists.command(name="switch", description="switch to a different todolist")
        async def todo_lists_switch(self, interaction: discord.Interaction):
            ... # /todo lists switch

.. image:: /images/guide/app_commands/todo_group_nested_preview.png
    :width: 400

Decorators like :func:`.app_commands.default_permissions` and :func:`.app_commands.guild_only`
can be added on top of a subclass to apply to the group, for example:

.. code-block:: python

    @app_commands.default_permissions(manage_emojis=True)
    class Emojis(app_commands.Group):
        ...

Due to a Discord limitation, individual subcommands cannot have differing official-checks.

.. _guild_commands:

Guild commands
---------------

So far, all the command examples in this page have been global commands,
which every guild your bot is in can see and use.

In contrast, guild commands are only seeable and usable by members of a certain guild.

There are 2 main ways to specify which guilds a command should sync a copy to:

- Via the :func:`.app_commands.guilds` decorator, which takes a variadic amount of guilds
- By passing in ``guild`` or ``guilds`` when adding a command to a :class:`~.app_commands.CommandTree`

To demonstrate:

.. code-block:: python

    @client.tree.command()
    @app_commands.guilds(discord.Object(336642139381301249))
    async def support(interaction: discord.Interaction):
        await interaction.response.send_message("hello, welcome to the discord.py server!")

    # or:

    @app_commands.command()
    async def support(interaction: discord.Interaction):
        await interaction.response.send_message("hello, welcome to the discord.py server!")

    client.tree.add_command(support, guild=discord.Object(336642139381301249))

.. note::

    For these to show up, :meth:`.CommandTree.sync` needs to be called for **each** guild
    using the ``guild`` keyword-argument.

Since guild commands can be useful in a development scenario, as often we don't want unfinished commands
to propagate to all guilds, the library offers a helper method :meth:`.CommandTree.copy_global_to`
to copy all global commands to a certain guild for syncing:

.. code-block:: python

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
            guild = discord.Object(695868929154744360) # a testing server
            self.tree.copy_global_to(guild)
            await self.tree.sync(guild=guild)

You'll typically find this syncing paradigm in some of the examples in the repository.

.. _checks:

Checks
-------

Checks refer to the restrictions an app command can have for invocation.
A user needs to pass all checks on a command in order to be able to invoke and see the command on their client.

Age-restriction
++++++++++++++++

Indicates whether this command can only be used in NSFW channels or not.

This can be configured by passing the ``nsfw`` keyword argument within the command decorator:

.. code-block:: python

    @client.tree.command(nsfw=True)
    async def evil(interaction: discord.Interaction):
        await interaction.response.send_message("******") # very explicit text!

Guild-only
+++++++++++

Indicates whether this command can only be used in guilds or not.

Enabled by adding the :func:`.app_commands.guild_only` decorator when defining an app command:

.. code-block:: python

    @client.tree.command()
    @app_commands.guild_only()
    async def serverinfo(interaction: discord.Interaction):
        assert interaction.guild is not None
        await interaction.response.send_message(interaction.guild.name)

Default permissions
++++++++++++++++++++

This sets the default permissions a user needs in order to be able to see and invoke an app command.

Configured by adding the :func:`.app_commands.default_permissions` decorator when defining an app command:

.. code-block:: python

    @client.tree.command()
    @app_commands.default_permissions(manage_nicknames=True)
    async def nickname(interaction: discord.Interaction, newname: str):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("i can't change my name here")
        else:
            await guild.me.edit(nick=newname)
            await interaction.response.send_message(f"hello i am {newname} now")

Commands with this check are still visible and invocable in the bot's direct messages,
regardless of the permissions specified.

To prevent this, :func:`~.app_commands.guild_only` can also be added.

.. warning::

    This can be overridden to a different set of permissions by server administrators through the "Integrations" tab on the official client,
    meaning, an invoking user might not actually have the permissions specified in the decorator.

Custom checks
++++++++++++++

waiting to be written

cover:

- how to make a check, what it should return, default behaviours
- builtin common checks and exceptions

Custom checks come in two forms:

- A local check, which runs for a single command
- A global check, which runs before all commands, and before any local checks

Global check
^^^^^^^^^^^^^

To define a global check, override :meth:`.CommandTree.interaction_check` in a :class:`~.app_commands.CommandTree` subclass.
This method is called before every command invoke.

For example:

.. code-block:: python

    whitelist = {236802254298939392, 402159684724719617} # cool people only

    class MyCommandTree(app_commands.CommandTree):
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id in whitelist

.. note::

    If your project uses :class:`.ext.commands.Bot` as the client instance,
    the :class:`.CommandTree` class can be configured via
    the ``tree_cls`` keyword argument in the bot constructor:

    .. code-block:: python
        :emphasize-lines: 6

        from discord.ext import commands

        bot = commands.Bot(
            command_prefix="?",
            intents=discord.Intents.default(),
            tree_cls=MyCommandTree
        )

Error handling
---------------

So far, any exceptions raised within a command callback, any custom checks or in a transformer should just be
logged in the program's ``stderr`` or through any custom logging handlers.

In order to catch exceptions, the library uses something called error handlers.

There are 3 handlers available:

1. A local handler, which only catches errors for a specific command
2. A group handler, which catches errors only for a certain group's subcommands
3. A global handler, which catches all errors in all commands

If an exception is raised, the library calls all 3 of these handlers in that order.

If a subcommand has multiple parents,
the subcommand's parent handler is called first, followed by it's parent handler.


waiting to be written further:

- code examples for each of the error handler types
- CommandInvokeError, TransformerError, __cause__
- creating custom erors to know which check/transformer raised what
- an example logging setup

.. _translating:

Translating
------------

heavy work-in-progress...!

Discord supports localisation for the following fields:

- Command names and descriptions
- Parameter names and descriptions
- Choice names (choices and autocomplete)

This allows the above fields to appear differently according to a user client's language setting.

Localisations can be done :ddocs:`partially <interactions/application-commands#localization>` -
when a locale doesn't have a translation for a given field, Discord will use the default/original string instead.

Support for localisation is implemented in discord.py with the :class:`.app_commands.Translator` interface,
which are effectively classes containing a core ``transform`` method that
takes the following parameters:

1. a ``string`` - the string to be translated according to ``locale``
2. a ``locale`` - the locale to translate to
3. a ``context`` - the context of this translation (what type of string is being translated)

When :meth:`.CommandTree.sync` is called, this method is called in a heavy loop for each
string for each locale.

A wide variety of translation systems can be implemented using this interface, such as
`gettext <https://docs.python.org/3/library/gettext.html>`_ and
`Project Fluent <https://projectfluent.org/>`_.

Only strings marked as ready for translation are passed to the method.
By default, every string is considered translatable and passed.

Nonetheless, to specify a translatable string explicitly,
simply pass a string wrapped in :class:`~.app_commands.locale_str` in places you'd usually use :class:`str`:

.. code-block:: python

    from discord.app_commands import locale_str as _

    @client.tree.command(name=_("example"), description=_("an example command"))
    async def example(interaction: discord.Interaction):
        ...

To toggle this behaviour, set the ``auto_locale_strings`` keyword-argument
to :obj:`False` when creating a command:

.. code-block:: python

    @client.tree.command(name="example", description="an example command", auto_locale_strings=False)
    async def example(interaction: discord.Interaction):
        # i am not translated

.. hint::

    Additional keyword-arguments passed to the :class:`~.app_commands.locale_str` constructor are
    inferred as "extra" information, which is kept untouched by the library in :attr:`~.locale_str.extras`.

    Utilise this field if additional info surrounding the string is required for translation.

Next, to create a translator, inherit from :class:`.app_commands.Translator` and
override the :meth:`~.Translator.translate` method:

.. code-block:: python

    class MyTranslator(app_commands.Translator):
        async def translate(
            self,
            string: app_commands.locale_str,
            locale: discord.Locale,
            context: app_commands.TranslationContext
        ) -> str:
            ...

A string should be returned according to the given ``locale``. If no translation is available,
:obj:`None` should be returned instead.

:class:`~.app_commands.TranslationContext`  provides contextual info for what is being translated.

This contains 2 properties:

- :attr:`~.app_commands.TranslationContext.location` - an enum representing what is being translated, eg. a command description.

- :attr:`~.app_commands.TranslationContext.data` - can point to different things depending on the ``location``.

  - When translating a field for a command or group, such as the name, this points to the command in question.

  - When translating a parameter name, this points to the :class:`~.app_commands.Parameter`.

  - For choice names, this points to the :class:`~.app_commands.Choice`.

Lastly, in order for a translator to be used, it needs to be attached to the tree
by calling :meth:`.CommandTree.set_translator`.

Since this is an async method, it's ideal to call it in an async entry-point, such as :meth:`.Client.setup_hook`:

.. code-block:: python

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
            await self.tree.set_translator(MyTranslator())

In summary:

- Use :class:`~.app_commands.locale_str` in-place of :class:`str` in parts of a command you want translated.

  - Done by default, so this step is skipped in-practice.

- Subclass :class:`.app_commands.Translator` and override the :meth:`.Translator.translate` method.

  - Return a translated string or :obj:`None`.

- Call :meth:`.CommandTree.set_translator` with a translator instance.

- Call :meth:`.CommandTree.sync`.

  - :meth:`.Translator.translate` will be called on all translatable strings.

Following is a quick demo using the `Project Fluent <https://projectfluent.org/>`_ translation system
and the `Python fluent library <https://pypi.org/project/fluent/>`_.

Relative to the bot's working directory is a translation resource
described in fluent's `FTL <https://projectfluent.org/fluent/guide/>`_ format - containing
the Japanese (locale: ``ja``) translations for the bot:

.. code-block::
    :caption: l10n/ja/commands.ftl

    # command metadata
    apple-command-name = リンゴ
    apple-command-description = ボットにリンゴを食べさせます。

    # parameters
    apple-command-amount = 食べさせるリンゴの数

    # responses from the command body
    apple-command-response = リンゴを{ $apple_count }個食べました。

In code, strings are only considered translatable if they have an
attached ``fluent_id`` extra:

.. code-block:: python

    @client.tree.command(
        name=_("apple", fluent_id="apple-command-name"),
        description=_("tell the bot to eat some apples", fluent_id="apple-command-description")
    )
    @app_commands.describe(amount=_("how many apples?", fluent_id="apple-command-amount"))
    async def apple(interaction: discord.Interaction, amount: int):
        translator = client.tree.translator

        # plurals for the bots native language (english) are handled here in the code.
        # fluent can handle plurals for secondary languages if needed.
        # see: https://projectfluent.org/fluent/guide/selectors.html

        plural = "apple" if amount == 1 else "apples"

        translated = await translator.translate_string(
            _(f"i ate {amount} {plural}", fluent_id="apple-command-response"),
            interaction.locale,
            apple_count=amount
        )

        await interaction.response.send_message(translated)

.. code-block:: python

    from fluent.runtime import FluentLocalization, FluentResourceLoader

    class JapaneseTranslator(app_commands.Translator):
        def __init__(self):
            self.resources = FluentResourceLoader("l10n/{locale}")
            self.mapping = {
                discord.Locale.japanese: FluentLocalization(["ja"], ["commands.ftl"], self.resources),
                # + additional locales as needed
            }

        # translates a given string for a locale,
        # subsituting any required parameters
        async def translate_string(
            self,
            string: locale_str,
            locale: discord.Locale,
            **params: Any
        ) -> str:
            l10n = self.mapping.get(locale)
            if not l10n:
                # return the string untouched
                return string.message

            fluent_id = string.extras["fluent_id"]
            return l10n.format_value(fluent_id, params)

        # core translate method called by the library
        async def translate(
            self,
            string: locale_str,
            locale: discord.Locale,
            context: app_commands.TranslationContext
        ):
            fluent_id = string.extras.get("fluent_id")
            if not fluent_id:
                # ignore strings without an attached fluent_id
                return None

            l10n = self.mapping.get(locale)
            if not l10n:
                # no translation available for this locale
                return None

            # otherwise, a translation is assumed to exist and is returned
            return l10n.format_value(fluent_id)

Viewing the command with an English (or any other) language setting:

.. image:: /images/guide/app_commands/apple_command_english.png
    :width: 300

With a Japanese language setting:

.. image:: /images/guide/app_commands/apple_command_japanese.png
    :width: 300

Recipes
--------

This section covers some common use-cases for slash commands.

Manually syncing
+++++++++++++++++

Syncing app commands on startup, such as inside :meth:`.Client.setup_hook` can often be spammy
and incur the heavy ratelimits set by Discord.
Therefore, it's helpful to control the syncing process manually.

A common and recommended approach is to create an owner-only traditional message command to do this.

The :ref:`commands extension <discord_ext_commands>` makes this easy:

.. code-block:: python

    from discord.ext import commands

    # requires the `message_content` intent to work!

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="?", intents=intents)

    @bot.command()
    @commands.is_owner()
    async def sync(ctx: commands.Context):
        synced = await bot.tree.sync()
        await ctx.reply(f"synced {len(synced)} global commands")

    # invocable only by yourself on discord using ?sync

A more complex command that offers higher granularity using arguments:

.. code-block:: python

    from typing import Literal, Optional

    import discord
    from discord.ext import commands

    # requires the `message_content` intent to work!

    # https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html

    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

If your bot isn't able to use the message content intent, due to verification requirements or otherwise,
bots can still read message content for direct-messages and for messages that mention the bot.

:func:`.commands.when_mentioned` can be used to apply a mention prefix to your bot:

.. code-block:: python

    bot = commands.Bot(
        command_prefix=commands.when_mentioned,
        intents=discord.Intents.default()
    )