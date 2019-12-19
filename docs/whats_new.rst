.. currentmodule:: discord

.. |commands| replace:: [:ref:`ext.commands <discord_ext_commands>`]
.. |tasks| replace:: [:ref:`ext.tasks <discord_ext_tasks>`]

.. _whats_new:

Changelog
============

This page keeps a detailed human friendly rendering of what's new and changed
in specific versions.

.. _vp1p2p5:

v1.2.5
--------

Bug Fixes
~~~~~~~~~~~

- Fix a bug that caused crashes due to missing ``animated`` field in Emoji structures in reactions.

.. _vp1p2p4:

v1.2.4
--------

Bug Fixes
~~~~~~~~~~~

- Fix a regression when :attr:`Message.channel` would be ``None``.
- Fix a regression where :attr:`Message.edited_at` would not update during edits.
- Fix a crash that would trigger during message updates (:issue:`2265`, :issue:`2287`).
- Fix a bug when :meth:`VoiceChannel.connect` would not return (:issue:`2274`, :issue:`2372`, :issue:`2373`, :issue:`2377`).
- Fix a crash relating to token-less webhooks (:issue:`2364`).
- Fix issue where :attr:`Guild.premium_subscription_count` would be ``None`` due to a Discord bug. (:issue:`2331`, :issue:`2376`).

.. _vp1p2p3:

v1.2.3
--------

Bug Fixes
~~~~~~~~~~~

- Fix an AttributeError when accessing :attr:`Member.premium_since` in :func:`on_member_update`. (:issue:`2213`)
- Handle :exc:`asyncio.CancelledError` in :meth:`abc.Messageable.typing` context manager. (:issue:`2218`)
- Raise the max encoder bitrate to 512kbps to account for nitro boosting. (:issue:`2232`)
- Properly propagate exceptions in :meth:`Client.run`. (:issue:`2237`)
- |commands| Ensure cooldowns are properly copied when used in cog level ``command_attrs``.

.. _vp1p2p2:

v1.2.2
--------

Bug Fixes
~~~~~~~~~~~

- Audit log related attribute access have been fixed to not error out when they shouldn't have.

.. _vp1p2p1:

v1.2.1
--------

Bug Fixes
~~~~~~~~~~~

- :attr:`User.avatar_url` and related attributes no longer raise an error.
- More compatibility shims with the ``enum.Enum`` code.

.. _vp1p2p0:

v1.2.0
--------

This update mainly brings performance improvements and various nitro boosting attributes (referred to in the API as "premium guilds").

New Features
~~~~~~~~~~~~~~

- Add :attr:`Guild.premium_tier` to query the guild's current nitro boost level.
- Add :attr:`Guild.emoji_limit`, :attr:`Guild.bitrate_limit`, :attr:`Guild.filesize_limit` to query the new limits of a guild when taking into consideration boosting.
- Add :attr:`Guild.premium_subscription_count` to query how many members are boosting a guild.
- Add :attr:`Member.premium_since` to query since when a member has boosted a guild.
- Add :attr:`Guild.premium_subscribers` to query all the members currently boosting the guild.
- Add :attr:`Guild.system_channel_flags` to query the settings for a guild's :attr:`Guild.system_channel`.
    - This includes a new type named :class:`SystemChannelFlags`
- Add :attr:`Emoji.available` to query if an emoji can be used (within the guild or otherwise).
- Add support for animated icons in :meth:`Guild.icon_url_as` and :attr:`Guild.icon_url`.
- Add :meth:`Guild.is_icon_animated`.
- Add support for the various new :class:`MessageType` involving nitro boosting.
- Add :attr:`VoiceRegion.india`. (:issue:`2145`)
- Add :meth:`Embed.insert_field_at`. (:issue:`2178`)
- Add a ``type`` attribute for all channels to their appropriate :class:`ChannelType`. (:issue:`2185`)
- Add :meth:`Client.fetch_channel` to fetch a channel by ID via HTTP. (:issue:`2169`)
- Add :meth:`Guild.fetch_channels` to fetch all channels via HTTP. (:issue:`2169`)
- |tasks| Add :meth:`Loop.stop <.ext.tasks.Loop.stop>` to gracefully stop a task rather than cancelling.
- |tasks| Add :meth:`Loop.failed <.ext.tasks.Loop.failed>` to query if a task had failed somehow.
- |tasks| Add :meth:`Loop.change_interval <.ext.tasks.Loop.change_interval>` to change the sleep interval at runtime (:issue:`2158`, :issue:`2162`)

