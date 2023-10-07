:orphan:

.. _discord_slash_commands:

Slash commands
===============

Slash commands are one of Discord's primary methods of implementing a user-interface for bots.
They're a branch of application commands, the other type being context menu commands, and analogous to their name,
they're previewed and invoked in the Discord client by beginning your message with a forward-slash:

.. image:: /images/guide/app_commands/meow_command_preview.png
    :width: 400

Both types of app commands are implemented within the :ref:`discord.app_commands <discord_app_commands>` package.
Any code example in this page will always assume the following two imports:

.. code-block:: python

    import discord
    from discord import app_commands

Setting up
-----------

To work with app commands, bots need the ``applications.commands`` scope.

You can enable this scope when generating an OAuth2 URL for your bot, the steps to do so outlined :ref:`here <discord_invite_bot>`.

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

        await interaction.response.send_message('meow')

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

    @client.tree.command(name='woof', description='Woof woof woof')
    async def meow(interaction: discord.Interaction):
        pass

    # or...
    @client.tree.command(name='list')
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

        weathers = ['sunny', 'clear', 'cloudy', 'rainy', 'stormy', 'snowy']
        await asyncio.sleep(5) # an expensive operation... (no more than 15 minutes!)
        forecast = random.choice(weathers)

        await interaction.followup.send(f'the weather today is {forecast}!')

Syncing
++++++++

In order for this command to show up on Discord, the API needs some information regarding it, namely:

- The name and description

- Any :ref:`parameter names, types and descriptions <parameters>`
- Any :ref:`checks <checks>` attached
- Whether this command is a :ref:`group <command_groups>`
- Whether this is a :ref:`global or guild command <guild_commands>`
- Any :ref:`localisations <translating>` for the above

Syncing is the process of sending this information, which is done by
calling the :meth:`.CommandTree.sync` method.

Typically, this is called on start-up in :meth:`.Client.setup_hook`:

.. code-block:: python

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
            await self.tree.sync()

Commands need to be synced again each time a new command is added or removed, or if any of the above properties change.

Syncing is **not** required when changing client-side behaviour,
such as by adding a :ref:`library-side check <custom_checks>`, adding a :ref:`transformer <transformers>`
or changing anything within the function body.

Reloading your own client is sometimes needed for new changes to be visible -
old commands tend to linger in the command preview if a client hasn't yet refreshed, but Discord
blocks invocation with this message in red:

.. image:: /images/guide/app_commands/outdated_command.png

As another measure, the library will log warnings if there's a mismatch with what Discord provides and
what the bot defines in code during invocation.

.. _parameters:

Parameters
-----------

Since slash commands are defined by making Python functions, parameters are similarly defined with function parameters.

Each parameter must have an assiociated type. This restricts what type of value a user can and cannot input.
Types are specified in code through :pep:`3107` function annotations.

For example, the following command has a ``liquid`` string parameter:

.. code-block:: python

    @client.tree.command()
    async def bottles(interaction: discord.Interaction, liquid: str):
        await interaction.response.send_message(f'99 bottles of {liquid} on the wall!')

On the client, parameters show up as these little black boxes that need to be filled out during invocation:

.. image:: /images/guide/app_commands/bottles_command_preview.png
    :width: 300

