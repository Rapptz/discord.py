.. currentmodule:: discord

.. _migrating_2_0:

Migrating to v2.0
======================

Compared to v1.0, v2.0 mostly has breaking changes related to better developer experience and API coverage.
While the changes aren't as massive to require an entire rewrite, there are still many changes that need to be accounted for.

Python Version Change
-----------------------

In order to ease development, maintain security updates, and use newer features **v2.0 drops support for Python 3.7 and earlier**.

.. _migrating_2_0_userbot_removal:

Removal of Support For User Accounts
--------------------------------------

Logging on with a user token is against the Discord `Terms of Service <https://support.discord.com/hc/en-us/articles/115002192352>`_
and as such all support for user-only endpoints has been removed.

The following have been removed:

- ``bot`` parameter to :meth:`Client.login` and :meth:`Client.start`
- ``afk`` parameter to :meth:`Client.change_presence`
- ``password``, ``new_password``, ``email``, and ``house`` parameters to :meth:`ClientUser.edit`
- ``CallMessage`` model
- ``GroupCall`` model
- ``Profile`` model
- ``Relationship`` model
- ``RelationshipType`` enumeration
- ``HypeSquadHouse`` enumeration
- ``PremiumType`` enumeration
- ``UserContentFilter`` enumeration
- ``FriendFlags`` enumeration
- ``Theme`` enumeration
- ``on_relationship_add`` event
- ``on_relationship_remove`` event
- ``on_relationship_update`` event
- ``Client.fetch_user_profile`` method
- ``ClientUser.create_group`` method
- ``ClientUser.edit_settings`` method
- ``ClientUser.get_relationship`` method
- ``GroupChannel.add_recipients`` method
- ``GroupChannel.remove_recipients`` method
- ``GroupChannel.edit`` method
- ``Guild.ack`` method
- ``Message.ack`` method
- ``User.block`` method
- ``User.is_blocked`` method
- ``User.is_friend`` method
- ``User.profile`` method
- ``User.remove_friend`` method
- ``User.send_friend_request`` method
- ``User.unblock`` method
- ``ClientUser.blocked`` attribute
- ``ClientUser.email`` attribute
- ``ClientUser.friends`` attribute
- ``ClientUser.premium`` attribute
- ``ClientUser.premium_type`` attribute
- ``ClientUser.relationships`` attribute
- ``Message.call`` attribute
- ``User.mutual_friends`` attribute
- ``User.relationship`` attribute

Abstract Base Classes Changes
-------------------------------

:ref:`discord_api_abcs` that inherited from :class:`abc.ABCMeta` now inherit from :class:`typing.Protocol`.

This results in a change of the base metaclass used by these classes
but this should generally be completely transparent to the user.

All of the classes are either :func:`runtime-checkable <typing.runtime_checkable>` protocols or explicitly inherited from
and as such usage with :func:`isinstance` and :func:`issubclass` is not affected.

The following have been changed to :func:`runtime-checkable <typing.runtime_checkable>` :class:`~typing.Protocol`\s:

- :class:`abc.Snowflake`
- :class:`abc.User`
- :class:`abc.PrivateChannel`

The following have been changed to subclass :class:`~typing.Protocol`:

- :class:`abc.GuildChannel`
- :class:`abc.Connectable`

The following have been changed to use the default metaclass instead of :class:`abc.ABCMeta`:

- :class:`abc.Messageable`

``datetime`` Objects Are Now UTC-Aware
----------------------------------------

All usage of naive :class:`datetime.datetime` objects in the library has been replaced with aware objects using UTC timezone.
Methods that accepted naive :class:`~datetime.datetime` objects now also accept timezone-aware objects.
To keep behavior inline with :class:`~datetime.datetime`'s methods, this library's methods now assume
that naive :class:`~datetime.datetime` objects are local time (note that some of the methods may not accept
naive :class:`~datetime.datetime`, such exceptions are listed below).

Because naive :class:`~datetime.datetime` objects are treated by many of its methods as local times, the previous behavior
was more likely to result in programming errors with their usage.

To ease the migration :func:`utils.utcnow` helper function has been added.

.. warning::
    Using :meth:`datetime.datetime.utcnow` can be problematic since it returns a naive UTC ``datetime`` object.

Quick example:

.. code:: python

    # before
    week_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    if member.created_at > week_ago:
        print(f'Member account {member} was created less than a week ago!')

    # after
    # The new helper function can be used here:
    week_ago = discord.utils.utcnow() - datetime.timedelta(days=7)
    # ...or the equivalent result can be achieved with datetime.datetime.now():
    week_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    if member.created_at > week_ago:
        print(f'Member account {member} was created less than a week ago!')

The following have been changed from naive to aware :class:`~datetime.datetime` objects in UTC:

- :attr:`AuditLogEntry.created_at` attribute
- :attr:`BaseActivity.created_at` attribute
- :attr:`ClientUser.created_at` attribute
- :attr:`DMChannel.created_at` attribute
- :attr:`Emoji.created_at` attribute
- :attr:`GroupChannel.created_at` attribute
- :attr:`Guild.created_at` attribute
- :attr:`abc.GuildChannel.created_at` attribute
- :attr:`Invite.created_at` attribute
- :attr:`Object.created_at` attribute
- :attr:`Member.created_at` attribute
- :attr:`Message.created_at` attribute
- :attr:`PartialEmoji.created_at` attribute
- :attr:`PartialInviteChannel.created_at` attribute
- :attr:`PartialInviteGuild.created_at` attribute
- :attr:`PartialMessage.created_at` attribute
- :attr:`Role.created_at` attribute
- :attr:`Spotify.created_at` attribute
- :attr:`Sticker.created_at` attribute
- :attr:`TeamMember.created_at` attribute
- :attr:`Template.created_at` attribute
- :attr:`User.created_at` attribute
- :attr:`Webhook.created_at` attribute
- :attr:`Widget.created_at` attribute
- :attr:`WidgetChannel.created_at` attribute
- :attr:`WidgetMember.created_at` attribute
- :attr:`Message.edited_at` attribute
- :attr:`Invite.expires_at` attribute
- :attr:`Activity.end` attribute
- :attr:`Game.end` attribute
- :attr:`Spotify.end` attribute
- :attr:`Member.joined_at` attribute
- :attr:`Member.premium_since` attribute
- :attr:`VoiceState.requested_to_speak_at` attribute
- :attr:`Activity.start` attribute
- :attr:`Game.start` attribute
- :attr:`Spotify.start` attribute
- :attr:`StreamIntegration.synced_at` attribute
- :attr:`Embed.timestamp` attribute
- :attr:`Template.updated_at` attribute
- ``timestamp`` parameter in :func:`on_typing` event
- ``last_pin`` parameter in :func:`on_private_channel_pins_update` event
- ``last_pin`` parameter in :func:`on_guild_channel_pins_update` event
- Return type of :func:`utils.snowflake_time`