Bug Fixes
~~~~~~~~~~~

- Fix internal error when using :meth:`Guild.prune_members`.
- |commands| Fix :attr:`.Command.invoked_subcommand` being invalid in many cases.
- |tasks| Reset iteration count when the loop terminates and is restarted.
- |tasks| The decorator interface now works as expected when stacking (:issue:`2154`)

Miscellaneous
~~~~~~~~~~~~~~~

- Improve performance of all Enum related code significantly.
    - This was done by replacing the ``enum.Enum`` code with an API compatible one.
    - This should not be a breaking change for most users due to duck-typing.
- Improve performance of message creation by about 1.5x.
- Improve performance of message editing by about 1.5-4x depending on payload size.
- Improve performance of attribute access on :class:`Member` about by 2x.
- Improve performance of :func:`utils.get` by around 4-6x depending on usage.
- Improve performance of event parsing lookup by around 2.5x.
- Keyword arguments in :meth:`Client.start` and :meth:`Client.run` are now validated (:issue:`953`, :issue:`2170`)
- The Discord error code is now shown in the exception message for :exc:`HTTPException`.
- Internal tasks launched by the library will now have their own custom ``__repr__``.
- All public facing types should now have a proper and more detailed ``__repr__``.
- |tasks| Errors are now logged via the standard :mod:`py:logging` module.

.. _vp1p1p1:

v1.1.1
--------

Bug Fixes
~~~~~~~~~~~~

- Webhooks do not overwrite data on retrying their HTTP requests (:issue:`2140`)

Miscellaneous
~~~~~~~~~~~~~~

- Add back signal handling to :meth:`Client.run` due to issues some users had with proper cleanup.

.. _vp1p1p0:

v1.1.0
---------

New Features
~~~~~~~~~~~~~~

- **There is a new extension dedicated to making background tasks easier.**
    - You can check the documentation here: :ref:`ext_tasks_api`.
- Add :attr:`Permissions.stream` permission. (:issue:`2077`)
- Add equality comparison and hash support to :class:`Asset`
- Add ``compute_prune_members`` parameter to :meth:`Guild.prune_members` (:issue:`2085`)
- Add :attr:`Client.cached_messages` attribute to fetch the message cache (:issue:`2086`)
- Add :meth:`abc.GuildChannel.clone` to clone a guild channel. (:issue:`2093`)
- Add ``delay`` keyword-only argument to :meth:`Message.delete` (:issue:`2094`)
- Add support for ``<:name:id>`` when adding reactions (:issue:`2095`)
- Add :meth:`Asset.read` to fetch the bytes content of an asset (:issue:`2107`)
- Add :meth:`Attachment.read` to fetch the bytes content of an attachment (:issue:`2118`)
- Add support for voice kicking by passing ``None`` to :meth:`Member.move_to`.

``discord.ext.commands``
++++++++++++++++++++++++++

- Add new :func:`~.commands.dm_only` check.
- Support callable converters in :data:`~.commands.Greedy`
- Add new :class:`~.commands.MessageConverter`.
    - This allows you to use :class:`Message` as a type hint in functions.
- Allow passing ``cls`` in the :func:`~.commands.group` decorator (:issue:`2061`)
- Add :attr:`.Command.parents` to fetch the parents of a command (:issue:`2104`)


Bug Fixes
~~~~~~~~~~~~

- Fix :exc:`AttributeError` when using ``__repr__`` on :class:`Widget`.
- Fix issue with :attr:`abc.GuildChannel.overwrites` returning ``None`` for keys.
- Remove incorrect legacy NSFW checks in e.g. :meth:`TextChannel.is_nsfw`.
- Fix :exc:`UnboundLocalError` when :class:`RequestsWebhookAdapter` raises an error.
- Fix bug where updating your own user did not update your member instances.
- Tighten constraints of ``__eq__`` in :class:`Spotify` objects (:issue:`2113`, :issue:`2117`)