Since this is a string parameter, virtually anything can be inputted (up to Discord's limits).

Other parameter types are more restrictive - for example, if an integer parameter is added:

.. code-block:: python

    @client.tree.command()
    async def bottles(interaction: discord.Interaction, liquid: str, amount: int):
        await interaction.response.send_message(f'{amount} bottles of {liquid} on the wall!')

Trying to enter a non-numeric character for ``amount`` will result with this red message:

.. image:: /images/guide/app_commands/input_a_valid_integer.png
    :width: 300

Additionally, since both of these parameters are required, trying to skip one will result in this message in red:

.. image:: /images/guide/app_commands/this_option_is_required.png
    :width: 300

Some parameter types have different modes of input.

For example, annotating to :class:`~discord.User` will show a selection of users to
pick from in the current context and :class:`~discord.Attachment` will show a file-dropbox.

A full overview of supported types can be seen in the :ref:`type conversion table <type_conversion>`.

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
    :width: 300

:pep:`Python version 3.10+ union types <604>` are also supported instead of :obj:`typing.Optional`.

typing.Union
+++++++++++++

Some types comprise of multiple other types.
For example, the ``MENTIONABLE`` type includes both the user and role types:

- :class:`discord.User` and :class:`discord.Member`
- :class:`discord.Role`

To use a mentionable type, a parameter should annotate to a :obj:`~typing.Union` with each model:

.. code-block:: python

    from typing import Union

    @client.tree.command()
    async def something(
        interaction: discord.Interaction,
        mentionable: Union[discord.User, discord.Member, discord.Role]
    ):
        await interaction.response.send_message(
            f'i got: {mentionable}, of type: {mentionable.__class__.__name__}'
        )

Not everything has to be included - for example, a ``CHANNEL`` type parameter
can point to any channel in a guild, but can be narrowed down to a specific set of types:

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

.. warning::

    Union types can't mix Discord types.

    Something like ``Union[discord.Member, discord.TextChannel]`` isn't possible.

Refer to the :ref:`type conversion table <type_conversion>` for full information.

Describing
+++++++++++

Descriptions are added to parameters using the :func:`.app_commands.describe` decorator,
where each keyword is treated as a parameter name.

.. code-block:: python

    @client.tree.command()
    @app_commands.describe(
        liquid='what type of liquid is on the wall',
        amount='how much of it is on the wall'
    )
    async def bottles(interaction: discord.Interaction, liquid: str, amount: int):
        await interaction.response.send_message(f'{amount} bottles of {liquid} on the wall!')

These show up on Discord just beside the parameter's name:

.. image:: /images/guide/app_commands/bottles_command_described.png

Not specifying a description results with an ellipsis "..." being used instead.

In addition to the decorator, parameter descriptions can also be added using
Google, Sphinx or NumPy style docstrings.

Examples using a command to add 2 numbers together:

.. tab:: NumPy

    .. code-block:: python

        @client.tree.command()
        async def addition(interaction: discord.Interaction, a: int, b: int):
            """adds 2 numbers together.

            Parameters
            -----------
            a: int
                left operand
            b: int
                right operand
            """

            await interaction.response.send_message(f'{a + b = }')

.. tab:: Google

    .. code-block:: python

        @client.tree.command()
        async def addition(interaction: discord.Interaction, a: int, b: int):
            """adds 2 numbers together.

            Args:
                a (int): left operand
                b (int): right operand
            """

            await interaction.response.send_message(f'{a + b = }')

.. tab:: Sphinx

    .. code-block:: python

        @client.tree.command()
        async def addition(interaction: discord.Interaction, a: int, b: int):
            """adds 2 numbers together.

            :param a: left operand
            :param b: right operand
            """

            await interaction.response.send_message(f'{a + b = }')

Other meta info can be specified in the docstring, such as the function return type,
but in-practice only the parameter descriptions are used.

Parameter descriptions added using :func:`.app_commands.describe` always
take precedence over ones specified in the docstring.

Naming
^^^^^^^

Since parameter names are confined to the rules of Python's syntax,
the library offers a method to rename them with the :func:`.app_commands.rename` decorator.

In use:

.. code-block:: python

    @client.tree.command()
    @app_commands.rename(amount='liquid-count')
    async def bottles(interaction: discord.Interaction, liquid: str, amount: int):
        await interaction.response.send_message(f'{amount} bottles of {liquid} on the wall!')

When referring to a renamed parameter in other decorators, the original parameter name should be used.
For example, to use :func:`~.app_commands.describe` and :func:`~.app_commands.rename` together:

.. code-block:: python

    @client.tree.command()
    @app_commands.rename(amount='liquid-count')
    @app_commands.describe(
        liquid='what type of liquid is on the wall',
        amount='how much of it is on the wall'
    )
    async def bottles(interaction: discord.Interaction, liquid: str, amount: int):
        await interaction.response.send_message(f'{amount} bottles of {liquid} on the wall!')

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

    from discord.app_commands import Choice

    @client.tree.command()
    @app_commands.describe(colour='pick your favourite colour')
    @app_commands.choices(colour=[
        Choice(name='Red', value=0xFF0000),
        Choice(name='Green', value=0x00FF00),
        Choice(name='Blue', value=0x0000FF)
    ])
    async def colour(interaction: discord.Interaction, colour: Choice[int]):
        """show a colour"""

        embed = discord.Embed(title=colour.name, colour=colour.value)
        await interaction.response.send_message(embed=embed)

On the client:

.. image:: /images/guide/app_commands/colour_command_preview.png
    :width: 400

discord.py also supports 2 other pythonic ways of adding choices to a command,
shown :func:`here <discord.app_commands.choices>` in the reference.

.. _autocompletion:

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

.. _transformers:

Transformers
+++++++++++++

Sometimes additional logic for parsing arguments is wanted.
For instance, to parse a date string into a :class:`datetime.datetime` we might do:

.. code-block:: python

    import datetime

    @client.tree.command()
    async def date(interaction: discord.Interaction, date: str):
        when = datetime.datetime.strptime(date, '%d/%m/%Y') # dd/mm/yyyy format
        when = when.replace(tzinfo=datetime.timezone.utc) # attach timezone information

        # do something with 'when'...

However, this can get verbose pretty quickly if the parsing is more complex or we need to do this parsing in multiple commands.
It helps to isolate this code into it's own place, which we can do with transformers.

Transformers are effectively classes containing a ``transform`` method that "transforms" a raw argument value into a new value.

To make one, inherit from :class:`.app_commands.Transformer` and override the :meth:`~.Transformer.transform` method:

.. code-block:: python

    # the above example adapted to a transformer

    class DateTransformer(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, value: str) -> datetime.datetime:
            when = datetime.datetime.strptime(date, '%d/%m/%Y')
            when = when.replace(tzinfo=datetime.timezone.utc)
            return when

If you're familar with the commands extension (:ref:`ext.commands <discord_ext_commands>`), a lot of similarities can be drawn between transformers and converters.

To use this transformer in a command, a paramater needs to annotate to :class:`.app_commands.Transform`,
passing the transformed type and transformer respectively.

.. code-block:: python

    from discord.app_commands import Transform

    @client.tree.command()
    async def date(interaction: discord.Interaction, when: Transform[datetime.datetime, DateTransformer]):
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
                relative = discord.utils.format_dt(joined, 'R')
                info = f'{info} (joined this server {relative})'

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

This class is customisable by subclassing and passing in any relevant fields in the class constructor:

.. code-block:: python

    class Todo(app_commands.Group, description='manages a todolist'):
        ...

    client.tree.add_command(Todo()) # required!

.. note::

    Groups need to be added to the command tree manually with :meth:`.CommandTree.add_command`,
    since we lose the shortcut decorator :meth:`.CommandTree.command` with this class approach.

If ``name`` or ``description`` are omitted, the class defaults to using a lower-case kebab-case
version of the class name, and the class's docstring shortened to 100 characters for the description.

Subcommands can be made in-line by decorating bound methods in the class:

.. code-block:: python

    class Todo(app_commands.Group, description='manages a todolist'):
        @app_commands.command(name='add', description='add a todo')
        async def todo_add(self, interaction: discord.Interaction):
            await interaction.response.send_message('added something to your todolist...!')

    client.tree.add_command(Todo())

After syncing:

.. image:: /images/guide/app_commands/todo_group_preview.png
    :width: 400

To add 1-level of nesting, create another :class:`~.app_commands.Group` in the class:

.. code-block:: python

    class Todo(app_commands.Group, description='manages a todolist'):
        @app_commands.command(name='add', description='add a todo')
        async def todo_add(self, interaction: discord.Interaction):
            await interaction.response.send_message('added something to your todolist...!')

        todo_lists = app_commands.Group(
            name='lists',
            description='commands for managing different todolists for different purposes'
        )

        @todo_lists.command(name='switch', description='switch to a different todolist')
        async def todo_lists_switch(self, interaction: discord.Interaction):
            ... # /todo lists switch

.. image:: /images/guide/app_commands/todo_group_nested_preview.png
    :width: 400

Nested group commands can be moved into another class if it ends up being a bit too much to read in one class:

.. code-block:: python

    class TodoLists(app_commands.Group, name='lists'):
        """commands for managing different todolists for different purposes"""

        @app_commands.command(name='switch', description='switch to a different todolist')
        async def todo_lists_switch(self, interaction: discord.Interaction):
            ...

    class Todo(app_commands.Group, description='manages a todolist'):
        @app_commands.command(name='add', description='add a todo')
        async def todo_add(self, interaction: discord.Interaction):
            await interaction.response.send_message('added something to your todolist...!')

        todo_lists = TodoLists()

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
        await interaction.response.send_message('hello, welcome to the discord.py server!')

    # or:

    @app_commands.command()
    async def support(interaction: discord.Interaction):
        await interaction.response.send_message('hello, welcome to the discord.py server!')

    client.tree.add_command(support, guild=discord.Object(336642139381301249))

.. note::

    For these to show up, :meth:`.CommandTree.sync` needs to be called for **each** guild
    using the ``guild`` keyword-argument.

Whilst multiple guilds can be specified on a single command, it's important to be aware that after
syncing individually to each guild, each guild is then maintaing its own copy of the command.

New changes will require syncing to every guild again, which can cause a temporary mismatch with what a guild has
and what's defined in code.

Since guild commands can be useful in a development scenario, as often we don't want unfinished commands
to propagate to all guilds, the library offers a helper method :meth:`.CommandTree.copy_global_to`
to copy all global commands to a certain guild for syncing:

.. code-block:: python

    class MyClient(discord.Client):
        def __init__(self):
            super().__init__(intents=discord.Intents.default())
            self.tree = app_commands.CommandTree(self)

        async def setup_hook(self):
            guild = discord.Object(695868929154744360) # a bot testing server
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
        await interaction.response.send_message('******') # very explicit text!

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
            await interaction.response.send_message(f'hello i am {newname} now')

Commands with this check are still visible and invocable in the bot's direct messages,
regardless of the permissions specified.

To prevent this, :func:`~.app_commands.guild_only` can also be added.

.. warning::

    This can be overridden to a different set of permissions by server administrators through the "Integrations" tab on the official client,
    meaning, an invoking user might not actually have the permissions specified in the decorator.

.. _custom_checks:

Custom checks
--------------

A custom check is something that can be applied to a command to check if someone should be able to run it.

They're unique to the :ref:`officially supported checks <checks>` by Discord in that they're handled
entirely client-side.

In short, a check is an async function that takes in the :class:`~discord.Interaction` as its sole parameter.
It has the following options:

- Return a :obj:`True`-like to signal this check passes.

 - If a command has multiple checks, **all** of them need to pass in order for the invocation to continue.

- Raise a :class:`~.app_commands.AppCommandError`-derived exception to signal a person can't run the command.

 - Exceptions are passed to the bot's :ref:`error handlers <error_handling>`.

- Return a :obj:`False`-like to signal a person can't run the command.

 - :class:`~.app_commands.CheckFailure` will be raised instead.

To add a check, use the :func:`.app_commands.check` decorator:

.. code-block:: python

    import random

    async def predicate(interaction: discord.Interaction) -> bool:
        return random.randint(0, 1) == 1

    @client.tree.command()
    @app_commands.check(predicate)
    async def fiftyfifty(interaction: discord.Interaction):
        await interaction.response.send_message("you're lucky!")

Transforming the check into its own decorator for easier usage:

.. code-block:: python

    import random

    def coinflip():
        async def predicate(interaction: discord.Interaction) -> bool:
            return random.randint(0, 1) == 1
        return app_commands.check(predicate)

    @client.tree.command()
    @coinflip()
    async def fiftyfifty(interaction: discord.Interaction):
        await interaction.response.send_message("you're lucky!")

Checks are called sequentially and retain decorator order, bottom-to-top.

Take advantage of this order if, for example, you only want a cooldown to apply if a previous check passes:

.. code-block:: python

    @client.tree.command()
    @app_commands.checks.cooldown(1, 5.0) # called second
    @coinflip() # called first
    async def fiftyfifty(interaction: discord.Interaction):
        await interaction.response.send_message("you're very patient and lucky!")

Custom checks can either be:

- local, only running for a single command (as seen above).

- on a group, running for all child commands, and before any local checks.

 - Added using the :meth:`.app_commands.Group.error` decorator or overriding :meth:`.app_commands.Group.on_error`.

- :ref:`global <global_check>`, running for all commands, and before any group or local checks.

.. note::

    In the ``app_commands.checks`` namespace, there exists a lot of builtin checks
    to account for common use-cases, such as checking for roles or applying a cooldown.

    Refer to the :ref:`checks guide <guide_interaction_checks>` for more info.

.. _global_check:

Global check
+++++++++++++

To define a global check, override :meth:`.CommandTree.interaction_check` in a :class:`~.app_commands.CommandTree` subclass.
This method is called before every command invoke.

For example:

.. code-block:: python

    whitelist = {
        # cool people only
        236802254298939392,
        402159684724719617,
        155863164544614402
    }

    class CoolPeopleTree(app_commands.CommandTree):
        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id in whitelist

.. note::

    If your project uses :class:`.ext.commands.Bot` as the client instance,
    the :class:`.CommandTree` class can be configured via
    the ``tree_cls`` keyword argument in the bot constructor:

    .. code-block:: python

        from discord.ext import commands

        bot = commands.Bot(
            command_prefix='?',
            intents=discord.Intents.default(),
            tree_cls=CoolPeopleTree
        )

.. _error_handling:

Error handling
---------------

So far, any exceptions raised within a command callback, any custom checks, in a transformer
or during localisation, et cetera should just be logged in the program's :obj:`~sys.stderr` or through any custom logging handlers.

In order to catch exceptions and do something else, such as sending a message to let
a user know their invocation failed for some reason, the library uses something called error handlers.

There are 3 types of handlers:

1. A local handler, which only catches exceptions for a specific command

   Attached using the :meth:`.app_commands.Command.error` decorator.

2. A group handler, which catches exceptions only for a certain group's subcommands.

   Added by using the :meth:`.app_commands.Group.error` decorator or overriding :meth:`.app_commands.Group.on_error`.

3. A global handler, which catches all exceptions in all commands.

   Added by using the :meth:`.CommandTree.error` decorator or overriding :meth:`.CommandTree.on_error`.

If an exception is raised, the library calls **all 3** of these handlers in that order.

If a subcommand has multiple parents, the subcommand's parent handler is called first,
followed by its parent handler.

**Examples**

Attaching a local handler to a command to catch a check exception:

.. code-block:: python

    @app_commands.command()
    @app_commands.checks.has_any_role('v1.0 Alpha Tester', 'v2.0 Tester')
    async def tester(interaction: discord.Interaction):
        await interaction.response.send_message('thanks for testing')

    @tester.error
    async def tester_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingAnyRole):
            roles = ', '.join(str(r) for r in error.missing_roles)
            await interaction.response.send_message('i only thank people who have one of these roles!: {roles}')

