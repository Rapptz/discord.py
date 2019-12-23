.. currentmodule:: discord

.. _ext_commands_commands:

Commands
==========

One of the most appealing aspect of the command extension is how easy it is to define commands and
how you can arbitrarily nest groups and commands to have a rich sub-command system.

Commands are defined by attaching it to a regular Python function. The command is then invoked by the user using a similar
signature to the Python function.

For example, in the given command definition:

.. code-block:: python3

    @bot.command()
    async def foo(ctx, arg):
        await ctx.send(arg)

With the following prefix (``$``), it would be invoked by the user via:

.. code-block:: none

    $foo abc

A command must always have at least one parameter, ``ctx``, which is the :class:`.Context` as the first one.

There are two ways of registering a command. The first one is by using :meth:`.Bot.command` decorator,
as seen in the example above. The second is using the :func:`~ext.commands.command` decorator followed by
:meth:`.Bot.add_command` on the instance.

Essentially, these two are equivalent: ::

    from discord.ext import commands

    bot = commands.Bot(command_prefix='$')

    @bot.command()
    async def test(ctx):
        pass

    # or:

    @commands.command()
    async def test(ctx):
        pass

    bot.add_command(test)

Since the :meth:`.Bot.command` decorator is shorter and easier to comprehend, it will be the one used throughout the
documentation here.

Any parameter that is accepted by the :class:`.Command` constructor can be passed into the decorator. For example, to change
the name to something other than the function would be as simple as doing this:

.. code-block:: python3

    @bot.command(name='list')
    async def _list(ctx, arg):
        pass

Parameters
------------

Since we define commands by making Python functions, we also define the argument passing behaviour by the function
parameters.

Certain parameter types do different things in the user side and most forms of parameter types are supported.

Positional
++++++++++++

The most basic form of parameter passing is the positional parameter. This is where we pass a parameter as-is:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg):
        await ctx.send(arg)


On the bot using side, you can provide positional arguments by just passing a regular string:

.. image:: /images/commands/positional1.png

To make use of a word with spaces in between, you should quote it:

.. image:: /images/commands/positional2.png

As a note of warning, if you omit the quotes, you will only get the first word:

.. image:: /images/commands/positional3.png

Since positional arguments are just regular Python arguments, you can have as many as you want:

.. code-block:: python3

    @bot.command()
    async def test(ctx, arg1, arg2):
        await ctx.send('You passed {} and {}'.format(arg1, arg2))

Variable
++++++++++

Sometimes you want users to pass in an undetermined number of parameters. The library supports this
similar to how variable list parameters are done in Python:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *args):
        await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

This allows our user to accept either one or many arguments as they please. This works similar to positional arguments,
so multi-word parameters should be quoted.

For example, on the bot side:

.. image:: /images/commands/variable1.png

If the user wants to input a multi-word argument, they have to quote it like earlier:

.. image:: /images/commands/variable2.png

Do note that similar to the Python function behaviour, a user can technically pass no arguments
at all:

.. image:: /images/commands/variable3.png

Since the ``args`` variable is a :class:`py:tuple`,
you can do anything you would usually do with one.

Keyword-Only Arguments
++++++++++++++++++++++++

When you want to handle parsing of the argument yourself or do not feel like you want to wrap multi-word user input into
quotes, you can ask the library to give you the rest as a single argument. We do this by using a **keyword-only argument**,
seen below:

.. code-block:: python3

    @bot.command()
    async def test(ctx, *, arg):
        await ctx.send(arg)

.. warning::

    You can only have one keyword-only argument due to parsing ambiguities.

On the bot side, we do not need to quote input with spaces:

.. image:: /images/commands/keyword1.png

Do keep in mind that wrapping it in quotes leaves it as-is:

.. image:: /images/commands/keyword2.png

By default, the keyword-only arguments are stripped of white space to make it easier to work with. This behaviour can be
toggled by the :attr:`.Command.rest_is_raw` argument in the decorator.

.. _ext_commands_context:

Invocation Context
-------------------

As seen earlier, every command must take at least a single parameter, called the :class:`~ext.commands.Context`.

This parameter gives you access to something called the "invocation context". Essentially all the information you need to
know how the command was executed. It contains a lot of useful information:

- :attr:`.Context.guild` to fetch the :class:`Guild` of the command, if any.
- :attr:`.Context.message` to fetch the :class:`Message` of the command.
- :attr:`.Context.author` to fetch the :class:`Member` or :class:`User` that called the command.
- :meth:`.Context.send` to send a message to the channel the command was used in.

