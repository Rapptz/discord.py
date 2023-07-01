.. currentmodule:: discord

.. |commands| replace:: [:ref:`ext.commands <discord_ext_commands>`]
.. |tasks| replace:: [:ref:`ext.tasks <discord_ext_tasks>`]

.. _whats_new:

Changelog
============

This page keeps a detailed human friendly rendering of what's new and changed
in specific versions.

.. _vp2p3p1:

v2.3.1
-------

Bug Fixes
~~~~~~~~~~

- Fix username lookup in :meth:`Guild.get_member_named` (:issue:`9451`).
- Use cache data first for :attr:`Interaction.channel` instead of API data.
    - This bug usually manifested in incomplete channel objects (e.g. no ``overwrites``) because Discord does not provide this data.

- Fix false positives in :meth:`PartialEmoji.from_str` inappropriately setting ``animated`` to ``True`` (:issue:`9456`, :issue:`9457`).
- Fix certain select types not appearing in :attr:`Message.components` (:issue:`9462`).
- |commands| Change lookup order for :class:`~ext.commands.MemberConverter` and :class:`~ext.commands.UserConverter` to prioritise usernames instead of nicknames.

.. _vp2p3p0:

v2.3.0
--------

New Features
~~~~~~~~~~~~~

- Add support for the new username system (also known as "pomelo").
    - Add :attr:`User.global_name` to get their global nickname or "display name".
    - Update :attr:`User.display_name` and :attr:`Member.display_name` to understand global nicknames.
    - Update ``__str__`` for :class:`User` to drop discriminators if the user has been migrated.
    - Update :meth:`Guild.get_member_named` to work with migrated users.
    - Update :attr:`User.default_avatar` to work with migrated users.
    - |commands| Update user and member converters to understand migrated users.

- Add :attr:`DefaultAvatar.pink` for new pink default avatars.
- Add :meth:`Colour.pink` to get the pink default avatar colour.
- Add support for voice messages (:issue:`9358`)
    - Add :attr:`MessageFlags.voice`
    - Add :attr:`Attachment.duration` and :attr:`Attachment.waveform`
    - Add :meth:`Attachment.is_voice_message`
    - This does not support *sending* voice messages because this is currently unsupported by the API.

- Add support for new :attr:`Interaction.channel` attribute from the API update (:issue:`9339`).
- Add support for :attr:`TextChannel.default_thread_slowmode_delay` (:issue:`9291`).
- Add support for :attr:`ForumChannel.default_sort_order` (:issue:`9290`).
- Add support for ``default_reaction_emoji`` and ``default_forum_layout`` in :meth:`Guild.create_forum` (:issue:`9300`).
- Add support for ``widget_channel``, ``widget_enabled``, and ``mfa_level`` in :meth:`Guild.edit` (:issue:`9302`, :issue:`9303`).
- Add various new :class:`Permissions` and changes (:issue:`9312`, :issue:`9325`, :issue:`9358`, :issue:`9378`)
    - Add new :attr:`~Permissions.manage_expressions`, :attr:`~Permissions.use_external_sounds`, :attr:`~Permissions.use_soundboard`, :attr:`~Permissions.send_voice_messages`, :attr:`~Permissions.create_expressions` permissions.
    - Change :attr:`Permissions.manage_emojis` to be an alias of :attr:`~Permissions.manage_expressions`.

- Add various new properties to :class:`PartialAppInfo` and :class:`AppInfo` (:issue:`9298`).
- Add support for ``with_counts`` parameter to :meth:`Client.fetch_guilds` (:issue:`9369`).
- Add new :meth:`Guild.get_emoji` helper (:issue:`9296`).
- Add :attr:`ApplicationFlags.auto_mod_badge` (:issue:`9313`).
- Add :attr:`Guild.max_stage_video_users` and :attr:`Guild.safety_alerts_channel` (:issue:`9318`).
- Add support for ``raid_alerts_disabled`` and ``safety_alerts_channel`` in :meth:`Guild.edit` (:issue:`9318`).
- |commands| Add :attr:`BadLiteralArgument.argument <ext.commands.BadLiteralArgument.argument>` to get the failed argument's value (:issue:`9283`).
- |commands| Add :attr:`Context.filesize_limit <ext.commands.Context.filesize_limit>` property (:issue:`9416`).
- |commands| Add support for :attr:`Parameter.displayed_name <ext.commands.Parameter.displayed_name>` (:issue:`9427`).

Bug Fixes
~~~~~~~~~~

- Fix ``FileHandler`` handlers being written ANSI characters when the bot is executed inside PyCharm.
    - This has the side effect of removing coloured logs from the PyCharm terminal due an upstream bug involving TTY detection. This issue is tracked under `PY-43798 <https://youtrack.jetbrains.com/issue/PY-43798>`_.

- Fix channel edits with :meth:`Webhook.edit` sending two requests instead of one.
- Fix :attr:`StageChannel.last_message_id` always being ``None`` (:issue:`9422`).
- Fix piped audio input ending prematurely (:issue:`9001`, :issue:`9380`).
- Fix persistent detection for :class:`ui.TextInput` being incorrect if the ``custom_id`` is set later (:issue:`9438`).
- Fix custom attributes not being copied over when inheriting from :class:`app_commands.Group` (:issue:`9383`).
- Fix AutoMod audit log entry error due to empty channel_id (:issue:`9384`).
- Fix handling of ``around`` parameter in :meth:`abc.Messageable.history` (:issue:`9388`).
- Fix occasional :exc:`AttributeError` when accessing the :attr:`ClientUser.mutual_guilds` property (:issue:`9387`).
- Fix :func:`utils.escape_markdown` not escaping the new markdown (:issue:`9361`).
- Fix webhook targets not being converted in audit logs (:issue:`9332`).
- Fix error when not passing ``enabled`` in :meth:`Guild.create_automod_rule` (:issue:`9292`).
- Fix how various parameters are handled in :meth:`Guild.create_scheduled_event` (:issue:`9275`).
- Fix not sending the ``ssrc`` parameter when sending the SPEAKING payload (:issue:`9301`).
- Fix :attr:`Message.guild` being ``None`` sometimes when received via an interaction.
- Fix :attr:`Message.system_content` for :attr:`MessageType.channel_icon_change` (:issue:`9410`).

Miscellaneous
~~~~~~~~~~~~~~

- Update the base :attr:`Guild.filesize_limit` to 25MiB (:issue:`9353`).
- Allow Interaction webhook URLs to be used in :meth:`Webhook.from_url`.
- Set the socket family of internal connector to ``AF_INET`` to prevent IPv6 connections (:issue:`9442`, :issue:`9443`).

.. _vp2p2p3:

v2.2.3
-------

Bug Fixes
~~~~~~~~~~

- Fix crash from Discord sending null ``channel_id`` for automod audit logs.
- Fix ``channel`` edits when using :meth:`Webhook.edit` sending two requests.
- Fix :attr:`AuditLogEntry.target` being ``None`` for invites (:issue:`9336`).
- Fix :exc:`KeyError` when accessing data for :class:`GuildSticker` (:issue:`9324`).


.. _vp2p2p2:

v2.2.2
-------

Bug Fixes
~~~~~~~~~~

- Fix UDP discovery in voice not using new 74 byte layout which caused voice to break (:issue:`9277`, :issue:`9278`)

.. _vp2p2p0:

