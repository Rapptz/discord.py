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

import asyncio
import itertools
import copy

import discord.abc

from . import utils
from .user import BaseUser, User
from .activity import create_activity
from .permissions import Permissions
from .enums import Status, try_enum
from .colour import Colour
from .object import Object

class VoiceState:
    """Represents a Discord user's voice state.

    Attributes
    ------------
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the guild.
    mute: :class:`bool`
        Indicates if the user is currently muted by the guild.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    afk: :class:`bool`
        Indicates if the user is currently in the AFK channel in the guild.
    channel: :class:`VoiceChannel`
        The voice channel that the user is currently connected to. None if the user
        is not currently in a voice channel.
    """

    __slots__ = ( 'session_id', 'deaf', 'mute', 'self_mute',
                  'self_deaf', 'afk', 'channel' )

    def __init__(self, *, data, channel=None):
        self.session_id = data.get('session_id')
        self._update(data, channel)

    def _update(self, data, channel):
        self.self_mute = data.get('self_mute', False)
        self.self_deaf = data.get('self_deaf', False)
        self.afk = data.get('suppress', False)
        self.mute = data.get('mute', False)
        self.deaf = data.get('deaf', False)
        self.channel = channel

    def __repr__(self):
        return '<VoiceState self_mute={0.self_mute} self_deaf={0.self_deaf} channel={0.channel!r}>'.format(self)

def flatten_user(cls):
    for attr, value in itertools.chain(BaseUser.__dict__.items(), User.__dict__.items()):
        # ignore private/special methods
        if attr.startswith('_'):
            continue

        # don't override what we already have
        if attr in cls.__dict__:
            continue

        # if it's a slotted attribute or a property, redirect it
        # slotted members are implemented as member_descriptors in Type.__dict__
        if not hasattr(value, '__annotations__'):
            def getter(self, x=attr):
                return getattr(self._user, x)
            setattr(cls, attr, property(getter, doc='Equivalent to :attr:`User.%s`' % attr))
        else:
            # probably a member function by now
            def generate_function(x):
                def general(self, *args, **kwargs):
                    return getattr(self._user, x)(*args, **kwargs)

                general.__name__ = x
                return general

            func = generate_function(attr)
            func.__doc__ = value.__doc__
            setattr(cls, attr, func)

    return cls

_BaseUser = discord.abc.User