Attaching an error handler to a group:

.. code-block:: python

    @my_group.error
    async def my_group_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        pass # im called for all subcommands and subgroups


    # or in a subclass:
    class MyGroup(app_commands.Group):
        async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
            pass

Adding a global error handler:

.. code-block:: python

    @client.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        pass # im called for all commands


    # alternatively, you can override `CommandTree.on_error`
    # when using commands.Bot, ensure you pass this class to the `tree_cls` kwarg in the bot constructor!

    class MyTree(app_commands.CommandTree):
        async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
            pass

.. warning::

    When overriding the global error handler, ensure you're at least catching any invocation errors (covered below)
    to make sure your bot isn't unexpectedly failing silently.

Invocation errors
++++++++++++++++++

When an exception that doesn't derive :class:`~.app_commands.AppCommandError` is raised in a command callback,
it's wrapped into :class:`~.app_commands.CommandInvokeError` before being sent to any error handlers.

Likewise:

- For transformers, exceptions that don't derive :class:`~.app_commands.AppCommandError` are wrapped in :class:`~.app_commands.TransformerError`.
- For translators, exceptions that don't derive :class:`~.app_commands.TranslationError` are wrapped into it.

This exception is helpful to differentiate between exceptions that the bot expects, such as those from a command check,
over exceptions like :class:`TypeError` or :class:`ValueError`, which tend to trace back to a programming mistake or API error.