The following now accept aware :class:`~datetime.datetime` and assume that if the passed :class:`~datetime.datetime` is naive, it is a local time:

- :meth:`abc.Messageable.history` method
- :meth:`Client.fetch_guilds` method
- :meth:`Guild.audit_logs` method
- :meth:`Guild.fetch_members` method
- :meth:`TextChannel.purge` method
- :attr:`Embed` constructor
- :attr:`Embed.timestamp` property setter
- :func:`utils.sleep_until` function
- ``utils.time_snowflake`` function

Currently, there's only one place in this library that doesn't accept naive :class:`datetime.datetime` objects:

- ``timed_out_until`` parameter in :meth:`Member.edit`

    This has been done to prevent users from mistakenly applying incorrect timeouts to guild members.

Major Webhook Changes
-----------------------

Webhook support has been rewritten to work better with typings and rate limits.

As a result, synchronous functionality has been split to separate classes.

Quick example for asynchronous webhooks:

.. code:: python

    # before
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url('url-here', adapter=discord.AsyncWebhookAdapter(session))
        await webhook.send('Hello World', username='Foo')

    # after
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url('url-here', session=session)
        await webhook.send('Hello World', username='Foo')

Quick example for synchronous webhooks:

.. code:: python

    # before
    webhook = discord.Webhook.partial(123456, 'token-here', adapter=discord.RequestsWebhookAdapter())
    webhook.send('Hello World', username='Foo')

    # after
    webhook = discord.SyncWebhook.partial(123456, 'token-here')
    webhook.send('Hello World', username='Foo')

The following breaking changes have been made:

- Synchronous functionality of :class:`Webhook` and :class:`WebhookMessage` has been split to
  :class:`SyncWebhook` and :class:`SyncWebhookMessage`.
- ``WebhookAdapter`` class has been removed and the interfaces based on it (``AsyncWebhookAdapter``
  and ``RequestsWebhookAdapter``) are now considered implementation detail and should not be depended on.
- ``execute`` alias for :meth:`Webhook.send`/:meth:`SyncWebhook.send` has been removed.

Asset Redesign and Changes
----------------------------

The :class:`Asset` object now encompasses all of the methods and attributes related to a CDN asset.

This means that all models with asset-related attribute and methods have been transformed to use this new design.
As an example, here's how these changes look for :attr:`Guild.icon` (of :class:`Asset` type):

- ``Guild.icon`` (of :class:`str` type) has been replaced with :attr:`Guild.icon.key <Asset.key>`.
- ``Guild.is_icon_animated`` has been replaced with :meth:`Guild.icon.is_animated <Asset.is_animated>`.
- ``Guild.icon_url`` has been replaced with :attr:`Guild.icon`.
- ``Guild.icon_url_as`` has been replaced with :meth:`Guild.icon.replace <Asset.replace>`.

    - Helper methods :meth:`Asset.with_size`, :meth:`Asset.with_format`, and :meth:`Asset.with_static_format` have also been added.

In addition to this, :class:`Emoji` and :class:`PartialEmoji` now also share an interface similar to :class:`Asset`'s:

- :attr:`Emoji.url` is now of :class:`str` type.
- ``Emoji.url_as`` has been removed.
- ``Emoji.url.read`` has been replaced with :meth:`Emoji.read`.
- ``Emoji.url.save`` has been replaced with :meth:`Emoji.save`.

:class:`Asset` now always represent an actually existing CDN asset. This means that:

- ``str(x)`` on an :class:`Asset` can no longer return an empty string.
- ``bool(x)`` on an :class:`Asset` can no longer return ``False``.
- Attributes containing an optional :class:`Asset` can now be ``None``.

The following were affected by this change:

- :attr:`AppInfo.cover_image`

    - ``AppInfo.cover_image`` (replaced by :attr:`AppInfo.cover_image.key <Asset.key>`)
    - ``AppInfo.cover_image_url`` (replaced by :attr:`AppInfo.cover_image`)

        - The new attribute may now be ``None``.

    - ``AppInfo.cover_image_url_as`` (replaced by :meth:`AppInfo.cover_image.replace <Asset.replace>`)

- :attr:`AppInfo.icon`

    - ``AppInfo.icon`` (replaced by :attr:`AppInfo.icon.key <Asset.key>`)
    - ``AppInfo.icon_url`` (replaced by :attr:`AppInfo.icon`)

        - The new attribute may now be ``None``.

    - ``AppInfo.icon_url_as`` (replaced by :meth:`AppInfo.icon.replace <Asset.replace>`)

- :class:`AuditLogDiff`

    - :attr:`AuditLogDiff.avatar` is now of :class:`Asset` type.
    - :attr:`AuditLogDiff.icon` is now of :class:`Asset` type.
    - :attr:`AuditLogDiff.splash` is now of :class:`Asset` type.

- :attr:`Emoji.url`

    - :attr:`Emoji.url` is now of :class:`str` type.
    - ``Emoji.url_as`` has been removed.
    - ``Emoji.url.read`` (replaced by :meth:`Emoji.read`)
    - ``Emoji.url.save`` (replaced by :meth:`Emoji.save`)