``discord.ext.commands``
++++++++++++++++++++++++++

- Fix lambda converters in a non-module context (e.g. ``eval``).
- Use message creation time for reference time when computing cooldowns.
    - This prevents cooldowns from triggering during e.g. a RESUME session.
- Fix the default :func:`on_command_error` to work with new-style cogs (:issue:`2094`)
- DM channels are now recognised as NSFW in :func:`~.commands.is_nsfw` check.
- Fix race condition with help commands (:issue:`2123`)
- Fix cog descriptions not showing in :class:`~.commands.MinimalHelpCommand` (:issue:`2139`)

Miscellaneous
~~~~~~~~~~~~~~~

- Improve the performance of internal enum creation in the library by about 5x.
- Make the output of ``python -m discord --version`` a bit more useful.
- The loop cleanup facility has been rewritten again.
- The signal handling in :meth:`Client.run` has been removed.

``discord.ext.commands``
++++++++++++++++++++++++++

- Custom exception classes are now used for all default checks in the library (:issue:`2101`)


.. _vp1p0p1:

v1.0.1
--------

Bug Fixes
~~~~~~~~~~~

- Fix issue with speaking state being cast to ``int`` when it was invalid.
- Fix some issues with loop cleanup that some users experienced on Linux machines.
- Fix voice handshake race condition (:issue:`2056`, :issue:`2063`)

.. _vp1p0p0:

v1.0.0
--------

The changeset for this version are too big to be listed here, for more information please
see :ref:`the migrating page <migrating_1_0>`.


.. _vp0p16p6:

v0.16.6
--------

Bug Fixes
~~~~~~~~~~

- Fix issue with :meth:`Client.create_server` that made it stop working.
- Fix main thread being blocked upon calling ``StreamPlayer.stop``.
- Handle HEARTBEAT_ACK and resume gracefully when it occurs.
- Fix race condition when pre-emptively rate limiting that caused releasing an already released lock.
- Fix invalid state errors when immediately cancelling a coroutine.

.. _vp0p16p1:

v0.16.1
--------

This release is just a bug fix release with some better rate limit implementation.

Bug Fixes
~~~~~~~~~~~

- Servers are now properly chunked for user bots.
- The CDN URL is now used instead of the API URL for assets.
- Rate limit implementation now tries to use header information if possible.
- Event loop is now properly propagated (:issue:`420`)
- Allow falsey values in :meth:`Client.send_message` and :meth:`Client.send_file`.

.. _vp0p16p0:

v0.16.0
---------

New Features
~~~~~~~~~~~~~~

- Add :attr:`Channel.overwrites` to get all the permission overwrites of a channel.
- Add :attr:`Server.features` to get information about partnered servers.

Bug Fixes
~~~~~~~~~~

- Timeout when waiting for offline members while triggering :func:`on_ready`.

    - The fact that we did not timeout caused a gigantic memory leak in the library that caused
      thousands of duplicate :class:`Member` instances causing big memory spikes.

- Discard null sequences in the gateway.

    - The fact these were not discarded meant that :func:`on_ready` kept being called instead of
      :func:`on_resumed`. Since this has been corrected, in most cases :func:`on_ready` will be
      called once or twice with :func:`on_resumed` being called much more often.

.. _vp0p15p1:

v0.15.1
---------

- Fix crash on duplicate or out of order reactions.

.. _vp0p15p0:

v0.15.0
--------

New Features
~~~~~~~~~~~~~~

- Rich Embeds for messages are now supported.

    - To do so, create your own :class:`Embed` and pass the instance to the ``embed`` keyword argument to :meth:`Client.send_message` or :meth:`Client.edit_message`.
- Add :meth:`Client.clear_reactions` to remove all reactions from a message.
- Add support for MESSAGE_REACTION_REMOVE_ALL event, under :func:`on_reaction_clear`.
- Add :meth:`Permissions.update` and :meth:`PermissionOverwrite.update` for bulk permission updates.

    - This allows you to use e.g. ``p.update(read_messages=True, send_messages=False)`` in a single line.
