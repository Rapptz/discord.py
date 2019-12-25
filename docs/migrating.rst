.. currentmodule:: discord

.. _migrating_1_0:

Migrating to v1.0
======================

v1.0 is one of the biggest breaking changes in the library due to a complete
redesign.

The amount of changes are so massive and long that for all intents and purposes, it is a completely
new library.

Part of the redesign involves making things more easy to use and natural. Things are done on the
:ref:`models <discord_api_models>` instead of requiring a :class:`Client` instance to do any work.

Python Version Change
-----------------------

In order to make development easier and also to allow for our dependencies to upgrade to allow usage of 3.7 or higher,
the library had to remove support for Python versions lower than 3.5.3, which essentially means that **support for Python 3.4
is dropped**.

Major Model Changes
---------------------

Below are major model changes that have happened in v1.0

Snowflakes are int
~~~~~~~~~~~~~~~~~~~~

Before v1.0, all snowflakes (the ``id`` attribute) were strings. This has been changed to :class:`int`.

Quick example: ::

    # before
    ch = client.get_channel('84319995256905728')
    if message.author.id == '80528701850124288':
        ...

    # after
    ch = client.get_channel(84319995256905728)
    if message.author.id == 80528701850124288:
        ...

This change allows for fewer errors when using the Copy ID feature in the official client since you no longer have
to wrap it in quotes and allows for optimisation opportunities by allowing ETF to be used instead of JSON internally.

Server is now Guild
~~~~~~~~~~~~~~~~~~~~~

The official API documentation calls the "Server" concept a "Guild" instead. In order to be more consistent with the
API documentation when necessary, the model has been renamed to :class:`Guild` and all instances referring to it has
been changed as well.

A list of changes is as follows:

+-------------------------------+----------------------------------+
|             Before            |              After               |
+-------------------------------+----------------------------------+
| ``Message.server``            | :attr:`Message.guild`            |
+-------------------------------+----------------------------------+
| ``Channel.server``            | :attr:`.GuildChannel.guild`      |
+-------------------------------+----------------------------------+
| ``Client.servers``            | :attr:`Client.guilds`            |
+-------------------------------+----------------------------------+
| ``Client.get_server``         | :meth:`Client.get_guild`         |
+-------------------------------+----------------------------------+
| ``Emoji.server``              | :attr:`Emoji.guild`              |
+-------------------------------+----------------------------------+
| ``Role.server``               | :attr:`Role.guild`               |
+-------------------------------+----------------------------------+
| ``Invite.server``             | :attr:`Invite.guild`             |
+-------------------------------+----------------------------------+
| ``Member.server``             | :attr:`Member.guild`             |
+-------------------------------+----------------------------------+
| ``Permissions.manage_server`` | :attr:`Permissions.manage_guild` |
+-------------------------------+----------------------------------+
| ``VoiceClient.server``        | :attr:`VoiceClient.guild`        |
+-------------------------------+----------------------------------+
| ``Client.create_server``      | :meth:`Client.create_guild`      |
+-------------------------------+----------------------------------+

.. _migrating_1_0_model_state:

Models are Stateful
~~~~~~~~~~~~~~~~~~~~~

As mentioned earlier, a lot of functionality was moved out of :class:`Client` and
put into their respective :ref:`model <discord_api_models>`.

A list of these changes is enumerated below.