v2.2.0
-------

New Features
~~~~~~~~~~~~

- Add support for new :func:`on_audit_log_entry_create` event
- Add support for silent messages via ``silent`` parameter in :meth:`abc.Messageable.send`
    - This is queryable via :attr:`MessageFlags.suppress_notifications`

- Implement :class:`abc.Messageable` for :class:`StageChannel` (:issue:`9248`)
- Add setter for :attr:`discord.ui.ChannelSelect.channel_types` (:issue:`9068`)
- Add support for custom messages in automod via :attr:`AutoModRuleAction.custom_message` (:issue:`9267`)
- Add :meth:`ForumChannel.get_thread` (:issue:`9106`)
- Add :attr:`StageChannel.slowmode_delay` and :attr:`VoiceChannel.slowmode_delay` (:issue:`9111`)
- Add support for editing the slowmode for :class:`StageChannel` and :class:`VoiceChannel` (:issue:`9111`)
- Add :attr:`Locale.indonesian`
- Add ``delete_after`` keyword argument to :meth:`Interaction.edit_message` (:issue:`9415`)
- Add ``delete_after`` keyword argument to :meth:`InteractionMessage.edit` (:issue:`9206`)
- Add support for member flags (:issue:`9204`)
    - Accessible via :attr:`Member.flags` and has a type of :class:`MemberFlags`
    - Support ``bypass_verification`` within :meth:`Member.edit`

- Add support for passing a client to :meth:`Webhook.from_url` and :meth:`Webhook.partial`
    - This allows them to use views (assuming they are "bot owned" webhooks)

- Add :meth:`Colour.dark_embed` and :meth:`Colour.light_embed` (:issue:`9219`)
- Add support for many more parameters within :meth:`Guild.create_stage_channel` (:issue:`9245`)
- Add :attr:`AppInfo.role_connections_verification_url`
- Add support for :attr:`ForumChannel.default_layout`
- Add various new :class:`MessageType` values such as ones related to stage channel and role subscriptions
- Add support for role subscription related attributes
    - :class:`RoleSubscriptionInfo` within :attr:`Message.role_subscription`
    - :attr:`MessageType.role_subscription_purchase`
    - :attr:`SystemChannelFlags.role_subscription_purchase_notifications`
    - :attr:`SystemChannelFlags.role_subscription_purchase_notification_replies`
    - :attr:`RoleTags.subscription_listing_id`
    - :meth:`RoleTags.is_available_for_purchase`

- Add support for checking if a role is a linked role under :meth:`RoleTags.is_guild_connection`
- Add support for GIF sticker type
- Add support for :attr:`Message.application_id` and :attr:`Message.position`
- Add :func:`utils.maybe_coroutine` helper
- Add :attr:`ScheduledEvent.creator_id` attribute
- |commands| Add support for :meth:`~ext.commands.Cog.interaction_check` for :class:`~ext.commands.GroupCog` (:issue:`9189`)

Bug Fixes
~~~~~~~~~~

- Fix views not being removed from message store backing leading to a memory leak when used from an application command context
- Fix async iterators requesting past their bounds when using ``oldest_first`` and ``after`` or ``before`` (:issue:`9093`)
- Fix :meth:`Guild.audit_logs` pagination logic being buggy when using ``after`` (:issue:`9269`)
- Fix :attr:`Message.channel` sometimes being :class:`Object` instead of :class:`PartialMessageable`
- Fix :class:`ui.View` not properly calling ``super().__init_subclass__`` (:issue:`9231`)
- Fix ``available_tags`` and ``default_thread_slowmode_delay`` not being respected in :meth:`Guild.create_forum`
- Fix :class:`AutoModTrigger` ignoring ``allow_list`` with type keyword (:issue:`9107`)
- Fix implicit permission resolution for :class:`Thread` (:issue:`9153`)
- Fix :meth:`AutoModRule.edit` to work with actual snowflake types such as :class:`Object` (:issue:`9159`)
- Fix :meth:`Webhook.send` returning :class:`ForumChannel` for :attr:`WebhookMessage.channel`
- When a lookup for :attr:`AuditLogEntry.target` fails, it will fallback to :class:`Object` with the appropriate :attr:`Object.type` (:issue:`9171`)
- Fix :attr:`AuditLogDiff.type` for integrations returning :class:`ChannelType` instead of :class:`str` (:issue:`9200`)
- Fix :attr:`AuditLogDiff.type` for webhooks returning :class:`ChannelType` instead of :class:`WebhookType` (:issue:`9251`)
- Fix webhooks and interactions not properly closing files after the request has completed
- Fix :exc:`NameError` in audit log target for app commands
- Fix :meth:`ScheduledEvent.edit` requiring some arguments to be passed in when unnecessary (:issue:`9261`, :issue:`9268`)
- |commands| Explicit set a traceback for hybrid command invocations (:issue:`9205`)

Miscellaneous
~~~~~~~~~~~~~~

- Add colour preview for the colours predefined in :class:`Colour`
- Finished views are no longer stored by the library when sending them (:issue:`9235`)
- Force enable colour logging for the default logging handler when run under Docker.
- Add various overloads for :meth:`Client.wait_for` to aid in static analysis (:issue:`9184`)
- :class:`Interaction` can now optionally take a generic parameter, ``ClientT`` to represent the type for :attr:`Interaction.client`
- |commands| Respect :attr:`~ext.commands.Command.ignore_extra` for :class:`~discord.ext.commands.FlagConverter` keyword-only parameters
- |commands| Change :attr:`Paginator.pages <ext.commands.Paginator.pages>` to not prematurely close (:issue:`9257`)

.. _vp2p1p1:

v2.1.1
-------

Bug Fixes
~~~~~~~~~~

- Fix crash involving GIF stickers when looking up their filename extension.

.. _vp2p1p0:

v2.1.0
-------

New Features
~~~~~~~~~~~~

- Add support for ``delete_message_seconds`` in :meth:`Guild.ban` (:issue:`8391`)
- Add support for automod related audit log actions (:issue:`8389`)
- Add support for :class:`ForumChannel` annotations in app commands
- Add support for :attr:`ForumChannel.default_thread_slowmode_delay`.
- Add support for :attr:`ForumChannel.default_reaction_emoji`.
- Add support for forum tags under :class:`ForumTag`.
    - Tags can be obtained using :attr:`ForumChannel.available_tags` or :meth:`ForumChannel.get_tag`.
    - See :meth:`Thread.edit` and :meth:`ForumChannel.edit` for modifying tags and their usage.

- Add support for new select types (:issue:`9013`, :issue:`9003`).
    - These are split into separate classes, :class:`~discord.ui.ChannelSelect`, :class:`~discord.ui.RoleSelect`, :class:`~discord.ui.UserSelect`, :class:`~discord.ui.MentionableSelect`.
    - The decorator still uses a single function, :meth:`~discord.ui.select`. Changing the select type is done by the ``cls`` keyword parameter.

