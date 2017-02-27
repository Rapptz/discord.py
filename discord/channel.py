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

from .permissions import Permissions, PermissionOverwrite
from .enums import ChannelType, try_enum
from .mixins import Hashable
from .role import Role
from .user import User
from .member import Member
from . import utils
from .errors import ClientException, NoMoreItems

import discord.abc

import copy
import time
import asyncio

__all__ = ('TextChannel', 'VoiceChannel', 'DMChannel', 'GroupChannel', '_channel_factory')

@asyncio.coroutine
def _single_delete_strategy(messages):
    for m in messages:
        yield from m.delete()

class TextChannel(discord.abc.Messageable, discord.abc.GuildChannel, Hashable):
    """Represents a Discord guild text channel.

    Supported Operations:

    +-----------+---------------------------------------+
    | Operation |              Description              |
    +===========+=======================================+
    | x == y    | Checks if two channels are equal.     |
    +-----------+---------------------------------------+
    | x != y    | Checks if two channels are not equal. |
    +-----------+---------------------------------------+
    | hash(x)   | Returns the channel's hash.           |
    +-----------+---------------------------------------+
    | str(x)    | Returns the channel's name.           |
    +-----------+---------------------------------------+

    Attributes
    -----------
    name: str
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: int
        The channel ID.
    topic: Optional[str]
        The channel's topic. None if it doesn't exist.
    position: int
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    """

    __slots__ = ( 'name', 'id', 'guild', 'topic', '_state',
                  'position', '_overwrites' )

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<TextChannel id={0.id} name={0.name!r} position={0.position}>'.format(self)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.topic = data.get('topic')
        self.position = data['position']
        self._fill_overwrites(data)

    @asyncio.coroutine
    def _get_channel(self):
        return self

    def permissions_for(self, member):
        base = super().permissions_for(member)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    permissions_for.__doc__ = discord.abc.GuildChannel.permissions_for.__doc__

    @asyncio.coroutine
    def edit(self, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`Permissions.manage_channel` permission to
        use this.

        Parameters
        ----------
        name: str
            The new channel name.
        topic: str
            The new channel's topic.
        position: int
            The new channel's position.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of channels.
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        try:
            position = options.pop('position')
        except KeyError:
            pass
        else:
            yield from self._move(position)
            self.position = position

        if options:
            data = yield from self._state.http.edit_channel(self.id, **options)
            self._update(self.guild, data)

    @asyncio.coroutine
    def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        Usable only by bot accounts.

        Parameters
        -----------
        messages : iterable of :class:`Message`
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete is less than 2 or more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        HTTPException
            Deleting the messages failed.
        """

        messages = list(messages)
        if len(messages) > 100 or len(messages) < 2:
            raise ClientException('Can only delete messages in the range of [2, 100]')

        message_ids = [m.id for m in messages]
        channel = yield from self._get_channel()

        yield from self._state.http.delete_messages(channel.id, message_ids)

    @asyncio.coroutine
    def purge(self, *, limit=100, check=None, before=None, after=None, around=None):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have :attr:`Permissions.manage_messages` permission to delete
        messages even if they are your own (unless you are a user account).
        The :attr:`Permissions.read_message_history` permission is also needed
        to retrieve message history.

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
            await channel.send_message('Deleted {} message(s)'.format(len(deleted)))

        Returns
        --------
        list
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, around=around)
        ret = []
        count = 0

        minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
        strategy = self.delete_messages if self._state.is_bot else _single_delete_strategy

        while True:
            try:
                msg = yield from iterator.get()
            except NoMoreItems:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    yield from strategy(to_delete)
                elif count == 1:
                    # delete a single message
                    yield from ret[-1].delete()

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    yield from strategy(to_delete)
                    count = 0
                    yield from asyncio.sleep(1)

                if check(msg):
                    if msg.id < minimum_time:
                        # older than 14 days old
                        if count == 1:
                            yield from ret[-1].delete()
                        elif count >= 2:
                            to_delete = ret[-count:]
                            yield from strategy(to_delete)

                        count = 0
                        strategy = _single_delete_strategy

                    count += 1
                    ret.append(msg)

class VoiceChannel(discord.abc.GuildChannel, Hashable):
    """Represents a Discord guild voice channel.

    Supported Operations:

    +-----------+---------------------------------------+
    | Operation |              Description              |
    +===========+=======================================+
    | x == y    | Checks if two channels are equal.     |
    +-----------+---------------------------------------+
    | x != y    | Checks if two channels are not equal. |
    +-----------+---------------------------------------+
    | hash(x)   | Returns the channel's hash.           |
    +-----------+---------------------------------------+
    | str(x)    | Returns the channel's name.           |
    +-----------+---------------------------------------+

    Attributes
    -----------
    name: str
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: int
        The channel ID.
    position: int
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: int
        The channel's preferred audio bitrate in bits per second.
    user_limit: int
        The channel's limit for number of members that can be in a voice channel.
    """

    __slots__ = ('name', 'id', 'guild', 'bitrate',  'user_limit',
                 '_state', 'position', '_overwrites' )

    def __init__(self, *, state, guild, data):
        self._state = state
        self.id = int(data['id'])
        self._update(guild, data)

    def __repr__(self):
        return '<VoiceChannel id={0.id} name={0.name!r} position={0.position}>'.format(self)

    def _update(self, guild, data):
        self.guild = guild
        self.name = data['name']
        self.position = data['position']
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')
        self._fill_overwrites(data)

    @property
    def voice_members(self):
        """Returns a list of :class:`Member` that are currently inside this voice channel."""
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret

    @asyncio.coroutine
    def edit(self, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`Permissions.manage_channel` permission to
        use this.

        Parameters
        ----------
        bitrate: int
            The new channel's bitrate.
        user_limit: int
            The new channel's user limit.
        position: int
            The new channel's position.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """

        try:
            position = options.pop('position')
        except KeyError:
            pass
        else:
            yield from self._move(position)
            self.position = position

        if options:
            data = yield from self._state.http.edit_channel(self.id, **options)
            self._update(self.guild, data)

class DMChannel(discord.abc.Messageable, Hashable):
    """Represents a Discord direct message channel.

    Supported Operations:

    +-----------+-------------------------------------------------+
    | Operation |                   Description                   |
    +===========+=================================================+
    | x == y    | Checks if two channels are equal.               |
    +-----------+-------------------------------------------------+
    | x != y    | Checks if two channels are not equal.           |
    +-----------+-------------------------------------------------+
    | hash(x)   | Returns the channel's hash.                     |
    +-----------+-------------------------------------------------+
    | str(x)    | Returns a string representation of the channel  |
    +-----------+-------------------------------------------------+

    Attributes
    ----------
    recipient: :class:`User`
        The user you are participating with in the direct message channel.
    me: :class:`User`
        The user presenting yourself.
    id: int
        The direct message channel ID.
    """

    __slots__ = ('id', 'recipient', 'me', '_state')

    def __init__(self, *, me, state, data):
        self._state = state
        self.recipient = state.store_user(data['recipients'][0])
        self.me = me
        self.id = int(data['id'])

    @asyncio.coroutine
    def _get_channel(self):
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

    Supported Operations:

    +-----------+-------------------------------------------------+
    | Operation |                   Description                   |
    +===========+=================================================+
    | x == y    | Checks if two channels are equal.               |
    +-----------+-------------------------------------------------+
    | x != y    | Checks if two channels are not equal.           |
    +-----------+-------------------------------------------------+
    | hash(x)   | Returns the channel's hash.                     |
    +-----------+-------------------------------------------------+
    | str(x)    | Returns a string representation of the channel  |
    +-----------+-------------------------------------------------+

    Attributes
    ----------
    recipients: list of :class:`User`
        The users you are participating with in the group channel.
    me: :class:`User`
        The user presenting yourself.
    id: int
        The group channel ID.
    owner: :class:`User`
        The user that owns the group channel.
    icon: Optional[str]
        The group channel's icon hash if provided.
    name: Optional[str]
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

    @asyncio.coroutine
    def _get_channel(self):
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

    @asyncio.coroutine
    def add_recipients(self, *recipients):
        """|coro|

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
            yield from req(self.id, recipient.id)

    @asyncio.coroutine
    def remove_recipients(self, *recipients):
        """|coro|

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
            yield from req(self.id, recipient.id)

    @asyncio.coroutine
    def edit(self, **fields):
        """|coro|

        Edits the group.

        Parameters
        -----------
        name: Optional[str]
            The new name to change the group to.
            Could be ``None`` to remove the name.
        icon: Optional[bytes]
            A bytes-like object representing the new icon.
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

        data = yield from self._state.http.edit_group(self.id, **fields)
        self._update_group(data)

    @asyncio.coroutine
    def leave(self):
        """|coro|

        Leave the group.

        If you are the only one in the group, this deletes it as well.

        Raises
        -------
        HTTPException
            Leaving the group failed.
        """

        yield from self._state.http.leave_group(self.id)

def _channel_factory(channel_type):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    else:
        return None, value