- Add :meth:`PermissionOverwrite.is_empty` to check if the overwrite is empty (i.e. has no overwrites set explicitly as true or false).

For the command extension, the following changed:

- ``Context`` is no longer slotted to facilitate setting dynamic attributes.

.. _vp0p14p3:

v0.14.3
---------

Bug Fixes
~~~~~~~~~~~

- Fix crash when dealing with MESSAGE_REACTION_REMOVE
- Fix incorrect buckets for reactions.

.. _v0p14p2:

v0.14.2
---------

New Features
~~~~~~~~~~~~~~

- :meth:`Client.wait_for_reaction` now returns a namedtuple with ``reaction`` and ``user`` attributes.
    - This is for better support in the case that ``None`` is returned since tuple unpacking can lead to issues.

Bug Fixes
~~~~~~~~~~

- Fix bug that disallowed ``None`` to be passed for ``emoji`` parameter in :meth:`Client.wait_for_reaction`.

.. _v0p14p1:

v0.14.1
---------

Bug fixes
~~~~~~~~~~

- Fix bug with `Reaction` not being visible at import.
    - This was also breaking the documentation.

.. _v0p14p0:

v0.14.0
--------

This update adds new API features and a couple of bug fixes.

New Features
~~~~~~~~~~~~~

- Add support for Manage Webhooks permission under :attr:`Permissions.manage_webhooks`
- Add support for ``around`` argument in 3.5+ :meth:`Client.logs_from`.
- Add support for reactions.
    - :meth:`Client.add_reaction` to add a reactions
    - :meth:`Client.remove_reaction` to remove a reaction.
    - :meth:`Client.get_reaction_users` to get the users that reacted to a message.
    - :attr:`Permissions.add_reactions` permission bit support.
    - Two new events, :func:`on_reaction_add` and :func:`on_reaction_remove`.
    - :attr:`Message.reactions` to get reactions from a message.
    - :meth:`Client.wait_for_reaction` to wait for a reaction from a user.

Bug Fixes
~~~~~~~~~~

- Fix bug with Paginator still allowing lines that are too long.
- Fix the :attr:`Permissions.manage_emojis` bit being incorrect.

.. _v0p13p0:

v0.13.0
---------

This is a backwards compatible update with new features.

New Features
~~~~~~~~~~~~~

- Add the ability to manage emojis.

    - :meth:`Client.create_custom_emoji` to create new emoji.
    - :meth:`Client.edit_custom_emoji` to edit an old emoji.
    - :meth:`Client.delete_custom_emoji` to delete a custom emoji.
- Add new :attr:`Permissions.manage_emojis` toggle.

    - This applies for :class:`PermissionOverwrite` as well.
- Add new statuses for :class:`Status`.

    - :attr:`Status.dnd` (aliased with :attr:`Status.do_not_disturb`\) for Do Not Disturb.
    - :attr:`Status.invisible` for setting your status to invisible (please see the docs for a caveat).
- Deprecate :meth:`Client.change_status`

    - Use :meth:`Client.change_presence` instead for better more up to date functionality.
    - This method is subject for removal in a future API version.
- Add :meth:`Client.change_presence` for changing your status with the new Discord API change.

    - This is the only method that allows changing your status to invisible or do not disturb.

Bug Fixes
~~~~~~~~~~

- Paginator pages do not exceed their max_size anymore (:issue:`340`)
- Do Not Disturb users no longer show up offline due to the new :class:`Status` changes.

.. _v0p12p0:

v0.12.0
---------

This is a bug fix update that also comes with new features.

New Features
~~~~~~~~~~~~~

- Add custom emoji support.

    - Adds a new class to represent a custom Emoji named :class:`Emoji`
    - Adds a utility generator function, :meth:`Client.get_all_emojis`.
    - Adds a list of emojis on a server, :attr:`Server.emojis`.
    - Adds a new event, :func:`on_server_emojis_update`.