- Add support for toggling discoverable and invites_disabled features in :meth:`Guild.edit` (:issue:`8390`).
- Add :meth:`Interaction.translate` helper method (:issue:`8425`).
- Add :meth:`Forum.archived_threads` (:issue:`8476`).
- Add :attr:`ApplicationFlags.active`, :attr:`UserFlags.active_developer`, and :attr:`PublicUserFlags.active_developer`.
- Add ``delete_after`` to :meth:`InteractionResponse.send_message` (:issue:`9022`).
- Add support for :attr:`AutoModTrigger.regex_patterns`.
- |commands| Add :attr:`GroupCog.group_extras <discord.ext.commands.GroupCog.group_extras>` to set :attr:`app_commands.Group.extras` (:issue:`8405`).
- |commands| Add support for NumPy style docstrings for regular commands to set parameter descriptions.
- |commands| Allow :class:`~discord.ext.commands.Greedy` to potentially maintain state between calls.
- |commands| Add :meth:`Cog.has_app_command_error_handler <discord.ext.commands.Cog.has_app_command_error_handler>` (:issue:`8991`).
- |commands| Allow ``delete_after`` in :meth:`Context.send <discord.ext.commands.Context.send>` on ephemeral messages (:issue:`9021`).

Bug Fixes
~~~~~~~~~

- Fix an :exc:`KeyError` being raised when constructing :class:`app_commands.Group` with no module (:issue:`8411`).
- Fix unescaped period in webhook URL regex (:issue:`8443`).
- Fix :exc:`app_commands.CommandSyncFailure` raising for other 400 status code errors.
- Fix potential formatting issues showing `_errors` in :exc:`app_commands.CommandSyncFailure`.
- Fix :attr:`Guild.stage_instances` and :attr:`Guild.schedule_events` clearing on ``GUILD_UPDATE``.
- Fix detection of overriden :meth:`app_commands.Group.on_error`
- Fix :meth:`app_commands.CommandTree.on_error` still being called when a bound error handler is set.
- Fix thread permissions being set to ``True`` in :meth:`DMChannel.permissions_for` (:issue:`8965`).
- Fix ``on_scheduled_event_delete`` occasionally dispatching with too many parameters (:issue:`9019`).
- |commands| Fix :meth:`Context.from_interaction <discord.ext.commands.Context.from_interaction>` ignoring :attr:`~discord.ext.commands.Context.command_failed`.
- |commands| Fix :class:`~discord.ext.commands.Range` to allow 3.10 Union syntax (:issue:`8446`).
- |commands| Fix ``before_invoke`` not triggering for fallback commands in a hybrid group command (:issue:`8461`, :issue:`8462`).

Miscellaneous
~~~~~~~~~~~~~

- Change error message for unbound callbacks in :class:`app_commands.ContextMenu` to make it clearer that bound methods are not allowed.
- Normalize type formatting in TypeError exceptions (:issue:`8453`).
- Change :meth:`VoiceProtocol.on_voice_state_update` and :meth:`VoiceProtocol.on_voice_server_update` parameters to be positional only (:issue:`8463`).
- Add support for PyCharm when using the default coloured logger (:issue:`9015`).

.. _vp2p0p1:

v2.0.1
-------

Bug Fixes
~~~~~~~~~~

- Fix ``cchardet`` being installed on Python >=3.10 when using the ``speed`` extras.
- Fix :class:`ui.View` timeout updating when the :meth:`ui.View.interaction_check` failed.
- Fix :meth:`app_commands.CommandTree.on_error` not triggering if :meth:`~app_commands.CommandTree.interaction_check` raises.
- Fix ``__main__`` script to use ``importlib.metadata`` instead of the deprecated ``pkg_resources``.
- Fix library callbacks triggering a type checking error if the parameter names were different.
    - This required a change in the :ref:`version_guarantees`

- |commands| Fix Python 3.10 union types not working with :class:`commands.Greedy <discord.ext.commands.Greedy>`.

.. _vp2p0p0:

v2.0.0
--------

The changeset for this version are too big to be listed here, for more information please
see :ref:`the migrating page <migrating_2_0>`.

.. _vp1p7p3:

v1.7.3
--------

Bug Fixes
~~~~~~~~~~

- Fix a crash involving guild uploaded stickers
- Fix :meth:`DMChannel.permissions_for` not having :attr:`Permissions.read_messages` set.

.. _vp1p7p2:

v1.7.2
-------

Bug Fixes
~~~~~~~~~~~

- Fix ``fail_if_not_exists`` causing certain message references to not be usable within :meth:`abc.Messageable.send` and :meth:`Message.reply` (:issue:`6726`)
- Fix :meth:`Guild.chunk` hanging when the user left the guild. (:issue:`6730`)
- Fix loop sleeping after final iteration rather than before (:issue:`6744`)

.. _vp1p7p1:

v1.7.1
-------

Bug Fixes
~~~~~~~~~~~

- |commands| Fix :meth:`Cog.has_error_handler <ext.commands.Cog.has_error_handler>` not working as intended.

.. _vp1p7p0:

v1.7.0
--------

This version is mainly for improvements and bug fixes. This is more than likely the last major version in the 1.x series.
Work after this will be spent on v2.0. As a result, **this is the last version to support Python 3.5**.
Likewise, **this is the last version to support user bots**.

Development of v2.0 will have breaking changes and support for newer API features.

New Features
~~~~~~~~~~~~~~

- Add support for stage channels via :class:`StageChannel` (:issue:`6602`, :issue:`6608`)
- Add support for :attr:`MessageReference.fail_if_not_exists` (:issue:`6484`)
    - By default, if the message you're replying to doesn't exist then the API errors out.
      This attribute tells the Discord API that it's okay for that message to be missing.

- Add support for Discord's new permission serialisation scheme.
- Add an easier way to move channels using :meth:`abc.GuildChannel.move`
- Add :attr:`Permissions.use_slash_commands`
- Add :attr:`Permissions.request_to_speak`
- Add support for voice regions in voice channels via :attr:`VoiceChannel.rtc_region` (:issue:`6606`)
- Add support for :meth:`PartialEmoji.url_as` (:issue:`6341`)
- Add :attr:`MessageReference.jump_url` (:issue:`6318`)
- Add :attr:`File.spoiler` (:issue:`6317`)
- Add support for passing ``roles`` to :meth:`Guild.estimate_pruned_members` (:issue:`6538`)
- Allow callable class factories to be used in :meth:`abc.Connectable.connect` (:issue:`6478`)
- Add a way to get mutual guilds from the client's cache via :attr:`User.mutual_guilds` (:issue:`2539`, :issue:`6444`)
- :meth:`PartialMessage.edit` now returns a full :class:`Message` upon success (:issue:`6309`)
- Add :attr:`RawMessageUpdateEvent.guild_id` (:issue:`6489`)
- :class:`AuditLogEntry` is now hashable (:issue:`6495`)
- :class:`Attachment` is now hashable
- Add :attr:`Attachment.content_type` attribute (:issue:`6618`)
- Add support for casting :class:`Attachment` to :class:`str` to get the URL.
- Add ``seed`` parameter for :class:`Colour.random` (:issue:`6562`)
    - This only seeds it for one call. If seeding for multiple calls is desirable, use :func:`random.seed`.