- :attr:`GroupChannel.icon`

    - ``GroupChannel.icon`` (replaced by :attr:`GroupChannel.icon.key <Asset.key>`)
    - ``GroupChannel.icon_url`` (replaced by :attr:`GroupChannel.icon`)

        - The new attribute may now be ``None``.

    - ``GroupChannel.icon_url_as`` (replaced by :meth:`GroupChannel.icon.replace <Asset.replace>`)

- :attr:`Guild.banner`

    - ``Guild.banner`` (replaced by :attr:`Guild.banner.key <Asset.key>`)
    - ``Guild.banner_url`` (replaced by :attr:`Guild.banner`)

        - The new attribute may now be ``None``.

    - ``Guild.banner_url_as`` (replaced by :meth:`Guild.banner.replace <Asset.replace>`)

- :attr:`Guild.discovery_splash`

    - ``Guild.discovery_splash`` (replaced by :attr:`Guild.discovery_splash.key <Asset.key>`)
    - ``Guild.discovery_splash_url`` (replaced by :attr:`Guild.discovery_splash`)

        - The new attribute may now be ``None``.

    - ``Guild.discovery_splash_url_as`` (replaced by :meth:`Guild.discovery_splash.replace <Asset.replace>`)

- :attr:`Guild.icon`

    - ``Guild.icon`` (replaced by :attr:`Guild.icon.key <Asset.key>`)
    - ``Guild.is_icon_animated`` (replaced by :meth:`Guild.icon.is_animated <Asset.is_animated>`)
    - ``Guild.icon_url`` (replaced by :attr:`Guild.icon`)

        - The new attribute may now be ``None``.

    - ``Guild.icon_url_as`` (replaced by :meth:`Guild.icon.replace <Asset.replace>`)

- :attr:`Guild.splash`

    - ``Guild.splash`` (replaced by :attr:`Guild.splash.key <Asset.key>`)
    - ``Guild.splash_url`` (replaced by :attr:`Guild.splash`)

        - The new attribute may now be ``None``.

    - ``Guild.splash_url_as`` (replaced by :meth:`Guild.splash.replace <Asset.replace>`)

- :attr:`Member.avatar`

    - ``Member.avatar`` (replaced by :attr:`Member.avatar.key <Asset.key>`)
    - ``Member.is_avatar_animated`` (replaced by :meth:`Member.avatar.is_animated <Asset.is_animated>`)
    - ``Member.avatar_url`` (replaced by :attr:`Member.avatar`)

        - The new attribute may now be ``None``.

    - ``Member.avatar_url_as`` (replaced by :meth:`Member.avatar.replace <Asset.replace>`)

- :attr:`Member.default_avatar`

    - ``Member.default_avatar`` (replaced by :attr:`Member.default_avatar.key <Asset.key>`)
    - ``Member.default_avatar_url`` (replaced by :attr:`Member.default_avatar`)
    - ``Member.default_avatar_url_as`` (replaced by :meth:`Member.default_avatar.replace <Asset.replace>`)

- :attr:`PartialEmoji.url`

    - :attr:`PartialEmoji.url` is now of :class:`str` type.
    - ``PartialEmoji.url_as`` has been removed.
    - ``PartialEmoji.url.read`` (replaced by :meth:`PartialEmoji.read`)
    - ``PartialEmoji.url.save`` (replaced by :meth:`PartialEmoji.save`)

- :attr:`PartialInviteGuild.banner`

    - ``PartialInviteGuild.banner`` (replaced by :attr:`PartialInviteGuild.banner.key <Asset.key>`)
    - ``PartialInviteGuild.banner_url`` (replaced by :attr:`PartialInviteGuild.banner`)

        - The new attribute may now be ``None``.

    - ``PartialInviteGuild.banner_url_as`` (replaced by :meth:`PartialInviteGuild.banner.replace <Asset.replace>`)

- :attr:`PartialInviteGuild.icon`

    - ``PartialInviteGuild.icon`` (replaced by :attr:`PartialInviteGuild.icon.key <Asset.key>`)
    - ``PartialInviteGuild.is_icon_animated`` (replaced by :meth:`PartialInviteGuild.icon.is_animated <Asset.is_animated>`)
    - ``PartialInviteGuild.icon_url`` (replaced by :attr:`PartialInviteGuild.icon`)

        - The new attribute may now be ``None``.

    - ``PartialInviteGuild.icon_url_as`` (replaced by :meth:`PartialInviteGuild.icon.replace <Asset.replace>`)

- :attr:`PartialInviteGuild.splash`

    - ``PartialInviteGuild.splash`` (replaced by :attr:`PartialInviteGuild.splash.key <Asset.key>`)
    - ``PartialInviteGuild.splash_url`` (replaced by :attr:`PartialInviteGuild.splash`)

        - The new attribute may now be ``None``.

    - ``PartialInviteGuild.splash_url_as`` (replaced by :meth:`PartialInviteGuild.splash.replace <Asset.replace>`)

- :attr:`Team.icon`

    - ``Team.icon`` (replaced by :attr:`Team.icon.key <Asset.key>`)
    - ``Team.icon_url`` (replaced by :attr:`Team.icon`)

        - The new attribute may now be ``None``.

    - ``Team.icon_url_as`` (replaced by :meth:`Team.icon.replace <Asset.replace>`)

- :attr:`User.avatar`

    - ``User.avatar`` (replaced by :attr:`User.avatar.key <Asset.key>`)
    - ``User.is_avatar_animated`` (replaced by :meth:`User.avatar.is_animated <Asset.is_animated>`)
    - ``User.avatar_url`` (replaced by :attr:`User.avatar`)

        - The new attribute may now be ``None``.

    - ``User.avatar_url_as`` (replaced by :meth:`User.avatar.replace <Asset.replace>`)

