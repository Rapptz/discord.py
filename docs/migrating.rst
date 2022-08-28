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

.. _migrating_2_0_client_async_setup:

asyncio Event Loop Changes
---------------------------

Python 3.7 introduced a new helper function :func:`asyncio.run` which automatically creates and destroys the asynchronous event loop.

In order to support this, the way discord.py handles the :mod:`asyncio` event loop has changed.

This allows you to rather than using :meth:`Client.run` create your own asynchronous loop to setup other asynchronous code as needed.

Quick example:

.. code-block:: python

    client = discord.Client()

    async def main():
        # do other async things
        await my_async_function()

        # start the client
        async with client:
            await client.start(TOKEN)

    asyncio.run(main())

A new :meth:`~Client.setup_hook` method has also been added to the :class:`Client` class.
This method is called after login but before connecting to the discord gateway.

It is intended to be used to setup various bot features in an asynchronous context.

:meth:`~Client.setup_hook` can be defined by subclassing the :class:`Client` class.

Quick example:

.. code-block:: python

    class MyClient(discord.Client):
        async def setup_hook(self):
            print('This is asynchronous!')

    client = MyClient()
    client.run(TOKEN)

With this change, constructor of :class:`Client` no longer accepts ``connector`` and ``loop`` parameters.

In parallel with this change, changes were made to loading and unloading of commands extension extensions and cogs,
see :ref:`migrating_2_0_commands_extension_cog_async` for more information.

Intents Are Now Required
--------------------------

In earlier versions, the ``intents`` keyword argument was optional and defaulted to :meth:`Intents.default`. In order to better educate users on their intents and to also make it more explicit, this parameter is now required to pass in.

For example:

.. code-block:: python3

    # before
    client = discord.Client()

    # after
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

This change applies to **all** subclasses of :class:`Client`.

- :class:`AutoShardedClient`
- :class:`~discord.ext.commands.Bot`
- :class:`~discord.ext.commands.AutoShardedBot`


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

To ease the migration, :func:`utils.utcnow` helper function has been added.

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
- :func:`utils.time_snowflake` function

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

- Threads do not have their own NSFW status, they inherit it from their parent channel.

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
- :attr:`Message.channel_mentions` list may now contain a :class:`Thread`.
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

Changing certain lists to be lazy sequences instead
-----------------------------------------------------

In order to improve performance when calculating the length of certain lists, certain attributes were changed to return a sequence rather than a :class:`list`.

A sequence is similar to a :class:`list` except it is read-only. In order to get a list again you can call :class:`list` on the resulting sequence.

The following properties were changed to return a sequence instead of a list:

- :attr:`Client.guilds`
- :attr:`Client.emojis`
- :attr:`Client.private_channels`
- :attr:`Guild.roles`
- :attr:`Guild.channels`
- :attr:`Guild.members`

This change should be transparent, unless you are modifying the sequence by doing things such as ``list.append``.


Embed Changes
--------------

Originally, embeds used a special sentinel to denote emptiness or remove an attribute from display. The ``Embed.Empty`` sentinel was made when Discord's embed design was in a nebulous state of flux. Since then, the embed design has stabilised and thus the sentinel is seen as legacy.

Therefore, ``Embed.Empty`` has been removed in favour of ``None``.

Additionally, ``Embed.__eq__`` has been implemented thus embeds becoming unhashable (e.g. using them in sets or dict keys).

.. code-block:: python

    # before
    embed = discord.Embed(title='foo')
    embed.title = discord.Embed.Empty
    embed == embed.copy() # False

    # after
    embed = discord.Embed(title='foo')
    embed.title = None
    embed == embed.copy() # True
    {embed, embed} # Raises TypeError



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

Logging Changes
----------------

The library now provides a default logging configuration if using :meth:`Client.run`. To disable it, pass ``None`` to the ``log_handler`` keyword parameter. Since the library now provides a default logging configuration, certain methods were changed to no longer print to :data:`sys.stderr` but use the logger instead:

- :meth:`Client.on_error`
- :meth:`discord.ext.tasks.Loop.error`
- :meth:`discord.ext.commands.Bot.on_command_error`
- :meth:`VoiceClient.play`

For more information, check :doc:`logging`.

Text in Voice
---------------

In order to support text in voice functionality, a few changes had to be made:

- :class:`VoiceChannel` is now :class:`abc.Messageable` so it can have messages sent and received.
- :attr:`Message.channel` can now be :class:`VoiceChannel`.

In the future this may include :class:`StageChannel` when Discord implements it.

Removal of ``StoreChannel``
-----------------------------

Discord's API has removed store channels as of `March 10th, 2022 <https://support-dev.discord.com/hc/en-us/articles/4414590563479>`_. Therefore, the library has removed support for it as well.

This removes the following:

- ``StoreChannel``
- ``commands.StoreChannelConverter``
- ``ChannelType.store``

Change in ``Guild.bans`` endpoint
-----------------------------------

Due to a breaking API change by Discord, :meth:`Guild.bans` no longer returns a list of every ban in the guild but instead is paginated using an asynchronous iterator.

.. code-block:: python3

    # before

    bans = await guild.bans()

    # after
    async for ban in guild.bans(limit=1000):
        ...


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
- :meth:`Client.on_error`
- :meth:`abc.Messageable.fetch_message`
- :meth:`abc.GuildChannel.permissions_for`
- :meth:`DMChannel.get_partial_message`
- :meth:`TextChannel.get_partial_message`
- :meth:`TextChannel.delete_messages`
- :meth:`Webhook.delete_message`
- :func:`utils.find`
- :func:`utils.snowflake_time`

The following parameters are now positional-only:

- ``iterable`` in :func:`utils.get`
- ``event_method`` in :meth:`Client.on_error`
- ``event`` in :meth:`Client.wait_for`
- ``dt`` in :func:`utils.time_snowflake`

The following are now keyword-only:

- Parameters in :meth:`Reaction.users`
- Parameters in :meth:`Client.create_guild`
- ``permissions``, ``guild``, ``redirect_uri``, and ``scopes`` parameters in :func:`utils.oauth_url`
- ``high`` in :func:`utils.snowflake_time`

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
- :meth:`Widget.fetch_invite` may now be ``None``.
- :attr:`Guild.shard_id` is now ``0`` instead of ``None`` if :class:`AutoShardedClient` is not used.
- :attr:`Guild.mfa_level` is now of type :class:`MFALevel`.
- :attr:`Guild.member_count` is now of type Optional[:class:`int`].
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
- :attr:`abc.GuildChannel.overwrites` keys can now have :class:`Object` in them.

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

- ``Permissions.use_slash_commands`` and ``PermissionOverwrite.use_slash_commands``
    - Use :attr:`Permissions.use_application_commands` and ``PermissionOverwrite.use_application_commands`` instead.

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

- ``abc.Messageable.trigger_typing``

    - Use :meth:`abc.Messageable.typing` with ``await`` instead.

Miscellaneous Changes
----------------------

The following changes have been made:

- :func:`on_socket_raw_receive` is now only called if ``enable_debug_events`` is set on :class:`Client`.
- :func:`on_socket_raw_receive` is now only called once the **complete** message is received and decompressed. The passed ``msg`` parameter is now always :class:`str`.
- :func:`on_socket_raw_send` is now only called if ``enable_debug_events`` is set on :class:`Client`.
- The documented return type for :meth:`Guild.fetch_channels` changed to Sequence[:class:`abc.GuildChannel`].
- :func:`utils.resolve_invite` now returns a :class:`ResolvedInvite` class.
- :func:`utils.oauth_url` now defaults to ``bot`` and ``applications.commands`` scopes when not given instead of just ``bot``.
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

- :meth:`Permissions.stage_moderator` now includes the :attr:`Permissions.manage_channels` permission and the :attr:`Permissions.request_to_speak` permission is no longer included.