To catch these exceptions in a global error handler for example:

.. code-block:: python

    import sys
    import traceback

    @client.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        assert interaction.command is not None

        if isinstance(error, app_commands.CommandInvokeError):
            print(f'Ignoring unknown exception in command {interaction.command.name}', file=sys.stderr)
            traceback.print_exception(error.__class__, error, error.__traceback__)

            # the original exception can be accessed using error.__cause__

Custom exceptions
++++++++++++++++++

When a command has multiple checks, it can be hard to know *which* check failed in an error handler,
since the default behaviour is to raise a blanket :class:`~.app_commands.CheckFailure` exception.

To solve this, inherit from the exception and raise it from the check instead of returning :obj:`False`:

.. code-block:: python

    import random

    class Unlucky(app_commands.CheckFailure):
        pass

    def coinflip():
        async def predicate(interaction: discord.Interaction) -> bool:
            if random.randint(0, 1) == 0:
                raise Unlucky("you're unlucky!")
            return True
        return app_commands.check(predicate)

    @client.tree.command()
    @coinflip()
    async def fiftyfifty(interaction: discord.Interaction):
        await interaction.response.send_message("you're lucky!")

    @fiftyfifty.error
    async def fiftyfifty_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, Unlucky):
            await interaction.response.send_message(str(error))

