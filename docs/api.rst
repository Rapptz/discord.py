.. currentmodule:: discord

API Reference
===============

The following section outlines the API of discord.py.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    discord.py.

Version Related Info
---------------------

There are two main ways to query version information about the library. For guarantees, check :ref:`version_guarantees`.

.. data:: version_info

    A named tuple that is similar to :obj:`py:sys.version_info`.

    Just like :obj:`py:sys.version_info` the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

.. data:: __version__

    A string representation of the version. e.g. ``'1.0.0rc1'``. This is based
    off of :pep:`440`.

Clients
--------

Client
~~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :exclude-members: fetch_guilds

    .. automethod:: Client.fetch_guilds
        :async-for:

AutoShardedClient
~~~~~~~~~~~~~~~~~~

.. attributetable:: AutoShardedClient

.. autoclass:: AutoShardedClient
    :members:

Application Info
------------------

AppInfo
~~~~~~~~

.. attributetable:: AppInfo

.. autoclass:: AppInfo()
    :members:

Team
~~~~~

.. attributetable:: Team

.. autoclass:: Team()
    :members:

TeamMember
~~~~~~~~~~~

.. attributetable:: TeamMember

.. autoclass:: TeamMember()
    :members:

Voice Related
---------------

VoiceClient
~~~~~~~~~~~~

.. attributetable:: VoiceClient

.. autoclass:: VoiceClient()
    :members:

VoiceProtocol
~~~~~~~~~~~~~~~

.. attributetable:: VoiceProtocol

.. autoclass:: VoiceProtocol
    :members:

AudioSource
~~~~~~~~~~~~

.. attributetable:: AudioSource

.. autoclass:: AudioSource
    :members:

PCMAudio
~~~~~~~~~

.. attributetable:: PCMAudio

.. autoclass:: PCMAudio
    :members:

FFmpegAudio
~~~~~~~~~~~~

.. attributetable:: FFmpegAudio

.. autoclass:: FFmpegAudio
    :members:

FFmpegPCMAudio
~~~~~~~~~~~~~~~

.. attributetable:: FFmpegPCMAudio

.. autoclass:: FFmpegPCMAudio
    :members:

FFmpegOpusAudio
~~~~~~~~~~~~~~~~

.. attributetable:: FFmpegOpusAudio

.. autoclass:: FFmpegOpusAudio
    :members:

PCMVolumeTransformer
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PCMVolumeTransformer

.. autoclass:: PCMVolumeTransformer
    :members:

Opus Library
~~~~~~~~~~~~~

.. autofunction:: discord.opus.load_opus

.. autofunction:: discord.opus.is_loaded

.. _discord-api-events:

Event Reference
---------------

