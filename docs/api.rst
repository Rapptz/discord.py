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

Client
-------

.. autoclass:: Client
    :members:
    :exclude-members: on_connect, on_disconnect, on_ready, on_shard_ready,
                      on_resumed, on_error, on_socket_raw_receive, on_socket_raw_send,
                      on_typing, on_message, on_message_delete, on_bulk_message_delete,
                      on_raw_message_delete, on_raw_bulk_message_delete, on_message_edit,
                      on_raw_message_edit, on_reaction_add, on_raw_reaction_add,
                      on_reaction_remove, on_raw_reaction_remove, on_reaction_clear,
                      on_raw_reaction_clear, on_reaction_clear_emoji,
                      on_raw_reaction_clear_emoji, on_private_channel_delete,
                      on_private_channel_create, on_private_channel_update,
                      on_private_channel_pins_update, on_guild_channel_delete,
                      on_guild_channel_create, on_guild_channel_update,
                      on_guild_channel_pins_update, on_guild_integrations_update,
                      on_webhooks_update, on_member_join, on_member_remove, on_member_update,
                      on_user_update, on_guild_join, on_guild_remove, on_guild_update,
                      on_guild_role_create, on_guild_role_delete, on_guild_role_update,
                      on_guild_emojis_update, on_guild_available, on_guild_unavailable,
                      on_voice_state_update, on_member_ban, on_member_unban, on_invite_create,
                      on_invite_delete, on_group_join, on_group_remove, on_relationship_add,
                      on_relationship_remove, on_relationship_update

.. autoclass:: AutoShardedClient
    :members:

.. autoclass:: AppInfo()
    :members:

.. autoclass:: Team()
    :members:

.. autoclass:: TeamMember()
    :members:

Voice
------

.. autoclass:: VoiceClient()
    :members:

.. autoclass:: AudioSource
    :members:

.. autoclass:: PCMAudio
    :members:

.. autoclass:: FFmpegAudio
    :members:

.. autoclass:: FFmpegPCMAudio
    :members:

.. autoclass:: FFmpegOpusAudio
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
            if message.author == self.user:
                return

            if message.content.startswith('$hello'):
                await message.channel.send('Hello World!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to print a traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, a :exc:`TypeError` will be raised.
    In order to turn a function into a coroutine they must be ``async def``
    functions.

.. autofunction Client.on_connect

.. autofunction Client.on_disconnect

.. autofunction Client.on_ready

.. autofunction Client.on_shard_ready

.. autofunction Client.on_resumed

.. autofunction Client.on_error

.. autofunction Client.on_socket_raw_receive

.. autofunction Client.on_socket_raw_send

.. autofunction Client.on_typing

.. autofunction Client.on_message

.. autofunction Client.on_message_delete

.. autofunction Client.on_bulk_message_delete

.. autofunction Client.on_raw_message_delete

.. autofunction Client.on_raw_bulk_message_delete

.. autofunction Client.on_message_edit

.. autofunction Client.on_raw_message_edit

.. autofunction Client.on_reaction_add

.. autofunction Client.on_raw_reaction_add

.. autofunction Client.on_reaction_remove

.. autofunction Client.on_raw_reaction_remove

.. autofunction Client.on_reaction_clear

.. autofunction Client.on_raw_reaction_clear

.. autofunction Client.on_reaction_clear_emoji

.. autofunction Client.on_raw_reaction_clear_emoji

.. autofunction Client.on_private_channel_delete

.. autofunction Client.on_private_channel_create

.. autofunction Client.on_private_channel_update

.. autofunction Client.on_private_channel_pins_update

.. autofunction Client.on_guild_channel_delete

.. autofunction Client.on_guild_channel_create

.. autofunction Client.on_guild_channel_update

.. autofunction Client.on_guild_channel_pins_update

.. autofunction Client.on_guild_integrations_update

.. autofunction Client.on_webhooks_update

.. autofunction Client.on_member_join

.. autofunction Client.on_member_remove

.. autofunction Client.on_member_update

.. autofunction Client.on_user_update

.. autofunction Client.on_guild_join

.. autofunction Client.on_guild_remove

.. autofunction Client.on_guild_update

.. autofunction Client.on_guild_role_create

.. autofunction Client.on_guild_role_delete

.. autofunction Client.on_guild_role_update

.. autofunction Client.on_guild_emojis_update

.. autofunction Client.on_guild_available

.. autofunction Client.on_guild_unavailable

.. autofunction Client.on_voice_state_update

.. autofunction Client.on_member_ban

.. autofunction Client.on_member_unban

.. autofunction Client.on_invite_create

.. autofunction Client.on_invite_delete

.. autofunction Client.on_group_join

.. autofunction Client.on_group_remove

.. autofunction Client.on_relationship_add

.. autofunction Client.on_relationship_remove

.. autofunction Client.on_relationship_update


.. _discord-api-utils:

Utility Functions
-----------------

.. autofunction:: discord.utils.find

.. autofunction:: discord.utils.get

.. autofunction:: discord.utils.snowflake_time

.. autofunction:: discord.utils.oauth_url

.. autofunction:: discord.utils.escape_markdown

.. autofunction:: discord.utils.escape_mentions

.. autofunction:: discord.utils.resolve_invite

.. autofunction:: discord.utils.sleep_until

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
    .. attribute:: bug_hunter

        A boolean indicating if the user is a Bug Hunter.
    .. attribute:: early_supporter

        A boolean indicating if the user has had premium before 10 October, 2018.
    .. attribute:: hypesquad

        A boolean indicating if the user is in Discord HypeSquad.
    .. attribute:: hypesquad_houses

        A list of :class:`HypeSquadHouse` that the user is in.
    .. attribute:: team_user

        A boolean indicating if the user is in part of a team.

        .. versionadded:: 1.3

    .. attribute:: system

        A boolean indicating if the user is officially part of the Discord urgent message system.

        .. versionadded:: 1.3

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

    .. note::

        This only applies to users, *not* bots.

    .. attribute:: nitro

        Represents the Discord Nitro with Nitro-exclusive games.

    .. attribute:: nitro_classic

        Represents the Discord Nitro with no Nitro-exclusive games.


.. class:: Theme

    Represents the theme synced across all Discord clients.

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
        :return: An async iterator.

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
        :return: An async iterator.

.. _discord-api-audit-logs:

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

        Returns an iterator over (attribute, value) tuple of this diff.

    .. attribute:: name

        :class:`str` – A name of something.

    .. attribute:: icon

        :class:`str` – A guild's icon hash. See also :attr:`Guild.icon`.

    .. attribute:: splash

        :class:`str` – The guild's invite splash hash. See also :attr:`Guild.splash`.

    .. attribute:: owner

        Union[:class:`Member`, :class:`User`] – The guild's owner. See also :attr:`Guild.owner`

    .. attribute:: region

        :class:`VoiceRegion` – The guild's voice region. See also :attr:`Guild.region`.

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

    .. attribute:: default_notifications

        :class:`NotificationLevel` – The guild's default notification level.

        See also :attr:`Guild.default_notifications`.

    .. attribute:: explicit_content_filter

        :class:`ContentFilter` – The guild's content filter.

        See also :attr:`Guild.explicit_content_filter`.

    .. attribute:: default_message_notifications

        :class:`int` – The guild's default message notification setting.

    .. attribute:: vanity_url_code

        :class:`str` – The guild's vanity URL.

        See also :meth:`Guild.vanity_invite` and :meth:`Guild.edit`.

    .. attribute:: position

        :class:`int` – The position of a :class:`Role` or :class:`abc.GuildChannel`.

    .. attribute:: type

        Union[:class:`int`, :class:`str`] – The type of channel or channel permission overwrite.

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

        Optional[:class:`str`] – The nickname of a member.

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

    .. attribute:: slowmode_delay

        :class:`int` – The number of seconds members have to wait before
        sending another message in the channel.

        See also :attr:`TextChannel.slowmode_delay`.

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

An :term:`py:abstract base class` (also known as an ``abc``) is a class that models can inherit
to get their behaviour. The Python implementation of an :doc:`abc <py:library/abc>` is
slightly different in that you can register them at run-time. **Abstract base classes cannot be instantiated**.
They are mainly there for usage with :func:`py:isinstance` and :func:`py:issubclass`\.

This library has a module related to abstract base classes, some of which are actually from the :doc:`abc <py:library/abc>` standard
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

    .. automethod:: discord.abc.Messageable.history
        :async-for:

    .. automethod:: discord.abc.Messageable.typing
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

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.


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

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

Attachment
~~~~~~~~~~~

.. autoclass:: Attachment()
    :members:

Asset
~~~~~

.. autoclass:: Asset()
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

    .. automethod:: users
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

    .. automethod:: audit_logs
        :async-for:

Member
~~~~~~

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

    .. automethod:: history
        :async-for:

    .. automethod:: typing
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

    .. automethod:: history
        :async-for:

    .. automethod:: typing
        :async-with:

GroupChannel
~~~~~~~~~~~~

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

.. autoclass:: PartialInviteGuild()
    :members:

PartialInviteChannel
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PartialInviteChannel()
    :members:

Invite
~~~~~~~

.. autoclass:: Invite()
    :members:

WidgetChannel
~~~~~~~~~~~~~~~

.. autoclass:: WidgetChannel()
    :members:

WidgetMember
~~~~~~~~~~~~~

.. autoclass:: WidgetMember()
    :members:
    :inherited-members:

Widget
~~~~~~~

.. autoclass:: Widget()
    :members:

RawMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawMessageDeleteEvent()
    :members:

RawBulkMessageDeleteEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawBulkMessageDeleteEvent()
    :members:

RawMessageUpdateEvent
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawMessageUpdateEvent()
    :members:

RawReactionActionEvent
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawReactionActionEvent()
    :members:

RawReactionClearEvent
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawReactionClearEvent()
    :members:

RawReactionClearEmojiEvent
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: RawReactionClearEmojiEvent()
    :members:


.. _discord_api_data:

Data Classes
--------------

Some classes are just there to be data containers, this lists them.

Unlike :ref:`models <discord_api_models>` you are allowed to create
these yourself, even if they can also be used to hold attributes.

Nearly all classes here have :ref:`py:slots` defined which means that it is
impossible to have dynamic attributes to the data classes.

The only exception to this rule is :class:`abc.Snowflake`, which is made with
dynamic attributes in mind.


Object
~~~~~~~

.. autoclass:: Object
    :members:

Embed
~~~~~~

.. autoclass:: Embed
    :members:

AllowedMentions
~~~~~~~~~~~~~~~~~

.. autoclass:: AllowedMentions
    :members:

File
~~~~~

.. autoclass:: File
    :members:

Colour
~~~~~~

.. autoclass:: Colour
    :members:

BaseActivity
~~~~~~~~~~~~~~

.. autoclass:: BaseActivity
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

CustomActivity
~~~~~~~~~~~~~~~

.. autoclass:: CustomActivity
    :members:

Permissions
~~~~~~~~~~~~

.. autoclass:: Permissions
    :members:

PermissionOverwrite
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PermissionOverwrite
    :members:

SystemChannelFlags
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SystemChannelFlags
    :members:

MessageFlags
~~~~~~~~~~~~

.. autoclass:: MessageFlags
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

.. autoexception:: InvalidData

.. autoexception:: InvalidArgument

.. autoexception:: GatewayNotFound

.. autoexception:: ConnectionClosed

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
            - :exc:`NoMoreItems`
            - :exc:`GatewayNotFound`
            - :exc:`HTTPException`
                - :exc:`Forbidden`
                - :exc:`NotFound`