Transformers behave similarly, but should derive :class:`~.app_commands.AppCommandError` instead:

.. code-block:: python

    from discord.app_commands import Transform

    class BadDateArgument(app_commands.AppCommandError):
        def __init__(self, argument: str):
            super().__init__(f'expected a date in dd/mm/yyyy format, not "{argument}".')

    class DateTransformer(app_commands.Transformer):
        async def transform(self, interaction: discord.Interaction, value: str) -> datetime.datetime:
            try:
                when = datetime.datetime.strptime(date, '%d/%m/%Y')
            except ValueError:
                raise BadDateArgument(value)

            when = when.replace(tzinfo=datetime.timezone.utc)
            return when

    # pretend `some_command` is a command that uses this transformer

    @some_command.error
    async def some_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, BadDateArgument):
            await interaction.response.send_message(str(error))

Since a unique exception is used, extra state can be attached using :meth:`~object.__init__` for the error handler to work with.

One example of this is in the library with :attr:`.app_commands.MissingAnyRole.missing_roles`.

Logging
++++++++

Instead of printing plainly to :obj:`~sys.stderr`, the standard :mod:`logging` module can be configured instead -
which is what discord.py uses to write its own exceptions.

Whilst its a little bit more involved to set up, it has some added benefits such as using coloured text
in a terminal and being able to write to a file.

