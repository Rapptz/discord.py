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

from .user import User
from .game import Game
from .permissions import Permissions
from . import utils
from .enums import Status, ChannelType, try_enum
from .colour import Colour

import copy
import inspect

class VoiceState:
    """Represents a Discord user's voice state.

    Attributes
    ------------
    deaf: bool
        Indicates if the user is currently deafened by the server.
    mute: bool
        Indicates if the user is currently muted by the server.
    self_mute: bool
        Indicates if the user is currently muted by their own accord.
    self_deaf: bool
        Indicates if the user is currently deafened by their own accord.
    is_afk: bool
        Indicates if the user is currently in the AFK channel in the server.
    voice_channel: Optional[Union[:class:`Channel`, :class:`PrivateChannel`]]
        The voice channel that the user is currently connected to. None if the user
        is not currently in a voice channel.
    """

    __slots__ = ( 'session_id', 'deaf', 'mute', 'self_mute',
                  'self_deaf', 'is_afk', 'voice_channel' )

    def __init__(self, **kwargs):
        self.session_id = kwargs.get('session_id')
        self._update_voice_state(**kwargs)

    def _update_voice_state(self, **kwargs):
        self.self_mute = kwargs.get('self_mute', False)
        self.self_deaf = kwargs.get('self_deaf', False)
        self.is_afk = kwargs.get('suppress', False)
        self.mute = kwargs.get('mute', False)
        self.deaf = kwargs.get('deaf', False)
        self.voice_channel = kwargs.get('voice_channel')

def flatten_voice_states(cls):
    for attr in VoiceState.__slots__:
        def getter(self, x=attr):
            return getattr(self.voice, x)
        setattr(cls, attr, property(getter))
    return cls

def flatten_user(cls):
    for attr, value in User.__dict__.items():
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

@flatten_voice_states
@flatten_user
class Member:
    """Represents a Discord member to a :class:`Server`.

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
    voice: :class:`VoiceState`
        The member's voice state. Properties are defined to mirror access of the attributes.
        e.g. ``Member.is_afk`` is equivalent to `Member.voice.is_afk``.
    roles
        A list of :class:`Role` that the member belongs to. Note that the first element of this
        list is always the default '@everyone' role.
    joined_at : `datetime.datetime`
        A datetime object that specifies the date and time in UTC that the member joined the server for
        the first time.
    status : :class:`Status`
        The member's status. There is a chance that the status will be a ``str``
        if it is a value that is not recognised by the enumerator.
    game : :class:`Game`
        The game that the user is currently playing. Could be None if no game is being played.
    server : :class:`Server`
        The server that the member belongs to.
    nick : Optional[str]
        The server specific nickname of the user.
    """

    __slots__ = ('roles', 'joined_at', 'status', 'game', 'server', 'nick', 'voice', '_user', '_state')

    def __init__(self, *, data, server, state):
        self._state = state
        self._user = state.try_insert_user(data['user'])
        self.voice = VoiceState(**data)
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.roles = data.get('roles', [])
        self.status = Status.offline
        game = data.get('game', {})
        self.game = Game(**game) if game else None
        self.server = server
        self.nick = data.get('nick', None)

    def __str__(self):
        return self._user.__str__()

    def __eq__(self, other):
        return isinstance(other, Member) and other._user.id == self._user.id and self.server.id == other.server.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._user.id)

    def _update_voice_state(self, **kwargs):
        self.voice.self_mute = kwargs.get('self_mute', False)
        self.voice.self_deaf = kwargs.get('self_deaf', False)
        self.voice.is_afk = kwargs.get('suppress', False)
        self.voice.mute = kwargs.get('mute', False)
        self.voice.deaf = kwargs.get('deaf', False)
        old_channel = getattr(self, 'voice_channel', None)
        vc = kwargs.get('voice_channel')

        if old_channel is None and vc is not None:
            # we joined a channel
            vc.voice_members.append(self)
        elif old_channel is not None:
            try:
                # we either left a channel or we switched channels
                old_channel.voice_members.remove(self)
            except ValueError:
                pass
            finally:
                # we switched channels
                if vc is not None:
                    vc.voice_members.append(self)

        self.voice.voice_channel = vc

    def _copy(self):
        ret = copy.copy(self)
        ret.voice = copy.copy(self.voice)
        return ret

    def _update(self, data, user):
        self._user.name = user['username']
        self._user.discriminator = user['discriminator']
        self._user.avatar = user['avatar']
        self._user.bot = user.get('bot', False)

        # the nickname change is optional,
        # if it isn't in the payload then it didn't change
        if 'nick' in data:
            self.nick = data['nick']

        # update the roles
        self.roles = [self.server.default_role]
        for role in self.server.roles:
            if role.id in data['roles']:
                self.roles.append(role)

        # sort the roles by ID since they can be "randomised"
        self.roles.sort(key=lambda r: int(r.id))

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
    def server_permissions(self):
        """Returns the member's server permissions.

        This only takes into consideration the server permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use either :meth:`permissions_in` or
        :meth:`Channel.permissions_for`.

        This does take into consideration server ownership and the
        administrator implication.
        """

        if self.server.owner == self:
            return Permissions.all()

        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value

        if base.administrator:
            return Permissions.all()

        return base
