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

import discord.abc

from . import utils
from .user import BaseUser, User
from .game import Game
from .permissions import Permissions
from .enums import Status, ChannelType, try_enum
from .colour import Colour

class VoiceState:
    """Represents a Discord user's voice state.

    Attributes
    ------------
    deaf: bool
        Indicates if the user is currently deafened by the guild.
    mute: bool
        Indicates if the user is currently muted by the guild.
    self_mute: bool
        Indicates if the user is currently muted by their own accord.
    self_deaf: bool
        Indicates if the user is currently deafened by their own accord.
    afk: bool
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
        if hasattr(value, '__get__'):
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

@flatten_user
class Member(discord.abc.Messageable):
    """Represents a Discord member to a :class:`Guild`.

    This implements a lot of the functionality of :class:`User`.

    Supported Operations:

    +-----------+-----------------------------------------------+
    | Operation |                  Description                  |
    +===========+===============================================+
    | x == y    | Checks if two members are equal.              |
    +-----------+-----------------------------------------------+
    | x != y    | Checks if two members are not equal.          |
    +-----------+-----------------------------------------------+
    | hash(x)   | Return the member's hash.                     |
    +-----------+-----------------------------------------------+
    | str(x)    | Returns the member's name with discriminator. |
    +-----------+-----------------------------------------------+

    Attributes
    ----------
    roles
        A list of :class:`Role` that the member belongs to. Note that the first element of this
        list is always the default '@everyone' role.
    joined_at : `datetime.datetime`
        A datetime object that specifies the date and time in UTC that the member joined the guild for
        the first time.
    status : :class:`Status`
        The member's status. There is a chance that the status will be a ``str``
        if it is a value that is not recognised by the enumerator.
    game : :class:`Game`
        The game that the user is currently playing. Could be None if no game is being played.
    guild : :class:`Guild`
        The guild that the member belongs to.
    nick : Optional[str]
        The guild specific nickname of the user.
    """

    __slots__ = ('roles', 'joined_at', 'status', 'game', 'guild', 'nick', '_user', '_state')

    def __init__(self, *, data, guild, state):
        self._state = state
        self._user = state.store_user(data['user'])
        self.guild = guild
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self._update_roles(data)
        self.status = Status.offline
        game = data.get('game', {})
        self.game = Game(**game) if game else None
        self.nick = data.get('nick', None)

    def __str__(self):
        return str(self._user)

    def __repr__(self):
        return '<Member id={1.id} name={1.name!r} discriminator={1.discriminator!r}' \
               ' bot={1.bot} nick={0.nick!r} guild={0.guild!r}>'.format(self, self._user)

    def __eq__(self, other):
        return isinstance(other, Member) and other._user.id == self._user.id and self.guild.id == other.guild.id

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

        # sort the roles by ID since they can be "randomised"
        self.roles.sort(key=lambda r: r.id)

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
        game = data.get('game', {})
        self.game = Game(**game) if game else None
        u = self._user
        u.name = user.get('username', u.name)
        u.avatar = user.get('avatar', u.avatar)
        u.discriminator = user.get('discriminator', u.discriminator)

    @property
    def colour(self):
        """A property that returns a :class:`Colour` denoting the rendered colour
        for the member. If the default colour is the one rendered then an instance
        of :meth:`Colour.default` is returned.

        There is an alias for this under ``color``.
        """

        default_colour = Colour.default()
        # highest order of the colour is the one that gets rendered.
        # if the highest is the default colour then the next one with a colour
        # is chosen instead
        if self.roles:
            roles = sorted(self.roles, key=lambda r: r.position, reverse=True)
            for role in roles:
                if role.colour == default_colour:
                    continue
                else:
                    return role.colour

        return default_colour

    color = colour

    @property
    def mention(self):
        """Returns a string that mentions the member."""
        if self.nick:
            return '<@!{}>'.format(self.id)
        return '<@{}>'.format(self.id)

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

    @property
    def top_role(self):
        """Returns the member's highest role.

        This is useful for figuring where a member stands in the role
        hierarchy chain.
        """

        if self.roles:
            roles = sorted(self.roles, reverse=True)
            return roles[0]
        return None

    @property
    def guild_permissions(self):
        """Returns the member's guild permissions.

        This only takes into consideration the guild permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use either :meth:`permissions_in` or
        :meth:`Channel.permissions_for`.

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
    def ban(self):
        """|coro|

        Bans this member. Equivalent to :meth:`Guild.ban`
        """
        yield from self.guild.ban(self)

    @asyncio.coroutine
    def unban(self):
        """|coro|

        Unbans this member. Equivalent to :meth:`Guild.unban`
        """
        yield from self.guild.unban(self)

    @asyncio.coroutine
    def kick(self):
        """|coro|

        Kicks this member. Equivalent to :meth:`Guild.kick`
        """
        yield from self.guild.kick(self)

    @asyncio.coroutine
    def edit(self, **fields):
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
                yield from http.change_my_nickname(guild_id, nick)
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

        yield from http.edit_member(guild_id, self.id, **payload)

        # TODO: wait for WS event for modify-in-place behaviour

    @asyncio.coroutine
    def move_to(self, channel):
        """|coro|

        Moves a member to a new voice channel (they must be connected first).

        You must have the :attr:`Permissions.move_members` permission to
        use this.

        This raises the same exceptions as :meth:`edit`.

        Parameters
        -----------
        channel: :class:`VoiceChannel`
            The new voice channel to move the member to.
        """
        yield from self.edit(voice_channel=channel)

    @asyncio.coroutine
    def add_roles(self, *roles):
        """|coro|

        Gives the member a number of :class:`Role`\s.

        You must have the :attr:`Permissions.manage_roles` permission to
        use this.

        Parameters
        -----------
        \*roles
            An argument list of :class:`Role`\s to give the member.

        Raises
        -------
        Forbidden
            You do not have permissions to add these roles.
        HTTPException
            Adding roles failed.
        """

        new_roles = utils._unique(r for s in (self.roles[1:], roles) for r in s)
        yield from self.edit(roles=new_roles)

    @asyncio.coroutine
    def remove_roles(self, *roles):
        """|coro|

        Removes :class:`Role`\s from this member.

        You must have the :attr:`Permissions.manage_roles` permission to
        use this.

        Parameters
        -----------
        \*roles
            An argument list of :class:`Role`\s to remove from the member.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these roles.
        HTTPException
            Removing the roles failed.
        """

        new_roles = self.roles[1:] # remove @everyone
        for role in roles:
            try:
                new_roles.remove(role)
            except ValueError:
                pass

        yield from self.edit(roles=new_roles)
