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

There are two main ways to query version information about the library.

.. data:: version_info

    A named tuple that is similar to `sys.version_info`_.

    Just like `sys.version_info`_ the valid values for ``releaselevel`` are
    'alpha', 'beta', 'candidate' and 'final'.

    .. _sys.version_info: https://docs.python.org/3.5/library/sys.html#sys.version_info

.. data:: __version__

    A string representation of the version. e.g. ``'0.10.0-alpha0'``.

Client
-------

.. autoclass:: Client
    :members:

.. autoclass:: AutoShardedClient
    :members:

Voice
------

.. autoclass:: VoiceClient
    :members:

.. autoclass:: AudioSource
    :members:

.. autoclass:: PCMAudio
    :members:

.. autoclass:: FFmpegPCMAudio
    :members:

.. autoclass:: PCMVolumeTransformer
    :members:

Opus Library
~~~~~~~~~~~~~

.. autofunction:: discord.opus.load_opus

.. autofunction:: discord.opus.is_loaded

.. _discord-api-events:

Event Reference
---------------

This page outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord

    class MyClient(discord.Client):
        async def on_message(self, message):
            if message.author != self.user:
                return

            if message.content.startswith('$hello'):
                await message.channel.send('Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |corourl|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must either be ``async def``
    functions or in 3.4 decorated with :func:`asyncio.coroutine`.

    The following two functions are examples of coroutine functions: ::

        async def on_ready():
            pass

        @asyncio.coroutine
        def on_ready():
            pass

.. function:: on_connect()

    Called when the client has successfully connected to Discord. This is not
    the same as the client being fully prepared, see :func:`on_ready` for that.

    The warnings on :func:`on_ready` also apply.

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

.. function:: on_resumed()

    Called when the client has resumed a session.

.. function:: on_error(event, \*args, \*\*kwargs)

    Usually when an event raises an uncaught exception, a traceback is
    printed to stderr and the exception is ignored. If you want to
    change this behaviour and handle the exception for whatever reason
    yourself, this event can be overridden. Which, when done, will
    supress the default action of printing the traceback.

    The information of the exception rasied and the exception itself can
    be retreived with a standard call to ``sys.exc_info()``.

    If you want exception to propogate out of the :class:`Client` class
    you can define an ``on_error`` handler consisting of a single empty
    ``raise`` statement.  Exceptions raised by ``on_error`` will not be
    handled in any way by :class:`Client`.

    :param event: The name of the event that raised the exception.
    :param args: The positional arguments for the event that raised the
        exception.
    :param kwargs: The keyword arguments for the event that raised the
        execption.

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

.. function:: on_socket_raw_send(payload)

    Called whenever a send operation is done on the WebSocket before the
    message is sent. The passed parameter is the message that is being
    sent to the WebSocket.

    This is only really useful for grabbing the WebSocket stream and
    debugging purposes.

    .. note::

        This is only for the messages received from the client
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

    :param channel: The location where the typing originated from.
    :param user: The user that started typing.
    :param when: A ``datetime.datetime`` object representing when typing started.

.. function:: on_message(message)

    Called when a :class:`Message` is created and sent.

    .. warning::

        Your bot's own messages and private messages are sent through this
        event. This can lead cases of 'recursion' depending on how your bot was
        programmed. If you want the bot to not reply to itself, consider
        checking the user IDs. Note that :class:`~ext.commands.Bot` does not
        have this problem.

    :param message: A :class:`Message` of the current message.

.. function:: on_message_delete(message)

    Called when a message is deleted. If the message is not found in the
    :attr:`Client.messages` cache, then these events will not be called. This
    happens if the message is too old or the client is participating in high
    traffic guilds. To fix this, increase the ``max_messages`` option of
    :class:`Client`.

    :param message: A :class:`Message` of the deleted message.

.. function:: on_raw_message_delete(message_id, channel_id)

    Called when a message is deleted. Unlike :func:`on_message_delete`, this is
    called regardless of the message being in the internal message cache or not.

    :param int message_id: The message ID of the message being deleted.
    :param int channel_id: The channel ID where the message was deleted.

.. function:: on_raw_bulk_message_delete(message_ids, channel_id)

    Called when a bulk delete is triggered. This event is called regardless
    of the message IDs being in the internal message cache or not.

    :param message_ids: The message IDs that were bulk deleted.
    :type message_ids: Set[int]
    :param int channel_id: The channel ID where the messages were deleted.

.. function:: on_message_edit(before, after)

    Called when a :class:`Message` receives an update event. If the message is not found
    in the :attr:`Client.messages` cache, then these events will not be called.
    This happens if the message is too old or the client is participating in high
    traffic guilds. To fix this, increase the ``max_messages`` option of :class:`Client`.

    The following non-exhaustive cases trigger this event:

    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.

        - For performance reasons, the embed server does not do this in a "consistent" manner.

    - A call message has received an update to its participants or ending time.

    :param before: A :class:`Message` of the previous version of the message.
    :param after: A :class:`Message` of the current version of the message.

.. function:: on_raw_message_edit(message_id, data)

    Called when a message is edited. Unlike :func:`on_message_edit`, this is called
    regardless of the state of the internal message cache.

    Due to the inherently raw nature of this event, the data parameter coincides with
    the raw data given by the `gateway <https://discordapp.com/developers/docs/topics/gateway#message-update>`_

    Since the data payload can be partial, care must be taken when accessing stuff in the dictionary.
    One example of a common case of partial data is when the ``'content'`` key is inaccessible. This
    denotes an "embed" only edit, which is an edit in which only the embeds are updated by the Discord
    embed server.

    :param int message_id: The message ID of the message being edited.
    :param dict data: The raw data being passed to the MESSAGE_UPDATE gateway event.

.. function:: on_reaction_add(reaction, user)

    Called when a message has a reaction added to it. Similar to on_message_edit,
    if the message is not found in the :attr:`Client.messages` cache, then this
    event will not be called.

    .. note::

        To get the :class:`Message` being reacted, access it via :attr:`Reaction.message`.

    :param reaction: A :class:`Reaction` showing the current state of the reaction.
    :param user: A :class:`User` or :class:`Member` of the user who added the reaction.

.. function:: on_raw_reaction_add(emoji, message_id, channel_id, user_id)

    Called when a reaction has a reaction added. Unlike :func:`on_reaction_add`, this is
    called regardless of the state of the internal message cache.

    :param emoji: The custom or unicode emoji being reacted to.
    :type emoji: :class:`PartialEmoji`
    :param int message_id: The message ID of the message being reacted.
    :param int channel_id: The channel ID where the message belongs to.
    :param int user_id: The user ID of the user who did the reaction.

.. function:: on_reaction_remove(reaction, user)

    Called when a message has a reaction removed from it. Similar to on_message_edit,
    if the message is not found in the :attr:`Client.messages` cache, then this event
    will not be called.

    .. note::

        To get the message being reacted, access it via :attr:`Reaction.message`.

    :param reaction: A :class:`Reaction` showing the current state of the reaction.
    :param user: A :class:`User` or :class:`Member` of the user who removed the reaction.

.. function:: on_raw_reaction_remove(emoji, message_id, channel_id, user_id)

    Called when a reaction has a reaction removed. Unlike :func:`on_reaction_remove`, this is
    called regardless of the state of the internal message cache.

    :param emoji: The custom or unicode emoji that got un-reacted.
    :type emoji: :class:`PartialEmoji`
    :param int message_id: The message ID of the message being un-reacted.
    :param int channel_id: The channel ID where the message belongs to.
    :param int user_id: The user ID of the user who removed the reaction.

.. function:: on_reaction_clear(message, reactions)

    Called when a message has all its reactions removed from it. Similar to :func:`on_message_edit`,
    if the message is not found in the :attr:`Client.messages` cache, then this event
    will not be called.

    :param message: The :class:`Message` that had its reactions cleared.
    :param reactions: A list of :class:`Reaction`\s that were removed.

.. function:: on_raw_reaction_clear(message_id, channel_id)

    Called when a message has all its reactions removed. Unlike :func:`on_reaction_clear`,
    this is called regardless of the state of the internal message cache.

    :param int message_id: The message ID of the message having its reactions removed.
    :param int channel_id: The channel ID of where the message belongs to.

.. function:: on_private_channel_delete(channel)
              on_private_channel_create(channel)

    Called whenever a private channel is deleted or created.

    :param channel: The :class:`abc.PrivateChannel` that got created or deleted.

.. function:: on_private_channel_update(before, after)

    Called whenever a private group DM is updated. e.g. changed name or topic.

    :param before: The :class:`GroupChannel` that got updated with the old info.
    :param after: The :class:`GroupChannel` that got updated with the updated info.

.. function:: on_private_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a private channel.

    :param channel: The :class:`abc.PrivateChannel` that had it's pins updated.
    :param last_pin: A ``datetime.datetime`` object representing when the latest message
                     was pinned or ``None`` if there are no pins.

.. function:: on_guild_channel_delete(channel)
              on_guild_channel_create(channel)

    Called whenever a guild channel is deleted or created.

    Note that you can get the guild from :attr:`~abc.GuildChannel.guild`.

    :param channel: The :class:`abc.GuildChannel` that got created or deleted.

.. function:: on_guild_channel_update(before, after)

    Called whenever a guild channel is updated. e.g. changed name, topic, permissions.

    :param before: The :class:`abc.GuildChannel` that got updated with the old info.
    :param after: The :class:`abc.GuildChannel` that got updated with the updated info.

.. function:: on_guild_channel_pins_update(channel, last_pin)

    Called whenever a message is pinned or unpinned from a guild channel.

    :param channel: The :class:`abc.GuildChannel` that had it's pins updated.
    :param last_pin: A ``datetime.datetime`` object representing when the latest message
                     was pinned or ``None`` if there are no pins.

.. function:: on_member_join(member)
              on_member_remove(member)

    Called when a :class:`Member` leaves or joins a :class:`Guild`.

    :param member: The :class:`Member` that joined or left.

.. function:: on_member_update(before, after)

    Called when a :class:`Member` updates their profile.

    This is called when one or more of the following things change:

    - status
    - game playing
    - avatar
    - nickname
    - roles

    :param before: The :class:`Member` that updated their profile with the old info.
    :param after: The :class:`Member` that updated their profile with the updated info.

.. function:: on_guild_join(guild)

    Called when a :class:`Guild` is either created by the :class:`Client` or when the
    :class:`Client` joins a guild.

    :param guild: The :class:`Guild` that was joined.

.. function:: on_guild_remove(guild)

    Called when a :class:`Guild` is removed from the :class:`Client`.

    This happens through, but not limited to, these circumstances:

    - The client got banned.
    - The client got kicked.
    - The client left the guild.
    - The client or the guild owner deleted the guild.

    In order for this event to be invoked then the :class:`Client` must have
    been part of the guild to begin with. (i.e. it is part of :attr:`Client.guilds`)

    :param guild: The :class:`Guild` that got removed.

.. function:: on_guild_update(before, after)

    Called when a :class:`Guild` updates, for example:

    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc

    :param before: The :class:`Guild` prior to being updated.
    :param after: The :class:`Guild` after being updated.

.. function:: on_guild_role_create(role)
              on_guild_role_delete(role)

    Called when a :class:`Guild` creates or deletes a new :class:`Role`.

    To get the guild it belongs to, use :attr:`Role.guild`.

    :param role: The :class:`Role` that was created or deleted.

.. function:: on_guild_role_update(before, after)

    Called when a :class:`Role` is changed guild-wide.

    :param before: The :class:`Role` that updated with the old info.
    :param after: The :class:`Role` that updated with the updated info.

.. function:: on_guild_emojis_update(guild, before, after)

    Called when a :class:`Guild` adds or removes :class:`Emoji`.

    :param guild: The :class:`Guild` who got their emojis updated.
    :param before: A list of :class:`Emoji` before the update.
    :param after: A list of :class:`Emoji` after the update.

.. function:: on_guild_available(guild)
              on_guild_unavailable(guild)

    Called when a guild becomes available or unavailable. The guild must have
    existed in the :attr:`Client.guilds` cache.

    :param guild: The :class:`Guild` that has changed availability.

.. function:: on_voice_state_update(member, before, after)

    Called when a :class:`Member` changes their :class:`VoiceState`.

    The following, but not limited to, examples illustrate when this event is called:

    - A member joins a voice room.
    - A member leaves a voice room.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a guild administrator.

    :param member: The :class:`Member` whose voice states changed.
    :param before: The :class:`VoiceState` prior to the changes.
    :param after: The :class:`VoiceState` after to the changes.

.. function:: on_member_ban(guild, user)

    Called when user gets banned from a :class:`Guild`.

    :param guild: The :class:`Guild` the user got banned from.
    :param user: The user that got banned.
                 Can be either :class:`User` or :class:`Member` depending if
                 the user was in the guild or not at the time of removal.

.. function:: on_member_unban(guild, user)

    Called when a :class:`User` gets unbanned from a :class:`Guild`.

    :param guild: The :class:`Guild` the user got unbanned from.
    :param user: The :class:`User` that got unbanned.

.. function:: on_group_join(channel, user)
              on_group_remove(channel, user)

    Called when someone joins or leaves a group, i.e. a :class:`PrivateChannel`
    with a :attr:`PrivateChannel.type` of :attr:`ChannelType.group`.

    :param channel: The group that the user joined or left.
    :param user: The user that joined or left.

.. function:: on_relationship_add(relationship)
              on_relationship_remove(relationship)

    Called when a :class:`Relationship` is added or removed from the
    :class:`ClientUser`.

    :param relationship: The relationship that was added or removed.

.. function:: on_relationship_update(before, after)

    Called when a :class:`Relationship` is updated, e.g. when you
    block a friend or a friendship is accepted.

    :param before: The previous relationship status.
    :param after: The updated relationship status.

.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: discord.utils.find

.. autofunction:: discord.utils.get

.. autofunction:: discord.utils.snowflake_time

.. autofunction:: discord.utils.oauth_url

Application Info
------------------

.. class:: AppInfo

    A namedtuple representing the bot's application info.

    .. attribute:: id

        The application's ``client_id``.
    .. attribute:: name

        The application's name.
    .. attribute:: description

        The application's description
    .. attribute:: icon

        The application's icon hash if it exists, ``None`` otherwise.
    .. attribute:: icon_url

        A property that retrieves the application's icon URL if it exists.

        If it doesn't exist an empty string is returned.
    .. attribute:: owner

        The owner of the application. This is a :class:`User` instance
        with the owner's information at the time of the call.

Profile
---------

.. class:: Profile

    A namedtuple representing a user's Discord public profile.

    .. attribute:: user

        The :class:`User` the profile belongs to.
    .. attribute:: premium

        A boolean indicating if the user has premium (i.e. Discord Nitro).
    .. attribute:: nitro

        An alias for :attr:`premium`.
    .. attribute:: premium_since

        A naive UTC datetime indicating how long the user has been premium since.
        This could be ``None`` if not applicable.
    .. attribute:: staff

        A boolean indicating if the user is Discord Staff.
    .. attribute:: partner

        A boolean indicating if the user is a Discord Partner.
    .. attribute:: hypesquad

        A boolean indicating if the user is in Discord HypeSquad.
    .. attribute:: mutual_guilds

        A list of :class:`Guild` that the :class:`ClientUser` shares with this
        user.
    .. attribute:: connected_accounts

        A list of dict objects indicating the accounts the user has connected.

        An example entry can be seen below: ::

            {type: "twitch", id: "92473777", name: "discordapp"}

.. _discord-api-enums:

Enumerations
-------------

The API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of `enum`_.

.. _enum: https://docs.python.org/3/library/enum.html

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

.. class:: MessageType

    Specifies the type of :class:`Message`. This is used to denote if a message
    is to be interpreted as a system message or a regular message.

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

.. class:: VoiceRegion

    Specifies the region a voice server belongs to.

    .. attribute:: us_west

        The US West region.
    .. attribute:: us_east

        The US East region.
    .. attribute:: us_south

        The US South region.
    .. attribute:: us_central

        The US Central region.
    .. attribute:: eu_west

        The EU West region.
    .. attribute:: eu_central

        The EU Central region.
    .. attribute:: singapore

        The Singapore region.
    .. attribute:: london

        The London region.
    .. attribute:: sydney

        The Sydney region.
    .. attribute:: amsterdam

        The Amsterdam region.
    .. attribute:: frankfurt

        The Frankfurt region.

    .. attribute:: brazil

        The Brazil region.
    .. attribute:: hongkong

        The Hong Kong region.
    .. attribute:: russia

        The Russia region.
    .. attribute:: vip_us_east

        The US East region for VIP guilds.
    .. attribute:: vip_us_west

        The US West region for VIP guilds.
    .. attribute:: vip_amsterdam

        The Amsterdam region for VIP guilds.

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

.. class:: RelationshipType

    Specifies the type of :class:`Relationship`

    .. attribute:: friend

        You are friends with this user.
    .. attribute:: blocked

        You have blocked this user.
    .. attribute:: incoming_request

        The user has sent you a friend request.
    .. attribute:: outgoing_request

        You have sent a friend request to this user.


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
        set to `None`.

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
        only triggers if the message was deleted by either bulk delete
        or deletion by someone other than the author.

        When this is the action, the type of :attr:`~AuditLogEntry.target` is
        the :class:`Member` or :class:`User` who had their message deleted.

        When this is the action, the type of :attr:`~AuditLogEntry.extra` is
        set to an unspecified proxy object with two attributes:

        - ``count``: An integer specifying how many messages were deleted.
        - ``channel``: A :class:`TextChannel` or :class:`Object` with the channel ID where the message got deleted.


.. class:: AuditLogActionCategory

    Represents the category that the :class:`AuditLogAction` belongs to.

    This can be retrieved via :attr:`AuditLogEntry.category`.

    .. attribute:: create

        The action is the creation of something.

    .. attribute:: delete

        The action is the deletion of something.

    .. attribute:: update

        The action is the update of something.



Async Iterator
----------------

Some API functions return an "async iterator". An async iterator is something that is
capable of being used in an `async for <https://docs.python.org/3/reference/compound_stmts.html#the-async-for-statement>`_
statement.

These async iterators can be used as follows in 3.5 or higher: ::

    async for elem in channel.history():
        # do stuff with elem here

If you are using 3.4 however, you will have to use the more verbose way: ::

    iterator = channel.history() # or whatever returns an async iterator
    while True:
        try:
            item = yield from iterator.next()
        except discord.NoMoreItems:
            break

        # do stuff with item here

Certain utilities make working with async iterators easier, detailed below.

.. class:: AsyncIterator

    Represents the "AsyncIterator" concept. Note that no such class exists,
    it is purely abstract.

    .. container:: operations

        .. describe:: async for x in y

            Iterates over the contents of the async iterator. Note
            that this is only available in Python 3.5 or higher.


    .. comethod:: next()

        |coro|

        Advances the iterator by one, if possible. If no more items are found
        then this raises :exc:`NoMoreItems`.

    .. comethod:: get(**attrs)

        |coro|

        Similar to :func:`utils.get` except run over the async iterator.

        Getting the last message by a user named 'Dave' or ``None``: ::

            msg = await channel.history().get(author__name='Dave')

    .. comethod:: find(predicate)

        |coro|

        Similar to :func:`utils.find` except run over the async iterator.

        Unlike :func:`utils.find`\, the predicate provided can be a
        coroutine.

        Getting the last audit log with a reason or ``None``: ::

            def predicate(event):
                return event.reason is not None

            event = await guild.audit_logs().find(predicate)

        :param predicate: The predicate to use. Can be a coroutine.
        :return: The first element that returns ``True`` for the predicate or ``None``.

    .. comethod:: flatten()

        |coro|

        Flattens the async iterator into a :class:`list` with all the elements.

        :return: A list of every element in the async iterator.
        :rtype: list

    .. method:: map(func)

        This is similar to the built-in :func:`map <python:map>` function. Another
        :class:`AsyncIterator` is returned that executes the function on
        every element it is iterating over. This function can either be a
        regular function or a coroutine.

        Creating a content iterator: ::

            def transform(message):
                return message.content

            async for content in channel.history().map(transform):
                message_length = len(content)

        :param func: The function to call on every element. Could be a coroutine.
        :return: An async iterator.

    .. method:: filter(predicate)

        This is similar to the built-in :func:`filter <python:filter>` function. Another
        :class:`AsyncIterator` is returned that filters over the original
        async iterator. This predicate can be a regular function or a coroutine.

        Getting messages by non-bot accounts: ::

            def predicate(message):
                return not message.author.bot

            async for elem in channel.history().filter(predicate):
                ...

        :param predicate: The predicate to call on every element. Could be a coroutine.
        :return: An async iterator.


Audit Log Data
----------------

Working with :meth:`Guild.audit_logs` is a complicated process with a lot of machinery
involved. The library attempts to make it easy to use and friendly. In order to accomplish
this goal, it must make use of a couple of data classes that aid in this goal.

.. autoclass:: AuditLogEntry
    :members:

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

    .. describe:: iter(diff)

        Return an iterator over (attribute, value) tuple of this diff.

    .. attribute:: name

        :class:`str` – A name of something.

    .. attribute:: icon

        :class:`str` – A guild's icon hash. See also :attr:`Guild.icon`.

    .. attribute:: splash

        :class:`str` – The guild's invite splash hash. See also :attr:`Guild.splash`.

    .. attribute:: owner

        Union[:class:`Member`, :class:`User`] – The guild's owner. See also :attr:`Guild.owner`

    .. attribute:: region

        :class:`GuildRegion` – The guild's voice region. See also :attr:`Guild.region`.

    .. attribute:: afk_channel

        Union[:class:`VoiceChannel`, :class:`Object`] – The guild's AFK channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.afk_channel`.

    .. attribute:: system_channel

        Union[:class:`TextChannel`, :class:`Object`] – The guild's system channel.

        If this could not be found, then it falls back to a :class:`Object`
        with the ID being set.

        See :attr:`Guild.system_channel`.

    .. attribute:: afk_timeout

        :class:`int` – The guild's AFK timeout. See :attr:`Guild.afk_timeout`.

    .. attribute:: mfa_level

        :class:`int` - The guild's MFA level. See :attr:`Guild.mfa_level`.

    .. attribute:: widget_enabled

        :class:`bool` – The guild's widget has been enabled or disabled.

    .. attribute:: widget_channel

        Union[:class:`TextChannel`, :class:`Object`] – The widget's channel.

        If this could not be found then it falls back to a :class:`Object`
        with the ID being set.

    .. attribute:: verification_level

        :class:`VerificationLevel` – The guild's verification level.

        See also :attr:`Guild.verification_level`.

    .. attribute:: explicit_content_filter

        :class:`ContentFilter` – The guild's content filter.

        See also :attr:`Guild.explicit_content_filter`.

    .. attribute:: default_message_notifications

        :class:`int` – The guild's default message notification setting.

    .. attribute:: vanity_url_code

        :class:`str` – The guild's vanity URL.

        See also :meth:`Guild.vanity_invite` and :meth:`Guild.change_vanity_invite`.

    .. attribute:: position

        :class:`int` – The position of a :class:`Role` or :class:`abc.GuildChannel`.

    .. attribute:: type

        *Union[int, str]* – The type of channel or channel permission overwrite.

        If the type is an :class:`int`, then it is a type of channel which can be either
        ``0`` to indicate a text channel or ``1`` to indicate a voice channel.

        If the type is a :class:`str`, then it is a type of permission overwrite which
        can be either ``'role'`` or ``'member'``.

    .. attribute:: topic

        :class:`str` – The topic of a :class:`TextChannel`.

        See also :attr:`TextChannel.topic`.

    .. attribute:: bitrate

        :class:`int` – The bitrate of a :class:`VoiceChannel`.

        See also :attr:`VoiceChannel.bitrate`.

    .. attribute:: overwrites

        List[Tuple[target, :class:`PermissionOverwrite`]] – A list of
        permission overwrite tuples that represents a target and a
        :class:`PermissionOverwrite` for said target.

        The first element is the object being targeted, which can either
        be a :class:`Member` or :class:`User` or :class:`Role`. If this object
        is not found then it is a :class:`Object` with an ID being filled and
        a ``type`` attribute set to either ``'role'`` or ``'member'`` to help
        decide what type of ID it is.

    .. attribute:: roles

        List[Union[:class:`Role`, :class:`Object`]] – A list of roles being added or removed
        from a member.

        If a role is not found then it is a :class:`Object` with the ID and name being
        filled in.

    .. attribute:: nick

        *Optional[str]* – The nickname of a member.

        See also :attr:`Member.nick`

    .. attribute:: deaf

        :class:`bool` – Whether the member is being server deafened.

        See also :attr:`VoiceState.deaf`.

    .. attribute:: mute

        :class:`bool` – Whether the member is being server muted.

        See also :attr:`VoiceState.mute`.

    .. attribute:: permissions

        :class:`Permissions` – The permissions of a role.

        See also :attr:`Role.permissions`.

    .. attribute:: colour
                   color

        :class:`Colour` – The colour of a role.

        See also :attr:`Role.colour`

    .. attribute:: hoist

        :class:`bool` – Whether the role is being hoisted or not.

        See also :attr:`Role.hoist`

    .. attribute:: mentionable

        :class:`bool` – Whether the role is mentionable or not.

        See also :attr:`Role.mentionable`

    .. attribute:: code

        :class:`str` – The invite's code.

        See also :attr:`Invite.code`

    .. attribute:: channel

        Union[:class:`abc.GuildChannel`, :class:`Object`] – A guild channel.

        If the channel is not found then it is a :class:`Object` with the ID
        being set. In some cases the channel name is also set.

    .. attribute:: inviter

        :class:`User` – The user who created the invite.

        See also :attr:`Invite.inviter`.

    .. attribute:: max_uses

        :class:`int` – The invite's max uses.

        See also :attr:`Invite.max_uses`.

    .. attribute:: uses

        :class:`int` – The invite's current uses.

        See also :attr:`Invite.uses`.

    .. attribute:: max_age

        :class:`int` – The invite's max age in seconds.

        See also :attr:`Invite.max_age`.

    .. attribute:: temporary

        :class:`bool` – If the invite is a temporary invite.

        See also :attr:`Invite.temporary`.

    .. attribute:: allow
                   deny

        :class:`Permissions` – The permissions being allowed or denied.

    .. attribute:: id

        :class:`int` – The ID of the object being changed.

    .. attribute:: avatar

        :class:`str` – The avatar hash of a member.

        See also :attr:`User.avatar`.

.. this is currently missing the following keys: reason and application_id
   I'm not sure how to about porting these

Webhook Support
------------------

discord.py offers support for creating, editing, and executing webhooks through the :class:`Webhook` class.

.. autoclass:: Webhook
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

An abstract base class (also known as an ``abc``) is a class that models can inherit
to get their behaviour. The Python implementation of an `abc <https://docs.python.org/3/library/abc.html>`_ is
slightly different in that you can register them at run-time. **Abstract base classes cannot be instantiated**.
They are mainly there for usage with ``isinstance`` and ``issubclass``\.

This library has a module related to abstract base classes, some of which are actually from the ``abc`` standard
module, others which are not.

.. autoclass:: discord.abc.Snowflake
    :members:

.. autoclass:: discord.abc.User
    :members:

.. autoclass:: discord.abc.PrivateChannel
    :members:

.. autoclass:: discord.abc.GuildChannel
    :members:

.. autoclass:: discord.abc.Messageable
    :members:
    :exclude-members: history, typing

    .. autocomethod:: discord.abc.Messageable.history
        :async-for:

    .. autocomethod:: discord.abc.Messageable.typing
        :async-with:

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

    Nearly all classes here have ``__slots__`` defined which means that it is
    impossible to have dynamic attributes to the data classes.

    More information about ``__slots__`` can be found
    `in the official python documentation <https://docs.python.org/3/reference/datamodel.html#slots>`_.


ClientUser
~~~~~~~~~~~~

.. autoclass:: ClientUser()
    :members:
    :inherited-members:

Relationship
~~~~~~~~~~~~~~

.. autoclass:: Relationship()
    :members:

User
~~~~~

.. autoclass:: User()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: history
        :async-for:

    .. autocomethod:: typing
        :async-with:

Attachment
~~~~~~~~~~~

.. autoclass:: Attachment()
    :members:

Message
~~~~~~~

.. autoclass:: Message()
    :members:

Reaction
~~~~~~~~~

.. autoclass:: Reaction()
    :members:
    :exclude-members: users

    .. autocomethod:: users
        :async-for:

CallMessage
~~~~~~~~~~~~

.. autoclass:: CallMessage()
    :members:

GroupCall
~~~~~~~~~~

.. autoclass:: GroupCall()
    :members:

Guild
~~~~~~

.. autoclass:: Guild()
    :members:
    :exclude-members: audit_logs

    .. autocomethod:: audit_logs
        :async-for:

Member
~~~~~~

.. autoclass:: Member()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: history
        :async-for:

    .. autocomethod:: typing
        :async-with:

Spotify
~~~~~~~~

.. autoclass:: Spotify()
    :members:

VoiceState
~~~~~~~~~~~

.. autoclass:: VoiceState()
    :members:

Emoji
~~~~~

.. autoclass:: Emoji()
    :members:

PartialEmoji
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PartialEmoji()
    :members:

Role
~~~~~

.. autoclass:: Role()
    :members:

TextChannel
~~~~~~~~~~~~

.. autoclass:: TextChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: history
        :async-for:

    .. autocomethod:: typing
        :async-with:

VoiceChannel
~~~~~~~~~~~~~

.. autoclass:: VoiceChannel()
    :members:
    :inherited-members:

CategoryChannel
~~~~~~~~~~~~~~~~~

.. autoclass:: CategoryChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. autoclass:: DMChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: history
        :async-for:

    .. autocomethod:: typing
        :async-with:

GroupChannel
~~~~~~~~~~~~

.. autoclass:: GroupChannel()
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. autocomethod:: history
        :async-for:

    .. autocomethod:: typing
        :async-with:


Invite
~~~~~~~

.. autoclass:: Invite()
    :members:

.. _discord_api_data:

Data Classes
--------------

Some classes are just there to be data containers, this lists them.

Unlike :ref:`models <discord_api_models>` you are allowed to create
these yourself, even if they can also be used to hold attributes.

Nearly all classes here have ``__slots__`` defined which means that it is
impossible to have dynamic attributes to the data classes.

The only exception to this rule is :class:`Object`, which is made with
dynamic attributes in mind.

More information about ``__slots__`` can be found
`in the official python documentation <https://docs.python.org/3/reference/datamodel.html#slots>`_.


Object
~~~~~~~

.. autoclass:: Object
    :members:

Embed
~~~~~~

.. autoclass:: Embed
    :members:

File
~~~~~

.. autoclass:: File
    :members:

Colour
~~~~~~

.. autoclass:: Colour
    :members:

Activity
~~~~~~~~~

.. autoclass:: Activity
    :members:

Game
~~~~~

.. autoclass:: Game
    :members:

Streaming
~~~~~~~~~~~

.. autoclass:: Streaming
    :members:

Permissions
~~~~~~~~~~~~

.. autoclass:: Permissions
    :members:

PermissionOverwrite
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PermissionOverwrite
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

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

.. autoexception:: discord.opus.OpusError

.. autoexception:: discord.opus.OpusNotLoaded
