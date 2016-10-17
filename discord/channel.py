# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

from . import utils, abc
from .permissions import Permissions, PermissionOverwrite
from .enums import ChannelType, try_enum
from collections import namedtuple
from .mixins import Hashable
from .role import Role
from .user import User
from .member import Member

import copy
import asyncio

__all__ = ('TextChannel', 'VoiceChannel', 'DMChannel', 'GroupChannel', '_channel_factory')

Overwrites = namedtuple('Overwrites', 'id allow deny type')

class CommonGuildChannel(Hashable):
    __slots__ = ()

    def __str__(self):
        return self.name

    @asyncio.coroutine
    def _move(self, position):
        if position < 0:
            raise InvalidArgument('Channel position cannot be less than 0.')

        http = self._state.http
        url = '{0}/{1.server.id}/channels'.format(http.GUILDS, self)
        channels = [c for c in self.server.channels if isinstance(c, type(self))]

        if position >= len(channels):
            raise InvalidArgument('Channel position cannot be greater than {}'.format(len(channels) - 1))

        channels.sort(key=lambda c: c.position)

        try:
            # remove ourselves from the channel list
            channels.remove(self)
        except ValueError:
            # not there somehow lol
            return
        else:
            # add ourselves at our designated position
            channels.insert(position, self)

        payload = [{'id': c.id, 'position': index } for index, c in enumerate(channels)]
        yield from http.patch(url, json=payload, bucket='move_channel')

    def _fill_overwrites(self, data):
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.server.id

        for index, overridden in enumerate(data.get('permission_overwrites', [])):
            overridden_id = int(overridden.pop('id'))
            self._overwrites.append(Overwrites(id=overridden_id, **overridden))

            if overridden['type'] == 'member':
                continue

            if overridden_id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self):
        """Returns a list of :class:`Roles` that have been overridden from
        their default values in the :attr:`Server.roles` attribute."""
        ret = []
        for overwrite in filter(lambda o: o.type == 'role', self._overwrites):
            role = utils.get(self.server.roles, id=overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def is_default(self):
        """bool : Indicates if this is the default channel for the :class:`Server` it belongs to."""
        return self.server.id == self.id

    @property
    def mention(self):
        """str : The string that allows you to mention the channel."""
        return '<#{0.id}>'.format(self)

    @property
    def created_at(self):
        """Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj):
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj
            The :class:`Role` or :class:`Member` or :class:`Object` denoting
            whose overwrite to get.

        Returns
        ---------
        :class:`PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, Member):
            predicate = lambda p: p.type == 'member'
        elif isinstance(obj, Role):
            predicate = lambda p: p.type == 'role'
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self):
        """Returns all of the channel's overwrites.

        This is returned as a list of two-element tuples containing the target,
        which can be either a :class:`Role` or a :class:`Member` and the overwrite
        as the second element as a :class:`PermissionOverwrite`.

        Returns
        --------
        List[Tuple[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]]:
            The channel's permission overwrites.
        """
        ret = []
        for ow in self._permission_overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)

            if ow.type == 'role':
                # accidentally quadratic
                target = utils.find(lambda r: r.id == ow.id, self.server.roles)
            elif ow.type == 'member':
                target = self.server.get_member(ow.id)

            ret.append((target, overwrite))
        return ret

    def permissions_for(self, member):
        """Handles permission resolution for the current :class:`Member`.

        This function takes into consideration the following cases:

        - Server owner
        - Server roles
        - Channel overrides
        - Member overrides
        - Whether the channel is the default channel.

        Parameters
        ----------
        member : :class:`Member`
            The member to resolve permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the member.
        """

        # The current cases can be explained as:
        # Server owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to
        # True. If the channel is the default channel then everyone gets
        # read permissions regardless.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if member.id == self.server.owner.id:
            return Permissions.all()

        default = self.server.default_role
        base = Permissions(default.permissions.value)

        # Apply server roles that the member has.
        for role in member.roles:
            base.value |= role.permissions.value

        # Server-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        member_role_ids = set(map(lambda r: r.id, member.roles))
        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in self._overwrites:
            if overwrite.type == 'role' and overwrite.id in member_role_ids:
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in self._overwrites:
            if overwrite.type == 'member' and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        # default channels can always be read
        if self.is_default:
            base.read_messages = True

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        # text channels do not have voice related permissions
        if isinstance(self, TextChannel):
            denied = Permissions.voice()
            base.value &= ~denied.value

        return base

    @asyncio.coroutine
    def delete(self):
        """|coro|

        Deletes the channel.

        You must have Manage Channel permission to use this.

        Raises
        -------
        Forbidden
            You do not have proper permissions to delete the channel.
        NotFound
            The channel was not found or was already deleted.
        HTTPException
            Deleting the channel failed.
        """
        yield from self._state.http.delete_channel(self.id)

class TextChannel(abc.MessageChannel, CommonGuildChannel):
    """Represents a Discord server text channel.

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
    server: :class:`Server`
        The server the channel belongs to.
    id: int
        The channel ID.
    topic: Optional[str]
        The channel's topic. None if it doesn't exist.
    position: int
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    """

    __slots__ = ( 'name', 'id', 'server', 'topic', '_state',
                  'position', '_overwrites' )

    def __init__(self, *, state, server, data):
        self._state = state
        self.id = int(data['id'])
        self._update(server, data)

    def _update(self, server, data):
        self.server = server
        self.name = data['name']
        self.topic = data.get('topic')
        self.position = data['position']
        self._fill_overwrites(data)

    def _get_destination(self):
        return self.id, self.server.id

    @asyncio.coroutine
    def edit(self, **options):
        """|coro|

        Edits the channel.

        You must have the Manage Channel permission to use this.

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
            self._update(self.server, data)

class VoiceChannel(CommonGuildChannel):
    """Represents a Discord server voice channel.

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
    server: :class:`Server`
        The server the channel belongs to.
    id: int
        The channel ID.
    position: int
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: int
        The channel's preferred audio bitrate in bits per second.
    voice_members
        A list of :class:`Members` that are currently inside this voice channel.
    user_limit: int
        The channel's limit for number of members that can be in a voice channel.
    """

    __slots__ = ( 'voice_members', 'name', 'id', 'server', 'bitrate',
                  'user_limit', '_state', 'position', '_overwrites' )

    def __init__(self, *, state, server, data):
        self._state = state
        self.id = int(data['id'])
        self._update(server, data)
        self.voice_members = []

    def _update(self, server, data):
        self.server = server
        self.name = data['name']
        self.position = data['position']
        self.bitrate = data.get('bitrate')
        self.user_limit = data.get('user_limit')
        self._fill_overwrites(data)

    @asyncio.coroutine
    def edit(self, **options):
        """|coro|

        Edits the channel.

        You must have the Manage Channel permission to use this.

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
            self._update(self.server, data)

class DMChannel(abc.MessageChannel, Hashable):
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
        self.recipient = state.try_insert_user(data['recipients'][0])
        self.me = me
        self.id = int(data['id'])

    def _get_destination(self):
        return self.id, None

    def __str__(self):
        return 'Direct Message with %s' % self.recipient

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

class GroupChannel(abc.MessageChannel, Hashable):
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
        self.recipients = [state.try_insert_user(u) for u in data['recipients']]
        self.id = int(data['id'])
        self.me = me
        self._update_group(data)

    def _update_group(self, data):
        owner_id = utils._get_as_snowflake(data, 'owner_id')
        self.icon = data.get('icon')
        self.name = data.get('name')

        if owner_id == self.me.id:
            self.owner = self.me
        else:
            self.owner = utils.find(lambda u: u.id == owner_id, self.recipients)

    def _get_destination(self):
        return self.id, None

    def __str__(self):
        if self.name:
            return self.name

        if len(self.recipients) == 0:
            return 'Unnamed'

        return ', '.join(map(lambda x: x.name, self.recipients))

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