- Add a :func:`utils.remove_markdown` helper function (:issue:`6573`)
- Add support for passing scopes to :func:`utils.oauth_url` (:issue:`6568`)
- |commands| Add support for ``rgb`` CSS function as a parameter to :class:`ColourConverter <ext.commands.ColourConverter>` (:issue:`6374`)
- |commands| Add support for converting :class:`StoreChannel` via :class:`StoreChannelConverter <ext.commands.StoreChannelConverter>` (:issue:`6603`)
- |commands| Add support for stripping whitespace after the prefix is encountered using the ``strip_after_prefix`` :class:`~ext.commands.Bot` constructor parameter.
- |commands| Add :attr:`Context.invoked_parents <ext.commands.Context.invoked_parents>` to get the aliases a command's parent was invoked with (:issue:`1874`, :issue:`6462`)
- |commands| Add a converter for :class:`PartialMessage` under :class:`ext.commands.PartialMessageConverter` (:issue:`6308`)
- |commands| Add a converter for :class:`Guild` under :class:`ext.commands.GuildConverter` (:issue:`6016`, :issue:`6365`)
- |commands| Add :meth:`Command.has_error_handler <ext.commands.Command.has_error_handler>`
    - This is also adds :meth:`Cog.has_error_handler <ext.commands.Cog.has_error_handler>`
- |commands| Allow callable types to act as a bucket key for cooldowns (:issue:`6563`)
- |commands| Add ``linesep`` keyword argument to :class:`Paginator <ext.commands.Paginator>` (:issue:`5975`)
- |commands| Allow ``None`` to be passed to :attr:`HelpCommand.verify_checks <ext.commands.HelpCommand.verify_checks>` to only verify in a guild context (:issue:`2008`, :issue:`6446`)
- |commands| Allow relative paths when loading extensions via a ``package`` keyword argument (:issue:`2465`, :issue:`6445`)

Bug Fixes
~~~~~~~~~~

- Fix mentions not working if ``mention_author`` is passed in :meth:`abc.Messageable.send` without :attr:`Client.allowed_mentions` set (:issue:`6192`, :issue:`6458`)
- Fix user created instances of :class:`CustomActivity` triggering an error (:issue:`4049`)
    - Note that currently, bot users still cannot set a custom activity due to a Discord limitation.
- Fix :exc:`ZeroDivisionError` being raised from :attr:`VoiceClient.average_latency` (:issue:`6430`, :issue:`6436`)
- Fix :attr:`User.public_flags` not updating upon edit (:issue:`6315`)
- Fix :attr:`Message.call` sometimes causing attribute errors (:issue:`6390`)
- Fix issue resending a file during request retries on newer versions of ``aiohttp`` (:issue:`6531`)
- Raise an error when ``user_ids`` is empty in :meth:`Guild.query_members`
- Fix ``__str__`` magic method raising when a :class:`Guild` is unavailable.
- Fix potential :exc:`AttributeError` when accessing :attr:`VoiceChannel.members` (:issue:`6602`)
- :class:`Embed` constructor parameters now implicitly convert to :class:`str` (:issue:`6574`)
- Ensure ``discord`` package is only run if executed as a script (:issue:`6483`)
- |commands| Fix irrelevant commands potentially being unloaded during cog unload due to failure.
- |commands| Fix attribute errors when setting a cog to :class:`~.ext.commands.HelpCommand` (:issue:`5154`)
- |commands| Fix :attr:`Context.invoked_with <ext.commands.Context.invoked_with>` being improperly reassigned during a :meth:`~ext.commands.Context.reinvoke` (:issue:`6451`, :issue:`6462`)
- |commands| Remove duplicates from :meth:`HelpCommand.get_bot_mapping <ext.commands.HelpCommand.get_bot_mapping>` (:issue:`6316`)
- |commands| Properly handle positional-only parameters in bot command signatures (:issue:`6431`)
- |commands| Group signatures now properly show up in :attr:`Command.signature <ext.commands.Command.signature>` (:issue:`6529`, :issue:`6530`)

Miscellaneous
~~~~~~~~~~~~~~

- User endpoints and all userbot related functionality has been deprecated and will be removed in the next major version of the library.
- :class:`Permission` class methods were updated to match the UI of the Discord client (:issue:`6476`)
- ``_`` and ``-`` characters are now stripped when making a new cog using the ``discord`` package (:issue:`6313`)

.. _vp1p6p0:

v1.6.0
--------

This version comes with support for replies and stickers.

New Features
~~~~~~~~~~~~~~

- An entirely redesigned documentation. This was the cumulation of multiple months of effort.
    - There's now a dark theme, feel free to navigate to the cog on the screen to change your setting, though this should be automatic.
- Add support for :meth:`AppInfo.icon_url_as` and :meth:`AppInfo.cover_image_url_as` (:issue:`5888`)
- Add :meth:`Colour.random` to get a random colour (:issue:`6067`)
- Add support for stickers via :class:`Sticker` (:issue:`5946`)
- Add support for replying via :meth:`Message.reply` (:issue:`6061`)
    - This also comes with the :attr:`AllowedMentions.replied_user` setting.
    - :meth:`abc.Messageable.send` can now accept a :class:`MessageReference`.
    - :class:`MessageReference` can now be constructed by users.
    - :meth:`Message.to_reference` can now convert a message to a :class:`MessageReference`.
- Add support for getting the replied to resolved message through :attr:`MessageReference.resolved`.
- Add support for role tags.
    - :attr:`Guild.premium_subscriber_role` to get the "Nitro Booster" role (if available).
    - :attr:`Guild.self_role` to get the bot's own role (if available).
    - :attr:`Role.tags` to get the role's tags.
    - :meth:`Role.is_premium_subscriber` to check if a role is the "Nitro Booster" role.
    - :meth:`Role.is_bot_managed` to check if a role is a bot role (i.e. the automatically created role for bots).
    - :meth:`Role.is_integration` to check if a role is role created by an integration.
- Add :meth:`Client.is_ws_ratelimited` to check if the websocket is rate limited.
    - :meth:`ShardInfo.is_ws_ratelimited` is the equivalent for checking a specific shard.
- Add support for chunking an :class:`AsyncIterator` through :meth:`AsyncIterator.chunk` (:issue:`6100`, :issue:`6082`)
- Add :attr:`PartialEmoji.created_at` (:issue:`6128`)
- Add support for editing and deleting webhook sent messages (:issue:`6058`)
    - This adds :class:`WebhookMessage` as well to power this behaviour.
- Add :class:`PartialMessage` to allow working with a message via channel objects and just a message_id (:issue:`5905`)
    - This is useful if you don't want to incur an extra API call to fetch the message.
- Add :meth:`Emoji.url_as` (:issue:`6162`)
- Add support for :attr:`Member.pending` for the membership gating feature.
- Allow ``colour`` parameter to take ``int`` in :meth:`Guild.create_role` (:issue:`6195`)
- Add support for ``presences`` in :meth:`Guild.query_members` (:issue:`2354`)
- |commands| Add support for ``description`` keyword argument in :class:`commands.Cog <ext.commands.Cog>` (:issue:`6028`)
- |tasks| Add support for calling the wrapped coroutine as a function via ``__call__``.


Bug Fixes
~~~~~~~~~~~

- Raise :exc:`DiscordServerError` when reaching 503s repeatedly (:issue:`6044`)
- Fix :exc:`AttributeError` when :meth:`Client.fetch_template` is called (:issue:`5986`)
- Fix errors when playing audio and moving to another channel (:issue:`5953`)
- Fix :exc:`AttributeError` when voice channels disconnect too fast (:issue:`6039`)
- Fix stale :class:`User` references when the members intent is off.
- Fix :func:`on_user_update` not dispatching in certain cases when a member is not cached but the user somehow is.
- Fix :attr:`Message.author` being overwritten in certain cases during message update.
    - This would previously make it so :attr:`Message.author` is a :class:`User`.