- Add new server regions to :class:`ServerRegion`

    - :attr:`ServerRegion.eu_central` and :attr:`ServerRegion.eu_west`.
- Add support for new pinned system message under :attr:`MessageType.pins_add`.
- Add order comparisons for :class:`Role` to allow it to be compared with regards to hierarchy.

    - This means that you can now do ``role_a > role_b`` etc to check if ``role_b`` is lower in the hierarchy.

- Add :attr:`Server.role_hierarchy` to get the server's role hierarchy.
- Add :attr:`Member.server_permissions` to get a member's server permissions without their channel specific overwrites.
- Add :meth:`Client.get_user_info` to retrieve a user's info from their ID.
- Add a new ``Player`` property, ``Player.error`` to fetch the error that stopped the player.

    - To help with this change, a player's ``after`` function can now take a single parameter denoting the current player.
- Add support for server verification levels.

    - Adds a new enum called :class:`VerificationLevel`.
    - This enum can be used in :meth:`Client.edit_server` under the ``verification_level`` keyword argument.
    - Adds a new attribute in the server, :attr:`Server.verification_level`.
- Add :attr:`Server.voice_client` shortcut property for :meth:`Client.voice_client_in`.

    - This is technically old (was added in v0.10.0) but was undocumented until v0.12.0.

For the command extension, the following are new:

- Add custom emoji converter.
- All default converters that can take IDs can now convert via ID.
- Add coroutine support for ``Bot.command_prefix``.
- Add a method to reset command cooldown.

Bug Fixes
~~~~~~~~~~

- Fix bug that caused the library to not work with the latest ``websockets`` library.
- Fix bug that leaked keep alive threads (:issue:`309`)
- Fix bug that disallowed :class:`ServerRegion` from being used in :meth:`Client.edit_server`.
- Fix bug in :meth:`Channel.permissions_for` that caused permission resolution to happen out of order.
- Fix bug in :attr:`Member.top_role` that did not account for same-position roles.

.. _v0p11p0:

v0.11.0
--------

This is a minor bug fix update that comes with a gateway update (v5 -> v6).

Breaking Changes
~~~~~~~~~~~~~~~~~

- ``Permissions.change_nicknames`` has been renamed to :attr:`Permissions.change_nickname` to match the UI.

New Features
~~~~~~~~~~~~~

- Add the ability to prune members via :meth:`Client.prune_members`.
- Switch the websocket gateway version to v6 from v5. This allows the library to work with group DMs and 1-on-1 calls.
- Add :attr:`AppInfo.owner` attribute.
- Add :class:`CallMessage` for group voice call messages.
- Add :class:`GroupCall` for group voice call information.
- Add :attr:`Message.system_content` to get the system message.
- Add the remaining VIP servers and the Brazil servers into :class:`ServerRegion` enum.
- Add ``stderr`` argument to :meth:`VoiceClient.create_ffmpeg_player` to redirect stderr.
- The library now handles implicit permission resolution in :meth:`Channel.permissions_for`.
- Add :attr:`Server.mfa_level` to query a server's 2FA requirement.
- Add :attr:`Permissions.external_emojis` permission.
- Add :attr:`Member.voice` attribute that refers to a :class:`VoiceState`.

    - For backwards compatibility, the member object will have properties mirroring the old behaviour.

For the command extension, the following are new:

- Command cooldown system with the ``cooldown`` decorator.
- ``UserInputError`` exception for the hierarchy for user input related errors.

Bug Fixes
~~~~~~~~~~

- :attr:`Client.email` is now saved when using a token for user accounts.
- Fix issue when removing roles out of order.
- Fix bug where discriminators would not update.
- Handle cases where ``HEARTBEAT`` opcode is received. This caused bots to disconnect seemingly randomly.

For the command extension, the following bug fixes apply:

- ``Bot.check`` decorator is actually a decorator not requiring parentheses.
- ``Bot.remove_command`` and ``Group.remove_command`` no longer throw if the command doesn't exist.
- Command names are no longer forced to be ``lower()``.
- Fix a bug where Member and User converters failed to work in private message contexts.
- ``HelpFormatter`` now ignores hidden commands when deciding the maximum width.