+---------------------------------------+------------------------------------------------------------------------------+
|                 Before                |                                    After                                     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.add_reaction``               | :meth:`Message.add_reaction`                                                 |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.add_roles``                  | :meth:`Member.add_roles`                                                     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.ban``                        | :meth:`Member.ban` or :meth:`Guild.ban`                                      |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.change_nickname``            | :meth:`Member.edit`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.clear_reactions``            | :meth:`Message.clear_reactions`                                              |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.create_channel``             | :meth:`Guild.create_text_channel` and :meth:`Guild.create_voice_channel`     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.create_custom_emoji``        | :meth:`Guild.create_custom_emoji`                                            |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.create_invite``              | :meth:`abc.GuildChannel.create_invite`                                       |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.create_role``                | :meth:`Guild.create_role`                                                    |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_channel``             | :meth:`abc.GuildChannel.delete`                                              |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_channel_permissions`` | :meth:`abc.GuildChannel.set_permissions` with ``overwrite`` set to ``None``  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_custom_emoji``        | :meth:`Emoji.delete`                                                         |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_invite``              | :meth:`Invite.delete` or :meth:`Client.delete_invite`                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_message``             | :meth:`Message.delete`                                                       |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_messages``            | :meth:`TextChannel.delete_messages`                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_role``                | :meth:`Role.delete`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.delete_server``              | :meth:`Guild.delete`                                                         |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_channel``               | :meth:`TextChannel.edit` or :meth:`VoiceChannel.edit`                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_channel_permissions``   | :meth:`abc.GuildChannel.set_permissions`                                     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_custom_emoji``          | :meth:`Emoji.edit`                                                           |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_message``               | :meth:`Message.edit`                                                         |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_profile``               | :meth:`ClientUser.edit` (you get this from :attr:`Client.user`)              |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_role``                  | :meth:`Role.edit`                                                            |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.edit_server``                | :meth:`Guild.edit`                                                           |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.estimate_pruned_members``    | :meth:`Guild.estimate_pruned_members`                                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_all_emojis``             | :attr:`Client.emojis`                                                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_bans``                   | :meth:`Guild.bans`                                                           |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_invite``                 | :meth:`Client.fetch_invite`                                                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_message``                | :meth:`abc.Messageable.fetch_message`                                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_reaction_users``         | :meth:`Reaction.users`                                                       |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.get_user_info``              | :meth:`Client.fetch_user`                                                    |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.invites_from``               | :meth:`abc.GuildChannel.invites` or :meth:`Guild.invites`                    |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.join_voice_channel``         | :meth:`VoiceChannel.connect` (see :ref:`migrating_1_0_voice`)                |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.kick``                       | :meth:`Guild.kick` or :meth:`Member.kick`                                    |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.leave_server``               | :meth:`Guild.leave`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.logs_from``                  | :meth:`abc.Messageable.history` (see :ref:`migrating_1_0_async_iter`)        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.move_channel``               | :meth:`TextChannel.edit` or :meth:`VoiceChannel.edit`                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.move_member``                | :meth:`Member.edit`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.move_role``                  | :meth:`Role.edit`                                                            |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.pin_message``                | :meth:`Message.pin`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.pins_from``                  | :meth:`abc.Messageable.pins`                                                 |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.prune_members``              | :meth:`Guild.prune_members`                                                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.purge_from``                 | :meth:`TextChannel.purge`                                                    |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.remove_reaction``            | :meth:`Message.remove_reaction`                                              |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.remove_roles``               | :meth:`Member.remove_roles`                                                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.replace_roles``              | :meth:`Member.edit`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.send_file``                  | :meth:`abc.Messageable.send` (see :ref:`migrating_1_0_sending_messages`)     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.send_message``               | :meth:`abc.Messageable.send` (see :ref:`migrating_1_0_sending_messages`)     |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.send_typing``                | :meth:`abc.Messageable.trigger_typing` (use :meth:`abc.Messageable.typing`)  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.server_voice_state``         | :meth:`Member.edit`                                                          |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.start_private_message``      | :meth:`User.create_dm`                                                       |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.unban``                      | :meth:`Guild.unban` or :meth:`Member.unban`                                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.unpin_message``              | :meth:`Message.unpin`                                                        |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.wait_for_message``           | :meth:`Client.wait_for` (see :ref:`migrating_1_0_wait_for`)                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.wait_for_reaction``          | :meth:`Client.wait_for` (see :ref:`migrating_1_0_wait_for`)                  |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.wait_until_login``           | Removed                                                                      |
+---------------------------------------+------------------------------------------------------------------------------+
| ``Client.wait_until_ready``           | No change                                                                    |
+---------------------------------------+------------------------------------------------------------------------------+