This section outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord

    class MyClient(discord.Client):
        async def on_message(self, message):
            if message.author == self.user:
                return

            if message.content.startswith('$hello'):
                await message.channel.send('Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must be ``async def``
    functions.

.. function:: on_connect()

    Called when the client has successfully connected to Discord. This is not
    the same as the client being fully prepared, see :func:`on_ready` for that.

    The warnings on :func:`on_ready` also apply.

.. function:: on_shard_connect(shard_id)

    Similar to :func:`on_connect` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has connected to Discord.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has connected.
    :type shard_id: :class:`int`

.. function:: on_disconnect()

    Called when the client has disconnected from Discord, or a connection attempt to Discord has failed.
    This could happen either through the internet being disconnected, explicit calls to close,
    or Discord terminating the connection one way or the other.

    This function can be called many times without a corresponding :func:`on_connect` call.

.. function:: on_shard_disconnect(shard_id)

    Similar to :func:`on_disconnect` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has disconnected from Discord.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has disconnected.
    :type shard_id: :class:`int`

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord. Usually after login is successful
    and the :attr:`Client.guilds` and co. are filled up.

    .. warning::

        This function is not guaranteed to be the first event called.
        Likewise, this function is **not** guaranteed to only be called
        once. This library implements reconnection logic and thus will
        end up calling this event whenever a RESUME request fails.

.. function:: on_shard_ready(shard_id)

    Similar to :func:`on_ready` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has become ready.

    :param shard_id: The shard ID that is ready.
    :type shard_id: :class:`int`

.. function:: on_resumed()

    Called when the client has resumed a session.

.. function:: on_shard_resumed(shard_id)

    Similar to :func:`on_resumed` except used by :class:`AutoShardedClient`
    to denote when a particular shard ID has resumed a session.

    .. versionadded:: 1.4

    :param shard_id: The shard ID that has resumed.
    :type shard_id: :class:`int`

.. function:: on_error(event, *args, **kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    suppress the default action of printing the traceback.

    The information of the exception raised and the exception itself can
    be retrieved with a standard call to :func:`sys.exc_info`.

    If you want exception to propagate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    :ref:`raise statement <py:raise>`. Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    .. note::

        ``on_error`` will only be dispatched to :meth:`Client.event`.

        It will not be received by :meth:`Client.wait_for`, or, if used,
        :ref:`ext_commands_api_bot` listeners such as
        :meth:`~ext.commands.Bot.listen` or :meth:`~ext.commands.Cog.listener`.

    :param event: The name of the event that raised the exception.
    :type event: :class:`str`

    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        exception.

.. function:: on_socket_raw_receive(msg)

    Called whenever a message is received from the WebSocket, before
    it's processed. This event is always dispatched when a message is
    received and the passed data is not processed in any way.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param msg: The message passed in from the WebSocket library.
                Could be :class:`bytes` for a binary message or :class:`str`
                for a regular message.
    :type msg: Union[:class:`bytes`, :class:`str`]

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the WebSocket before the
    message is sent. The passed parameter is the message that is being
    sent to the WebSocket.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    .. note::

        This is only for the messages sent from the client
        WebSocket. The voice WebSocket will not trigger this event.

    :param payload: The message that is about to be passed on to the
                    WebSocket library. It can be :class:`bytes` to denote a binary
                    message or :class:`str` to denote a regular text message.

.. function:: on_typing(channel, user, when)

    Called when someone begins typing a message.

    The ``channel`` parameter can be a :class:`abc.Messageable` instance.
    Which could either be :class:`TextChannel`, :class:`GroupChannel`, or
    :class:`DMChannel`.

    If the ``channel`` is a :class:`TextChannel` then the ``user`` parameter
    is a :class:`Member`, otherwise it is a :class:`User`.

    This requires :attr:`Intents.typing` to be enabled.

    :param channel: The location where the typing originated from.
    :type channel: :class:`abc.Messageable`
    :param user: The user that started typing.
    :type user: Union[:class:`User`, :class:`Member`]
    :param when: When the typing started as a naive datetime in UTC.
    :type when: :class:`datetime.datetime`

.. function:: on_message(message)

    Called when a :class:`Message` is created and sent.

    This requires :attr:`Intents.messages` to be enabled.

    .. warning::

        Your bot's own messages and private messages are sent through this
        event. This can lead cases of 'recursion' depending on how your bot was
        programmed. If you want the bot to not reply to itself, consider
        checking the user IDs. Note that :class:`~ext.commands.Bot` does not
        have this problem.

    :param message: The current message.
    :type message: :class:`Message`

.. function:: on_message_delete(message)

    Called when a message is deleted. If the message is not found in the
    internal message cache, then this event will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :attr:`Client.max_messages` attribute
    or use the :func:`on_raw_message_delete` event instead.

    This requires :attr:`Intents.messages` to be enabled.

    :param message: The deleted message.
    :type message: :class:`Message`

.. function:: on_bulk_message_delete(messages)

    Called when messages are bulk deleted. If none of the messages deleted
    are found in the internal message cache, then this event will not be called.
    If individual messages were not found in the internal message cache,
    this event will still be called, but the messages not found will not be included in
    the messages list. Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :attr:`Client.max_messages` attribute
    or use the :func:`on_raw_bulk_message_delete` event instead.

    This requires :attr:`Intents.messages` to be enabled.

    :param messages: The messages that have been deleted.
    :type messages: List[:class:`Message`]

.. function:: on_raw_message_delete(payload)

    Called when a message is deleted. Unlike :func:`on_message_delete`, this is
    called regardless of the message being in the internal message cache or not.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageDeleteEvent.cached_message`

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageDeleteEvent`

.. function:: on_raw_bulk_message_delete(payload)

    Called when a bulk delete is triggered. Unlike :func:`on_bulk_message_delete`, this is
    called regardless of the messages being in the internal message cache or not.

    If the messages are found in the message cache,
    they can be accessed via :attr:`RawBulkMessageDeleteEvent.cached_messages`

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawBulkMessageDeleteEvent`

.. function:: on_message_edit(before, after)

    Called when a :class:`Message` receives an update event. If the message is not found
    in the internal message cache, then these events will not be called.
    Messages might not be in cache if the message is too old
    or the client is participating in high traffic guilds.

    If this occurs increase the :attr:`Client.max_messages` attribute
    or use the :func:`on_raw_message_edit` event instead.

    The following non-exhaustive cases trigger this event:

    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.

        - For performance reasons, the embed server does not do this in a "consistent" manner.

    - The message's embeds were suppressed or unsuppressed.
    - A call message has received an update to its participants or ending time.

    This requires :attr:`Intents.messages` to be enabled.

    :param before: The previous version of the message.
    :type before: :class:`Message`
    :param after: The current version of the message.
    :type after: :class:`Message`

.. function:: on_raw_message_edit(payload)

    Called when a message is edited. Unlike :func:`on_message_edit`, this is called
    regardless of the state of the internal message cache.

    If the message is found in the message cache,
    it can be accessed via :attr:`RawMessageUpdateEvent.cached_message`. The cached message represents
    the message before it has been edited. For example, if the content of a message is modified and
    triggers the :func:`on_raw_message_edit` coroutine, the :attr:`RawMessageUpdateEvent.cached_message`
    will return a :class:`Message` object that represents the message before the content was modified.

    Due to the inherently raw nature of this event, the data parameter coincides with
    the raw data given by the `gateway <https://discord.com/developers/docs/topics/gateway#message-update>`_.

    Since the data payload can be partial, care must be taken when accessing stuff in the dictionary.
    One example of a common case of partial data is when the ``'content'`` key is inaccessible. This
    denotes an "embed" only edit, which is an edit in which only the embeds are updated by the Discord
    embed server.

    This requires :attr:`Intents.messages` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawMessageUpdateEvent`

.. function:: on_reaction_add(reaction, user)

    Called when a message has a reaction added to it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this
    event will not be called. Consider using :func:`on_raw_reaction_add` instead.

    .. note::

        To get the :class:`Message` being reacted, access it via :attr:`Reaction.message`.

    This requires :attr:`Intents.reactions` to be enabled.

    .. note::

        This doesn't require :attr:`Intents.members` within a guild context,
        but due to Discord not providing updated user information in a direct message
        it's required for direct messages to receive this event.
        Consider using :func:`on_raw_reaction_add` if you need this and do not otherwise want
        to enable the members intent.

    :param reaction: The current state of the reaction.
    :type reaction: :class:`Reaction`
    :param user: The user who added the reaction.
    :type user: Union[:class:`Member`, :class:`User`]

.. function:: on_raw_reaction_add(payload)

    Called when a message has a reaction added. Unlike :func:`on_reaction_add`, this is
    called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionActionEvent`

.. function:: on_reaction_remove(reaction, user)

    Called when a message has a reaction removed from it. Similar to on_message_edit,
    if the message is not found in the internal message cache, then this event
    will not be called.

    .. note::

        To get the message being reacted, access it via :attr:`Reaction.message`.

    This requires both :attr:`Intents.reactions` and :attr:`Intents.members` to be enabled.

    .. note::

        Consider using :func:`on_raw_reaction_remove` if you need this and do not want
        to enable the members intent.

    :param reaction: The current state of the reaction.
    :type reaction: :class:`Reaction`
    :param user: The user who added the reaction.
    :type user: Union[:class:`Member`, :class:`User`]

.. function:: on_raw_reaction_remove(payload)

    Called when a message has a reaction removed. Unlike :func:`on_reaction_remove`, this is
    called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionActionEvent`

.. function:: on_reaction_clear(message, reactions)

    Called when a message has all its reactions removed from it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this event
    will not be called. Consider using :func:`on_raw_reaction_clear` instead.

    This requires :attr:`Intents.reactions` to be enabled.

    :param message: The message that had its reactions cleared.
    :type message: :class:`Message`
    :param reactions: The reactions that were removed.
    :type reactions: List[:class:`Reaction`]

.. function:: on_raw_reaction_clear(payload)

    Called when a message has all its reactions removed. Unlike :func:`on_reaction_clear`,
    this is called regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionClearEvent`

.. function:: on_reaction_clear_emoji(reaction)

    Called when a message has a specific reaction removed from it. Similar to :func:`on_message_edit`,
    if the message is not found in the internal message cache, then this event
    will not be called. Consider using :func:`on_raw_reaction_clear_emoji` instead.

    This requires :attr:`Intents.reactions` to be enabled.

    .. versionadded:: 1.3

    :param reaction: The reaction that got cleared.
    :type reaction: :class:`Reaction`

.. function:: on_raw_reaction_clear_emoji(payload)

    Called when a message has a specific reaction removed from it. Unlike :func:`on_reaction_clear_emoji` this is called
    regardless of the state of the internal message cache.

    This requires :attr:`Intents.reactions` to be enabled.

    .. versionadded:: 1.3

    :param payload: The raw event payload data.
    :type payload: :class:`RawReactionClearEmojiEvent`

.. function:: on_private_channel_delete(channel)
              on_private_channel_create(channel)

    Called whenever a private channel is deleted or created.

    This requires :attr:`Intents.messages` to be enabled.

    :param channel: The private channel that got created or deleted.
    :type channel: :class:`abc.PrivateChannel`

.. function:: on_private_channel_update(before, after)

    Called whenever a private group DM is updated. e.g. changed name or topic.

    This requires :attr:`Intents.messages` to be enabled.

    :param before: The updated group channel's old info.
    :type before: :class:`GroupChannel`
    :param after: The updated group channel's new info.
    :type after: :class:`GroupChannel`

.. function:: on_private_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a private channel.

    :param channel: The private channel that had its pins updated.
    :type channel: :class:`abc.PrivateChannel`
    :param last_pin: The latest message that was pinned as a naive datetime in UTC. Could be ``None``.
    :type last_pin: Optional[:class:`datetime.datetime`]

.. function:: on_guild_channel_delete(channel)
              on_guild_channel_create(channel)

    Called whenever a guild channel is deleted or created.

    Note that you can get the guild from :attr:`~abc.GuildChannel.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    :param channel: The guild channel that got created or deleted.
    :type channel: :class:`abc.GuildChannel`

.. function:: on_guild_channel_update(before, after)

    Called whenever a guild channel is updated. e.g. changed name, topic, permissions.

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The updated guild channel's old info.
    :type before: :class:`abc.GuildChannel`
    :param after: The updated guild channel's new info.
    :type after: :class:`abc.GuildChannel`

.. function:: on_guild_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a guild channel.

    This requires :attr:`Intents.guilds` to be enabled.

    :param channel: The guild channel that had its pins updated.
    :type channel: :class:`abc.GuildChannel`
    :param last_pin: The latest message that was pinned as a naive datetime in UTC. Could be ``None``.
    :type last_pin: Optional[:class:`datetime.datetime`]

.. function:: on_guild_integrations_update(guild)

    .. versionadded:: 1.4

    Called whenever an integration is created, modified, or removed from a guild.

    This requires :attr:`Intents.integrations` to be enabled.

    :param guild: The guild that had its integrations updated.
    :type guild: :class:`Guild`

.. function:: on_webhooks_update(channel)

    Called whenever a webhook is created, modified, or removed from a guild channel.

    This requires :attr:`Intents.webhooks` to be enabled.

    :param channel: The channel that had its webhooks updated.
    :type channel: :class:`abc.GuildChannel`

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Guild`.

    This requires :attr:`Intents.members` to be enabled.

    :param member: The member who joined or left.
    :type member: :class:`Member`

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - status
    - activity
    - nickname
    - roles
    - pending

    This requires :attr:`Intents.members` to be enabled.

    :param before: The updated member's old info.
    :type before: :class:`Member`
    :param after: The updated member's updated info.
    :type after: :class:`Member`

.. function:: on_user_update(before, after)

    Called when a :class:`User` updates their profile.

    This is called when one or more of the following things change:

    - avatar
    - username
    - discriminator

    This requires :attr:`Intents.members` to be enabled.

    :param before: The updated user's old info.
    :type before: :class:`User`
    :param after: The updated user's updated info.
    :type after: :class:`User`

.. function:: on_guild_join(guild)

    Called when a :class:`Guild` is either created by the :class:`Client` or when the
    :class:`Client` joins a guild.

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The guild that was joined.
    :type guild: :class:`Guild`

.. function:: on_guild_remove(guild)

    Called when a :class:`Guild` is removed from the :class:`Client`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the guild.
    - The client or the guild owner deleted the guild.

    In order for this event to be invoked then the :class:`Client` must have
    been part of the guild to begin with. (i.e. it is part of :attr:`Client.guilds`)

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The guild that got removed.
    :type guild: :class:`Guild`

.. function:: on_guild_update(before, after)

    Called when a :class:`Guild` updates, for example:

    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The guild prior to being updated.
    :type before: :class:`Guild`
    :param after: The guild after being updated.
    :type after: :class:`Guild`

.. function:: on_guild_role_create(role)
              on_guild_role_delete(role)

    Called when a :class:`Guild` creates or deletes a new :class:`Role`.

    To get the guild it belongs to, use :attr:`Role.guild`.

    This requires :attr:`Intents.guilds` to be enabled.

    :param role: The role that was created or deleted.
    :type role: :class:`Role`

.. function:: on_guild_role_update(before, after)

    Called when a :class:`Role` is changed guild-wide.

    This requires :attr:`Intents.guilds` to be enabled.

    :param before: The updated role's old info.
    :type before: :class:`Role`
    :param after: The updated role's updated info.
    :type after: :class:`Role`

.. function:: on_guild_emojis_update(guild, before, after)

    Called when a :class:`Guild` adds or removes :class:`Emoji`.

    This requires :attr:`Intents.emojis` to be enabled.

    :param guild: The guild who got their emojis updated.
    :type guild: :class:`Guild`
    :param before: A list of emojis before the update.
    :type before: Sequence[:class:`Emoji`]
    :param after: A list of emojis after the update.
    :type after: Sequence[:class:`Emoji`]

.. function:: on_guild_available(guild)
              on_guild_unavailable(guild)

    Called when a guild becomes available or unavailable. The guild must have
    existed in the :attr:`Client.guilds` cache.

    This requires :attr:`Intents.guilds` to be enabled.

    :param guild: The :class:`Guild` that has changed availability.

.. function:: on_voice_state_update(member, before, after)

    Called when a :class:`Member` changes their :class:`VoiceState`.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice channel.
    - A member leaves a voice channel.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a guild administrator.

    This requires :attr:`Intents.voice_states` to be enabled.

    :param member: The member whose voice states changed.
    :type member: :class:`Member`
    :param before: The voice state prior to the changes.
    :type before: :class:`VoiceState`
    :param after: The voice state after the changes.
    :type after: :class:`VoiceState`

.. function:: on_member_ban(guild, user)

    Called when user gets banned from a :class:`Guild`.

    This requires :attr:`Intents.bans` to be enabled.

    :param guild: The guild the user got banned from.
    :type guild: :class:`Guild`
    :param user: The user that got banned.
                 Can be either :class:`User` or :class:`Member` depending if
                 the user was in the guild or not at the time of removal.
    :type user: Union[:class:`User`, :class:`Member`]

.. function:: on_member_unban(guild, user)

    Called when a :class:`User` gets unbanned from a :class:`Guild`.

    This requires :attr:`Intents.bans` to be enabled.

    :param guild: The guild the user got unbanned from.
    :type guild: :class:`Guild`
    :param user: The user that got unbanned.
    :type user: :class:`User`

.. function:: on_invite_create(invite)

    Called when an :class:`Invite` is created.
    You must have the :attr:`~Permissions.manage_channels` permission to receive this.

    .. versionadded:: 1.3

    .. note::

        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

    This requires :attr:`Intents.invites` to be enabled.

    :param invite: The invite that was created.
    :type invite: :class:`Invite`

.. function:: on_invite_delete(invite)

    Called when an :class:`Invite` is deleted.
    You must have the :attr:`~Permissions.manage_channels` permission to receive this.

    .. versionadded:: 1.3

    .. note::

        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

        Outside of those two attributes, the only other attribute guaranteed to be
        filled by the Discord gateway for this event is :attr:`Invite.code`.

    This requires :attr:`Intents.invites` to be enabled.

    :param invite: The invite that was deleted.
    :type invite: :class:`Invite`

.. function:: on_group_join(channel, user)
              on_group_remove(channel, user)

    Called when someone joins or leaves a :class:`GroupChannel`.

    :param channel: The group that the user joined or left.
    :type channel: :class:`GroupChannel`
    :param user: The user that joined or left.
    :type user: :class:`User`

.. function:: on_relationship_add(relationship)
              on_relationship_remove(relationship)

    Called when a :class:`Relationship` is added or removed from the
    :class:`ClientUser`.

    .. deprecated:: 1.7

    :param relationship: The relationship that was added or removed.
    :type relationship: :class:`Relationship`

.. function:: on_relationship_update(before, after)

    Called when a :class:`Relationship` is updated, e.g. when you
    block a friend or a friendship is accepted.

    .. deprecated:: 1.7

    :param before: The previous relationship status.
    :type before: :class:`Relationship`
    :param after: The updated relationship status.
    :type after: :class:`Relationship`

.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: discord.utils.find

.. autofunction:: discord.utils.get

.. autofunction:: discord.utils.snowflake_time

.. autofunction:: discord.utils.oauth_url

.. autofunction:: discord.utils.remove_markdown

.. autofunction:: discord.utils.escape_markdown

.. autofunction:: discord.utils.escape_mentions

.. autofunction:: discord.utils.resolve_invite

.. autofunction:: discord.utils.resolve_template

.. autofunction:: discord.utils.sleep_until

Profile
---------

.. class:: Profile

    A namedtuple representing a user's Discord public profile.

    .. deprecated:: 1.7

    .. attribute:: user

        The :class:`User` the profile belongs to.

        :type: :class:`User`
    .. attribute:: premium

        A boolean indicating if the user has premium (i.e. Discord Nitro).

        :type: :class:`bool`
    .. attribute:: nitro

        An alias for :attr:`premium`.
    .. attribute:: premium_since

        A naive UTC datetime indicating how long the user has been premium since.
        This could be ``None`` if not applicable.

        :type: :class:`datetime.datetime`
    .. attribute:: staff

        A boolean indicating if the user is Discord Staff.

        :type: :class:`bool`
    .. attribute:: partner

        A boolean indicating if the user is a Discord Partner.

        :type: :class:`bool`
    .. attribute:: bug_hunter

        A boolean indicating if the user is a Bug Hunter.

        :type: :class:`bool`
    .. attribute:: early_supporter

        A boolean indicating if the user has had premium before 10 October, 2018.

        :type: :class:`bool`
    .. attribute:: hypesquad

        A boolean indicating if the user is in Discord HypeSquad.

        :type: :class:`bool`
    .. attribute:: hypesquad_houses

        A list of :class:`HypeSquadHouse` that the user is in.

        :type: List[:class:`HypeSquadHouse`]
    .. attribute:: team_user

        A boolean indicating if the user is in part of a team.

        .. versionadded:: 1.3

        :type: :class:`bool`

    .. attribute:: system

        A boolean indicating if the user is officially part of the Discord urgent message system.

        .. versionadded:: 1.3

        :type: :class:`bool`

    .. attribute:: mutual_guilds

        A list of :class:`Guild` that the :class:`ClientUser` shares with this
        user.

        :type: List[:class:`Guild`]

    .. attribute:: connected_accounts

        A list of dict objects indicating the accounts the user has connected.

        An example entry can be seen below: ::

            {"type": "twitch", "id": "92473777", "name": "discordapp"}

        :type: List[Dict[:class:`str`, :class:`str`]]

.. _discord-api-enums:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of an internal class which mimics the behaviour
of :class:`enum.Enum`.

.. class:: ChannelType

    Specifies the type of channel.

    .. attribute:: text

        A text channel.
    .. attribute:: voice

        A voice channel.
    .. attribute:: private

        A private text channel. Also called a direct message.
    .. attribute:: group

        A private group text channel.
    .. attribute:: category

        A category channel.
    .. attribute:: news

        A guild news channel.

    .. attribute:: store

        A guild store channel.

    .. attribute:: stage_voice

        A guild stage voice channel.

        .. versionadded:: 1.7

.. class:: MessageType

    Specifies the type of :class:`Message`. This is used to denote if a message
    is to be interpreted as a system message or a regular message.

    .. container:: operations

      .. describe:: x == y

          Checks if two messages are equal.
      .. describe:: x != y

          Checks if two messages are not equal.

    .. attribute:: default

        The default message type. This is the same as regular messages.
    .. attribute:: recipient_add

        The system message when a recipient is added to a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: recipient_remove

        The system message when a recipient is removed from a group private
        message, i.e. a private channel of type :attr:`ChannelType.group`.
    .. attribute:: call

        The system message denoting call state, e.g. missed call, started call,
        etc.
    .. attribute:: channel_name_change

        The system message denoting that a channel's name has been changed.
    .. attribute:: channel_icon_change

        The system message denoting that a channel's icon has been changed.
    .. attribute:: pins_add

        The system message denoting that a pinned message has been added to a channel.
    .. attribute:: new_member

        The system message denoting that a new member has joined a Guild.

    .. attribute:: premium_guild_subscription

        The system message denoting that a member has "nitro boosted" a guild.
    .. attribute:: premium_guild_tier_1

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 1.
    .. attribute:: premium_guild_tier_2

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 2.
    .. attribute:: premium_guild_tier_3

        The system message denoting that a member has "nitro boosted" a guild
        and it achieved level 3.
    .. attribute:: channel_follow_add

        The system message denoting that an announcement channel has been followed.

        .. versionadded:: 1.3
    .. attribute:: guild_stream

        The system message denoting that a member is streaming in the guild.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_disqualified

        The system message denoting that the guild is no longer eligible for Server
        Discovery.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_requalified

        The system message denoting that the guild has become eligible again for Server
        Discovery.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_grace_period_initial_warning

        The system message denoting that the guild has failed to meet the Server
        Discovery requirements for one week.

        .. versionadded:: 1.7
    .. attribute:: guild_discovery_grace_period_final_warning

        The system message denoting that the guild has failed to meet the Server
        Discovery requirements for 3 weeks in a row.

        .. versionadded:: 1.7

.. class:: ActivityType

    Specifies the type of :class:`Activity`. This is used to check how to
    interpret the activity itself.

    .. attribute:: unknown

        An unknown activity type. This should generally not happen.
    .. attribute:: playing

        A "Playing" activity type.
    .. attribute:: streaming

        A "Streaming" activity type.
    .. attribute:: listening

        A "Listening" activity type.
    .. attribute:: watching

        A "Watching" activity type.
    .. attribute:: custom

        A custom activity type.
    .. attribute:: competing

        A competing activity type.

        .. versionadded:: 1.5

.. class:: HypeSquadHouse

    Specifies the HypeSquad house a user belongs to.

    .. attribute:: bravery

        The "Bravery" house.
    .. attribute:: brilliance

        The "Brilliance" house.
    .. attribute:: balance

        The "Balance" house.

.. class:: VoiceRegion

    Specifies the region a voice server belongs to.

    .. attribute:: amsterdam

        The Amsterdam region.
    .. attribute:: brazil

        The Brazil region.
    .. attribute:: dubai

        The Dubai region.

        .. versionadded:: 1.3

    .. attribute:: eu_central

        The EU Central region.
    .. attribute:: eu_west

        The EU West region.
    .. attribute:: europe

        The Europe region.

        .. versionadded:: 1.3

    .. attribute:: frankfurt

        The Frankfurt region.
    .. attribute:: hongkong

        The Hong Kong region.
    .. attribute:: india

        The India region.

        .. versionadded:: 1.2

    .. attribute:: japan

        The Japan region.
    .. attribute:: london

        The London region.
    .. attribute:: russia

        The Russia region.
    .. attribute:: singapore

        The Singapore region.
    .. attribute:: southafrica

        The South Africa region.
    .. attribute:: south_korea

        The South Korea region.
    .. attribute:: sydney

        The Sydney region.
    .. attribute:: us_central

        The US Central region.
    .. attribute:: us_east

        The US East region.
    .. attribute:: us_south

        The US South region.
    .. attribute:: us_west

        The US West region.
    .. attribute:: vip_amsterdam

        The Amsterdam region for VIP guilds.
    .. attribute:: vip_us_east

        The US East region for VIP guilds.
    .. attribute:: vip_us_west

        The US West region for VIP guilds.

.. class:: VerificationLevel

    Specifies a :class:`Guild`\'s verification level, which is the criteria in
    which a member must meet before being able to send messages to the guild.

    .. container:: operations

        .. describe:: x == y

            Checks if two verification levels are equal.
        .. describe:: x != y

            Checks if two verification levels are not equal.
        .. describe:: x > y

            Checks if a verification level is higher than another.
        .. describe:: x < y

            Checks if a verification level is lower than another.
        .. describe:: x >= y

            Checks if a verification level is higher or equal to another.
        .. describe:: x <= y

            Checks if a verification level is lower or equal to another.

    .. attribute:: none

        No criteria set.
    .. attribute:: low

        Member must have a verified email on their Discord account.
    .. attribute:: medium

        Member must have a verified email and be registered on Discord for more
        than five minutes.
    .. attribute:: high

        Member must have a verified email, be registered on Discord for more
        than five minutes, and be a member of the guild itself for more than
        ten minutes.
    .. attribute:: table_flip

        An alias for :attr:`high`.
    .. attribute:: extreme

        Member must have a verified phone on their Discord account.

    .. attribute:: double_table_flip

        An alias for :attr:`extreme`.

    .. attribute:: very_high

        An alias for :attr:`extreme`.

        .. versionadded:: 1.4

.. class:: NotificationLevel

    Specifies whether a :class:`Guild` has notifications on for all messages or mentions only by default.

    .. attribute:: all_messages

        Members receive notifications for every message regardless of them being mentioned.
    .. attribute:: only_mentions

        Members receive notifications for messages they are mentioned in.

.. class:: ContentFilter

    Specifies a :class:`Guild`\'s explicit content filter, which is the machine
    learning algorithms that Discord uses to detect if an image contains
    pornography or otherwise explicit content.

    .. container:: operations

        .. describe:: x == y

            Checks if two content filter levels are equal.
        .. describe:: x != y

            Checks if two content filter levels are not equal.
        .. describe:: x > y

            Checks if a content filter level is higher than another.
        .. describe:: x < y

            Checks if a content filter level is lower than another.
        .. describe:: x >= y

            Checks if a content filter level is higher or equal to another.
        .. describe:: x <= y

            Checks if a content filter level is lower or equal to another.

    .. attribute:: disabled

        The guild does not have the content filter enabled.
    .. attribute:: no_role

        The guild has the content filter enabled for members without a role.
    .. attribute:: all_members

        The guild has the content filter enabled for every member.

.. class:: Status

    Specifies a :class:`Member` 's status.

    .. attribute:: online

        The member is online.
    .. attribute:: offline

        The member is offline.
    .. attribute:: idle

        The member is idle.
    .. attribute:: dnd

        The member is "Do Not Disturb".
    .. attribute:: do_not_disturb

        An alias for :attr:`dnd`.
    .. attribute:: invisible

        The member is "invisible". In reality, this is only used in sending
        a presence a la :meth:`Client.change_presence`. When you receive a
        user's presence this will be :attr:`offline` instead.


.. class:: AuditLogAction

    Represents the type of action being done for a :class:`AuditLogEntry`\,
    which is retrievable via :meth:`Guild.audit_logs`.

    .. attribute:: guild_update

        The guild has updated. Things that trigger this include:

        - Changing the guild vanity URL
        - Changing the guild invite splash
        - Changing the guild AFK channel or timeout
        - Changing the guild voice server region
        - Changing the guild icon
        - Changing the guild moderation settings
        - Changing things related to the guild widget

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Guild`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.afk_channel`
        - :attr:`~AuditLogDiff.system_channel`
        - :attr:`~AuditLogDiff.afk_timeout`
        - :attr:`~AuditLogDiff.default_message_notifications`
        - :attr:`~AuditLogDiff.explicit_content_filter`
        - :attr:`~AuditLogDiff.mfa_level`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.owner`
        - :attr:`~AuditLogDiff.splash`
        - :attr:`~AuditLogDiff.vanity_url_code`

    .. attribute:: channel_create

        A new channel was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        either a :class:`abc.GuildChannel` or :class:`Object` with an ID.

        A more filled out object in the :class:`Object` case can be found
        by using :attr:`~AuditLogEntry.after`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.overwrites`

    .. attribute:: channel_update

        A channel was updated. Things that trigger this include:

        - The channel name or topic was changed
        - The channel bitrate was changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`abc.GuildChannel` or :class:`Object` with an ID.

        A more filled out object in the :class:`Object` case can be found
        by using :attr:`~AuditLogEntry.after` or :attr:`~AuditLogEntry.before`.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.position`
        - :attr:`~AuditLogDiff.overwrites`
        - :attr:`~AuditLogDiff.topic`
        - :attr:`~AuditLogDiff.bitrate`

    .. attribute:: channel_delete

        A channel was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        an :class:`Object` with an ID.

        A more filled out object can be found by using the
        :attr:`~AuditLogEntry.before` object.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type`
        - :attr:`~AuditLogDiff.overwrites`

    .. attribute:: overwrite_create

        A channel permission overwrite was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`abc.GuildChannel` or :class:`Object` with an ID.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        either a :class:`Role` or :class:`Member`. If the object is not found
        then it is a :class:`Object` with an ID being filled, a name, and a
        ``type`` attribute set to either ``'role'`` or ``'member'`` to help
        dictate what type of ID it is.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: overwrite_update

        A channel permission overwrite was changed, this is typically
        when the permission values change.

        See :attr:`overwrite_create` for more information on how the
        :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
        are set.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: overwrite_delete

        A channel permission overwrite was deleted.

        See :attr:`overwrite_create` for more information on how the
        :attr:`~AuditLogEntry.target` and :attr:`~AuditLogEntry.extra` fields
        are set.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.deny`
        - :attr:`~AuditLogDiff.allow`
        - :attr:`~AuditLogDiff.id`
        - :attr:`~AuditLogDiff.type`

    .. attribute:: kick

        A member was kicked.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got kicked.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: member_prune

        A member prune was triggered.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        set to ``None``.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``delete_members_days``: An integer specifying how far the prune was.
        - ``members_removed``: An integer specifying how many members were removed.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: ban

        A member was banned.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got banned.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: unban

        A member was unbanned.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`User` who got unbanned.

        When this is the action, :attr:`~AuditLogEntry.changes` is empty.

    .. attribute:: member_update

        A member has updated. This triggers in the following situations:

        - A nickname was changed
        - They were server muted or deafened (or it was undo'd)

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who got updated.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.nick`
        - :attr:`~AuditLogDiff.mute`
        - :attr:`~AuditLogDiff.deaf`

    .. attribute:: member_role_update

        A member's role has been updated. This triggers when a member
        either gains a role or losses a role.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who got the role.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.roles`

    .. attribute:: member_move

        A member's voice channel has been updated. This triggers when a
        member is moved to a different voice channel.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the members were moved.
        - ``count``: An integer specifying how many members were moved.

        .. versionadded:: 1.3

    .. attribute:: member_disconnect

        A member's voice state has changed. This triggers when a
        member is force disconnected from voice.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with one attribute:

        - ``count``: An integer specifying how many members were disconnected.

        .. versionadded:: 1.3

    .. attribute:: bot_add

        A bot was added to the guild.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` which was added to the guild.

        .. versionadded:: 1.3

    .. attribute:: role_create

        A new role was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: role_update

        A role was updated. This triggers in the following situations:

        - The name has changed
        - The permissions have changed
        - The colour has changed
        - Its hoist/mentionable state has changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: role_delete

        A role was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Role` or a :class:`Object` with the ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.colour`
        - :attr:`~AuditLogDiff.mentionable`
        - :attr:`~AuditLogDiff.hoist`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.permissions`

    .. attribute:: invite_create

        An invite was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was created.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.max_age`
        - :attr:`~AuditLogDiff.code`
        - :attr:`~AuditLogDiff.temporary`
        - :attr:`~AuditLogDiff.inviter`
        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.uses`
        - :attr:`~AuditLogDiff.max_uses`

    .. attribute:: invite_update

        An invite was updated.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was updated.

    .. attribute:: invite_delete

        An invite was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Invite` that was deleted.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.max_age`
        - :attr:`~AuditLogDiff.code`
        - :attr:`~AuditLogDiff.temporary`
        - :attr:`~AuditLogDiff.inviter`
        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.uses`
        - :attr:`~AuditLogDiff.max_uses`

    .. attribute:: webhook_create

        A webhook was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type` (always set to ``1`` if so)

    .. attribute:: webhook_update

        A webhook was updated. This trigger in the following situations:

        - The webhook name changed
        - The webhook channel changed

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`

    .. attribute:: webhook_delete

        A webhook was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the webhook ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.channel`
        - :attr:`~AuditLogDiff.name`
        - :attr:`~AuditLogDiff.type` (always set to ``1`` if so)

    .. attribute:: emoji_create

        An emoji was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Emoji` or :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: emoji_update

        An emoji was updated. This triggers when the name has changed.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Emoji` or :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: emoji_delete

        An emoji was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the emoji ID.

        Possible attributes for :class:`AuditLogDiff`:

        - :attr:`~AuditLogDiff.name`

    .. attribute:: message_delete

        A message was deleted by a moderator. Note that this
        only triggers if the message was deleted by someone other than the author.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``count``: An integer specifying how many messages were deleted.
        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message got deleted.

    .. attribute:: message_bulk_delete

        Messages were bulk deleted by a moderator.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`TextChannel` or :class:`Object` with the ID of the channel that was purged.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with one attribute:

        - ``count``: An integer specifying how many messages were deleted.

        .. versionadded:: 1.3

    .. attribute:: message_pin

        A message was pinned in a channel.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message pinned.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was pinned.
        - ``message_id``: the ID of the message which was pinned.

        .. versionadded:: 1.3

    .. attribute:: message_unpin

        A message was unpinned in a channel.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message unpinned.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message was unpinned.
        - ``message_id``: the ID of the message which was unpinned.

        .. versionadded:: 1.3

    .. attribute:: integration_create

        A guild integration was created.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was created.

        .. versionadded:: 1.3

    .. attribute:: integration_update

        A guild integration was updated.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was updated.

        .. versionadded:: 1.3

    .. attribute:: integration_delete

        A guild integration was deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Object` with the integration ID of the integration which was deleted.

        .. versionadded:: 1.3

.. class:: AuditLogActionCategory

    Represents the category that the :class:`AuditLogAction` belongs to.

    This can be retrieved via :attr:`AuditLogEntry.category`.

    .. attribute:: create

        The action is the creation of something.

    .. attribute:: delete

        The action is the deletion of something.

    .. attribute:: update

        The action is the update of something.

.. class:: RelationshipType

    Specifies the type of :class:`Relationship`.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: friend

        You are friends with this user.

    .. attribute:: blocked

        You have blocked this user.

    .. attribute:: incoming_request

        The user has sent you a friend request.

    .. attribute:: outgoing_request

        You have sent a friend request to this user.


.. class:: UserContentFilter

    Represents the options found in ``Settings > Privacy & Safety > Safe Direct Messaging``
    in the Discord client.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: all_messages

        Scan all direct messages from everyone.

    .. attribute:: friends

        Scan all direct messages that aren't from friends.

    .. attribute:: disabled

        Don't scan any direct messages.


.. class:: FriendFlags

    Represents the options found in ``Settings > Privacy & Safety > Who Can Add You As A Friend``
    in the Discord client.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: noone

        This allows no-one to add you as a friend.

    .. attribute:: mutual_guilds

        This allows guild members to add you as a friend.

    .. attribute:: mutual_friends

        This allows friends of friends to add you as a friend.

    .. attribute:: guild_and_friends

        This is a superset of :attr:`mutual_guilds` and :attr:`mutual_friends`.

    .. attribute:: everyone

        This allows everyone to add you as a friend.


.. class:: PremiumType

    Represents the user's Discord Nitro subscription type.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: nitro

        Represents the Discord Nitro with Nitro-exclusive games.

    .. attribute:: nitro_classic

        Represents the Discord Nitro with no Nitro-exclusive games.


.. class:: Theme

    Represents the theme synced across all Discord clients.

    .. deprecated:: 1.7

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: light

        Represents the Light theme on Discord.

    .. attribute:: dark

        Represents the Dark theme on Discord.


.. class:: TeamMembershipState

    Represents the membership state of a team member retrieved through :func:`Bot.application_info`.

    .. versionadded:: 1.3

    .. attribute:: invited

        Represents an invited member.

    .. attribute:: accepted

        Represents a member currently in the team.

.. class:: WebhookType

    Represents the type of webhook that can be received.

    .. versionadded:: 1.3

    .. attribute:: incoming

        Represents a webhook that can post messages to channels with a token.

    .. attribute:: channel_follower

        Represents a webhook that is internally managed by Discord, used for following channels.

.. class:: ExpireBehaviour

    Represents the behaviour the :class:`Integration` should perform
    when a user's subscription has finished.

    There is an alias for this called ``ExpireBehavior``.

    .. versionadded:: 1.4

    .. attribute:: remove_role

        This will remove the :attr:`Integration.role` from the user
        when their subscription is finished.

    .. attribute:: kick

        This will kick the user when their subscription is finished.

.. class:: DefaultAvatar

    Represents the default avatar of a Discord :class:`User`

    .. attribute:: blurple

        Represents the default avatar with the color blurple.
        See also :attr:`Colour.blurple`
    .. attribute:: grey

        Represents the default avatar with the color grey.
        See also :attr:`Colour.greyple`
    .. attribute:: gray

        An alias for :attr:`grey`.
    .. attribute:: green

        Represents the default avatar with the color green.
        See also :attr:`Colour.green`
    .. attribute:: orange

        Represents the default avatar with the color orange.
        See also :attr:`Colour.orange`
    .. attribute:: red

        Represents the default avatar with the color red.
        See also :attr:`Colour.red`

.. class:: StickerType

    Represents the type of sticker images.

    .. versionadded:: 1.6

    .. attribute:: png

        Represents a sticker with a png image.

    .. attribute:: apng

        Represents a sticker with an apng image.

    .. attribute:: lottie

        Represents a sticker with a lottie image.

Async Iterator
----------------

Some API functions return an "async iterator". An async iterator is something that is
capable of being used in an :ref:`async for statement <py:async for>`.

These async iterators can be used as follows: ::

    async for elem in channel.history():
        # do stuff with elem here

Certain utilities make working with async iterators easier, detailed below.

.. class:: AsyncIterator

    Represents the "AsyncIterator" concept. Note that no such class exists,
    it is purely abstract.

    .. container:: operations

        .. describe:: async for x in y

            Iterates over the contents of the async iterator.


    .. method:: next()
        :async:

        |coro|

        Advances the iterator by one, if possible. If no more items are found
        then this raises :exc:`NoMoreItems`.

    .. method:: get(**attrs)
        :async:

        |coro|

        Similar to :func:`utils.get` except run over the async iterator.

        Getting the last message by a user named 'Dave' or ``None``: ::

            msg = await channel.history().get(author__name='Dave')

    .. method:: find(predicate)
        :async:

        |coro|

        Similar to :func:`utils.find` except run over the async iterator.

        Unlike :func:`utils.find`\, the predicate provided can be a
        |coroutine_link|_.

        Getting the last audit log with a reason or ``None``: ::

            def predicate(event):
                return event.reason is not None

            event = await guild.audit_logs().find(predicate)

        :param predicate: The predicate to use. Could be a |coroutine_link|_.
        :return: The first element that returns ``True`` for the predicate or ``None``.

    .. method:: flatten()
        :async:

        |coro|

        Flattens the async iterator into a :class:`list` with all the elements.

        :return: A list of every element in the async iterator.
        :rtype: list

    .. method:: chunk(max_size)

        Collects items into chunks of up to a given maximum size.
        Another :class:`AsyncIterator` is returned which collects items into
        :class:`list`\s of a given size. The maximum chunk size must be a positive integer.

        .. versionadded:: 1.6

        Collecting groups of users: ::

            async for leader, *users in reaction.users().chunk(3):
                ...

        .. warning::

            The last chunk collected may not be as large as ``max_size``.

        :param max_size: The size of individual chunks.
        :rtype: :class:`AsyncIterator`

    .. method:: map(func)

        This is similar to the built-in :func:`map <py:map>` function. Another
        :class:`AsyncIterator` is returned that executes the function on
        every element it is iterating over. This function can either be a
        regular function or a |coroutine_link|_.

        Creating a content iterator: ::

            def transform(message):
                return message.content

            async for content in channel.history().map(transform):
                message_length = len(content)

        :param func: The function to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

    .. method:: filter(predicate)

        This is similar to the built-in :func:`filter <py:filter>` function. Another
        :class:`AsyncIterator` is returned that filters over the original
        async iterator. This predicate can be a regular function or a |coroutine_link|_.

        Getting messages by non-bot accounts: ::

            def predicate(message):
                return not message.author.bot

            async for elem in channel.history().filter(predicate):
                ...

        :param predicate: The predicate to call on every element. Could be a |coroutine_link|_.
        :rtype: :class:`AsyncIterator`

.. _discord-api-audit-logs:

Audit Log Data
----------------

Working with :meth:`Guild.audit_logs` is a complicated process with a lot of machinery
involved. The library attempts to make it easy to use and friendly. In order to accomplish
this goal, it must make use of a couple of data classes that aid in this goal.

AuditLogEntry
~~~~~~~~~~~~~~~

.. attributetable:: AuditLogEntry

.. autoclass:: AuditLogEntry
    :members:

AuditLogChanges
~~~~~~~~~~~~~~~~~

.. attributetable:: AuditLogChanges

.. class:: AuditLogChanges

    An audit log change set.

    .. attribute:: before

        The old value. The attribute has the type of :class:`AuditLogDiff`.

        Depending on the :class:`AuditLogActionCategory` retrieved by
        :attr:`~AuditLogEntry.category`\, the data retrieved by this
        attribute differs:

        +----------------------------------------+---------------------------------------------------+
        |                Category                |                    Description                    |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.create` | All attributes are set to ``None``.               |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.delete` | All attributes are set the value before deletion. |
        +----------------------------------------+---------------------------------------------------+
        | :attr:`~AuditLogActionCategory.update` | All attributes are set the value before updating. |
        +----------------------------------------+---------------------------------------------------+
        | ``None``                               | No attributes are set.                            |
        +----------------------------------------+---------------------------------------------------+

    .. attribute:: after

        The new value. The attribute has the type of :class:`AuditLogDiff`.

        Depending on the :class:`AuditLogActionCategory` retrieved by
        :attr:`~AuditLogEntry.category`\, the data retrieved by this
        attribute differs:

        +----------------------------------------+--------------------------------------------------+
        |                Category                |                   Description                    |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.create` | All attributes are set to the created value      |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.delete` | All attributes are set to ``None``               |
        +----------------------------------------+--------------------------------------------------+
        | :attr:`~AuditLogActionCategory.update` | All attributes are set the value after updating. |
        +----------------------------------------+--------------------------------------------------+
        | ``None``                               | No attributes are set.                           |
        +----------------------------------------+--------------------------------------------------+

AuditLogDiff
~~~~~~~~~~~~~

.. attributetable:: AuditLogDiff

.. class:: AuditLogDiff

    Represents an audit log "change" object. A change object has dynamic
    attributes that depend on the type of action being done. Certain actions
    map to certain attributes being set.

    Note that accessing an attribute that does not match the specified action
    will lead to an attribute error.

    To get a list of attributes that have been set, you can iterate over
    them. To see a list of all possible attributes that could be set based
    on the action being done, check the documentation for :class:`AuditLogAction`,
    otherwise check the documentation below for all attributes that are possible.

    .. container:: operations

        .. describe:: iter(diff)

            Returns an iterator over (attribute, value) tuple of this diff.

    .. attribute:: name

        A name of something.

        :type: :class:`str`

    .. attribute:: icon

        A guild's icon hash. See also :attr:`Guild.icon`.

        :type: :class:`str`

    .. attribute:: splash

        The guild's invite splash hash. See also :attr:`Guild.splash`.

        :type: :class:`str`

    .. attribute:: owner

        The guild's owner. See also :attr:`Guild.owner`

        :type: Union[:class:`Member`, :class:`User`]

    .. attribute:: region

        The guild's voice region. See also :attr:`Guild.region`.

        :type: :class:`VoiceRegion`

    .. attribute:: afk_channel

        The guild's AFK channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.afk_channel`.

        :type: Union[:class:`VoiceChannel`, :class:`Object`]

    .. attribute:: system_channel

        The guild's system channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.system_channel`.

        :type: Union[:class:`TextChannel`, :class:`Object`]

    .. attribute:: afk_timeout

        The guild's AFK timeout. See :attr:`Guild.afk_timeout`.

        :type: :class:`int`

    .. attribute:: mfa_level

        The guild's MFA level. See :attr:`Guild.mfa_level`.

        :type: :class:`int`

    .. attribute:: widget_enabled

        The guild's widget has been enabled or disabled.

        :type: :class:`bool`

    .. attribute:: widget_channel

        The widget's channel.

        If this could not be found then it falls back to a :class:`Object`
        with the ID being set.

        :type: Union[:class:`TextChannel`, :class:`Object`]

    .. attribute:: verification_level

        The guild's verification level.

        See also :attr:`Guild.verification_level`.

        :type: :class:`VerificationLevel`

    .. attribute:: default_notifications

        The guild's default notification level.

        See also :attr:`Guild.default_notifications`.

        :type: :class:`NotificationLevel`

    .. attribute:: explicit_content_filter

        The guild's content filter.

        See also :attr:`Guild.explicit_content_filter`.

        :type: :class:`ContentFilter`

    .. attribute:: default_message_notifications

        The guild's default message notification setting.

        :type: :class:`int`

    .. attribute:: vanity_url_code

        The guild's vanity URL.

        See also :meth:`Guild.vanity_invite` and :meth:`Guild.edit`.

        :type: :class:`str`

    .. attribute:: position

        The position of a :class:`Role` or :class:`abc.GuildChannel`.

        :type: :class:`int`

    .. attribute:: type

        The type of channel or channel permission overwrite.

        If the type is an :class:`int`, then it is a type of channel which can be either
        ``0`` to indicate a text channel or ``1`` to indicate a voice channel.

        If the type is a :class:`str`, then it is a type of permission overwrite which
        can be either ``'role'`` or ``'member'``.

        :type: Union[:class:`int`, :class:`str`]

    .. attribute:: topic

        The topic of a :class:`TextChannel`.

        See also :attr:`TextChannel.topic`.

        :type: :class:`str`

    .. attribute:: bitrate

        The bitrate of a :class:`VoiceChannel`.

        See also :attr:`VoiceChannel.bitrate`.

        :type: :class:`int`

    .. attribute:: overwrites

        A list of permission overwrite tuples that represents a target and a
        :class:`PermissionOverwrite` for said target.

        The first element is the object being targeted, which can either
        be a :class:`Member` or :class:`User` or :class:`Role`. If this object
        is not found then it is a :class:`Object` with an ID being filled and
        a ``type`` attribute set to either ``'role'`` or ``'member'`` to help
        decide what type of ID it is.

        :type: List[Tuple[target, :class:`PermissionOverwrite`]]

    .. attribute:: roles

        A list of roles being added or removed from a member.

        If a role is not found then it is a :class:`Object` with the ID and name being
        filled in.

        :type: List[Union[:class:`Role`, :class:`Object`]]

    .. attribute:: nick

        The nickname of a member.

        See also :attr:`Member.nick`

        :type: Optional[:class:`str`]

    .. attribute:: deaf

        Whether the member is being server deafened.

        See also :attr:`VoiceState.deaf`.

        :type: :class:`bool`

    .. attribute:: mute

        Whether the member is being server muted.

        See also :attr:`VoiceState.mute`.

        :type: :class:`bool`

    .. attribute:: permissions

        The permissions of a role.

        See also :attr:`Role.permissions`.

        :type: :class:`Permissions`

    .. attribute:: colour
                   color

        The colour of a role.

        See also :attr:`Role.colour`

        :type: :class:`Colour`

    .. attribute:: hoist

        Whether the role is being hoisted or not.

        See also :attr:`Role.hoist`

        :type: :class:`bool`

    .. attribute:: mentionable

        Whether the role is mentionable or not.

        See also :attr:`Role.mentionable`

        :type: :class:`bool`

    .. attribute:: code

        The invite's code.

        See also :attr:`Invite.code`

        :type: :class:`str`

    .. attribute:: channel

        A guild channel.

        If the channel is not found then it is a :class:`Object` with the ID
        being set. In some cases the channel name is also set.

        :type: Union[:class:`abc.GuildChannel`, :class:`Object`]

    .. attribute:: inviter

        The user who created the invite.

        See also :attr:`Invite.inviter`.

        :type: :class:`User`

    .. attribute:: max_uses

        The invite's max uses.

        See also :attr:`Invite.max_uses`.

        :type: :class:`int`

    .. attribute:: uses

        The invite's current uses.

        See also :attr:`Invite.uses`.

        :type: :class:`int`

    .. attribute:: max_age

        The invite's max age in seconds.

        See also :attr:`Invite.max_age`.

        :type: :class:`int`

    .. attribute:: temporary

        If the invite is a temporary invite.

        See also :attr:`Invite.temporary`.

        :type: :class:`bool`

    .. attribute:: allow
                   deny

        The permissions being allowed or denied.

        :type: :class:`Permissions`

    .. attribute:: id

        The ID of the object being changed.

        :type: :class:`int`

    .. attribute:: avatar

        The avatar hash of a member.

        See also :attr:`User.avatar`.

        :type: :class:`str`

    .. attribute:: slowmode_delay

        The number of seconds members have to wait before
        sending another message in the channel.

        See also :attr:`TextChannel.slowmode_delay`.

        :type: :class:`int`

.. this is currently missing the following keys: reason and application_id
   I'm not sure how to about porting these

Webhook Support
------------------

discord.py offers support for creating, editing, and executing webhooks through the :class:`Webhook` class.

Webhook
~~~~~~~~~

.. attributetable:: Webhook

.. autoclass:: Webhook
    :members:

WebhookMessage
~~~~~~~~~~~~~~~~

.. attributetable:: WebhookMessage

.. autoclass:: WebhookMessage
    :members:

Adapters
~~~~~~~~~

Adapters allow you to change how the request should be handled. They all build on a single
interface, :meth:`WebhookAdapter.request`.

.. autoclass:: WebhookAdapter
    :members:

.. autoclass:: AsyncWebhookAdapter
    :members:

.. autoclass:: RequestsWebhookAdapter
    :members:

.. _discord_api_abcs:

Abstract Base Classes
-----------------------

An :term:`py:abstract base class` (also known as an ``abc``) is a class that models can inherit
to get their behaviour. The Python implementation of an :doc:`abc <py:library/abc>` is
slightly different in that you can register them at run-time. **Abstract base classes cannot be instantiated**.
They are mainly there for usage with :func:`py:isinstance` and :func:`py:issubclass`\.

This library has a module related to abstract base classes, some of which are actually from the :doc:`abc <py:library/abc>` standard
module, others which are not.

Snowflake
~~~~~~~~~~

.. attributetable:: discord.abc.Snowflake

.. autoclass:: discord.abc.Snowflake
    :members:

User
~~~~~

.. attributetable:: discord.abc.User

.. autoclass:: discord.abc.User
    :members:

PrivateChannel
~~~~~~~~~~~~~~~

.. attributetable:: discord.abc.PrivateChannel

.. autoclass:: discord.abc.PrivateChannel
    :members:

GuildChannel
~~~~~~~~~~~~~

.. attributetable:: discord.abc.GuildChannel

.. autoclass:: discord.abc.GuildChannel
    :members:

Messageable
~~~~~~~~~~~~

.. attributetable:: discord.abc.Messageable

.. autoclass:: discord.abc.Messageable
    :members:
    :exclude-members: history, typing

    .. automethod:: discord.abc.Messageable.history
        :async-for:

    .. automethod:: discord.abc.Messageable.typing
        :async-with:

Connectable
~~~~~~~~~~~~

.. attributetable:: discord.abc.Connectable

.. autoclass:: discord.abc.Connectable

.. _discord_api_models:

Discord Models
---------------

Models are classes that are received from Discord and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`User` instances
    nor should you modify the :class:`User` instance yourself.

    If you want to get one of these model classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of model classes that you receive from the events specified in the
    :ref:`discord-api-events`.

.. note::

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.


ClientUser
~~~~~~~~~~~~

.. attributetable:: ClientUser

.. autoclass:: ClientUser()
    :members:
    :inherited-members:

Relationship
~~~~~~~~~~~~~~

.. attributetable:: Relationship

.. autoclass:: Relationship()
    :members:

User
~~~~~

.. attributetable:: User

.. autoclass:: User()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Attachment
~~~~~~~~~~~

.. attributetable:: Attachment

.. autoclass:: Attachment()
    :members:

Asset
~~~~~

.. attributetable:: Asset

.. autoclass:: Asset()
    :members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message()
    :members:

DeletedReferencedMessage
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: DeletedReferencedMessage

.. autoclass:: DeletedReferencedMessage()
    :members:


Reaction
~~~~~~~~~

.. attributetable:: Reaction

.. autoclass:: Reaction()
    :members:
    :exclude-members: users

    .. automethod:: users
        :async-for:

CallMessage
~~~~~~~~~~~~

.. attributetable:: CallMessage

.. autoclass:: CallMessage()
    :members:

GroupCall
~~~~~~~~~~

.. attributetable:: GroupCall

.. autoclass:: GroupCall()
    :members:

Guild
~~~~~~

.. attributetable:: Guild

.. autoclass:: Guild()
    :members:
    :exclude-members: fetch_members, audit_logs

    .. automethod:: fetch_members
        :async-for:

    .. automethod:: audit_logs
        :async-for:

.. class:: BanEntry

    A namedtuple which represents a ban returned from :meth:`~Guild.bans`.

    .. attribute:: reason

        The reason this user was banned.

        :type: Optional[:class:`str`]
    .. attribute:: user

        The :class:`User` that was banned.

        :type: :class:`User`


Integration
~~~~~~~~~~~~

.. autoclass:: Integration()
    :members:

.. autoclass:: IntegrationAccount()
    :members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Spotify
~~~~~~~~

.. attributetable:: Spotify

.. autoclass:: Spotify()
    :members:

VoiceState
~~~~~~~~~~~

.. attributetable:: VoiceState

.. autoclass:: VoiceState()
    :members:

Emoji
~~~~~

.. attributetable:: Emoji

.. autoclass:: Emoji()
    :members:

PartialEmoji
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialEmoji

.. autoclass:: PartialEmoji()
    :members:

Role
~~~~~

.. attributetable:: Role

.. autoclass:: Role()
    :members:

RoleTags
~~~~~~~~~~

.. attributetable:: RoleTags

.. autoclass:: RoleTags()
    :members:

TextChannel
~~~~~~~~~~~~

.. attributetable:: TextChannel

.. autoclass:: TextChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

StoreChannel
~~~~~~~~~~~~~

.. attributetable:: StoreChannel

.. autoclass:: StoreChannel()
    :members:
    :inherited-members:

VoiceChannel
~~~~~~~~~~~~~

.. attributetable:: VoiceChannel

.. autoclass:: VoiceChannel()
    :members:
    :inherited-members:

StageChannel
~~~~~~~~~~~~~

.. attributetable:: StageChannel

.. autoclass:: StageChannel()
    :members:
    :inherited-members:

CategoryChannel
~~~~~~~~~~~~~~~~~

.. attributetable:: CategoryChannel

.. autoclass:: CategoryChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. attributetable:: DMChannel

.. autoclass:: DMChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

GroupChannel
~~~~~~~~~~~~

.. attributetable:: GroupChannel

.. autoclass:: GroupChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

PartialInviteGuild
~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteGuild

.. autoclass:: PartialInviteGuild()
    :members:

PartialInviteChannel
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialInviteChannel

.. autoclass:: PartialInviteChannel()
    :members:

Invite
~~~~~~~

.. attributetable:: Invite

.. autoclass:: Invite()
    :members:

Template
~~~~~~~~~

.. attributetable:: Template

.. autoclass:: Template()
    :members:

WidgetChannel
~~~~~~~~~~~~~~~

.. attributetable:: WidgetChannel

.. autoclass:: WidgetChannel()
    :members:

WidgetMember
~~~~~~~~~~~~~

.. attributetable:: WidgetMember

.. autoclass:: WidgetMember()
    :members:
    :inherited-members:

Widget
~~~~~~~

.. attributetable:: Widget

.. autoclass:: Widget()
    :members:

Sticker
~~~~~~~~~~~~~~~

.. attributetable:: Sticker

.. autoclass:: Sticker()
    :members:

RawMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageDeleteEvent

.. autoclass:: RawMessageDeleteEvent()
    :members:

RawBulkMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawBulkMessageDeleteEvent

.. autoclass:: RawBulkMessageDeleteEvent()
    :members:

RawMessageUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawMessageUpdateEvent

.. autoclass:: RawMessageUpdateEvent()
    :members:

RawReactionActionEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionActionEvent

.. autoclass:: RawReactionActionEvent()
    :members:

RawReactionClearEvent
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEvent

.. autoclass:: RawReactionClearEvent()
    :members:

RawReactionClearEmojiEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: RawReactionClearEmojiEvent

.. autoclass:: RawReactionClearEmojiEvent()
    :members:


.. _discord_api_data:

Data Classes
--------------

Some classes are just there to be data containers, this lists them.

Unlike :ref:`models <discord_api_models>` you are allowed to create
most of these yourself, even if they can also be used to hold attributes.

Nearly all classes here have :ref:`py:slots` defined which means that it is
impossible to have dynamic attributes to the data classes.

The only exception to this rule is :class:`abc.Snowflake`, which is made with
dynamic attributes in mind.


Object
~~~~~~~

.. attributetable:: Object

.. autoclass:: Object
    :members:

Embed
~~~~~~

.. attributetable:: Embed

.. autoclass:: Embed
    :members:

AllowedMentions
~~~~~~~~~~~~~~~~~

.. attributetable:: AllowedMentions

.. autoclass:: AllowedMentions
    :members:

MessageReference
~~~~~~~~~~~~~~~~~

.. attributetable:: MessageReference

.. autoclass:: MessageReference
    :members:

PartialMessage
~~~~~~~~~~~~~~~~~

.. attributetable:: PartialMessage

.. autoclass:: PartialMessage
    :members:

Intents
~~~~~~~~~~

.. attributetable:: Intents

.. autoclass:: Intents
    :members:

MemberCacheFlags
~~~~~~~~~~~~~~~~~~

.. attributetable:: MemberCacheFlags

.. autoclass:: MemberCacheFlags
    :members:

File
~~~~~

.. attributetable:: File

.. autoclass:: File
    :members:

Colour
~~~~~~

.. attributetable:: Colour

.. autoclass:: Colour
    :members:

BaseActivity
~~~~~~~~~~~~~~

.. attributetable:: BaseActivity

.. autoclass:: BaseActivity
    :members:

Activity
~~~~~~~~~

.. attributetable:: Activity

.. autoclass:: Activity
    :members:

Game
~~~~~

.. attributetable:: Game

.. autoclass:: Game
    :members:

Streaming
~~~~~~~~~~~

.. attributetable:: Streaming

.. autoclass:: Streaming
    :members:

CustomActivity
~~~~~~~~~~~~~~~

.. attributetable:: CustomActivity

.. autoclass:: CustomActivity
    :members:

Permissions
~~~~~~~~~~~~

.. attributetable:: Permissions

.. autoclass:: Permissions
    :members:

PermissionOverwrite
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PermissionOverwrite

.. autoclass:: PermissionOverwrite
    :members:

ShardInfo
~~~~~~~~~~~

.. attributetable:: ShardInfo

.. autoclass:: ShardInfo()
    :members:

SystemChannelFlags
~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SystemChannelFlags

.. autoclass:: SystemChannelFlags()
    :members:

MessageFlags
~~~~~~~~~~~~

.. attributetable:: MessageFlags

.. autoclass:: MessageFlags()
    :members:

PublicUserFlags
~~~~~~~~~~~~~~~

.. attributetable:: PublicUserFlags

.. autoclass:: PublicUserFlags()
    :members:

Exceptions
------------

The following exceptions are thrown by the library.

.. autoexception:: DiscordException

.. autoexception:: ClientException

.. autoexception:: LoginFailure

.. autoexception:: NoMoreItems

.. autoexception:: HTTPException
    :members:

.. autoexception:: Forbidden

.. autoexception:: NotFound

.. autoexception:: DiscordServerError

.. autoexception:: InvalidData

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

.. autoexception:: PrivilegedIntentsRequired

.. autoexception:: discord.opus.OpusError

.. autoexception:: discord.opus.OpusNotLoaded

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`Exception`
        - :exc:`DiscordException`
            - :exc:`ClientException`
                - :exc:`InvalidData`
                - :exc:`InvalidArgument`
                - :exc:`LoginFailure`
                - :exc:`ConnectionClosed`
                - :exc:`PrivilegedIntentsRequired`
            - :exc:`NoMoreItems`
            - :exc:`GatewayNotFound`
            - :exc:`HTTPException`
                - :exc:`Forbidden`
                - :exc:`NotFound`
                - :exc:`DiscordServerError`
