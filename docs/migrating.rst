.. currentmodule:: discord

.. _migrating:

Migrating to this library
==========================

| This library is designed to be compatible with discord.py.
| However, the user and bot APIs are *not* the same.

Most things bots can do, users can (in some capacity) as well.

However, a number of things have been removed.
For example:

- `Intents`: While the gateway technically accepts Intents for user accounts (and even modifies payloads to be a little more like bot payloads), it leads to breakage. Additionally, it's a giant waving red flag to Discord.
- `Shards`: The concept doesn't exist and is unneeded for users.
- `Guild.fetch_members`: The `/guilds/:id/members` and `/guilds/:id/members/search` endpoints instantly phone-lock your account. For more information about guild members, please read their respective section below.

Additionally, existing payloads and headers have been heavily changed to match the Discord client.

Guild members
--------------
| Since the concept of Intents (mostly) doesn't exist for user accounts; you just get all events, right?
| Well, yes but actually no.

For 80% of things, events are identical to bot events. However, other than the quite large amount of new events, not all events work the same.

The biggest example of this are the events `on_member_add`, `on_member_update`/`on_user_update`, and `on_member_remove`.

Bots
~~~~~
For bots (with the member intent), it's simple.

They request all guild members with an OPCode 8 (chunk the guild), and receive respective `GUILD_MEMBER_*` events, that are then parsed by the library and dispatched to users.

If the bot has the presence intent, it even gets an initial member cache in the `GUILD_CREATE` event.

Users
~~~~~~
| Users, however, do not work like this.
| If you have one of kick members, ban members, or manage roles, you can request all guild members the same way bots do. The client uses this in various areas of guild settings.

| But, here's the twist: users do not receive `GUILD_MEMBER_*` reliably.
| They receive them in certain circumstances, but they're usually rare and nothing to be relied on.

If the Discord client ever needs member objects for specific users, it sends an OPCode 8 with the specific user IDs/names.
This is why this is recommended if you want to fetch specific members (implemented as :func:`Guild.query_members` in the library).
The client almost never uses the :func:`Guild.fetch_member` endpoint.

However, the maximum amount of members you can get with this method is 100 per request.

But, you may be thinking, how does the member list work? Why can't you just utilize that? This is where it gets complicated.
First, let's make sure we understand a few things:

- The API doesn't differentiate between offline and invisible members (for a good reason).
- The concept of a member list is not per-guild, it's per-channel. This makes sense if you think about it, since the member list only shows users that have access to a specific channel.
- The member list is always up-to-date.
- If a server has >1k members, the member list does **not** have offline members.

The member list uses OPCode 14, and the `GUILD_MEMBER_LIST_UPDATE` event.

One more thing you need to understand, is that the member list is lazily loaded.
You subscribe to 100 member ranges, and can subscribe to 2 per-request (needs more testing).
So, to subscribe to all available ranges, you need to spam the gateway quite a bit (especially for large guilds).

| Once you subscribe to a range, you'll receive `GUILD_MEMBER_LIST_UPDATE` s for it whenever someone is added to it (i.e. someone joined the guild, changed their nickname so they moved in the member list alphabetically, came online, etc.), removed from it (i.e. someone left the guild, went offline, changed their nickname so they moved in the member list alphabetically), or updated in it (i.e. someone got their roles changed, or changed their nickname but remained in the same range).
| These can be parsed and dispatched as `on_member_add`, `on_member_update`/`on_user_update`, and `on_member_remove`.

You may have already noticed a few problems with this:

1. You'll get spammed with `member_add/remove` s whenever someone changes ranges.
2. For guilds with >1k members you don't receive offline members. So, you won't know if an offline member is kicked, or an invisible member joins/leaves. You also won't know if someone came online or joined. Or, if someone went offline or left.

