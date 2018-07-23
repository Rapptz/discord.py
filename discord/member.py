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
from .enums import Status, ChannelType
from .colour import Colour
import copy

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

    __slots__ = [ 'session_id', 'deaf', 'mute', 'self_mute',
                  'self_deaf', 'is_afk', 'voice_channel' ]

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

@flatten_voice_states
class Member(User):
    """Represents a Discord member to a :class:`Server`.

    This is a subclass of :class:`User` that extends more functionality
    that server members have such as roles and permissions.

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

    __slots__ = [ 'roles', 'joined_at', 'status', 'game', 'server', 'nick', 'voice' ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs.get('user'))
        self.voice = VoiceState(**kwargs)
        self.joined_at = utils.parse_time(kwargs.get('joined_at'))
        self.roles = kwargs.get('roles', [])
        self.status = Status.offline
        game = kwargs.get('game', {})
        self.game = Game(**game) if game else None
        self.server = kwargs.get('server', None)
        self.nick = kwargs.get('nick', None)

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
        if self.nick:
            return '<@!{}>'.format(self.id)
        return '<@{}>'.format(self.id)

    def mentioned_in(self, message):
        mentioned = super().mentioned_in(message)
        if mentioned:
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

        return self.roles[-1]

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
