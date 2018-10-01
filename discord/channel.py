# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from .permissions import Permissions
from .enums import ChannelType, try_enum
from .mixins import Hashable
from . import utils
from .errors import ClientException, NoMoreItems
from .webhook import Webhook

import discord.abc

import time
import asyncio

__all__ = ['TextChannel', 'VoiceChannel', 'DMChannel', 'CategoryChannel', 'GroupChannel', '_channel_factory']

async def _single_delete_strategy(messages):
    for m in messages:
        await m.delete()

class TextChannel(discord.abc.Messageable, discord.abc.GuildChannel, Hashable):
    """Represents a Discord guild text channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: :class:`int`
        The category channel ID this channel belongs to.
    topic: Optional[:class:`str`]
        The channel's topic. None if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    """

    __slots__ = ('name', 'id', 'guild', 'topic', '_state', 'nsfw',
                 'category_id', 'position', 'slowmode_delay', '_overwrites')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<TextChannel id={0.id} name={0.name!r} position={0.position}>'.format(self)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.topic = data.get('topic')
        self.position = data['position']
        self.nsfw = data.get('nsfw', False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._fill_overwrites(data)

    async def _get_channel(self):
        return self

    def permissions_for(self, member):
        base = super().permissions_for(member)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    permissions_for.__doc__ = discord.abc.GuildChannel.permissions_for.__doc__

    @property
    def members(self):
        """Returns a :class:`list` of :class:`Member` that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    def is_nsfw(self):
        """Checks if the channel is NSFW."""
        n = self.name
        return self.nsfw or n == 'nsfw' or n[:5] == 'nsfw-'

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel. A value of
            `0` disables slowmode. The maximum value possible is `120`.
        reason: Optional[:class:`str`]
            The reason for editing this channel. Shows up on the audit log.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        await self._edit(options, reason=reason)

    async def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        As a special case, if the number of messages is 0, then nothing
        is done. If the number of messages is 1 then single message
        delete is done. If it's more than two, then bulk delete is used.

        You cannot bulk delete more than 100 messages or messages that
        are older than 14 days old.

        You must have the :attr:`~Permissions.manage_messages` permission to
        use this.

        Usable only by bot accounts.

        Parameters
        -----------
        messages: Iterable[:class:`abc.Snowflake`]
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete was more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        HTTPException
            Deleting the messages failed.
        """
        if not isinstance(messages, (list, tuple)):
            messages = list(messages)

        if len(messages) == 0:
            return # do nothing

        if len(messages) == 1:
            message_id = messages[0].id
            await self._state.http.delete_message(self.id, message_id)
            return

        if len(messages) > 100:
            raise ClientException('Can only bulk delete messages up to 100 messages')

        message_ids = [m.id for m in messages]
        await self._state.http.delete_messages(self.id, message_ids)

    async def purge(self, *, limit=100, check=None, before=None, after=None, around=None, reverse=False, bulk=True):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have the :attr:`~Permissions.manage_messages` permission to
        delete messages even if they are your own (unless you are a user
        account). The :attr:`~Permissions.read_message_history` permission is
        also needed to retrieve message history.

        Internally, this employs a different number of strategies depending
        on the conditions met such as if a bulk delete is possible or if
        the account is a user bot or not.

        Parameters
        -----------
        limit: int
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: predicate
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before
            Same as ``before`` in :meth:`history`.
        after
            Same as ``after`` in :meth:`history`.
        around
            Same as ``around`` in :meth:`history`.
        reverse
            Same as ``reverse`` in :meth:`history`.
        bulk: bool
            If True, use bulk delete. bulk=False is useful for mass-deleting
            a bot's own messages without manage_messages. When True, will fall
            back to single delete if current account is a user bot, or if
            messages are older than two weeks.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required.
        HTTPException
            Purging the messages failed.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send('Deleted {} message(s)'.format(len(deleted)))

        Returns
        --------
        list
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, reverse=reverse, around=around)
        ret = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if self._state.is_bot and bulk else _single_delete_strategy

        while True:
            try:
                msg = await iterator.next()
            except NoMoreItems:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    await strategy(to_delete)
                elif count == 1:
                    # delete a single message
                    await ret[-1].delete()

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    await strategy(to_delete)
                    count = 0
                    await asyncio.sleep(1)

                if check(msg):
                    if msg.id < minimum_time:
                        # older than 14 days old
                        if count == 1:
                            await ret[-1].delete()
                        elif count >= 2:
                            to_delete = ret[-count:]
                            await strategy(to_delete)

                        count = 0
                        strategy = _single_delete_strategy

                    count += 1
                    ret.append(msg)

    async def webhooks(self):
        """|coro|

        Gets the list of webhooks from this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        -------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks for this channel.
        """

        data = await self._state.http.channel_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def create_webhook(self, *, name, avatar=None):
        """|coro|

        Creates a webhook for this channel.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Parameters
        -------------
        name: str
            The webhook's name.
        avatar: Optional[bytes]
            A :term:`py:bytes-like object` representing the webhook's default avatar.
            This operates similarly to :meth:`~ClientUser.edit`.

        Raises
        -------
        HTTPException
            Creating the webhook failed.
        Forbidden
            You do not have permissions to create a webhook.

        Returns
        --------
        :class:`Webhook`
            The created webhook.
        """

        if avatar is not None:
            avatar = utils._bytes_to_base64_data(avatar)

        data = await self._state.http.create_webhook(self.id, name=str(name), avatar=avatar)
        return Webhook.from_state(data, state=self._state)