- :attr:`File.filename` will no longer be ``None``, in situations where previously this was the case the filename is set to `'untitled'`.

- :attr:`Message.application` will no longer be a raw :class:`dict` of the API payload and now returns an instance of :class:`MessageApplication`.

:meth:`VoiceProtocol.connect` signature changes.
--------------------------------------------------

:meth:`VoiceProtocol.connect` will now be passed 2 keyword only arguments, ``self_deaf`` and ``self_mute``. These indicate
whether or not the client should join the voice chat being deafened or muted.

.. _migrating_2_0_commands:

Command Extension Changes
---------------------------

.. _migrating_2_0_commands_extension_cog_async:

Extension and Cog Loading / Unloading is Now Asynchronous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As an extension to the :ref:`asyncio changes <migrating_2_0_client_async_setup>` the loading and unloading of extensions and cogs is now asynchronous.

To accommodate this, the following changes have been made:

- The ``setup`` and ``teardown`` functions in extensions must now be coroutines.
- :meth:`ext.commands.Bot.load_extension` must now be awaited.
- :meth:`ext.commands.Bot.unload_extension` must now be awaited.
- :meth:`ext.commands.Bot.reload_extension` must now be awaited.
- :meth:`ext.commands.Bot.add_cog` must now be awaited.
- :meth:`ext.commands.Bot.remove_cog` must now be awaited.

Quick example of an extension setup function:

.. code:: python

    # before
    def setup(bot):
        bot.add_cog(MyCog(bot))

    # after
    async def setup(bot):
        await bot.add_cog(MyCog(bot))

Quick example of loading an extension:

.. code:: python

    # before
    bot.load_extension('my_extension')

    # after using setup_hook
    class MyBot(commands.Bot):
        async def setup_hook(self):
            await self.load_extension('my_extension')

    # after using async_with
    async def main():
        async with bot:
            await bot.load_extension('my_extension')
            await bot.start(TOKEN)

    asyncio.run(main())


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

Parameters in the following methods are now all positional-only:

- :meth:`ext.commands.when_mentioned`
- :meth:`ext.commands.Bot.on_command_error`
- :meth:`ext.commands.Bot.check`
- :meth:`ext.commands.Bot.check_once`
- :meth:`ext.commands.Bot.is_owner`
- :meth:`ext.commands.Bot.before_invoke`
- :meth:`ext.commands.Bot.after_invoke`
- :meth:`ext.commands.Bot.get_prefix`
- :meth:`ext.commands.Bot.invoke`
- :meth:`ext.commands.Bot.process_commands`
- :meth:`ext.commands.Command.is_on_cooldown`
- :meth:`ext.commands.Command.reset_cooldown`
- :meth:`ext.commands.Command.get_cooldown_retry_after`
- :meth:`ext.commands.Command.error`
- :meth:`ext.commands.Command.before_invoke`
- :meth:`ext.commands.Command.after_invoke`
- :meth:`ext.commands.Command.can_run`
- :meth:`ext.commands.check`
- :meth:`ext.commands.has_role`
- :meth:`ext.commands.bot_has_role`
- :meth:`ext.commands.before_invoke`
- :meth:`ext.commands.after_invoke`
- :meth:`ext.commands.HelpCommand.get_command_signature`
- :meth:`ext.commands.HelpCommand.remove_mentions`
- :meth:`ext.commands.HelpCommand.command_not_found`
- :meth:`ext.commands.HelpCommand.subcommand_not_found`
- :meth:`ext.commands.HelpCommand.get_max_size`
- :meth:`ext.commands.HelpCommand.send_error_message`
- :meth:`ext.commands.HelpCommand.on_help_command_error`
- :meth:`ext.commands.HelpCommand.send_bot_help`
- :meth:`ext.commands.HelpCommand.send_cog_help`
- :meth:`ext.commands.HelpCommand.send_group_help`
- :meth:`ext.commands.HelpCommand.send_command_help`
- :meth:`ext.commands.HelpCommand.prepare_help_command`
- :meth:`ext.commands.DefaultHelpCommand.shorten_text`
- :meth:`ext.commands.DefaultHelpCommand.add_command_formatting`
- :meth:`ext.commands.MinimalHelpCommand.get_command_signature`
- :meth:`ext.commands.MinimalHelpCommand.add_bot_commands_formatting`
- :meth:`ext.commands.MinimalHelpCommand.add_subcommand_formatting`
- :meth:`ext.commands.MinimalHelpCommand.add_aliases_formatting`
- :meth:`ext.commands.MinimalHelpCommand.add_command_formatting`