- :attr:`User.default_avatar`

    - ``User.default_avatar`` (replaced by :attr:`User.default_avatar.key <Asset.key>`)
    - ``User.default_avatar_url`` (replaced by :attr:`User.default_avatar`)
    - ``User.default_avatar_url_as`` (replaced by :meth:`User.default_avatar.replace <Asset.replace>`)

- :attr:`Webhook.avatar`

    - ``Webhook.avatar`` (replaced by :attr:`Webhook.avatar.key <Asset.key>`)
    - ``Webhook.avatar_url`` (replaced by :attr:`Webhook.avatar`)

        - The new attribute may now be ``None``.

    - ``Webhook.avatar_url_as`` (replaced by :meth:`Webhook.avatar.replace <Asset.replace>`)

.. _migrating_2_0_thread_support:

Thread Support
----------------

v2.0 has been updated to use a newer API gateway version which supports threads and as a result of this had to make few breaking changes. Most notably messages sent in guilds can, in addition to a :class:`TextChannel`, be sent in a :class:`Thread`.

The main differences between text channels and threads are:

- Threads do not have their own permissions, they inherit the permissions of their parent channel.

    - This means that threads do not have these attributes:

        - ``changed_roles``
        - ``overwrites``
        - ``permissions_synced``

    .. note::

        Text channels have a few dedicated permissions for threads:

        - :attr:`Permissions.manage_threads`
        - :attr:`Permissions.create_public_threads`
        - :attr:`Permissions.create_private_threads`
        - :attr:`Permissions.send_messages_in_threads`

- Threads do not have their own nsfw status, they inherit it from their parent channel.

    - This means that :class:`Thread` does not have an ``nsfw`` attribute.

- Threads do not have their own topic.

    - This means that :class:`Thread` does not have a ``topic`` attribute.

- Threads do not have their own position in the channel list.

    - This means that :class:`Thread` does not have a ``position`` attribute.

- :attr:`Thread.created_at` of threads created before 10 January 2022 is ``None``.
- :attr:`Thread.members` is of type List[:class:`ThreadMember`] rather than List[:class:`Member`]

    - Most of the time, this data is not provided and a call to :meth:`Thread.fetch_members` is needed.

For convenience, :class:`Thread` has a set of properties and methods that return the information about the parent channel:

- :attr:`Thread.category`
- :attr:`Thread.category_id`
- :meth:`Thread.is_news`
- :meth:`Thread.is_nsfw`
- :meth:`Thread.permissions_for`

    - Note that this outputs the permissions of the parent channel and you might need to check for different permissions
      when trying to determine if a member can do something.

      Here are some notable examples:

      - A guild member can send messages in a text channel if they have :attr:`~Permissions.send_messages` permission in it.

        A guild member can send messages in a public thread if:
            - They have :attr:`~Permissions.send_messages_in_threads` permission in its parent channel.
            - The thread is not :attr:`~Thread.locked`.

        A guild member can send messages in a private thread if:
            - They have :attr:`~Permissions.send_messages_in_threads` permission in its parent channel.
            - They're either already a member of the thread
              or have a :attr:`~Permissions.manage_threads` permission in its parent channel.
            - The thread is not :attr:`~Thread.locked`.

      - A guild member can edit a text channel if they have :attr:`~Permissions.manage_channels` permission in it.

        A guild member can edit a thread if they have :attr:`~Permissions.manage_threads` permission in its parent channel.

        .. note::

            A thread's :attr:`~Thread.owner` can archive a (not-locked) thread and edit its :attr:`~Thread.name`
            and :attr:`~Thread.auto_archive_duration` without :attr:`~Permissions.manage_threads` permission.

      - A guild member can react with an emoji to messages in a text channel if:
            - They have :attr:`~Permissions.read_message_history` permission in it.
            - They have :attr:`~Permissions.add_reactions` permission in it or the message already has that emoji reaction.

        A guild member can react with an emoji to messages in a public thread if:
            - They have :attr:`~Permissions.read_message_history` permission in its parent channel.
            - They have :attr:`~Permissions.add_reactions` permission in its parent channel or the message already has that emoji reaction.
            - The thread is not :attr:`~Thread.archived`. Note that the guild member can unarchive a thread
              (if it's not :attr:`~Thread.locked`) to react to a message.

        A guild member can react with an emoji to messages in a private thread if:
            - They have :attr:`~Permissions.read_message_history` permission in its parent channel.
            - They have :attr:`~Permissions.add_reactions` permission in its parent channel or the message already has that emoji reaction.
            - They're either already a member of the thread
              or have a :attr:`~Permissions.manage_threads` permission in its parent channel.
            - The thread is not :attr:`~Thread.archived`. Note that the guild member can unarchive a thread
              (if it's not :attr:`~Thread.locked`) to react to a message.

The following changes have been made:

- :attr:`Message.channel` may now be a :class:`Thread`.
- :attr:`AuditLogEntry.target` may now be a :class:`Thread`.
- :attr:`PartialMessage.channel` may now be a :class:`Thread`.
- :attr:`Guild.get_channel` does not return :class:`Thread`\s.

    - If you're looking to get a channel or thread, use :attr:`Guild.get_channel_or_thread` instead.
    - If you're only looking to get threads, use :attr:`Guild.get_thread` or :attr:`TextChannel.get_thread` instead.

- ``channel`` parameter in :func:`on_guild_channel_pins_update` may now be a :class:`Thread`.
- ``channel`` parameter in :func:`on_typing` may now be a :class:`Thread`.
- :meth:`Client.fetch_channel` may now return :class:`Thread`.
- :meth:`Client.get_channel` may now return :class:`Thread`.
- :meth:`Guild.fetch_channel` may now return :class:`Thread`.

Removing In-Place Edits
-------------------------

Most of the model methods that previously edited the model in-place have been updated to no longer do this.
Instead, these methods will now return a new instance of the newly updated model.
This has been done to avoid the library running into race conditions between in-place edits and gateway events on model updates. See :issue:`4098` for more information.

Quick example:

.. code:: python

    # before
    await member.edit(nick='new nick')
    await member.send(f'Your new nick is {member.nick}')

    # after
    updated_member = await member.edit(nick='new nick')
    await member.send(f'Your new nick is {updated_member.nick}')

The following have been changed:

- :meth:`CategoryChannel.edit`

    - Note that this method will return ``None`` instead of :class:`CategoryChannel` if the edit was only positional.

- :meth:`Member.edit`

    - Note that this method only returns the updated :class:`Member` when certain fields are updated.

- :meth:`StageChannel.edit`

    - Note that this method will return ``None`` instead of :class:`StageChannel` if the edit was only positional.

- :meth:`StoreChannel.edit`

    - Note that this method will return ``None`` instead of :class:`StoreChannel` if the edit was only positional.

- :meth:`TextChannel.edit`

    - Note that this method will return ``None`` instead of :class:`TextChannel` if the edit was only positional.

- :meth:`VoiceChannel.edit`

    - Note that this method will return ``None`` instead of :class:`VoiceChannel` if the edit was only positional.

- :meth:`ClientUser.edit`
- :meth:`Emoji.edit`
- :meth:`Guild.edit`
- :meth:`Message.edit`
- :meth:`Role.edit`
- :meth:`Template.edit`
- :meth:`Template.sync`
- :meth:`Webhook.edit`
- :meth:`Webhook.edit_message`
- :meth:`WebhookMessage.edit`

Sticker Changes
-----------------

Discord has changed how their stickers work and as such, sticker support has been reworked.

The following breaking changes have been made:

- Type of :attr:`Message.stickers` changed to List[:class:`StickerItem`].

    - To get the :class:`Sticker` from :class:`StickerItem`, use :meth:`StickerItem.fetch`
      or (only for stickers from guilds the bot is in) :meth:`Client.get_sticker`.

- :attr:`Sticker.format` is now of :class:`StickerFormatType` type.
- ``Sticker.tags`` has been removed.

    - Depending on type of the sticker, :attr:`StandardSticker.tags` or :attr:`GuildSticker.emoji` can be used instead.

- ``Sticker.image`` and related methods have been removed.
- ``Sticker.preview_image`` and related methods have been removed.
- :attr:`AuditLogDiff.type` is now of Union[:class:`ChannelType`, :class:`StickerType`] type.
- The old ``StickerType`` enum has been renamed to :class:`StickerFormatType`.

    - :class:`StickerType` now refers to a sticker type (official sticker vs guild-uploaded sticker) rather than its format type.

Integrations Changes
----------------------

To support the new integration types, integration support has been reworked.

The following breaking changes have been made:

- The old ``Integration`` class has been renamed to :class:`StreamIntegration`.
- :meth:`Guild.integrations` now returns subclasses of the new :class:`Integration` class.

Presence Updates Now Have A Separate Event
--------------------------------------------

Presence updates (changes in member's status and activity) now have a separate :func:`on_presence_update` event.
:func:`on_member_update` event is now only called on member updates (changes in nickname, role, pending status, etc.).

From API perspective, these are separate events and as such, this change improves library's consistency with the API.
Presence updates usually are 90% of all handled events so splitting these should benefit listeners that were only interested
in member updates.

Quick example:

.. code:: python

    # before
    @client.event
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            await nick_changed(before, after)
        if before.status != after.status:
            await status_changed(before, after)

    # after
    @client.event
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            await nick_changed(before, after)

    @client.event
    async def on_presence_update(self, before, after):
        if before.status != after.status:
            await status_changed(before, after)

Moving Away From Custom AsyncIterator
--------------------------------------

Asynchronous iterators in v1.0 were implemented using a special class named ``AsyncIterator``.
v2.0 instead provides regular asynchronous iterators with no added utility methods.

This means that usage of the following utility methods is no longer possible:

- ``AsyncIterator.next()``

    Usage of an explicit ``async for`` loop should generally be preferred:

    .. code:: python

        # before
        it = channel.history()
        while True:
            try:
                message = await self.next()
            except discord.NoMoreItems:
                break
            print(f'Found message with ID {message.id}')

        # after
        async for message in channel.history():
            print(f'Found message with ID {message.id}')

    If you need to get next item from an iterator without a loop,
    you can use :func:`anext` (new in Python 3.10) or :meth:`~object.__anext__` instead:

    .. code:: python

        # before
        it = channel.history()
        first = await it.next()
        if first.content == 'do not iterate':
            return
        async for message in it:
            ...

        # after
        it = channel.history()
        first = await anext(it)  # await it.__anext__() on Python<3.10
        if first.content == 'do not iterate':
            return
        async for message in it:
            ...

- ``AsyncIterator.get()``

    .. code:: python

        # before
        msg = await channel.history().get(author__name='Dave')

        # after
        msg = await discord.utils.get(channel.history(), author__name='Dave')

- ``AsyncIterator.find()``

    .. code:: python

        def predicate(event):
            return event.reason is not None

        # before
        event = await guild.audit_logs().find(predicate)

        # after
        event = await discord.utils.find(predicate, guild.audit_logs())

- ``AsyncIterator.flatten()``

    .. code:: python

        # before
        users = await reaction.users().flatten()

        # after
        users = [user async for user in reaction.users()]

- ``AsyncIterator.chunk()``

    .. code:: python

        # before
        async for leader, *users in reaction.users().chunk(3):
            ...

        # after
        async for leader, *users in discord.utils.as_chunks(reaction.users(), 3):
            ...

- ``AsyncIterator.map()``

    .. code:: python

        # before
        content_of_messages = []
        async for content in channel.history().map(lambda m: m.content):
            content_of_messages.append(content)

        # after
        content_of_messages = [message.content async for message in channel.history()]

- ``AsyncIterator.filter()``

    .. code:: python

        def predicate(message):
            return not message.author.bot

        # before
        user_messages = []
        async for message in channel.history().filter(lambda m: not m.author.bot):
            user_messages.append(message)

        # after
        user_messages = [message async for message in channel.history() if not m.author.bot]

To ease this transition, these changes have been made:

- Added :func:`utils.as_chunks` as an alternative for ``AsyncIter.chunk``.
- Added support for :term:`asynchronous iterator` to :func:`utils.find`.
- Added support for :term:`asynchronous iterator` to :func:`utils.get`.

The return type of the following methods has been changed to an :term:`asynchronous iterator`:

- :meth:`abc.Messageable.history`
- :meth:`Client.fetch_guilds`
- :meth:`Guild.audit_logs`
- :meth:`Guild.fetch_members`
- :meth:`Reaction.users`

The ``NoMoreItems`` exception was removed as calling :func:`anext` or :meth:`~object.__anext__` on an 
:term:`asynchronous iterator` will now raise :class:`StopAsyncIteration`.

Removal of ``InvalidArgument`` Exception
-------------------------------------------

The custom ``InvalidArgument`` exception has been removed and functions and methods that
raised it are now raising :class:`TypeError` and/or :class:`ValueError` instead.

The following methods have been changed:

- :meth:`Message.add_reaction`
- :meth:`AutoShardedClient.change_presence`
- :meth:`Client.change_presence`
- :meth:`Reaction.clear`
- :meth:`Message.clear_reaction`
- :meth:`Guild.create_category`
- :meth:`Guild.create_custom_emoji`
- :meth:`Client.create_guild`
- :meth:`Template.create_guild`
- :meth:`StageChannel.create_instance`
- :meth:`Guild.create_role`
- :meth:`Guild.create_stage_channel`
- :meth:`Guild.create_text_channel`
- :meth:`Guild.create_voice_channel`
- :meth:`TextChannel.create_webhook`
- :meth:`Webhook.delete`
- :meth:`WebhookMessage.delete`
- :meth:`Webhook.delete_message`
- :meth:`CategoryChannel.edit`
- :meth:`ClientUser.edit`
- :meth:`Guild.edit`
- :meth:`Message.edit`
- :meth:`Role.edit`
- :meth:`StageChannel.edit`
- :meth:`StageInstance.edit`
- :meth:`StoreChannel.edit`
- :meth:`StreamIntegration.edit`
- :meth:`TextChannel.edit`
- :meth:`VoiceChannel.edit`
- :meth:`Webhook.edit`
- :meth:`WebhookMessage.edit`
- :meth:`Webhook.edit_message`
- :meth:`Guild.edit_role_positions`
- :meth:`Guild.estimate_pruned_members`
- :meth:`TextChannel.follow`
- :meth:`Webhook.from_url`
- :meth:`abc.GuildChannel.move`
- :meth:`Guild.prune_members`
- :meth:`Message.remove_reaction`
- :meth:`Message.reply`
- :meth:`abc.Messageable.send`
- :meth:`Webhook.send`
- :meth:`abc.GuildChannel.set_permissions`

Function Signature Changes
----------------------------

Parameters in the following methods are now all positional-only:

- :meth:`AutoShardedClient.get_shard`
- :meth:`Client.get_channel`
- :meth:`Client.fetch_channel`
- :meth:`Guild.get_channel`
- :meth:`Guild.fetch_channel`
- :meth:`Client.get_emoji`
- :meth:`Guild.fetch_emoji`
- :meth:`Client.get_guild`
- :meth:`Client.fetch_guild`
- :meth:`Client.delete_invite`
- :meth:`Guild.get_member`
- :meth:`Guild.get_member_named`
- :meth:`Guild.fetch_member`
- :meth:`Client.get_user`
- :meth:`Client.fetch_user`
- :meth:`Guild.get_role`
- :meth:`Client.fetch_webhook`
- :meth:`Client.fetch_widget`
- :meth:`Message.add_reaction`
- :meth:`abc.Messageable.fetch_message`
- :meth:`abc.GuildChannel.permissions_for`
- :meth:`DMChannel.get_partial_message`
- :meth:`TextChannel.get_partial_message`
- :meth:`TextChannel.delete_messages`
- :meth:`Webhook.delete_message`
- :meth:`utils.find`

The following parameters are now positional-only:

- ``iterable`` in :meth:`utils.get`

The following are now keyword-only:

- Parameters in :meth:`Reaction.users`
- Parameters in :meth:`Client.create_guild`
- ``permissions``, ``guild``, ``redirect_uri``, and ``scopes`` parameters in :meth:`utils.oauth_url`

The library now less often uses ``None`` as the default value for function/method parameters.

As a result, these parameters can no longer be ``None``:

- ``size``, ``format``, and ``static_format`` in :meth:`Asset.replace`
- ``check`` in :meth:`TextChannel.purge`
- ``icon`` and ``code`` in :meth:`Client.create_guild`
- ``roles`` in :meth:`Emoji.edit`
- ``topic``, ``position`` and ``overwrites`` in :meth:`Guild.create_text_channel`
- ``position`` and ``overwrites`` in :meth:`Guild.create_voice_channel`
- ``topic``, ``position`` and ``overwrites`` in :meth:`Guild.create_stage_channel`
- ``position`` and ``overwrites`` in :meth:`Guild.create_category`
- ``roles`` in :meth:`Guild.prune_members`
- ``roles`` in :meth:`Guild.estimate_pruned_members`
- ``description`` in :meth:`Guild.create_template`
- ``roles`` in :meth:`Guild.create_custom_emoji`
- ``before``, ``after``, ``oldest_first``, ``user``, and ``action`` in :meth:`Guild.audit_logs`
- ``enable_emoticons`` in :meth:`StreamIntegration.edit`
- ``mute``, ``deafen``, ``suppress``, and ``roles`` in :meth:`Member.edit`
- ``position`` in :meth:`Role.edit`
- ``icon`` in :meth:`Template.create_guild`
- ``name`` in :meth:`Template.edit`
- ``permissions``, ``guild``, ``redirect_uri``, ``scopes`` in :meth:`utils.oauth_url`
- ``content``, ``username``, ``avatar_url``, ``tts``, ``file``, ``files``, ``embed``, ``embeds``, and ``allowed_mentions`` in :meth:`Webhook.send`

Allowed types for the following parameters have been changed:

- ``rtc_region`` in :meth:`Guild.create_voice_channel` is now of type Optional[:class:`str`].
- ``rtc_region`` in :meth:`StageChannel.edit` is now of type Optional[:class:`str`].
- ``rtc_region`` in :meth:`VoiceChannel.edit` is now of type Optional[:class:`str`].
- ``preferred_locale`` in :meth:`Guild.edit` is now of type :class:`Locale`. 

Attribute Type Changes
------------------------

The following changes have been made:

- :attr:`DMChannel.recipient` may now be ``None``.
- :meth:`Guild.vanity_invite` may now be ``None``. This has been done to fix an issue with the method returning a broken :class:`Invite` object.
- :attr:`Guild.shard_id` is now ``0`` instead of ``None`` if :class:`AutoShardedClient` is not used.
- :attr:`Guild.mfa_level` is now of type :class:`MFALevel`.
- :attr:`AuditLogDiff.mfa_level` is now of type :class:`MFALevel`.
- :attr:`AuditLogDiff.rtc_region` is now of type :class:`str`.
- :attr:`StageChannel.rtc_region` is now of type :class:`str`.
- :attr:`VoiceChannel.rtc_region` is now of type :class:`str`.
- :attr:`ClientUser.avatar` is now ``None`` when the default avatar is used.

    - If you want the avatar that a user has displayed, consider :attr:`ClientUser.display_avatar`.

- :attr:`Member.avatar` is now ``None`` when the default avatar is used.

    - If you want the avatar that a member or user has displayed,
      consider :attr:`Member.display_avatar` or :attr:`User.display_avatar`.

- :attr:`User.avatar` is now ``None`` when the default avatar is used.

    - If you want the avatar that a user has displayed, consider :attr:`User.display_avatar`.

- :attr:`Webhook.avatar` is now ``None`` when the default avatar is used.

    - If you want the avatar that a webhook has displayed, consider :attr:`Webhook.display_avatar`.

- :attr:`AuditLogEntry.target` may now be a :class:`PartialMessageable`.
- :attr:`PartialMessage.channel` may now be a :class:`PartialMessageable`.
- :attr:`Guild.preferred_locale` is now of type :class:`Locale`.

Removals
----------

The following deprecated functionality have been removed:

- ``Client.request_offline_members``

    - Use :meth:`Guild.chunk` instead.

- ``AutoShardedClient.request_offline_members``

    - Use :meth:`Guild.chunk` instead.

- ``Client.logout``

    - Use :meth:`Client.close` instead.

- ``fetch_offline_members`` parameter from :class:`Client` constructor

    - Use ``chunk_guild_at_startup`` instead.

The following have been removed:

- ``MemberCacheFlags.online``

    - There is no replacement for this one. The current API version no longer provides enough data for this to be possible.

- ``AppInfo.summary``

    - There is no replacement for this one. The current API version no longer provides this field.

- ``User.permissions_in`` and ``Member.permissions_in``

    - Use :meth:`abc.GuildChannel.permissions_for` instead.

- ``guild_subscriptions`` parameter from :class:`Client` constructor

    - The current API version no longer provides this functionality. Use ``intents`` parameter instead.

- :class:`VerificationLevel` aliases:

    - ``VerificationLevel.table_flip`` - use :attr:`VerificationLevel.high` instead.
    - ``VerificationLevel.extreme`` - use :attr:`VerificationLevel.highest` instead.
    - ``VerificationLevel.double_table_flip`` - use :attr:`VerificationLevel.highest` instead.
    - ``VerificationLevel.very_high`` - use :attr:`VerificationLevel.highest` instead.

- ``topic`` parameter from :meth:`StageChannel.edit`

    - The ``topic`` parameter must now be set via :meth:`StageChannel.create_instance`.

- ``Reaction.custom_emoji``

    - Use :meth:`Reaction.is_custom_emoji` instead.

- ``AuditLogDiff.region``
- ``Guild.region``
- ``VoiceRegion``

    - This has been marked deprecated by Discord and it was usually more or less out of date due to the pace they added them anyway.

- ``region`` parameter from :meth:`Client.create_guild`
- ``region`` parameter from :meth:`Template.create_guild`
- ``region`` parameter from :meth:`Guild.edit`
- ``on_private_channel_create`` event

    - Discord API no longer sends channel create event for DMs.

- ``on_private_channel_delete`` event

    - Discord API no longer sends channel create event for DMs.

- The undocumented private ``on_socket_response`` event

    - Consider using the newer documented :func:`on_socket_event_type` event instead.

Miscellaneous Changes
----------------------

The following changes have been made:

- :func:`on_socket_raw_receive` is now only called if ``enable_debug_events`` is set on :class:`Client`.
- :func:`on_socket_raw_receive` is now only called once the **complete** message is received and decompressed. The passed ``msg`` parameter is now always :class:`str`.
- :func:`on_socket_raw_send` is now only called if ``enable_debug_events`` is set on :class:`Client`.
- The documented return type for :meth:`Guild.fetch_channels` changed to Sequence[:class:`abc.GuildChannel`].
- :func:`utils.resolve_invite` now returns a :class:`ResolvedInvite` class.
- :func:`utils.oauth_url` now defaults to ``bot`` and ``application.commands`` scopes when not given instead of just ``bot``.
- :meth:`abc.Messageable.typing` can no longer be used as a regular (non-async) context manager.
- :attr:`Intents.emojis` is now an alias of :attr:`Intents.emojis_and_stickers`.

    This may affect code that iterates through ``(name, value)`` pairs in an instance of this class:

    .. code:: python

        # before
        friendly_names = {
            ...,
            'emojis': 'Emojis Intent',
            ...,
        }
        for name, value in discord.Intents.all():
            print(f'{friendly_names[name]}: {value}')

        # after
        friendly_names = {
            ...,
            'emojis_and_stickers': 'Emojis Intent',
            ...,
        }
        for name, value in discord.Intents.all():
            print(f'{friendly_names[name]}: {value}')

- ``created_at`` is no longer part of :class:`abc.Snowflake`.

    All of the existing classes still keep this attribute. It is just no longer part of this protocol.
    This has been done because Discord reuses IDs (snowflakes) of some models in other models.
    For example, if :class:`Thread` is created from a message, its :attr:`Thread.id` is equivalent to the ID of that message
    and as such it doesn't contain information about creation time of the thread and :attr:`Thread.created_at` cannot be based on it.

- :class:`Embed`'s bool implementation now returns ``True`` when embed has any data set.
- Calling :meth:`Emoji.edit` without ``roles`` argument no longer makes the emoji available to everyone.

    - To make the emoji available to everyone, pass an empty list to ``roles`` instead.

- The old ``Colour.blurple`` has been renamed to :attr:`Colour.og_blurple`.

    - :attr:`Colour.blurple` refers to a different colour now.

- :attr:`Message.type` is now set to :attr:`MessageType.reply` when a message is a reply.

    - This is caused by a difference in behavior in the current Discord API version.

- :meth:`Message.edit` now merges object passed in ``allowed_mentions`` parameter with :attr:`Client.allowed_mentions`.
  If the parameter isn't provided, the defaults given by :attr:`Client.allowed_mentions` are used instead.

.. _migrating_2_0_commands:

Command Extension Changes
---------------------------

Converters Are Now Generic Runtime Protocols
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~ext.commands.Converter` is now a :func:`runtime-checkable <typing.runtime_checkable>` :class:`typing.Protocol`.

This results in a change of the base metaclass used by these classes
which may affect user-created classes that inherit from :class:`~ext.commands.Converter`.

Quick example:

.. code:: python

    # before
    class SomeConverterMeta(type):
        ...

    class SomeConverter(commands.Converter, metaclass=SomeConverterMeta):
        ...

    # after
    class SomeConverterMeta(type(commands.Converter)):
        ...

    class SomeConverter(commands.Converter, metaclass=SomeConverterMeta):
        ...

In addition, :class:`~ext.commands.Converter` is now a :class:`typing.Generic` which (optionally) allows the users to
define their type hints more accurately.

Function Signature Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following parameters are now positional-only:

- ``func`` in :meth:`ext.commands.Bot.add_check`
- ``func`` in :meth:`ext.commands.Bot.remove_check`
- ``func`` in :meth:`ext.commands.Command.add_check`
- ``func`` in :meth:`ext.commands.Command.remove_check`
- ``func`` in :meth:`ext.commands.HelpCommand.add_check`
- ``func`` in :meth:`ext.commands.HelpCommand.remove_check`
- ``cog`` in :meth:`ext.commands.Bot.add_cog`
- ``name`` in :meth:`ext.commands.Bot.get_cog`
- ``name`` in :meth:`ext.commands.Bot.remove_cog`
- ``command`` in :meth:`ext.commands.Context.invoke`
- ``command`` in :meth:`ext.commands.GroupMixin.add_command`
- ``name`` in :meth:`ext.commands.GroupMixin.get_command`
- ``name`` in :meth:`ext.commands.GroupMixin.remove_command`

The following parameters have been removed:

- ``self_bot`` from :class:`~ext.commands.Bot`

    - This has been done due to the :ref:`migrating_2_0_userbot_removal` changes.

The library now less often uses ``None`` as the default value for function/method parameters.

As a result, these parameters can no longer be ``None``:

- ``name`` in :meth:`ext.commands.Bot.add_listener`
- ``name`` in :meth:`ext.commands.Bot.remove_listener`
- ``name`` in :meth:`ext.commands.Bot.listen`
- ``name`` in :meth:`ext.commands.Cog.listener`
- ``name`` in :meth:`ext.commands.Command`
- ``name`` and ``cls`` in :meth:`ext.commands.command`
- ``name`` and ``cls`` in :meth:`ext.commands.group`

Removals
~~~~~~~~~~

The following attributes have been removed:

- ``original`` from the :exc:`~ext.commands.ExtensionNotFound`
- ``type`` from the :class:`~ext.commands.Cooldown` class
  that was provided by the :attr:`ext.commands.CommandOnCooldown.cooldown` attribute

    - Use :attr:`ext.commands.CommandOnCooldown.type` instead.

- ``clean_prefix`` from the :class:`~ext.commands.HelpCommand`
    
    - Use :attr:`ext.commands.Context.clean_prefix` instead.

Miscellanous Changes
~~~~~~~~~~~~~~~~~~~~~~

- :meth:`ext.commands.Bot.add_cog` is now raising :exc:`ClientException` when a cog with the same name is already loaded.

    - To override a cog, the new ``override`` parameter can be used.

- Metaclass of :class:`~ext.commands.Context` changed from :class:`abc.ABCMeta` to :class:`type`.
- Changed type of :attr:`ext.commands.Command.clean_params` from :class:`collections.OrderedDict` to :class:`dict`.
  as the latter is guaranteed to preserve insertion order since Python 3.7.
- :attr:`ext.commands.ChannelNotReadable.argument` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.NSFWChannelRequired.channel` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.Context.channel` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.Context.channel` may now be a :class:`PartialMessageable`.
- ``MissingPermissions.missing_perms`` has been renamed to :attr:`ext.commands.MissingPermissions.missing_permissions`.
- ``BotMissingPermissions.missing_perms`` has been renamed to :attr:`ext.commands.BotMissingPermissions.missing_permissions`.

.. _migrating_2_0_tasks:

Tasks Extension Changes
-------------------------

- Calling :meth:`ext.tasks.Loop.stop` in :meth:`~ext.tasks.Loop.before_loop` now stops the first iteration from running.
- Calling :meth:`ext.tasks.Loop.change_interval` now changes the interval for the sleep time right away,
  rather than on the next loop iteration.
- ``loop`` parameter in :func:`ext.tasks.loop` can no longer be ``None``.

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

- ``Client.messages``

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