The context implements the :class:`abc.Messageable` interface, so anything you can do on a :class:`abc.Messageable` you
can do on the :class:`~ext.commands.Context`.

Converters
------------

Adding bot arguments with function parameters is only the first step in defining your bot's command interface. To actually
make use of the arguments, we usually want to convert the data into a target type. We call these
:ref:`ext_commands_api_converters`.

Converters come in a few flavours:

- A regular callable object that takes an argument as a sole parameter and returns a different type.

    - These range from your own function, to something like :class:`bool` or :class:`int`.

- A custom class that inherits from :class:`~ext.commands.Converter`.

Basic Converters
++++++++++++++++++

At its core, a basic converter is a callable that takes in an argument and turns it into something else.

For example, if we wanted to add two numbers together, we could request that they are turned into integers
for us by specifying the converter:

.. code-block:: python3

    @bot.command()
    async def add(ctx, a: int, b: int):
        await ctx.send(a + b)

We specify converters by using something called a **function annotation**. This is a Python 3 exclusive feature that was
introduced in :pep:`3107`.

This works with any callable, such as a function that would convert a string to all upper-case:

.. code-block:: python3

    def to_upper(argument):
        return argument.upper()

    @bot.command()
    async def up(ctx, *, content: to_upper):
        await ctx.send(content)

bool
^^^^^^

Unlike the other basic converters, the :class:`bool` converter is treated slightly different. Instead of casting directly to the :class:`bool` type, which would result in any non-empty argument returning ``True``, it instead evaluates the argument as ``True`` or ``False`` based on its given content:

.. code-block:: python3

    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False

.. _ext_commands_adv_converters:

Advanced Converters
+++++++++++++++++++++

Sometimes a basic converter doesn't have enough information that we need. For example, sometimes we want to get some
information from the :class:`Message` that called the command or we want to do some asynchronous processing.

For this, the library provides the :class:`~ext.commands.Converter` interface. This allows you to have access to the
:class:`.Context` and have the callable be asynchronous. Defining a custom converter using this interface requires
overriding a single method, :meth:`.Converter.convert`.

An example converter:

.. code-block:: python3

    import random

    class Slapper(commands.Converter):
        async def convert(self, ctx, argument):
            to_slap = random.choice(ctx.guild.members)
            return '{0.author} slapped {1} because *{2}*'.format(ctx, to_slap, argument)

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

The converter provided can either be constructed or not. Essentially these two are equivalent:

.. code-block:: python3

    @bot.command()
    async def slap(ctx, *, reason: Slapper):
        await ctx.send(reason)

    # is the same as...

    @bot.command()
    async def slap(ctx, *, reason: Slapper()):
        await ctx.send(reason)

Having the possibility of the converter be constructed allows you to set up some state in the converter's ``__init__`` for
fine tuning the converter. An example of this is actually in the library, :class:`~ext.commands.clean_content`.

.. code-block:: python3

    @bot.command()
    async def clean(ctx, *, content: commands.clean_content):
        await ctx.send(content)

    # or for fine-tuning

    @bot.command()
    async def clean(ctx, *, content: commands.clean_content(use_nicknames=False)):
        await ctx.send(content)


If a converter fails to convert an argument to its designated target type, the :exc:`.BadArgument` exception must be
raised.

Inline Advanced Converters
+++++++++++++++++++++++++++++

If we don't want to inherit from :class:`~ext.commands.Converter`, we can still provide a converter that has the
advanced functionalities of an advanced converter and save us from specifying two types.

For example, a common idiom would be to have a class and a converter for that class:

.. code-block:: python3

    class JoinDistance:
        def __init__(self, joined, created):
            self.joined = joined
            self.created = created

        @property
        def delta(self):
            return self.joined - self.created

    class JoinDistanceConverter(commands.MemberConverter):
        async def convert(self, ctx, argument):
            member = await super().convert(ctx, argument)
            return JoinDistance(member.joined_at, member.created_at)

    @bot.command()
    async def delta(ctx, *, member: JoinDistanceConverter):
        is_new = member.delta.days < 100
        if is_new:
            await ctx.send("Hey you're pretty new!")
        else:
            await ctx.send("Hm you're not so new.")

This can get tedious, so an inline advanced converter is possible through a ``classmethod`` inside the type:

.. code-block:: python3

    class JoinDistance:
        def __init__(self, joined, created):
            self.joined = joined
            self.created = created

        @classmethod
        async def convert(cls, ctx, argument):
            member = await commands.MemberConverter().convert(ctx, argument)
            return cls(member.joined_at, member.created_at)

        @property
        def delta(self):
            return self.joined - self.created

    @bot.command()
    async def delta(ctx, *, member: JoinDistance):
        is_new = member.delta.days < 100
        if is_new:
            await ctx.send("Hey you're pretty new!")
        else:
            await ctx.send("Hm you're not so new.")

Discord Converters
++++++++++++++++++++

Working with :ref:`discord_api_models` is a fairly common thing when defining commands, as a result the library makes
working with them easy.

For example, to receive a :class:`Member` you can just pass it as a converter:

.. code-block:: python3

    @bot.command()
    async def joined(ctx, *, member: discord.Member):
        await ctx.send('{0} joined on {0.joined_at}'.format(member))

When this command is executed, it attempts to convert the string given into a :class:`Member` and then passes it as a
parameter for the function. This works by checking if the string is a mention, an ID, a nickname, a username + discriminator,
or just a regular username. The default set of converters have been written to be as easy to use as possible.

A lot of discord models work out of the gate as a parameter:

- :class:`Member`
- :class:`User`
- :class:`TextChannel`
- :class:`VoiceChannel`
- :class:`CategoryChannel`
- :class:`Role`
- :class:`Message` (since v1.1)
- :class:`Invite`
- :class:`Game`
- :class:`Emoji`
- :class:`PartialEmoji`
- :class:`Colour`

Having any of these set as the converter will intelligently convert the argument to the appropriate target type you
specify.

Under the hood, these are implemented by the :ref:`ext_commands_adv_converters` interface. A table of the equivalent
converter is given below:

+--------------------------+-------------------------------------------------+
|     Discord Class        |                    Converter                    |
+--------------------------+-------------------------------------------------+
| :class:`Member`          | :class:`~ext.commands.MemberConverter`          |
+--------------------------+-------------------------------------------------+
| :class:`Message`         | :class:`~ext.commands.MessageConverter`         |
+--------------------------+-------------------------------------------------+
| :class:`User`            | :class:`~ext.commands.UserConverter`            |
+--------------------------+-------------------------------------------------+
| :class:`TextChannel`     | :class:`~ext.commands.TextChannelConverter`     |
+--------------------------+-------------------------------------------------+
| :class:`VoiceChannel`    | :class:`~ext.commands.VoiceChannelConverter`    |
+--------------------------+-------------------------------------------------+
| :class:`CategoryChannel` | :class:`~ext.commands.CategoryChannelConverter` |
+--------------------------+-------------------------------------------------+
| :class:`Role`            | :class:`~ext.commands.RoleConverter`            |
+--------------------------+-------------------------------------------------+
| :class:`Invite`          | :class:`~ext.commands.InviteConverter`          |
+--------------------------+-------------------------------------------------+
| :class:`Game`            | :class:`~ext.commands.GameConverter`            |
+--------------------------+-------------------------------------------------+
| :class:`Emoji`           | :class:`~ext.commands.EmojiConverter`           |
+--------------------------+-------------------------------------------------+
| :class:`PartialEmoji`    | :class:`~ext.commands.PartialEmojiConverter`    |
+--------------------------+-------------------------------------------------+
| :class:`Colour`          | :class:`~ext.commands.ColourConverter`          |
+--------------------------+-------------------------------------------------+

By providing the converter it allows us to use them as building blocks for another converter:

.. code-block:: python3

    class MemberRoles(commands.MemberConverter):
        async def convert(self, ctx, argument):
            member = await super().convert(ctx, argument)
            return [role.name for role in member.roles[1:]] # Remove everyone role!

    @bot.command()
    async def roles(ctx, *, member: MemberRoles):
        """Tells you a member's roles."""
        await ctx.send('I see the following roles: ' + ', '.join(member))

.. _ext_commands_special_converters:

Special Converters
++++++++++++++++++++

The command extension also has support for certain converters to allow for more advanced and intricate use cases that go
beyond the generic linear parsing. These converters allow you to introduce some more relaxed and dynamic grammar to your
commands in an easy to use manner.

typing.Union
^^^^^^^^^^^^^^

A :data:`typing.Union` is a special type hint that allows for the command to take in any of the specific types instead of
a singular type. For example, given the following:

.. code-block:: python3

    import typing

    @bot.command()
    async def union(ctx, what: typing.Union[discord.TextChannel, discord.Member]):
        await ctx.send(what)


The ``what`` parameter would either take a :class:`discord.TextChannel` converter or a :class:`discord.Member` converter.
The way this works is through a left-to-right order. It first attempts to convert the input to a
:class:`discord.TextChannel`, and if it fails it tries to convert it to a :class:`discord.Member`. If all converters fail,
then a special error is raised, :exc:`~ext.commands.BadUnionArgument`.

Note that any valid converter discussed above can be passed in to the argument list of a :data:`typing.Union`.

typing.Optional
^^^^^^^^^^^^^^^^^

A :data:`typing.Optional` is a special type hint that allows for "back-referencing" behaviour. If the converter fails to
parse into the specified type, the parser will skip the parameter and then either ``None`` or the specified default will be
passed into the parameter instead. The parser will then continue on to the next parameters and converters, if any.

Consider the following example:

.. code-block:: python3

    import typing

    @bot.command()
    async def bottles(ctx, amount: typing.Optional[int] = 99, *, liquid="beer"):
        await ctx.send('{} bottles of {} on the wall!'.format(amount, liquid))


.. image:: /images/commands/optional1.png

In this example, since the argument could not be converted into an ``int``, the default of ``99`` is passed and the parser
resumes handling, which in this case would be to pass it into the ``liquid`` parameter.

.. note::

    This converter only works in regular positional parameters, not variable parameters or keyword-only parameters.

Greedy
^^^^^^^^

The :data:`~ext.commands.Greedy` converter is a generalisation of the :data:`typing.Optional` converter, except applied
to a list of arguments. In simple terms, this means that it tries to convert as much as it can until it can't convert
any further.

Consider the following example:

.. code-block:: python3

    @bot.command()
    async def slap(ctx, members: commands.Greedy[discord.Member], *, reason='no reason'):
        slapped = ", ".join(x.name for x in members)
        await ctx.send('{} just got slapped for {}'.format(slapped, reason))

When invoked, it allows for any number of members to be passed in:

.. image:: /images/commands/greedy1.png

The type passed when using this converter depends on the parameter type that it is being attached to:

- Positional parameter types will receive either the default parameter or a :class:`list` of the converted values.
- Variable parameter types will be a :class:`tuple` as usual.
- Keyword-only parameter types will be the same as if :data:`~ext.commands.Greedy` was not passed at all.

:data:`~ext.commands.Greedy` parameters can also be made optional by specifying an optional value.

When mixed with the :data:`typing.Optional` converter you can provide simple and expressive command invocation syntaxes:

.. code-block:: python3

    import typing

    @bot.command()
    async def ban(ctx, members: commands.Greedy[discord.Member],
                       delete_days: typing.Optional[int] = 0, *,
                       reason: str):
        """Mass bans members with an optional delete_days parameter"""
        for member in members:
            await member.ban(delete_message_days=delete_days, reason=reason)


This command can be invoked any of the following ways:

.. code-block:: none

    $ban @Member @Member2 spam bot
    $ban @Member @Member2 7 spam bot
    $ban @Member spam

.. warning::

    The usage of :data:`~ext.commands.Greedy` and :data:`typing.Optional` are powerful and useful, however as a
    price, they open you up to some parsing ambiguities that might surprise some people.

    For example, a signature expecting a :data:`typing.Optional` of a :class:`discord.Member` followed by a
    :class:`int` could catch a member named after a number due to the different ways a
    :class:`~ext.commands.MemberConverter` decides to fetch members. You should take care to not introduce
    unintended parsing ambiguities in your code. One technique would be to clamp down the expected syntaxes
    allowed through custom converters or reordering the parameters to minimise clashes.

    To help aid with some parsing ambiguities, :class:`str`, ``None`` and :data:`~ext.commands.Greedy` are
    forbidden as parameters for the :data:`~ext.commands.Greedy` converter.

.. _ext_commands_error_handler:

Error Handling
----------------

When our commands fail to parse we will, by default, receive a noisy error in ``stderr`` of our console that tells us
that an error has happened and has been silently ignored.

In order to handle our errors, we must use something called an error handler. There is a global error handler, called
:func:`on_command_error` which works like any other event in the :ref:`discord-api-events`. This global error handler is
called for every error reached.

Most of the time however, we want to handle an error local to the command itself. Luckily, commands come with local error
handlers that allow us to do just that. First we decorate an error handler function with :meth:`.Command.error`:

.. code-block:: python3

    @bot.command()
    async def info(ctx, *, member: discord.Member):
        """Tells you some info about the member."""
        fmt = '{0} joined on {0.joined_at} and has {1} roles.'
        await ctx.send(fmt.format(member, len(member.roles)))

    @info.error
    async def info_error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('I could not find that member...')

The first parameter of the error handler is the :class:`.Context` while the second one is an exception that is derived from
:exc:`~ext.commands.CommandError`. A list of errors is found in the :ref:`ext_commands_api_errors` page of the documentation.

Checks
-------

There are cases when we don't want a user to use our commands. They don't have permissions to do so or maybe we blocked
them from using our bot earlier. The commands extension comes with full support for these things in a concept called a
:ref:`ext_commands_api_checks`.

A check is a basic predicate that can take in a :class:`.Context` as its sole parameter. Within it, you have the following
options:

- Return ``True`` to signal that the person can run the command.
- Return ``False`` to signal that the person cannot run the command.
- Raise a :exc:`~ext.commands.CommandError` derived exception to signal the person cannot run the command.

    - This allows you to have custom error messages for you to handle in the
      :ref:`error handlers <ext_commands_error_handler>`.

To register a check for a command, we would have two ways of doing so. The first is using the :meth:`~ext.commands.check`
decorator. For example:

.. code-block:: python3

    async def is_owner(ctx):
        return ctx.author.id == 316026178463072268

    @bot.command(name='eval')
    @commands.check(is_owner)
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

This would only evaluate the command if the function ``is_owner`` returns ``True``. Sometimes we re-use a check often and
want to split it into its own decorator. To do that we can just add another level of depth:

.. code-block:: python3

    def is_owner():
        async def predicate(ctx):
            return ctx.author.id == 316026178463072268
        return commands.check(predicate)

    @bot.command(name='eval')
    @is_owner()
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))


Since an owner check is so common, the library provides it for you (:func:`~ext.commands.is_owner`):

.. code-block:: python3

    @bot.command(name='eval')
    @commands.is_owner()
    async def _eval(ctx, *, code):
        """A bad example of an eval command"""
        await ctx.send(eval(code))

When multiple checks are specified, **all** of them must be ``True``:

.. code-block:: python3

    def is_in_guild(guild_id):
        async def predicate(ctx):
            return ctx.guild and ctx.guild.id == guild_id
        return commands.check(predicate)

    @bot.command()
    @commands.is_owner()
    @is_in_guild(41771983423143937)
    async def secretguilddata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

If any of those checks fail in the example above, then the command will not be run.

When an error happens, the error is propagated to the :ref:`error handlers <ext_commands_error_handler>`. If you do not
raise a custom :exc:`~ext.commands.CommandError` derived exception, then it will get wrapped up into a
:exc:`~ext.commands.CheckFailure` exception as so:

.. code-block:: python3

    @bot.command()
    @commands.is_owner()
    @is_in_guild(41771983423143937)
    async def secretguilddata(ctx):
        """super secret stuff"""
        await ctx.send('secret stuff')

    @secretguilddata.error
    async def secretguilddata_error(ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('nothing to see here comrade.')

If you want a more robust error system, you can derive from the exception and raise it instead of returning ``False``:

.. code-block:: python3

    class NoPrivateMessages(commands.CheckFailure):
        pass

    def guild_only():
        async def predicate(ctx):
            if ctx.guild is None:
                raise NoPrivateMessages('Hey no DMs!')
            return True
        return commands.check(predicate)

    @guild_only()
    async def test(ctx):
        await ctx.send('Hey this is not a DM! Nice.')

    @test.error
    async def test_error(ctx, error):
        if isinstance(error, NoPrivateMessages):
            await ctx.send(error)

.. note::

    Since having a ``guild_only`` decorator is pretty common, it comes built-in via :func:`~ext.commands.guild_only`.

Global Checks
++++++++++++++

Sometimes we want to apply a check to **every** command, not just certain commands. The library supports this as well
using the global check concept.

Global checks work similarly to regular checks except they are registered with the :func:`.Bot.check` decorator.

For example, to block all DMs we could do the following:

.. code-block:: python3

    @bot.check
    async def globally_block_dms(ctx):
        return ctx.guild is not None

.. warning::

    Be careful on how you write your global checks, as it could also lock you out of your own bot.

.. need a note on global check once here I think