Refer to the :ref:`Setting Up logging <logging_setup>` page for more info and examples.

.. _translating:

Translating
------------

Discord supports localisation (l10n) for the following fields:

- Command names and descriptions
- Parameter names and descriptions
- Choice names (choices and autocomplete)

This allows the above fields to appear differently according to a user client's language setting.

Localisations can be done :ddocs:`partially <interactions/application-commands#localization>` -
when a locale doesn't have a translation for a given field, Discord will use the default/original string instead.

Support for l10n is implemented in discord.py with the :class:`.app_commands.Translator` interface,
which are effectively classes containing a core ``transform`` method that
takes the following parameters:

1. ``string`` - the string to be translated according to ``locale``
2. ``locale`` - the locale to translate to
3. ``context`` - the context of this translation (what type of string is being translated)

When :meth:`.CommandTree.sync` is called, this method is called in a heavy loop for each
string for each locale.

A wide variety of translation systems can be implemented using this interface, such as
:mod:`gettext` and `Project Fluent <https://projectfluent.org/>`_.

Only strings marked as ready for translation are passed to the method.
By default, every string is considered translatable and passed.

Nonetheless, to specify a translatable string explicitly,
simply pass a string wrapped in :class:`~.app_commands.locale_str` in places you'd usually use :class:`str`:

.. code-block:: python

    from discord.app_commands import locale_str as _

    @client.tree.command(name=_('example'), description=_('an example command'))
    async def example(interaction: discord.Interaction):
        ...

To toggle this behaviour, set the ``auto_locale_strings`` keyword-argument
to :obj:`False` when creating a command:

.. code-block:: python

    @client.tree.command(name='example', description='an example command', auto_locale_strings=False)
    async def example(interaction: discord.Interaction):
        ... # i am not translated

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

This contains 2 attributes:

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

Like a lot of other l10n systems, fluent uses directories and files to separate localisations.

A structure like this is used for this example:

.. code-block::

    discord_bot/
    ├── l10n/
    │   └── ja/
    │       └── commands.ftl
    └── bot.py

``commands.ftl`` is a translation resource described in fluent's `FTL <https://projectfluent.org/fluent/guide/>`_ format -
containing the Japanese (locale: ``ja``) localisations for a certain command in the bot:

.. code-block::

    # command metadata
    apple-command-name = リンゴ
    apple-command-description = ボットにリンゴを食べさせます。

    # parameters
    apple-command-amount = 食べさせるリンゴの数

    # responses from the command body
    apple-command-response = リンゴを{ $apple_count }個食べました。

Onto the translator:

.. code-block:: python

    from fluent.runtime import FluentLocalization, FluentResourceLoader

    class JapaneseTranslator(app_commands.Translator):
        def __init__(self):
            # load any resources when the translator initialises.
            # if asynchronous setup is needed, override `Translator.load()`!

            self.resources = FluentResourceLoader('./l10n/{locale}')
            self.mapping = {
                discord.Locale.japanese: FluentLocalization(['ja'], ['commands.ftl'], self.resources),
                # + additional locales as needed
            }

        async def translate(
            self,
            string: locale_str,
            locale: discord.Locale,
            context: app_commands.TranslationContext
        ):
            """core translate method called by the library"""

            fluent_id = string.extras.get('fluent_id')
            if not fluent_id:
                # ignore strings without an attached fluent_id
                return None

            l10n = self.mapping.get(locale)
            if not l10n:
                # no translation available for this locale
                return None

            # otherwise, a translation is assumed to exist and is returned
            return l10n.format_value(fluent_id)

        async def localise(
            self,
            string: locale_str,
            locale: discord.Locale,
            **params: Any
        ) -> str:
            """translates a given string for a locale, subsituting any required parameters.
            meant to be called for things outside what discord handles, eg. a message sent from the bot
            """

            l10n = self.mapping.get(locale)
            if not l10n:
                # return the string untouched
                return string.message

            # strings passed to this method need to include a fluent_id extra
            # since we are trying to explicitly localise a string
            fluent_id = string.extras['fluent_id']

            return l10n.format_value(fluent_id, params)

With the command, strings are only considered translatable if they have an
attached ``fluent_id`` extra:

.. code-block:: python

    @client.tree.command(
        name=_('apple', fluent_id='apple-command-name'),
        description=_('tell the bot to eat some apples', fluent_id='apple-command-description')
    )
    @app_commands.describe(amount=_('how many apples?', fluent_id='apple-command-amount'))
    async def apple(interaction: discord.Interaction, amount: int):
        translator = client.tree.translator

        # plurals for the bots native/default language (english) are handled here in the code.
        # fluent can handle plurals for secondary languages if needed.
        # see: https://projectfluent.org/fluent/guide/selectors.html

        plural = 'apple' if amount == 1 else 'apples'

        translated = await translator.localise(
            _(f'i ate {amount} {plural}', fluent_id='apple-command-response'),
            interaction.locale,
            apple_count=amount
        )

        await interaction.response.send_message(translated)

Viewing the command with an English (or any other) language setting:

.. image:: /images/guide/app_commands/apple_command_english.png
    :width: 300

A Japanese language setting shows the added localisations:

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
    bot = commands.Bot(command_prefix='?', intents=intents)

    @bot.command()
    @commands.is_owner()
    async def sync(ctx: commands.Context):
        synced = await bot.tree.sync()
        await ctx.reply(f'synced {len(synced)} global commands')

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