The following parameters are now positional-only:

- ``func`` in :meth:`ext.commands.Bot.check`
- ``func`` in :meth:`ext.commands.Bot.add_check`
- ``func`` in :meth:`ext.commands.Bot.remove_check`
- ``func`` in :meth:`ext.commands.Bot.check_once`
- ``func`` in :meth:`ext.commands.Bot.add_listener`
- ``func`` in :meth:`ext.commands.Bot.remove_listener`
- ``message`` in :meth:`ext.commands.Bot.get_context`
- ``func`` in :meth:`ext.commands.Command.add_check`
- ``func`` in :meth:`ext.commands.Command.remove_check`
- ``context`` in :meth:`ext.commands.Command.__call__`
- ``commands`` in :meth:`ext.commands.HelpCommand.filter_commands`
- ``ctx`` in :meth:`ext.commands.HelpCommand.command_callback`
- ``func`` in :meth:`ext.commands.HelpCommand.add_check`
- ``func`` in :meth:`ext.commands.HelpCommand.remove_check`
- ``commands`` in :meth:`ext.commands.DefaultHelpCommand.add_indented_commands`
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

Miscellaneous Changes
~~~~~~~~~~~~~~~~~~~~~~

- :meth:`ext.commands.Bot.add_cog` is now raising :exc:`ClientException` when a cog with the same name is already loaded.

    - To override a cog, the new ``override`` parameter can be used.

- Metaclass of :class:`~ext.commands.Context` changed from :class:`abc.ABCMeta` to :class:`type`.
- Changed type of :attr:`ext.commands.Command.clean_params` from :class:`collections.OrderedDict` to :class:`dict`.
  As the latter is guaranteed to preserve insertion order since Python 3.7.
- :attr:`ext.commands.ChannelNotReadable.argument` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.NSFWChannelRequired.channel` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.Context.channel` may now be a :class:`Thread` due to the :ref:`migrating_2_0_thread_support` changes.
- :attr:`ext.commands.Context.channel` may now be a :class:`PartialMessageable`.
- ``MissingPermissions.missing_perms`` has been renamed to :attr:`ext.commands.MissingPermissions.missing_permissions`.
- ``BotMissingPermissions.missing_perms`` has been renamed to :attr:`ext.commands.BotMissingPermissions.missing_permissions`.
- :meth:`ext.commands.Cog.cog_load` has been added as part of the :ref:`migrating_2_0_commands_extension_cog_async` changes.
- :meth:`ext.commands.Cog.cog_unload` may now be a :term:`coroutine` due to the :ref:`migrating_2_0_commands_extension_cog_async` changes.
- :attr:`ext.commands.Command.clean_params` type now uses a custom :class:`inspect.Parameter` to handle defaults.

.. _migrating_2_0_tasks:

Tasks Extension Changes
-------------------------

- Calling :meth:`ext.tasks.Loop.stop` in :meth:`~ext.tasks.Loop.before_loop` now stops the first iteration from running.
- Calling :meth:`ext.tasks.Loop.change_interval` now changes the interval for the sleep time right away,
  rather than on the next loop iteration.
- ``loop`` parameter in :func:`ext.tasks.loop` can no longer be ``None``.

Migrating to v1.0
======================

The contents of that migration has been moved to :ref:`migrating_1_0`.