| #1 is solveable with a bit of parsing, but #2 is a huge problem.
| If you have the permissions to request all guild members, you can combine that with member list scraping and get a *decent* local member cache. However, because of the nature of this (and the fact that you'll have to request all guild membesr again every so often), accurate events are nearly impossible.

Additionally, there are more caveats:

1. `GUILD_MEMBER_LIST_UPDATE` removes provide an index, not a user ID. The index starts at 0 from the top of the member list and includes hoisted roles.
2. For large servers, you get ratelimited pretty fast, so scraping can take over half an hour.
3. The scraping has to happen every time the bot starts. This not only slows things down, but *may* make Discord suspicious.
4. Remember that member lists are per-channel? Well, that means you can only subscribe all members that can *see* the channel you're subscribing too.

#1 is again solveable with a bit of parsing. There's not much you can do about #2 and #3. But, to solve #4, you *can* subscribe to multiple channels. Although, that will probably have problems of its own.

There are a few more pieces of the puzzle:

<<<<<<< HEAD
    async def on_member_ban(member)

After: ::

    async def on_member_ban(guild, user)

As part of the change, the event can either receive a :class:`User` or :class:`Member`. To help in the cases that have
:class:`User`, the :class:`Guild` is provided as the first parameter.

The ``on_channel_`` events have received a type level split (see :ref:`migrating_1_0_channel_split`).

Before:

- ``on_channel_delete``
- ``on_channel_create``
- ``on_channel_update``

After:

- :func:`on_guild_channel_delete`
- :func:`on_guild_channel_create`
- :func:`on_guild_channel_update`
- :func:`on_private_channel_delete`
- :func:`on_private_channel_create`
- :func:`on_private_channel_update`

The ``on_guild_channel_`` events correspond to :class:`abc.GuildChannel` being updated (i.e. :class:`TextChannel`
and :class:`VoiceChannel`) and the ``on_private_channel_`` events correspond to :class:`abc.PrivateChannel` being
updated (i.e. :class:`DMChannel` and :class:`GroupChannel`).

.. _migrating_1_0_voice:

Voice Changes
---------------

Voice sending has gone through a complete redesign.

In particular:

- Connection is done through :meth:`VoiceChannel.connect` instead of ``Client.join_voice_channel``.
- You no longer create players and operate on them (you no longer store them).
- You instead request :class:`VoiceClient` to play an :class:`AudioSource` via :meth:`VoiceClient.play`.
- There are different built-in :class:`AudioSource`\s.

  - :class:`FFmpegPCMAudio` is the equivalent of ``create_ffmpeg_player``

- create_ffmpeg_player/create_stream_player/create_ytdl_player have all been removed.

  - The goal is to create :class:`AudioSource` instead.

- Using :meth:`VoiceClient.play` will not return an ``AudioPlayer``.

  - Instead, it's "flattened" like :class:`User` -> :class:`Member` is.

- The ``after`` parameter now takes a single parameter (the error).

Basically:

Before: ::

    vc = await client.join_voice_channel(channel)
    player = vc.create_ffmpeg_player('testing.mp3', after=lambda: print('done'))
    player.start()

    player.is_playing()
    player.pause()
    player.resume()
    player.stop()
    # ...

After: ::

    vc = await channel.connect()
    vc.play(discord.FFmpegPCMAudio('testing.mp3'), after=lambda e: print('done', e))
    vc.is_playing()
    vc.pause()
    vc.resume()
    vc.stop()
    # ...

With the changed :class:`AudioSource` design, you can now change the source that the :class:`VoiceClient` is
playing at runtime via :attr:`VoiceClient.source`.

For example, you can add a :class:`PCMVolumeTransformer` to allow changing the volume: ::

    vc.source = discord.PCMVolumeTransformer(vc.source)
    vc.source.volume = 0.6

An added benefit of the redesign is that it will be much more resilient towards reconnections:

- The voice websocket will now automatically re-connect and re-do the handshake when disconnected.
- The initial connect handshake will now retry up to 5 times so you no longer get as many ``asyncio.TimeoutError``.
- Audio will now stop and resume when a disconnect is found.

  - This includes changing voice regions etc.


.. _migrating_1_0_wait_for:

Waiting For Events
--------------------

Prior to v1.0, the machinery for waiting for an event outside of the event itself was done through two different
functions, ``Client.wait_for_message`` and ``Client.wait_for_reaction``. One problem with one such approach is that it did
not allow you to wait for events outside of the ones provided by the library.

In v1.0 the concept of waiting for another event has been generalised to work with any event as :meth:`Client.wait_for`.

For example, to wait for a message: ::

    # before
    msg = await client.wait_for_message(author=message.author, channel=message.channel)

    # after
    def pred(m):
        return m.author == message.author and m.channel == message.channel

    msg = await client.wait_for('message', check=pred)

To facilitate multiple returns, :meth:`Client.wait_for` returns either a single argument, no arguments, or a tuple of
arguments.

For example, to wait for a reaction: ::

    reaction, user = await client.wait_for('reaction_add', check=lambda r, u: u.id == 176995180300206080)

    # use user and reaction

Since this function now can return multiple arguments, the ``timeout`` parameter will now raise a :exc:`asyncio.TimeoutError`
when reached instead of setting the return to ``None``. For example:

.. code-block:: python3

    def pred(m):
        return m.author == message.author and m.channel == message.channel

    try:

        msg = await client.wait_for('message', check=pred, timeout=60.0)
    except asyncio.TimeoutError:
        await channel.send('You took too long...')
    else:
        await channel.send('You said {0.content}, {0.author}.'.format(msg))

Upgraded Dependencies
-----------------------

Following v1.0 of the library, we've updated our requirements to :doc:`aiohttp <aio:index>` v2.0 or higher.

Since this is a backwards incompatible change, it is recommended that you see the
`changes <http://aiohttp.readthedocs.io/en/stable/changes.html#rc1-2017-03-15>`_
and the :doc:`aio:migration_to_2xx` pages for details on the breaking changes in
:doc:`aiohttp <aio:index>`.

Of the most significant for common users is the removal of helper functions such as:

- ``aiohttp.get``
- ``aiohttp.post``
- ``aiohttp.delete``
- ``aiohttp.patch``
- ``aiohttp.head``
- ``aiohttp.put``
- ``aiohttp.request``

It is recommended that you create a session instead: ::

    async with aiohttp.ClientSession() as sess:
        async with sess.get('url') as resp:
            # work with resp

Since it is better to not create a session for every request, you should store it in a variable and then call
``session.close`` on it when it needs to be disposed.

Sharding
----------

The library has received significant changes on how it handles sharding and now has sharding as a first-class citizen.

If using a Bot account and you want to shard your bot in a single process then you can use the :class:`AutoShardedClient`.

This class allows you to use sharding without having to launch multiple processes or deal with complicated IPC.

It should be noted that **the sharded client does not support user accounts**. This is due to the changes in connection
logic and state handling.

Usage is as simple as doing: ::

    client = discord.AutoShardedClient()

instead of using :class:`Client`.

This will launch as many shards as your bot needs using the ``/gateway/bot`` endpoint, which allocates about 1000 guilds
per shard.

If you want more control over the sharding you can specify ``shard_count`` and ``shard_ids``. ::

    # launch 10 shards regardless
    client = discord.AutoShardedClient(shard_count=10)

    # launch specific shard IDs in this process
    client = discord.AutoShardedClient(shard_count=10, shard_ids=(1, 2, 5, 6))

For users of the command extension, there is also :class:`~ext.commands.AutoShardedBot` which behaves similarly.

Connection Improvements
-------------------------

In v1.0, the auto reconnection logic has been powered up significantly.

:meth:`Client.connect` has gained a new keyword argument, ``reconnect`` that defaults to ``True`` which controls
the reconnect logic. When enabled, the client will automatically reconnect in all instances of your internet going
offline or Discord going offline with exponential back-off.

:meth:`Client.run` and :meth:`Client.start` gains this keyword argument as well, but for most cases you will not
need to specify it unless turning it off.

.. _migrating_1_0_commands:

Command Extension Changes
--------------------------

Due to the :ref:`migrating_1_0_model_state` changes, some of the design of the extension module had to
undergo some design changes as well.

Context Changes
~~~~~~~~~~~~~~~~~

In v1.0, the :class:`.Context` has received a lot of changes with how it's retrieved and used.

The biggest change is that ``pass_context=True`` no longer exists, :class:`.Context` is always passed. Ergo:

.. code-block:: python3

    # before
    @bot.command()
    async def foo():
        await bot.say('Hello')

    # after
    @bot.command()
    async def foo(ctx):
        await ctx.send('Hello')

The reason for this is because :class:`~ext.commands.Context` now meets the requirements of :class:`abc.Messageable`. This
makes it have similar functionality to :class:`TextChannel` or :class:`DMChannel`. Using :meth:`~.Context.send`
will either DM the user in a DM context or send a message in the channel it was in, similar to the old ``bot.say``
functionality. The old helpers have been removed in favour of the new :class:`abc.Messageable` interface. See
:ref:`migrating_1_0_removed_helpers` for more information.

Since the :class:`~ext.commands.Context` is now passed by default, several shortcuts have been added:

**New Shortcuts**

- :attr:`ctx.author <ext.commands.Context.author>` is a shortcut for ``ctx.message.author``.
- :attr:`ctx.guild <ext.commands.Context.guild>` is a shortcut for ``ctx.message.guild``.
- :attr:`ctx.channel <ext.commands.Context.channel>` is a shortcut for ``ctx.message.channel``.
- :attr:`ctx.me <ext.commands.Context.me>` is a shortcut for ``ctx.message.guild.me`` or ``ctx.bot.user``.
- :attr:`ctx.voice_client <ext.commands.Context.voice_client>` is a shortcut for ``ctx.message.guild.voice_client``.

**New Functionality**

- :meth:`.Context.reinvoke` to invoke a command again.

    - This is useful for bypassing cooldowns.
- :attr:`.Context.valid` to check if a context can be invoked with :meth:`.Bot.invoke`.
- :meth:`.Context.send_help` to show the help command for an entity using the new :class:`~.ext.commands.HelpCommand` system.

    - This is useful if you want to show the user help if they misused a command.

Subclassing Context
++++++++++++++++++++

In v1.0, there is now the ability to subclass :class:`~ext.commands.Context` and use it instead of the default
provided one.

For example, if you want to add some functionality to the context:

.. code-block:: python3

    class MyContext(commands.Context):
        @property
        def secret(self):
            return 'my secret here'

Then you can use :meth:`~ext.commands.Bot.get_context` inside :func:`on_message` with combination with
:meth:`~ext.commands.Bot.invoke` to use your custom context:

.. code-block:: python3

    class MyBot(commands.Bot):
        async def on_message(self, message):
            ctx = await self.get_context(message, cls=MyContext)
            await self.invoke(ctx)

Now inside your commands you will have access to your custom context:

.. code-block:: python3

    @bot.command()
    async def secret(ctx):
        await ctx.send(ctx.secret)

.. _migrating_1_0_removed_helpers:

Removed Helpers
+++++++++++++++++

With the new :class:`.Context` changes, a lot of message sending helpers have been removed.

For a full list of changes, see below:

+-----------------+------------------------------------------------------------+
|      Before     |                           After                            |
+-----------------+------------------------------------------------------------+
| ``Bot.say``     | :meth:`.Context.send`                                      |
+-----------------+------------------------------------------------------------+
| ``Bot.upload``  | :meth:`.Context.send`                                      |
+-----------------+------------------------------------------------------------+
| ``Bot.whisper`` | ``ctx.author.send``                                        |
+-----------------+------------------------------------------------------------+
| ``Bot.type``    | :meth:`.Context.typing` or :meth:`.Context.trigger_typing` |
+-----------------+------------------------------------------------------------+
| ``Bot.reply``   | No replacement.                                            |
+-----------------+------------------------------------------------------------+

Command Changes
~~~~~~~~~~~~~~~~~

As mentioned earlier, the first command change is that ``pass_context=True`` no longer
exists, so there is no need to pass this as a parameter.

Another change is the removal of ``no_pm=True``. Instead, use the new :func:`~ext.commands.guild_only` built-in
check.

The ``commands`` attribute of :class:`~ext.commands.Bot` and :class:`~ext.commands.Group` have been changed from a
dictionary to a set that does not have aliases. To retrieve the previous dictionary behaviour, use ``all_commands`` instead.

Command instances have gained new attributes and properties:

1. :attr:`~ext.commands.Command.signature` to get the signature of the command.
2. :attr:`~ext.commands.Command.usage`, an attribute to override the default signature.
3. :attr:`~ext.commands.Command.root_parent` to get the root parent group of a subcommand.

For :class:`~ext.commands.Group` and :class:`~ext.commands.Bot` the following changed:

- Changed :attr:`~.GroupMixin.commands` to be a :class:`set` without aliases.

    - Use :attr:`~.GroupMixin.all_commands` to get the old :class:`dict` with all commands.

Check Changes
~~~~~~~~~~~~~~~

Prior to v1.0, :func:`~ext.commands.check`\s could only be synchronous. As of v1.0 checks can now be coroutines.

Along with this change, a couple new checks were added.

- :func:`~ext.commands.guild_only` replaces the old ``no_pm=True`` functionality.
- :func:`~ext.commands.is_owner` uses the :meth:`Client.application_info` endpoint by default to fetch owner ID.

    - This is actually powered by a different function, :meth:`~ext.commands.Bot.is_owner`.
    - You can set the owner ID yourself by setting :attr:`.Bot.owner_id`.

- :func:`~ext.commands.is_nsfw` checks if the channel the command is in is a NSFW channel.

    - This is powered by the new :meth:`TextChannel.is_nsfw` method.

Event Changes
~~~~~~~~~~~~~~~

All command extension events have changed.

Before: ::

    on_command(command, ctx)
    on_command_completion(command, ctx)
    on_command_error(error, ctx)

After: ::

    on_command(ctx)
    on_command_completion(ctx)
    on_command_error(ctx, error)

The extraneous ``command`` parameter in :func:`.on_command` and :func:`.on_command_completion`
have been removed. The :class:`~ext.commands.Command` instance was not kept up-to date so it was incorrect. In order to get
the up to date :class:`~ext.commands.Command` instance, use the :attr:`.Context.command`
attribute.

The error handlers, either :meth:`~ext.commands.Command.error` or :func:`.on_command_error`,
have been re-ordered to use the :class:`~ext.commands.Context` as its first parameter to be consistent with other events
and commands.

HelpFormatter and Help Command Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``HelpFormatter`` class has been removed. It has been replaced with a :class:`~.commands.HelpCommand` class. This class now stores all the command handling and processing of the help command.

The help command is now stored in the :attr:`.Bot.help_command` attribute. As an added extension, you can disable the help command completely by assigning the attribute to ``None`` or passing it at ``__init__`` as ``help_command=None``.

The new interface allows the help command to be customised through special methods that can be overridden.

- :meth:`.HelpCommand.send_bot_help`
    - Called when the user requested for help with the entire bot.
- :meth:`.HelpCommand.send_cog_help`
    - Called when the user requested for help with a specific cog.
- :meth:`.HelpCommand.send_group_help`
    - Called when the user requested for help with a :class:`~.commands.Group`
- :meth:`.HelpCommand.send_command_help`
    - Called when the user requested for help with a :class:`~.commands.Command`
- :meth:`.HelpCommand.get_destination`
    - Called to know where to send the help messages. Useful for deciding whether to DM or not.
- :meth:`.HelpCommand.command_not_found`
    - A function (or coroutine) that returns a presentable no command found string.
- :meth:`.HelpCommand.subcommand_not_found`
    - A function (or coroutine) that returns a string when a subcommand is not found.
- :meth:`.HelpCommand.send_error_message`
    - A coroutine that gets passed the result of :meth:`.HelpCommand.command_not_found` and :meth:`.HelpCommand.subcommand_not_found`.
    - By default it just sends the message. But you can, for example, override it to put it in an embed.
- :meth:`.HelpCommand.on_help_command_error`
    - The :ref:`error handler <ext_commands_error_handler>` for the help command if you want to add one.
- :meth:`.HelpCommand.prepare_help_command`
    - A coroutine that is called right before the help command processing is done.

Certain subclasses can implement more customisable methods.

The old ``HelpFormatter`` was replaced with :class:`~.commands.DefaultHelpCommand`\, which implements all of the logic of the old help command. The customisable methods can be found in the accompanying documentation.

The library now provides a new more minimalistic :class:`~.commands.HelpCommand` implementation that doesn't take as much space, :class:`~.commands.MinimalHelpCommand`. The customisable methods can also be found in the accompanying documentation.

A frequent request was if you could associate a help command with a cog. The new design allows for dynamically changing of cog through binding it to the :attr:`.HelpCommand.cog` attribute. After this assignment the help command will pretend to be part of the cog and everything should work as expected. When the cog is unloaded then the help command will be "unbound" from the cog.

For example, to implement a :class:`~.commands.HelpCommand` in a cog, the following snippet can be used.

.. code-block:: python3

    class MyHelpCommand(commands.MinimalHelpCommand):
        def get_command_signature(self, command):
            return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    class MyCog(commands.Cog):
        def __init__(self, bot):
            self._original_help_command = bot.help_command
            bot.help_command = MyHelpCommand()
            bot.help_command.cog = self

        def cog_unload(self):
            self.bot.help_command = self._original_help_command

For more information, check out the relevant :ref:`documentation <ext_commands_help_command>`.

Cog Changes
~~~~~~~~~~~~~

Cogs have completely been revamped. They are documented in :ref:`ext_commands_cogs` as well.

Cogs are now required to have a base class, :class:`~.commands.Cog` for future proofing purposes. This comes with special methods to customise some behaviour.

* :meth:`.Cog.cog_unload`
    - This is called when a cog needs to do some cleanup, such as cancelling a task.
* :meth:`.Cog.bot_check_once`
    - This registers a :meth:`.Bot.check_once` check.
* :meth:`.Cog.bot_check`
    - This registers a regular :meth:`.Bot.check` check.
* :meth:`.Cog.cog_check`
    - This registers a check that applies to every command in the cog.
* :meth:`.Cog.cog_command_error`
    - This is a special error handler that is called whenever an error happens inside the cog.
* :meth:`.Cog.cog_before_invoke` and :meth:`.Cog.cog_after_invoke`
    - A special method that registers a cog before and after invoke hook. More information can be found in :ref:`migrating_1_0_before_after_hook`.

Those that were using listeners, such as ``on_message`` inside a cog will now have to explicitly mark them as such using the :meth:`.commands.Cog.listener` decorator.

Along with that, cogs have gained the ability to have custom names through specifying it in the class definition line. More options can be found in the metaclass that facilitates all this, :class:`.commands.CogMeta`.

An example cog with every special method registered and a custom name is as follows:

.. code-block:: python3

    class MyCog(commands.Cog, name='Example Cog'):
        def cog_unload(self):
            print('cleanup goes here')

        def bot_check(self, ctx):
            print('bot check')
            return True

        def bot_check_once(self, ctx):
            print('bot check once')
            return True

        async def cog_check(self, ctx):
            print('cog local check')
            return await ctx.bot.is_owner(ctx.author)

        async def cog_command_error(self, ctx, error):
            print('Error in {0.command.qualified_name}: {1}'.format(ctx, error))

        async def cog_before_invoke(self, ctx):
            print('cog local before: {0.command.qualified_name}'.format(ctx))

        async def cog_after_invoke(self, ctx):
            print('cog local after: {0.command.qualified_name}'.format(ctx))

        @commands.Cog.listener()
        async def on_message(self, message):
            pass


.. _migrating_1_0_before_after_hook:

Before and After Invocation Hooks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Commands have gained new before and after invocation hooks that allow you to do an action before and after a command is
run.

They take a single parameter, :class:`~ext.commands.Context` and they must be a coroutine.

They are on a global, per-cog, or per-command basis.

Basically: ::


    # global hooks:

    @bot.before_invoke
    async def before_any_command(ctx):
        # do something before a command is called
        pass

    @bot.after_invoke
    async def after_any_command(ctx):
        # do something after a command is called
        pass

The after invocation is hook always called, **regardless of an error in the command**. This makes it ideal for some error
handling or clean up of certain resources such a database connection.

The per-command registration is as follows: ::

    @bot.command()
    async def foo(ctx):
        await ctx.send('foo')

    @foo.before_invoke
    async def before_foo_command(ctx):
        # do something before the foo command is called
        pass

    @foo.after_invoke
    async def after_foo_command(ctx):
        # do something after the foo command is called
        pass

The special cog method for these is :meth:`.Cog.cog_before_invoke` and :meth:`.Cog.cog_after_invoke`, e.g.:

.. code-block:: python3

    class MyCog(commands.Cog):
        async def cog_before_invoke(self, ctx):
            ctx.secret_cog_data = 'foo'

        async def cog_after_invoke(self, ctx):
            print('{0.command} is done...'.format(ctx))

        @commands.command()
        async def foo(self, ctx):
            await ctx.send(ctx.secret_cog_data)

To check if a command failed in the after invocation hook, you can use
:attr:`.Context.command_failed`.

The invocation order is as follows:

1. Command local before invocation hook
2. Cog local before invocation hook
3. Global before invocation hook
4. The actual command
5. Command local after invocation hook
6. Cog local after invocation hook
7. Global after invocation hook

Converter Changes
~~~~~~~~~~~~~~~~~~~

Prior to v1.0, a converter was a type hint that could be a callable that could be invoked
with a singular argument denoting the argument passed by the user as a string.

This system was eventually expanded to support a :class:`~ext.commands.Converter` system to
allow plugging in the :class:`~ext.commands.Context` and do more complicated conversions such
as the built-in "discord" converters.

In v1.0 this converter system was revamped to allow instances of :class:`~ext.commands.Converter` derived
classes to be passed. For consistency, the :meth:`~ext.commands.Converter.convert` method was changed to
always be a coroutine and will now take the two arguments as parameters.

Essentially, before: ::

    class MyConverter(commands.Converter):
        def convert(self):
            return self.ctx.message.server.me

After: ::

    class MyConverter(commands.Converter):
        async def convert(self, ctx, argument):
            return ctx.me

The command framework also got a couple new converters:

- :class:`~ext.commands.clean_content` this is akin to :attr:`Message.clean_content` which scrubs mentions.
- :class:`~ext.commands.UserConverter` will now appropriately convert :class:`User` only.
- ``ChannelConverter`` is now split into two different converters.

    - :class:`~ext.commands.TextChannelConverter` for :class:`TextChannel`.
    - :class:`~ext.commands.VoiceChannelConverter` for :class:`VoiceChannel`.
=======
- There is a `/guilds/:id/roles/:id/member-ids` endpoint that provides up to 100 member IDs for any role other than the default role. You can use :func:`Guild.query_members` to fetch all these members in one go.
- With OPCode 14, you can subscribe to certain member IDs and receive presence updates for them. The limit of IDs per-request is currently unknown, but I have witnessed the client send over 200/request. This may help with the offline members issue.
- Thread member lists do *not* work the same. You just send an OPCode 14 with the thread IDs and receive a `THREAD_MEMBER_LIST_UPDATE` with all the members. The cache then stays updated with `GUILD_MEMBER_UPDATE` and `THREAD_MEMBERS_UPDATE` events.
- OPCode 14 lets you subscribe to multiple channels at once, and you *might* be able to do more than 2 ranges at once.
>>>>>>> rebase