- Fix :exc:`UnboundLocalError` for editing ``public_updates_channel`` in :meth:`Guild.edit` (:issue:`6093`)
- Fix uninitialised :attr:`CustomActivity.created_at` (:issue:`6095`)
- |commands| Errors during cog unload no longer stops module cleanup (:issue:`6113`)
- |commands| Properly cleanup lingering commands when a conflicting alias is found when adding commands (:issue:`6217`)

Miscellaneous
~~~~~~~~~~~~~~~

- ``ffmpeg`` spawned processes no longer open a window in Windows (:issue:`6038`)
- Update dependencies to allow the library to work on Python 3.9+ without requiring build tools. (:issue:`5984`, :issue:`5970`)
- Fix docstring issue leading to a SyntaxError in 3.9 (:issue:`6153`)
- Update Windows opus binaries from 1.2.1 to 1.3.1 (:issue:`6161`)
- Allow :meth:`Guild.create_role` to accept :class:`int` as the ``colour`` parameter (:issue:`6195`)
- |commands| :class:`MessageConverter <ext.commands.MessageConverter>` regex got updated to support ``www.`` prefixes (:issue:`6002`)
- |commands| :class:`UserConverter <ext.commands.UserConverter>` now fetches the API if an ID is passed and the user is not cached.
- |commands| :func:`max_concurrency <ext.commands.max_concurrency>` is now called before cooldowns (:issue:`6172`)

.. _vp1p5p1:

v1.5.1
-------

Bug Fixes
~~~~~~~~~~~

- Fix :func:`utils.escape_markdown` not escaping quotes properly (:issue:`5897`)
- Fix :class:`Message` not being hashable (:issue:`5901`, :issue:`5866`)
- Fix moving channels to the end of the channel list (:issue:`5923`)
- Fix seemingly strange behaviour in ``__eq__`` for :class:`PermissionOverwrite` (:issue:`5929`)
- Fix aliases showing up in ``__iter__`` for :class:`Intents` (:issue:`5945`)
- Fix the bot disconnecting from voice when moving them to another channel (:issue:`5904`)
- Fix attribute errors when chunking times out sometimes during delayed on_ready dispatching.
- Ensure that the bot's own member is not evicted from the cache (:issue:`5949`)

Miscellaneous
~~~~~~~~~~~~~~

- Members are now loaded during ``GUILD_MEMBER_UPDATE`` events if :attr:`MemberCacheFlags.joined` is set. (:issue:`5930`)
- |commands| :class:`MemberConverter <ext.commands.MemberConverter>` now properly lazily fetches members if not available from cache.
    - This is the same as having ``discord.Member`` as the type-hint.
- :meth:`Guild.chunk` now allows concurrent calls without spamming the gateway with requests.

.. _vp1p5p0:

v1.5.0
--------

This version came with forced breaking changes that Discord is requiring all bots to go through on October 7th. It is highly recommended to read the documentation on intents, :ref:`intents_primer`.

API Changes
~~~~~~~~~~~~~

- Members and presences will no longer be retrieved due to an API change. See :ref:`privileged_intents` for more info.
- As a consequence, fetching offline members is disabled if the members intent is not enabled.

New Features
~~~~~~~~~~~~~~

- Support for gateway intents, passed via ``intents`` in :class:`Client` using :class:`Intents`.
- Add :attr:`VoiceRegion.south_korea` (:issue:`5233`)
- Add support for ``__eq__`` for :class:`Message` (:issue:`5789`)
- Add :meth:`Colour.dark_theme` factory method (:issue:`1584`)
- Add :meth:`AllowedMentions.none` and :meth:`AllowedMentions.all` (:issue:`5785`)
- Add more concrete exceptions for 500 class errors under :class:`DiscordServerError` (:issue:`5797`)
- Implement :class:`VoiceProtocol` to better intersect the voice flow.
- Add :meth:`Guild.chunk` to fully chunk a guild.
- Add :class:`MemberCacheFlags` to better control member cache. See :ref:`intents_member_cache` for more info.
- Add support for :attr:`ActivityType.competing` (:issue:`5823`)
    - This seems currently unused API wise.

- Add support for message references, :attr:`Message.reference` (:issue:`5754`, :issue:`5832`)
- Add alias for :class:`ColourConverter` under ``ColorConverter`` (:issue:`5773`)
- Add alias for :attr:`PublicUserFlags.verified_bot_developer` under :attr:`PublicUserFlags.early_verified_bot_developer` (:issue:`5849`)
- |commands| Add support for ``require_var_positional`` for :class:`Command` (:issue:`5793`)

Bug Fixes
~~~~~~~~~~

- Fix issue with :meth:`Guild.by_category` not showing certain channels.
- Fix :attr:`abc.GuildChannel.permissions_synced` always being ``False`` (:issue:`5772`)
- Fix handling of cloudflare bans on webhook related requests (:issue:`5221`)
- Fix cases where a keep-alive thread would ack despite already dying (:issue:`5800`)
- Fix cases where a :class:`Member` reference would be stale when cache is disabled in message events (:issue:`5819`)
- Fix ``allowed_mentions`` not being sent when sending a single file (:issue:`5835`)
- Fix ``overwrites`` being ignored in :meth:`abc.GuildChannel.edit` if ``{}`` is passed (:issue:`5756`, :issue:`5757`)
- |commands| Fix exceptions being raised improperly in command invoke hooks (:issue:`5799`)
- |commands| Fix commands not being properly ejected during errors in a cog injection (:issue:`5804`)
- |commands| Fix cooldown timing ignoring edited timestamps.
- |tasks| Fix tasks extending the next iteration on handled exceptions (:issue:`5762`, :issue:`5763`)

Miscellaneous
~~~~~~~~~~~~~~~

- Webhook requests are now logged (:issue:`5798`)
- Remove caching layer from :attr:`AutoShardedClient.shards`. This was causing issues if queried before launching shards.
- Gateway rate limits are now handled.
- Warnings logged due to missed caches are now changed to DEBUG log level.
- Some strings are now explicitly interned to reduce memory usage.
- Usage of namedtuples has been reduced to avoid potential breaking changes in the future (:issue:`5834`)
- |commands| All :class:`BadArgument` exceptions from the built-in converters now raise concrete exceptions to better tell them apart (:issue:`5748`)
- |tasks| Lazily fetch the event loop to prevent surprises when changing event loop policy (:issue:`5808`)

.. _vp1p4p2:

v1.4.2
--------

This is a maintenance release with backports from :ref:`vp1p5p0`.

Bug Fixes
~~~~~~~~~~~

- Fix issue with :meth:`Guild.by_category` not showing certain channels.
- Fix :attr:`abc.GuildChannel.permissions_synced` always being ``False`` (:issue:`5772`)
- Fix handling of cloudflare bans on webhook related requests (:issue:`5221`)
- Fix cases where a keep-alive thread would ack despite already dying (:issue:`5800`)
- Fix cases where a :class:`Member` reference would be stale when cache is disabled in message events (:issue:`5819`)
- Fix ``allowed_mentions`` not being sent when sending a single file (:issue:`5835`)
- Fix ``overwrites`` being ignored in :meth:`abc.GuildChannel.edit` if ``{}`` is passed (:issue:`5756`, :issue:`5757`)
- |commands| Fix exceptions being raised improperly in command invoke hooks (:issue:`5799`)
- |commands| Fix commands not being properly ejected during errors in a cog injection (:issue:`5804`)
- |commands| Fix cooldown timing ignoring edited timestamps.
- |tasks| Fix tasks extending the next iteration on handled exceptions (:issue:`5762`, :issue:`5763`)