@flatten_user
class Member(discord.abc.Messageable, _BaseUser):
    """Represents a Discord member to a :class:`Guild`.

    This implements a lot of the functionality of :class:`User`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's name with the discriminator.

    Attributes
    ----------
    roles: List[:class:`Role`]
        A :class:`list` of :class:`Role` that the member belongs to. Note that the first element of this
        list is always the default '@everyone' role. These roles are sorted by their position
        in the role hierarchy.
    joined_at: `datetime.datetime`
        A datetime object that specifies the date and time in UTC that the member joined the guild for
        the first time.
    status : :class:`Status`
        The member's status. There is a chance that the status will be a :class:`str`
        if it is a value that is not recognised by the enumerator.
    activity: Union[:class:`Game`, :class:`Streaming`, :class:`Activity`]
        The activity that the user is currently doing. Could be None if no activity is being done.
    guild: :class:`Guild`
        The guild that the member belongs to.
    nick: Optional[:class:`str`]
        The guild specific nickname of the user.
    """

    __slots__ = ('roles', 'joined_at', 'status', 'activity', 'guild', 'nick', '_user', '_state')

    def __init__(self, *, data, guild, state):
        self._state = state
        self._user = state.store_user(data['user'])
        self.guild = guild
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self._update_roles(data)
        self.status = Status.offline
        self.activity = create_activity(data.get('game'))
        self.nick = data.get('nick', None)

    def __str__(self):
        return str(self._user)

    def __repr__(self):
        return '<Member id={1.id} name={1.name!r} discriminator={1.discriminator!r}' \
               ' bot={1.bot} nick={0.nick!r} guild={0.guild!r}>'.format(self, self._user)

    def __eq__(self, other):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._user.id)

    @asyncio.coroutine
    def _get_channel(self):
        ch = yield from self.create_dm()
        return ch

    def _update_roles(self, data):
        # update the roles
        self.roles = [self.guild.default_role]
        for roleid in map(int, data['roles']):
            role = utils.find(lambda r: r.id == roleid, self.guild.roles)
            if role is not None:
                self.roles.append(role)

        # sort the roles by hierarchy since they can be "randomised"
        self.roles.sort()

    def _update(self, data, user=None):
        if user:
            self._user.name = user['username']
            self._user.discriminator = user['discriminator']
            self._user.avatar = user['avatar']
            self._user.bot = user.get('bot', False)

        # the nickname change is optional,
        # if it isn't in the payload then it didn't change
        try:
            self.nick = data['nick']
        except KeyError:
            pass

        self._update_roles(data)

    def _presence_update(self, data, user):
        self.status = try_enum(Status, data['status'])
        self.activity = create_activity(data.get('game'))

        u = self._user
        u.name = user.get('username', u.name)
        u.avatar = user.get('avatar', u.avatar)
        u.discriminator = user.get('discriminator', u.discriminator)

    def _copy(self):
        c = copy.copy(self)
        c._user = copy.copy(self._user)
        return c

    @property
    def colour(self):
        """A property that returns a :class:`Colour` denoting the rendered colour
        for the member. If the default colour is the one rendered then an instance
        of :meth:`Colour.default` is returned.

        There is an alias for this under ``color``.
        """

        roles = self.roles[1:] # remove @everyone

        # highest order of the colour is the one that gets rendered.
        # if the highest is the default colour then the next one with a colour
        # is chosen instead
        for role in reversed(roles):
            if role.colour.value:
                return role.colour
        return Colour.default()

    color = colour

    @property
    def mention(self):
        """Returns a string that mentions the member."""
        if self.nick:
            return '<@!%s>' % self.id
        return '<@%s>' % self.id

    @property
    def display_name(self):
        """Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.nick if self.nick is not None else self.name

    def mentioned_in(self, message):
        """Checks if the member is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`Message`
            The message to check if you're mentioned in.
        """
        if self._user.mentioned_in(message):
            return True

        for role in message.role_mentions:
            has_role = utils.get(self.roles, id=role.id) is not None
            if has_role:
                return True

        return False

    def permissions_in(self, channel):
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel
            The channel to check your permissions for.
        """
        return channel.permissions_for(self)

    @property
    def top_role(self):
        """Returns the member's highest role.

        This is useful for figuring where a member stands in the role
        hierarchy chain.
        """
        return self.roles[-1]

    @property
    def guild_permissions(self):
        """Returns the member's guild permissions.

        This only takes into consideration the guild permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use either :meth:`permissions_in` or
        :meth:`abc.GuildChannel.permissions_for`.

        This does take into consideration guild ownership and the
        administrator implication.
        """

        if self.guild.owner == self:
            return Permissions.all()

        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value

        if base.administrator:
            return Permissions.all()

        return base

    @property
    def voice(self):
        """Optional[:class:`VoiceState`]: Returns the member's current voice state."""
        return self.guild._voice_state_for(self._user.id)

    @asyncio.coroutine
    def ban(self, **kwargs):
        """|coro|

        Bans this member. Equivalent to :meth:`Guild.ban`
        """
        yield from self.guild.ban(self, **kwargs)

    @asyncio.coroutine
    def unban(self, *, reason=None):
        """|coro|

        Unbans this member. Equivalent to :meth:`Guild.unban`
        """
        yield from self.guild.unban(self, reason=reason)

    @asyncio.coroutine
    def kick(self, *, reason=None):
        """|coro|

        Kicks this member. Equivalent to :meth:`Guild.kick`
        """
        yield from self.guild.kick(self, reason=reason)

    @asyncio.coroutine
    def edit(self, *, reason=None, **fields):
        """|coro|

        Edits the member's data.

        Depending on the parameter passed, this requires different permissions listed below:

        +---------------+--------------------------------------+
        |   Parameter   |              Permission              |
        +---------------+--------------------------------------+
        | nick          | :attr:`Permissions.manage_nicknames` |
        +---------------+--------------------------------------+
        | mute          | :attr:`Permissions.mute_members`     |
        +---------------+--------------------------------------+
        | deafen        | :attr:`Permissions.deafen_members`   |
        +---------------+--------------------------------------+
        | roles         | :attr:`Permissions.manage_roles`     |
        +---------------+--------------------------------------+
        | voice_channel | :attr:`Permissions.move_members`     |
        +---------------+--------------------------------------+

        All parameters are optional.

        Parameters
        -----------
        nick: str
            The member's new nickname. Use ``None`` to remove the nickname.
        mute: bool
            Indicates if the member should be guild muted or un-muted.
        deafen: bool
            Indicates if the member should be guild deafened or un-deafened.
        roles: List[:class:`Roles`]
            The member's new list of roles. This *replaces* the roles.
        voice_channel: :class:`VoiceChannel`
            The voice channel to move the member to.
        reason: Optional[str]
            The reason for editing this member. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to the action requested.
        HTTPException
            The operation failed.
        """
        http = self._state.http
        guild_id = self.guild.id
        payload = {}

        try:
            nick = fields['nick']
        except KeyError:
            # nick not present so...
            pass
        else:
            nick = nick if nick else ''
            if self._state.self_id == self.id:
                yield from http.change_my_nickname(guild_id, nick, reason=reason)
            else:
                payload['nick'] = nick

        deafen = fields.get('deafen')
        if deafen is not None:
            payload['deaf'] = deafen

        mute = fields.get('mute')
        if mute is not None:
            payload['mute'] = mute

        try:
            vc = fields['voice_channel']
        except KeyError:
            pass
        else:
            payload['channel_id'] = vc.id

        try:
            roles = fields['roles']
        except KeyError:
            pass
        else:
            payload['roles'] = tuple(r.id for r in roles)

        yield from http.edit_member(guild_id, self.id, reason=reason, **payload)

        # TODO: wait for WS event for modify-in-place behaviour

    @asyncio.coroutine
    def move_to(self, channel, *, reason=None):
        """|coro|

        Moves a member to a new voice channel (they must be connected first).

        You must have the :attr:`~Permissions.move_members` permission to
        use this.

        This raises the same exceptions as :meth:`edit`.

        Parameters
        -----------
        channel: :class:`VoiceChannel`
            The new voice channel to move the member to.
        reason: Optional[str]
            The reason for doing this action. Shows up on the audit log.
        """
        yield from self.edit(voice_channel=channel, reason=reason)

    @asyncio.coroutine
    def add_roles(self, *roles, reason=None, atomic=True):
        """|coro|

        Gives the member a number of :class:`Role`\s.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this.

        Parameters
        -----------
        \*roles
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to give to the member.
        reason: Optional[str]
            The reason for adding these roles. Shows up on the audit log.
        atomic: bool
            Whether to atomically add roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to add these roles.
        HTTPException
            Adding roles failed.
        """

        if not atomic:
            new_roles = utils._unique(Object(id=r.id) for s in (self.roles[1:], roles) for r in s)
            yield from self.edit(roles=new_roles, reason=reason)
        else:
            req = self._state.http.add_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                yield from req(guild_id, user_id, role.id, reason=reason)

    @asyncio.coroutine
    def remove_roles(self, *roles, reason=None, atomic=True):
        """|coro|

        Removes :class:`Role`\s from this member.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this.

        Parameters
        -----------
        \*roles
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to remove from the member.
        reason: Optional[str]
            The reason for removing these roles. Shows up on the audit log.
        atomic: bool
            Whether to atomically remove roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these roles.
        HTTPException
            Removing the roles failed.
        """

        if not atomic:
            new_roles = [Object(id=r.id) for r in self.roles[1:]] # remove @everyone
            for role in roles:
                try:
                    new_roles.remove(Object(id=role.id))
                except ValueError:
                    pass

            yield from self.edit(roles=new_roles, reason=reason)
        else:
            req = self._state.http.remove_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                yield from req(guild_id, user_id, role.id, reason=reason)
