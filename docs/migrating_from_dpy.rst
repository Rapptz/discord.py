.. currentmodule:: discord

.. _migrating_from_dpy:

Migrating to This Library
==========================

| This library is designed to be compatible with discord.py.
| However, the user and bot APIs are *not* the same.

Most things bots can do, users can (in some capacity) as well. The biggest difference is the amount of added things: users can do a lot more things than bots can.

However, a number of things have been removed.
For example:

- ``Intents``: While the gateway technically accepts intents for user accounts, they are—for the most part—useless and can break things.
- ``Shards``: Just like intents, users can utilize sharding but it is not very useful.
- ``discord.ui``: Users cannot utilize the bot UI kit.
- ``discord.app_commands``: Users cannot register application commands.

However, even in features that are shared between user and bot accounts, there may be variance in functionality or simply different design choices that better reflect a user account implementation.
An effort is made to minimize these differences and avoid migration pain, but it is not always the first priority.

Guild Subscriptions
-------------------

Guild subscriptions are a way for a client to limit the events it receives from a guild. For more information about guild subscriptions, see the :doc:`guild_subscriptions` section.

When compared to a bot account, the most noticeable differences they introduce are in relation to guild members and presence. 

Guild Members
~~~~~~~~~~~~~~

The concept of privileged intents does not exist for user accounts, so guild member access is limited in different ways.

By default, the library will subscribe to member updates for all guilds, meaning that events such as :func:`discord.on_member_join` and :func:`discord.on_raw_member_remove` will be dispatched for all guilds the user is in.
However, events that require the member cache to be populated (such as :func:`discord.on_member_update`) are only dispatched for guilds that are chunked.

A guild can only be chunked (have the local member cache populated) if the user has the :attr:`~Permissions.manage_roles`, :attr:`~Permissions.kick_members`, or :attr:`~Permissions.ban_members` permissions.
Additionally, guilds with less than 1,000 members may be chunked if there exists at least one channel that everyone can view.
By default, the library will attempt to chunk all guilds that are chunkable. This can be disabled by setting the ``chunk_guilds_at_startup`` parameter to ``False`` when creating a :class:`Client`.

If a guild is not chunked, the only members that will be cached are members with an active voice state and, if the guild has less than 75,000 members, members that the user is friends, has an implicit relationship, or has an open DM with.

The library offers two avenues to get the "entire" member list of a guild.

- :func:`Guild.chunk`: If chunking guilds at startup is disabled, you can use this method to chunk a guild manually.
- :func:`Guild.fetch_members`: If you have the permissions to request all guild members, you can use this method to fetch the entire member list. Else, this method scrapes the member sidebar (which can become very slow), only returning online members if the guild has more than 1,000 members.

Presence
~~~~~~~~~

User accounts are always synced the overall presence of friends and implicit relationships, tracked in the library via the :class:`Relationship` class. Overall user presence updates will dispatch a :func:`discord.on_presence_update` event with :class:`Relationship` instances.
Additionally, for guilds with less than 75,000 members, they're synced the per-guild presence of members that the user is friends, has an implicit relationship, or has an open DM with.

Outside of these cases, you will not receive presence updates for any other users. To obtain the presence of an arbitrary user, you can use the :meth:`Guild.query_members` method.
To stay informed of presence updates for a specific user, you can subscribe to them using the :meth:`Guild.subscribe_to` method. See the :doc:`guild_subscriptions` section for more information.

.. note::

    User updates (i.e. :func:`discord.on_user_update`) require either member updates (for at least one guild) or presence updates to be dispatched for the user as outlined above.

AutoMod
--------

The following Gateway events are not dispatched to user accounts:

- ``on_automod_rule_create``
- ``on_automod_rule_update``
- ``on_automod_rule_delete``
- ``on_automod_action``

The first three can be replaced by listening to the :func:`discord.on_audit_log_entry_create` event and checking the :attr:`~discord.AuditLogEntry.action` attribute.
The last one is partially replaceable by listening to the :func:`discord.on_message` event and checking for AutoMod system messages, but this is not a perfect solution.