Miscellaneous
~~~~~~~~~~~~~~~

- Remove caching layer from :attr:`AutoShardedClient.shards`. This was causing issues if queried before launching shards.
- |tasks| Lazily fetch the event loop to prevent surprises when changing event loop policy (:issue:`5808`)

.. _vp1p4p1:

v1.4.1
--------

Bug Fixes
~~~~~~~~~~~

- Properly terminate the connection when :meth:`Client.close` is called (:issue:`5207`)
- Fix error being raised when clearing embed author or image when it was already cleared (:issue:`5210`, :issue:`5212`)
- Fix ``__path__`` to allow editable extensions (:issue:`5213`)

.. _vp1p4p0:

v1.4.0
--------

Another version with a long development time. Features like Intents are slated to be released in a v1.5 release. Thank you for your patience!

New Features
~~~~~~~~~~~~~~

- Add support for :class:`AllowedMentions` to have more control over what gets mentioned.
    - This can be set globally through :attr:`Client.allowed_mentions`
    - This can also be set on a per message basis via :meth:`abc.Messageable.send`

- :class:`AutoShardedClient` has been completely redesigned from the ground up to better suit multi-process clusters (:issue:`2654`)
    - Add :class:`ShardInfo` which allows fetching specific information about a shard.
    - The :class:`ShardInfo` allows for reconnecting and disconnecting of a specific shard as well.
    - Add :meth:`AutoShardedClient.get_shard` and :attr:`AutoShardedClient.shards` to get information about shards.
    - Rework the entire connection flow to better facilitate the ``IDENTIFY`` rate limits.
    - Add a hook :meth:`Client.before_identify_hook` to have better control over what happens before an ``IDENTIFY`` is done.
    - Add more shard related events such as :func:`on_shard_connect`, :func:`on_shard_disconnect` and :func:`on_shard_resumed`.

- Add support for guild templates (:issue:`2652`)
    - This adds :class:`Template` to read a template's information.
    - :meth:`Client.fetch_template` can be used to fetch a template's information from the API.
    - :meth:`Client.create_guild` can now take an optional template to base the creation from.
    - Note that fetching a guild's template is currently restricted for bot accounts.

- Add support for guild integrations (:issue:`2051`, :issue:`1083`)
    - :class:`Integration` is used to read integration information.
    - :class:`IntegrationAccount` is used to read integration account information.
    - :meth:`Guild.integrations` will fetch all integrations in a guild.
    - :meth:`Guild.create_integration` will create an integration.
    - :meth:`Integration.edit` will edit an existing integration.
    - :meth:`Integration.delete` will delete an integration.
    - :meth:`Integration.sync` will sync an integration.
    - There is currently no support in the audit log for this.

- Add an alias for :attr:`VerificationLevel.extreme` under :attr:`VerificationLevel.very_high` (:issue:`2650`)
- Add various grey to gray aliases for :class:`Colour` (:issue:`5130`)
- Added :attr:`VoiceClient.latency` and :attr:`VoiceClient.average_latency` (:issue:`2535`)
- Add ``use_cached`` and ``spoiler`` parameters to :meth:`Attachment.to_file` (:issue:`2577`, :issue:`4095`)
- Add ``position`` parameter support to :meth:`Guild.create_category` (:issue:`2623`)
- Allow passing ``int`` for the colour in :meth:`Role.edit` (:issue:`4057`)
- Add :meth:`Embed.remove_author` to clear author information from an embed (:issue:`4068`)
- Add the ability to clear images and thumbnails in embeds using :attr:`Embed.Empty` (:issue:`4053`)
- Add :attr:`Guild.max_video_channel_users` (:issue:`4120`)
- Add :attr:`Guild.public_updates_channel` (:issue:`4120`)
- Add ``guild_ready_timeout`` parameter to :class:`Client` and subclasses to control timeouts when the ``GUILD_CREATE`` stream takes too long (:issue:`4112`)
- Add support for public user flags via :attr:`User.public_flags` and :class:`PublicUserFlags` (:issue:`3999`)
- Allow changing of channel types via :meth:`TextChannel.edit` to and from a news channel (:issue:`4121`)
- Add :meth:`Guild.edit_role_positions` to bulk edit role positions in a single API call (:issue:`2501`, :issue:`2143`)
- Add :meth:`Guild.change_voice_state` to change your voice state in a guild (:issue:`5088`)
- Add :meth:`PartialInviteGuild.is_icon_animated` for checking if the invite guild has animated icon (:issue:`4180`, :issue:`4181`)
- Add :meth:`PartialInviteGuild.icon_url_as` now supports ``static_format`` for consistency (:issue:`4180`, :issue:`4181`)
- Add support for ``user_ids`` in :meth:`Guild.query_members`
- Add support for pruning members by roles in :meth:`Guild.prune_members` (:issue:`4043`)
- |commands| Implement :func:`~ext.commands.before_invoke` and :func:`~ext.commands.after_invoke` decorators (:issue:`1986`, :issue:`2502`)
- |commands| Add a way to retrieve ``retry_after`` from a cooldown in a command via :meth:`Command.get_cooldown_retry_after <.ext.commands.Command.get_cooldown_retry_after>` (:issue:`5195`)
- |commands| Add a way to dynamically add and remove checks from a :class:`HelpCommand <.ext.commands.HelpCommand>` (:issue:`5197`)
- |tasks| Add :meth:`Loop.is_running <.ext.tasks.Loop.is_running>` method to the task objects (:issue:`2540`)
- |tasks| Allow usage of custom error handlers similar to the command extensions to tasks using :meth:`Loop.error <.ext.tasks.Loop.error>` decorator (:issue:`2621`)


Bug Fixes
~~~~~~~~~~~~