Property Changes
~~~~~~~~~~~~~~~~~~

In order to be a bit more consistent, certain things that were properties were changed to methods instead.

The following are now methods instead of properties (requires parentheses):

- :meth:`Role.is_default`
- :meth:`Client.is_ready`
- :meth:`Client.is_closed`

Dict Value Change
~~~~~~~~~~~~~~~~~~~~~

Prior to v1.0 some aggregating properties that retrieved models would return "dict view" objects.

As a consequence, when the dict would change size while you would iterate over it, a RuntimeError would
be raised and crash the task. To alleviate this, the "dict view" objects were changed into lists.

The following views were changed to a list:

- :attr:`Client.guilds`
- :attr:`Client.users` (new in v1.0)
- :attr:`Client.emojis` (new in v1.0)
- :attr:`Guild.channels`
- :attr:`Guild.text_channels` (new in v1.0)
- :attr:`Guild.voice_channels` (new in v1.0)
- :attr:`Guild.emojis`
- :attr:`Guild.members`

Voice State Changes
~~~~~~~~~~~~~~~~~~~~~

Earlier, in v0.11.0 a :class:`VoiceState` class was added to refer to voice states along with a
:attr:`Member.voice` attribute to refer to it.

However, it was transparent to the user. In an effort to make the library save more memory, the
voice state change is now more visible.

The only way to access voice attributes is via the :attr:`Member.voice` attribute. Note that if
the member does not have a voice state this attribute can be ``None``.

Quick example: ::

    # before
    member.deaf
    member.voice.voice_channel

    # after
    if member.voice: # can be None
        member.voice.deaf
        member.voice.channel


User and Member Type Split
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In v1.0 to save memory, :class:`User` and :class:`Member` are no longer inherited. Instead, they are "flattened"
by having equivalent properties that map out to the functional underlying :class:`User`. Thus, there is no functional
change in how they are used. However this breaks :func:`isinstance` checks and thus is something to keep in mind.

These memory savings were accomplished by having a global :class:`User` cache, and as a positive consequence you
can now easily fetch a :class:`User` by their ID by using the new :meth:`Client.get_user`. You can also get a list
of all :class:`User` your client can see with :attr:`Client.users`.

.. _migrating_1_0_channel_split:

Channel Type Split
~~~~~~~~~~~~~~~~~~~~~

Prior to v1.0, channels were two different types, ``Channel`` and ``PrivateChannel`` with a ``is_private``
property to help differentiate between them.

In order to save memory the channels have been split into 4 different types:

- :class:`TextChannel` for guild text channels.
- :class:`VoiceChannel` for guild voice channels.
- :class:`DMChannel` for DM channels with members.
- :class:`GroupChannel` for Group DM channels with members.

With this split came the removal of the ``is_private`` attribute. You should now use :func:`isinstance`.

The types are split into two different :ref:`discord_api_abcs`:

- :class:`abc.GuildChannel` for guild channels.
- :class:`abc.PrivateChannel` for private channels (DMs and group DMs).

So to check if something is a guild channel you would do: ::

    isinstance(channel, discord.abc.GuildChannel)

And to check if it's a private channel you would do: ::

    isinstance(channel, discord.abc.PrivateChannel)

Of course, if you're looking for only a specific type you can pass that too, e.g. ::

    isinstance(channel, discord.TextChannel)

With this type split also came event changes, which are enumerated in :ref:`migrating_1_0_event_changes`.


Miscellaneous Model Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There were lots of other things added or removed in the models in general.

They will be enumerated here.

**Removed**

- :meth:`Client.login` no longer accepts email and password logins.

    - Use a token and ``bot=False``.

