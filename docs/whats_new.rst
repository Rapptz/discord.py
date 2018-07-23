.. currentmodule:: discord

.. _whats_new:

What's New
============

This page keeps a detailed human friendly rendering of what's new and changed
in specific versions.

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