class VoiceChannel(discord.abc.Connectable, discord.abc.GuildChannel, Hashable):
    """Represents a Discord guild voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: :class:`int`
        The category channel ID this channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
    """

    __slots__ = ('name', 'id', 'guild', 'bitrate', 'user_limit',
                 '_state', 'position', '_overwrites', 'category_id')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<VoiceChannel id={0.id} name={0.name!r} position={0.position}>'.format(self)

    def _get_voice_client_key(self):
        return self.guild.id, 'guild_id'

    def _get_voice_state_pair(self):
        return self.guild.id, self.id

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.position = data['position']
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')
        self._fill_overwrites(data)

    @property
    def members(self):
        """Returns a list of :class:`Member` that are currently inside this voice channel."""
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: str
            The new channel's name.
        bitrate: int
            The new channel's bitrate.
        user_limit: int
            The new channel's user limit.
        position: int
            The new channel's position.
        sync_permissions: bool
            Whether to sync permissions with the channel's new or pre-existing
            category. Defaults to ``False``.
        category: Optional[:class:`CategoryChannel`]
            The new category for this channel. Can be ``None`` to remove the
            category.
        reason: Optional[str]
            The reason for editing this channel. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        await self._edit(options, reason=reason)

class CategoryChannel(discord.abc.GuildChannel, Hashable):
    """Represents a Discord channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    -----------
    name: :class:`str`
        The category name.
    guild: :class:`Guild`
        The guild the category belongs to.
    id: :class:`int`
        The category channel ID.
    position: :class:`int`
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    """

    __slots__ = ('name', 'id', 'guild', 'nsfw', '_state', 'position', '_overwrites', 'category_id')

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<CategoryChannel id={0.id} name={0.name!r} position={0.position}>'.format(self)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.category_id = utils._get_as_snowflake(data, 'parent_id')
        self.nsfw = data.get('nsfw', False)
        self.position = data['position']
        self._fill_overwrites(data)

    def is_nsfw(self):
        """Checks if the category is NSFW."""
        n = self.name
        return self.nsfw or n == 'nsfw' or n[:5] == 'nsfw-'

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        Parameters
        ----------
        name: str
            The new category's name.
        position: int
            The new category's position.
        nsfw: bool
            To mark the category as NSFW or not.
        reason: Optional[str]
            The reason for editing this category. Shows up on the audit log.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of categories.
        Forbidden
            You do not have permissions to edit the category.
        HTTPException
            Editing the category failed.
        """

        try:
            position = options.pop('position')
        except KeyError:
            pass
        else:
            await self._move(position, reason=reason)
            self.position = position

        if options:
            data = await self._state.http.edit_channel(self.id, reason=reason, **options)
            self._update(self.guild, data)

    @property
    def channels(self):
        """List[:class:`abc.GuildChannel`]: Returns the channels that are under this category.

        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """
        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret

class DMChannel(discord.abc.Messageable, Hashable):
    """Represents a Discord direct message channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipient: :class:`User`
        The user you are participating with in the direct message channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The direct message channel ID.
    """

    __slots__ = ('id', 'recipient', 'me', '_state')

    def __init__(self, *, me, state, data):
        self._state = state
        self.recipient = state.store_user(data['recipients'][0])
        self.me = me
        self.id = int(data['id'])

    async def _get_channel(self):
        return self

    def __str__(self):
        return 'Direct Message with %s' % self.recipient

    def __repr__(self):
        return '<DMChannel id={0.id} recipient={0.recipient!r}>'.format(self)

    @property
    def created_at(self):
        """Returns the direct message channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, user=None):
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to true except:

        - send_tts_messages: You cannot send TTS messages in a DM.
        - manage_messages: You cannot delete others messages in a DM.

        Parameters
        -----------
        user: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility.

        Returns
        --------
        :class:`Permissions`
            The resolved permissions.
        """

        base = Permissions.text()
        base.send_tts_messages = False
        base.manage_messages = False
        return base

class GroupChannel(discord.abc.Messageable, Hashable):
    """Represents a Discord group channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    recipients: :class:`list` of :class:`User`
        The users you are participating with in the group channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The group channel ID.
    owner: :class:`User`
        The user that owns the group channel.
    icon: Optional[:class:`str`]
        The group channel's icon hash if provided.
    name: Optional[:class:`str`]
        The group channel's name if provided.
    """

    __slots__ = ('id', 'recipients', 'owner', 'icon', 'name', 'me', '_state')

    def __init__(self, *, me, state, data):
        self._state = state
        self.id = int(data['id'])
        self.me = me
        self._update_group(data)

    def _update_group(self, data):
        owner_id = utils._get_as_snowflake(data, 'owner_id')
        self.icon = data.get('icon')
        self.name = data.get('name')

        try:
            self.recipients = [self._state.store_user(u) for u in data['recipients']]
        except KeyError:
            pass

        if owner_id == self.me.id:
            self.owner = self.me
        else:
            self.owner = utils.find(lambda u: u.id == owner_id, self.recipients)

    async def _get_channel(self):
        return self

    def __str__(self):
        if self.name:
            return self.name

        if len(self.recipients) == 0:
            return 'Unnamed'

        return ', '.join(map(lambda x: x.name, self.recipients))

    def __repr__(self):
        return '<GroupChannel id={0.id} name={0.name!r}>'.format(self)

    @property
    def icon_url(self):
        """Returns the channel's icon URL if available or an empty string otherwise."""
        if self.icon is None:
            return ''

        return 'https://cdn.discordapp.com/channel-icons/{0.id}/{0.icon}.jpg'.format(self)

    @property
    def created_at(self):
        """Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, user):
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to true except:

        - send_tts_messages: You cannot send TTS messages in a DM.
        - manage_messages: You cannot delete others messages in a DM.

        This also checks the kick_members permission if the user is the owner.

        Parameters
        -----------
        user: :class:`User`
            The user to check permissions for.

        Returns
        --------
        :class:`Permissions`
            The resolved permissions for the user.
        """

        base = Permissions.text()
        base.send_tts_messages = False
        base.manage_messages = False
        base.mention_everyone = True

        if user.id == self.owner.id:
            base.kick_members = True

        return base

    async def add_recipients(self, *recipients):
        r"""|coro|

        Adds recipients to this group.

        A group can only have a maximum of 10 members.
        Attempting to add more ends up in an exception. To
        add a recipient to the group, you must have a relationship
        with the user of type :attr:`RelationshipType.friend`.

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument list of users to add to this group.

        Raises
        -------
        HTTPException
            Adding a recipient to this group failed.
        """

        # TODO: wait for the corresponding WS event

        req = self._state.http.add_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id)

    async def remove_recipients(self, *recipients):
        r"""|coro|

        Removes recipients from this group.

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument list of users to remove from this group.

        Raises
        -------
        HTTPException
            Removing a recipient from this group failed.
        """

        # TODO: wait for the corresponding WS event

        req = self._state.http.remove_group_recipient
        for recipient in recipients:
            await req(self.id, recipient.id)

    async def edit(self, **fields):
        """|coro|

        Edits the group.

        Parameters
        -----------
        name: Optional[str]
            The new name to change the group to.
            Could be ``None`` to remove the name.
        icon: Optional[bytes]
            A :term:`py:bytes-like object` representing the new icon.
            Could be ``None`` to remove the icon.

        Raises
        -------
        HTTPException
            Editing the group failed.
        """

        try:
            icon_bytes = fields['icon']
        except KeyError:
            pass
        else:
            if icon_bytes is not None:
                fields['icon'] = utils._bytes_to_base64_data(icon_bytes)

        data = await self._state.http.edit_group(self.id, **fields)
        self._update_group(data)

    async def leave(self):
        """|coro|

        Leave the group.

        If you are the only one in the group, this deletes it as well.

        Raises
        -------
        HTTPException
            Leaving the group failed.
        """

        await self._state.http.leave_group(self.id)

def _channel_factory(channel_type):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    else:
        return None, value