- ``Client.get_all_emojis``

    - Use :attr:`Client.emojis` instead.

` ``Client.messages``

    - Use read-only :attr:`Client.cached_messages` instead.

- ``Client.wait_for_message`` and ``Client.wait_for_reaction`` are gone.

    - Use :meth:`Client.wait_for` instead.

- ``Channel.voice_members``

    - Use :attr:`VoiceChannel.members` instead.

- ``Channel.is_private``

    - Use ``isinstance`` instead with one of the :ref:`discord_api_abcs` instead.
    - e.g. ``isinstance(channel, discord.abc.GuildChannel)`` will check if it isn't a private channel.

- ``Client.accept_invite``

    - There is no replacement for this one. This functionality is deprecated API wise.

- ``Guild.default_channel`` / ``Server.default_channel`` and ``Channel.is_default``

    - The concept of a default channel was removed from Discord.
      See `#329 <https://github.com/hammerandchisel/discord-api-docs/pull/329>`_.

- ``Message.edited_timestamp``

    - Use :attr:`Message.edited_at` instead.

- ``Message.timestamp``

    - Use :attr:`Message.created_at` instead.

- ``Colour.to_tuple()``

    - Use :meth:`Colour.to_rgb` instead.

- ``Permissions.view_audit_logs``

    - Use :attr:`Permissions.view_audit_log` instead.

- ``Member.game``

    - Use :attr:`Member.activities` instead.

- ``Guild.role_hierarchy`` / ``Server.role_hierarchy``

    - Use :attr:`Guild.roles` instead. Note that while sorted, it is in the opposite order
      of what the old ``Guild.role_hierarchy`` used to be.

**Changed**

- :attr:`Member.avatar_url` and :attr:`User.avatar_url` now return the default avatar if a custom one is not set.
- :attr:`Message.embeds` is now a list of :class:`Embed` instead of :class:`dict` objects.
- :attr:`Message.attachments` is now a list of :class:`Attachment` instead of :class:`dict` object.
- :attr:`Guild.roles` is now sorted through hierarchy. The first element is always the ``@everyone`` role.

**Added**

- :class:`Attachment` to represent a discord attachment.
- :class:`CategoryChannel` to represent a channel category.
- :attr:`VoiceChannel.members` for fetching members connected to a voice channel.
- :attr:`TextChannel.members` for fetching members that can see the channel.
- :attr:`Role.members` for fetching members that have the role.
- :attr:`Guild.text_channels` for fetching text channels only.
- :attr:`Guild.voice_channels` for fetching voice channels only.
- :attr:`Guild.categories` for fetching channel categories only.
- :attr:`TextChannel.category` and :attr:`VoiceChannel.category` to get the category a channel belongs to.
- :meth:`Guild.by_category` to get channels grouped by their category.
- :attr:`Guild.chunked` to check member chunking status.
- :attr:`Guild.explicit_content_filter` to fetch the content filter.
- :attr:`Guild.shard_id` to get a guild's Shard ID if you're sharding.
- :attr:`Client.users` to get all visible :class:`User` instances.
- :meth:`Client.get_user` to get a :class:`User` by ID.
- :meth:`User.avatar_url_as` to get an avatar in a specific size or format.
- :meth:`Guild.vanity_invite` to fetch the guild's vanity invite.
- :meth:`Guild.audit_logs` to fetch the guild's audit logs.
- :attr:`Message.webhook_id` to fetch the message's webhook ID.
- :attr:`Message.activity` and :attr:`Message.application` for Rich Presence related information.
- :meth:`TextChannel.is_nsfw` to check if a text channel is NSFW.
- :meth:`Colour.from_rgb` to construct a :class:`Colour` from RGB tuple.
- :meth:`Guild.get_role` to get a role by its ID.

.. _migrating_1_0_sending_messages:

Sending Messages
------------------

One of the changes that were done was the merger of the previous ``Client.send_message`` and ``Client.send_file``
functionality into a single method, :meth:`~abc.Messageable.send`.