- Fix issue with :attr:`PartialEmoji.url` reads leading to a failure (:issue:`4015`, :issue:`4016`)
- Allow :meth:`abc.Messageable.history` to take a limit of ``1`` even if ``around`` is passed (:issue:`4019`)
- Fix :attr:`Guild.member_count` not updating in certain cases when a member has left the guild (:issue:`4021`)
- Fix the type of :attr:`Object.id` not being validated. For backwards compatibility ``str`` is still allowed but is converted to ``int`` (:issue:`4002`)
- Fix :meth:`Guild.edit` not allowing editing of notification settings (:issue:`4074`, :issue:`4047`)
- Fix crash when the guild widget contains channels that aren't in the payload (:issue:`4114`, :issue:`4115`)
- Close ffmpeg stdin handling from spawned processes with :class:`FFmpegOpusAudio` and :class:`FFmpegPCMAudio` (:issue:`4036`)
- Fix :func:`utils.escape_markdown` not escaping masked links (:issue:`4206`, :issue:`4207`)
- Fix reconnect loop due to failed handshake on region change (:issue:`4210`, :issue:`3996`)
- Fix :meth:`Guild.by_category` not returning empty categories (:issue:`4186`)
- Fix certain JPEG images not being identified as JPEG (:issue:`5143`)
- Fix a crash when an incomplete guild object is used when fetching reaction information (:issue:`5181`)
- Fix a timeout issue when fetching members using :meth:`Guild.query_members`
- Fix an issue with domain resolution in voice (:issue:`5188`, :issue:`5191`)
- Fix an issue where :attr:`PartialEmoji.id` could be a string (:issue:`4153`, :issue:`4152`)
- Fix regression where :attr:`Member.activities` would not clear.
- |commands| A :exc:`TypeError` is now raised when :obj:`typing.Optional` is used within :data:`commands.Greedy <.ext.commands.Greedy>` (:issue:`2253`, :issue:`5068`)
- |commands| :meth:`Bot.walk_commands <.ext.commands.Bot.walk_commands>` no longer yields duplicate commands due to aliases (:issue:`2591`)
- |commands| Fix regex characters not being escaped in :attr:`HelpCommand.clean_prefix <.ext.commands.HelpCommand.clean_prefix>` (:issue:`4058`, :issue:`4071`)
- |commands| Fix :meth:`Bot.get_command <.ext.commands.Bot.get_command>` from raising errors when a name only has whitespace (:issue:`5124`)
- |commands| Fix issue with :attr:`Context.subcommand_passed <.ext.commands.Context.subcommand_passed>` not functioning as expected (:issue:`5198`)
- |tasks| Task objects are no longer stored globally so two class instances can now start two separate tasks (:issue:`2294`)
- |tasks| Allow cancelling the loop within :meth:`before_loop <.ext.tasks.Loop.before_loop>` (:issue:`4082`)


Miscellaneous
~~~~~~~~~~~~~~~

- The :attr:`Member.roles` cache introduced in v1.3 was reverted due to issues caused (:issue:`4087`, :issue:`4157`)
- :class:`Webhook` objects are now comparable and hashable (:issue:`4182`)
- Some more API requests got a ``reason`` parameter for audit logs (:issue:`5086`)
    - :meth:`TextChannel.follow`
    - :meth:`Message.pin` and :meth:`Message.unpin`
    - :meth:`Webhook.delete` and :meth:`Webhook.edit`

- For performance reasons ``websockets`` has been dropped in favour of ``aiohttp.ws``.
- The blocking logging message now shows the stack trace of where the main thread was blocking
- The domain name was changed from ``discordapp.com`` to ``discord.com`` to prepare for the required domain migration
- Reduce memory usage when reconnecting due to stale references being held by the message cache (:issue:`5133`)
- Optimize :meth:`abc.GuildChannel.permissions_for` by not creating as many temporary objects (20-32% savings).
- |commands| Raise :exc:`~ext.commands.CommandRegistrationError` instead of :exc:`ClientException` when a duplicate error is registered (:issue:`4217`)
- |tasks| No longer handle :exc:`HTTPException` by default in the task reconnect loop (:issue:`5193`)

.. _vp1p3p4:

v1.3.4
--------

Bug Fixes
~~~~~~~~~~~

- Fix an issue with channel overwrites causing multiple issues including crashes (:issue:`5109`)

.. _vp1p3p3:

v1.3.3
--------

Bug Fixes
~~~~~~~~~~~~

- Change default WS close to 4000 instead of 1000.
    - The previous close code caused sessions to be invalidated at a higher frequency than desired.

- Fix ``None`` appearing in ``Member.activities``. (:issue:`2619`)

.. _vp1p3p2:

v1.3.2
---------

Another minor bug fix release.

Bug Fixes
~~~~~~~~~~~

- Higher the wait time during the ``GUILD_CREATE`` stream before ``on_ready`` is fired for :class:`AutoShardedClient`.
- :func:`on_voice_state_update` now uses the inner ``member`` payload which should make it more reliable.
- Fix various Cloudflare handling errors (:issue:`2572`, :issue:`2544`)
- Fix crashes if :attr:`Message.guild` is :class:`Object` instead of :class:`Guild`.
- Fix :meth:`Webhook.send` returning an empty string instead of ``None`` when ``wait=False``.
- Fix invalid format specifier in webhook state (:issue:`2570`)
- |commands| Passing invalid permissions to permission related checks now raises ``TypeError``.

.. _vp1p3p1:

v1.3.1
--------

Minor bug fix release.

Bug Fixes
~~~~~~~~~~~

- Fix fetching invites in guilds that the user is not in.
- Fix the channel returned from :meth:`Client.fetch_channel` raising when sending messages. (:issue:`2531`)

Miscellaneous
~~~~~~~~~~~~~~

- Fix compatibility warnings when using the Python 3.9 alpha.
- Change the unknown event logging from WARNING to DEBUG to reduce noise.

.. _vp1p3p0:

v1.3.0
--------

This version comes with a lot of bug fixes and new features. It's been in development for a lot longer than was anticipated!

New Features
~~~~~~~~~~~~~~

- Add :meth:`Guild.fetch_members` to fetch members from the HTTP API. (:issue:`2204`)
- Add :meth:`Guild.fetch_roles` to fetch roles from the HTTP API. (:issue:`2208`)
- Add support for teams via :class:`Team` when fetching with :meth:`Client.application_info`. (:issue:`2239`)
- Add support for suppressing embeds via :meth:`Message.edit`
- Add support for guild subscriptions. See the :class:`Client` documentation for more details.
- Add :attr:`VoiceChannel.voice_states` to get voice states without relying on member cache.
- Add :meth:`Guild.query_members` to request members from the gateway.
- Add :class:`FFmpegOpusAudio` and other voice improvements. (:issue:`2258`)
- Add :attr:`RawMessageUpdateEvent.channel_id` for retrieving channel IDs during raw message updates. (:issue:`2301`)
- Add :attr:`RawReactionActionEvent.event_type` to disambiguate between reaction addition and removal in reaction events.
- Add :attr:`abc.GuildChannel.permissions_synced` to query whether permissions are synced with the category. (:issue:`2300`, :issue:`2324`)
- Add :attr:`MessageType.channel_follow_add` message type for announcement channels being followed. (:issue:`2314`)
- Add :meth:`Message.is_system` to allow for quickly filtering through system messages.
- Add :attr:`VoiceState.self_stream` to indicate whether someone is streaming via Go Live. (:issue:`2343`)
- Add :meth:`Emoji.is_usable` to check if the client user can use an emoji. (:issue:`2349`)
- Add :attr:`VoiceRegion.europe` and :attr:`VoiceRegion.dubai`. (:issue:`2358`, :issue:`2490`)
- Add :meth:`TextChannel.follow` to follow a news channel. (:issue:`2367`)
- Add :attr:`Permissions.view_guild_insights` permission. (:issue:`2415`)
- Add support for new audit log types. See :ref:`discord-api-audit-logs` for more information. (:issue:`2427`)
    - Note that integration support is not finalized.

- Add :attr:`Webhook.type` to query the type of webhook (:class:`WebhookType`). (:issue:`2441`)
- Allow bulk editing of channel overwrites through :meth:`abc.GuildChannel.edit`. (:issue:`2198`)
- Add :class:`Activity.created_at` to see when an activity was started. (:issue:`2446`)
- Add support for ``xsalsa20_poly1305_lite`` encryption mode for voice. (:issue:`2463`)
- Add :attr:`RawReactionActionEvent.member` to get the member who did the reaction. (:issue:`2443`)
- Add support for new YouTube streaming via :attr:`Streaming.platform` and :attr:`Streaming.game`. (:issue:`2445`)
- Add :attr:`Guild.discovery_splash_url` to get the discovery splash image asset. (:issue:`2482`)
- Add :attr:`Guild.rules_channel` to get the rules channel of public guilds. (:issue:`2482`)
    - It should be noted that this feature is restricted to those who are either in Server Discovery or planning to be there.