.. _v0p10p0:

v0.10.0
-------

For breaking changes, see :ref:`migrating-to-async`. The breaking changes listed there will not be enumerated below. Since this version is rather a big departure from v0.9.2, this change log will be non-exhaustive.

New Features
~~~~~~~~~~~~~

- The library is now fully ``asyncio`` compatible, allowing you to write non-blocking code a lot more easily.
- The library now fully handles 429s and unconditionally retries on 502s.
- A new command extension module was added but is currently undocumented. Figuring it out is left as an exercise to the reader.
- Two new exception types, :exc:`Forbidden` and :exc:`NotFound` to denote permission errors or 404 errors.
- Added :meth:`Client.delete_invite` to revoke invites.
- Added support for sending voice. Check :class:`VoiceClient` for more details.
- Added :meth:`Client.wait_for_message` coroutine to aid with follow up commands.
- Added :data:`version_info` named tuple to check version info of the library.
- Login credentials are now cached to have a faster login experience. You can disable this by passing in ``cache_auth=False``
  when constructing a :class:`Client`.
- New utility function, :func:`discord.utils.get` to simplify retrieval of items based on attributes.
- All data classes now support ``!=``, ``==``, ``hash(obj)`` and ``str(obj)``.
- Added :meth:`Client.get_bans` to get banned members from a server.
- Added :meth:`Client.invites_from` to get currently active invites in a server.
- Added :attr:`Server.me` attribute to get the :class:`Member` version of :attr:`Client.user`.
- Most data classes now support a ``hash(obj)`` function to allow you to use them in ``set`` or ``dict`` classes or subclasses.
- Add :meth:`Message.clean_content` to get a text version of the content with the user and channel mentioned changed into their names.
- Added a way to remove the messages of the user that just got banned in :meth:`Client.ban`.
- Added :meth:`Client.wait_until_ready` to facilitate easy creation of tasks that require the client cache to be ready.
- Added :meth:`Client.wait_until_login` to facilitate easy creation of tasks that require the client to be logged in.
- Add :class:`discord.Game` to represent any game with custom text to send to :meth:`Client.change_status`.
- Add :attr:`Message.nonce` attribute.
- Add :meth:`Member.permissions_in` as another way of doing :meth:`Channel.permissions_for`.
- Add :meth:`Client.move_member` to move a member to another voice channel.
- You can now create a server via :meth:`Client.create_server`.
- Added :meth:`Client.edit_server` to edit existing servers.
- Added :meth:`Client.server_voice_state` to server mute or server deafen a member.
- If you are being rate limited, the library will now handle it for you.
- Add :func:`on_member_ban` and :func:`on_member_unban` events that trigger when a member is banned/unbanned.

Performance Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~

- All data classes now use ``__slots__`` which greatly reduce the memory usage of things kept in cache.
- Due to the usage of ``asyncio``, the CPU usage of the library has gone down significantly.
- A lot of the internal cache lists were changed into dictionaries to change the ``O(n)`` lookup into ``O(1)``.
- Compressed READY is now on by default. This means if you're on a lot of servers (or maybe even a few) you would
  receive performance improvements by having to download and process less data.
- While minor, change regex from ``\d+`` to ``[0-9]+`` to avoid unnecessary unicode character lookups.

Bug Fixes
~~~~~~~~~~

- Fix bug where guilds being updated did not edit the items in cache.
- Fix bug where ``member.roles`` were empty upon joining instead of having the ``@everyone`` role.
- Fix bug where :meth:`Role.is_everyone` was not being set properly when the role was being edited.
- :meth:`Client.logs_from` now handles cases where limit > 100 to sidestep the discord API limitation.
- Fix bug where a role being deleted would trigger a ``ValueError``.
- Fix bug where :meth:`Permissions.kick_members` and :meth:`Permissions.ban_members` were flipped.
- Mentions are now triggered normally. This was changed due to the way discord handles it internally.
- Fix issue when a :class:`Message` would attempt to upgrade a :attr:`Message.server` when the channel is
  a :class:`Object`.
- Unavailable servers were not being added into cache, this has been corrected.