Basically: ::

    # before
    await client.send_message(channel, 'Hello')

    # after
    await channel.send('Hello')

This supports everything that the old ``send_message`` supported such as embeds: ::

    e = discord.Embed(title='foo')
    await channel.send('Hello', embed=e)

There is a caveat with sending files however, as this functionality was expanded to support multiple
file attachments, you must now use a :class:`File` pseudo-namedtuple to upload a single file. ::

    # before
    await client.send_file(channel, 'cool.png', filename='testing.png', content='Hello')

    # after
    await channel.send('Hello', file=discord.File('cool.png', 'testing.png'))

This change was to facilitate multiple file uploads: ::

    my_files = [
        discord.File('cool.png', 'testing.png'),
        discord.File(some_fp, 'cool_filename.png'),
    ]

    await channel.send('Your images:', files=my_files)

.. _migrating_1_0_async_iter:

Asynchronous Iterators
------------------------

Prior to v1.0, certain functions like ``Client.logs_from`` would return a different type if done in Python 3.4 or 3.5+.

In v1.0, this change has been reverted and will now return a singular type meeting an abstract concept called
:class:`AsyncIterator`.

This allows you to iterate over it like normal: ::

    async for message in channel.history():
        print(message)

Or turn it into a list: ::

    messages = await channel.history().flatten()
    for message in messages:
        print(message)

A handy aspect of returning :class:`AsyncIterator` is that it allows you to chain functions together such as
:meth:`AsyncIterator.map` or :meth:`AsyncIterator.filter`: ::

    async for m_id in channel.history().filter(lambda m: m.author == client.user).map(lambda m: m.id):
        print(m_id)

The functions passed to :meth:`AsyncIterator.map` or :meth:`AsyncIterator.filter` can be either coroutines or regular
functions.

You can also get single elements a la :func:`discord.utils.find` or :func:`discord.utils.get` via
:meth:`AsyncIterator.get` or :meth:`AsyncIterator.find`: ::

    my_last_message = await channel.history().get(author=client.user)

The following return :class:`AsyncIterator`:

- :meth:`abc.Messageable.history`
- :meth:`Guild.audit_logs`
- :meth:`Reaction.users`

.. _migrating_1_0_event_changes:

Event Changes
--------------

A lot of events have gone through some changes.

Many events with ``server`` in the name were changed to use ``guild`` instead.

Before:

- ``on_server_join``
- ``on_server_remove``
- ``on_server_update``
- ``on_server_role_create``
- ``on_server_role_delete``
- ``on_server_role_update``
- ``on_server_emojis_update``
- ``on_server_available``
- ``on_server_unavailable``

After:

- :func:`on_guild_join`
- :func:`on_guild_remove`
- :func:`on_guild_update`
- :func:`on_guild_role_create`
- :func:`on_guild_role_delete`
- :func:`on_guild_role_update`
- :func:`on_guild_emojis_update`
- :func:`on_guild_available`
- :func:`on_guild_unavailable`


The :func:`on_voice_state_update` event has received an argument change.

Before: ::

    async def on_voice_state_update(before, after)

After: ::

    async def on_voice_state_update(member, before, after)

Instead of two :class:`Member` objects, the new event takes one :class:`Member` object and two :class:`VoiceState` objects.

The :func:`on_guild_emojis_update` event has received an argument change.

Before: ::

    async def on_guild_emojis_update(before, after)

After: ::

    async def on_guild_emojis_update(guild, before, after)

The first argument is now the :class:`Guild` that the emojis were updated from.

The :func:`on_member_ban` event has received an argument change as well:

Before: ::

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
2. :attr:`~.Command.usage`, an attribute to override the default signature.
3. :attr:`~.Command.root_parent` to get the root parent group of a subcommand.

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

The error handlers, either :meth:`.Command.error` or :func:`.on_command_error`,
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