- Add support for message flags via :attr:`Message.flags` and :class:`MessageFlags`. (:issue:`2433`)
- Add :attr:`User.system` and :attr:`Profile.system` to know whether a user is an official Discord Trust and Safety account.
- Add :attr:`Profile.team_user` to check whether a user is a member of a team.
- Add :meth:`Attachment.to_file` to easily convert attachments to :class:`File` for sending.
- Add certain aliases to :class:`Permissions` to match the UI better. (:issue:`2496`)
    - :attr:`Permissions.manage_permissions`
    - :attr:`Permissions.view_channel`
    - :attr:`Permissions.use_external_emojis`

- Add support for passing keyword arguments when creating :class:`Permissions`.
- Add support for custom activities via :class:`CustomActivity`. (:issue:`2400`)
    - Note that as of now, bots cannot send custom activities yet.

- Add support for :func:`on_invite_create` and :func:`on_invite_delete` events.
- Add support for clearing a specific reaction emoji from a message.
    - :meth:`Message.clear_reaction` and :meth:`Reaction.clear` methods.
    - :func:`on_raw_reaction_clear_emoji` and :func:`on_reaction_clear_emoji` events.

- Add :func:`utils.sleep_until` helper to sleep until a specific datetime. (:issue:`2517`, :issue:`2519`)
- |commands| Add support for teams and :attr:`Bot.owner_ids <.ext.commands.Bot.owner_ids>` to have multiple bot owners. (:issue:`2239`)
- |commands| Add new :attr:`BucketType.role <.ext.commands.BucketType.role>` bucket type. (:issue:`2201`)
- |commands| Expose :attr:`Command.cog <.ext.commands.Command.cog>` property publicly. (:issue:`2360`)
- |commands| Add non-decorator interface for adding checks to commands via :meth:`Command.add_check <.ext.commands.Command.add_check>` and :meth:`Command.remove_check <.ext.commands.Command.remove_check>`. (:issue:`2411`)
- |commands| Add :func:`has_guild_permissions <.ext.commands.has_guild_permissions>` check. (:issue:`2460`)
- |commands| Add :func:`bot_has_guild_permissions <.ext.commands.bot_has_guild_permissions>` check. (:issue:`2460`)
- |commands| Add ``predicate`` attribute to checks decorated with :func:`~.ext.commands.check`.
- |commands| Add :func:`~.ext.commands.check_any` check to logical OR multiple checks.
- |commands| Add :func:`~.ext.commands.max_concurrency` to allow only a certain amount of users to use a command concurrently before waiting or erroring.
- |commands| Add support for calling a :class:`~.ext.commands.Command` as a regular function.
- |tasks| :meth:`Loop.add_exception_type <.ext.tasks.Loop.add_exception_type>` now allows multiple exceptions to be set. (:issue:`2333`)
- |tasks| Add :attr:`Loop.next_iteration <.ext.tasks.Loop.next_iteration>` property. (:issue:`2305`)

Bug Fixes
~~~~~~~~~~

- Fix issue with permission resolution sometimes failing for guilds with no owner.
- Tokens are now stripped upon use. (:issue:`2135`)
- Passing in a ``name`` is no longer required for :meth:`Emoji.edit`. (:issue:`2368`)
- Fix issue with webhooks not re-raising after retries have run out. (:issue:`2272`, :issue:`2380`)
- Fix mismatch in URL handling in :func:`utils.escape_markdown`. (:issue:`2420`)
- Fix issue with ports being read in little endian when they should be big endian in voice connections. (:issue:`2470`)
- Fix :meth:`Member.mentioned_in` not taking into consideration the message's guild.
- Fix bug with moving channels when there are gaps in positions due to channel deletion and creation.
- Fix :func:`on_shard_ready` not triggering when ``fetch_offline_members`` is disabled. (:issue:`2504`)
- Fix issue with large sharded bots taking too long to actually dispatch :func:`on_ready`.
- Fix issue with fetching group DM based invites in :meth:`Client.fetch_invite`.
- Fix out of order files being sent in webhooks when there are 10 files.
- |commands| Extensions that fail internally due to ImportError will no longer raise :exc:`~.ext.commands.ExtensionNotFound`. (:issue:`2244`, :issue:`2275`, :issue:`2291`)
- |commands| Updating the :attr:`Paginator.suffix <.ext.commands.Paginator.suffix>` will not cause out of date calculations. (:issue:`2251`)
- |commands| Allow converters from custom extension packages. (:issue:`2369`, :issue:`2374`)
- |commands| Fix issue with paginator prefix being ``None`` causing empty pages. (:issue:`2471`)
- |commands| :class:`~.commands.Greedy` now ignores parsing errors rather than propagating them.
- |commands| :meth:`Command.can_run <.ext.commands.Command.can_run>` now checks whether a command is disabled.
- |commands| :attr:`HelpCommand.clean_prefix <.ext.commands.HelpCommand.clean_prefix>` now takes into consideration nickname mentions. (:issue:`2489`)
- |commands| :meth:`Context.send_help <.ext.commands.Context.send_help>` now properly propagates to the :meth:`HelpCommand.on_help_command_error <.ext.commands.HelpCommand.on_help_command_error>` handler.

Miscellaneous
~~~~~~~~~~~~~~~

- The library now fully supports Python 3.8 without warnings.
- Bump the dependency of ``websockets`` to 8.0 for those who can use it. (:issue:`2453`)
- Due to Discord providing :class:`Member` data in mentions, users will now be upgraded to :class:`Member` more often if mentioned.
- :func:`utils.escape_markdown` now properly escapes new quote markdown.
- The message cache can now be disabled by passing ``None`` to ``max_messages`` in :class:`Client`.
- The default message cache size has changed from 5000 to 1000 to accommodate small bots.
- Lower memory usage by only creating certain objects as needed in :class:`Role`.
- There is now a sleep of 5 seconds before re-IDENTIFYing during a reconnect to prevent long loops of session invalidation.
- The rate limiting code now uses millisecond precision to have more granular rate limit handling.
    - Along with that, the rate limiting code now uses Discord's response to wait. If you need to use the system clock again for whatever reason, consider passing ``assume_synced_clock`` in :class:`Client`.

- The performance of :attr:`Guild.default_role` has been improved from O(N) to O(1). (:issue:`2375`)
- The performance of :attr:`Member.roles` has improved due to usage of caching to avoid surprising performance traps.
- The GC is manually triggered during things that cause large deallocations (such as guild removal) to prevent memory fragmentation.
- There have been many changes to the documentation for fixes both for usability, correctness, and to fix some linter errors. Thanks to everyone who contributed to those.
- The loading of the opus module has been delayed which would make the result of :func:`opus.is_loaded` somewhat surprising.
- |commands| Usernames prefixed with @ inside DMs will properly convert using the :class:`User` converter. (:issue:`2498`)
- |tasks| The task sleeping time will now take into consideration the amount of time the task body has taken before sleeping. (:issue:`2516`)

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

- Fix bug with ``Reaction`` not being visible at import.
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
