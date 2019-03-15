# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from .utils import valid_icon_size, snowflake_time, get
from .errors import InvalidArgument
from .activity import Game
from .enums import Status, DefaultAvatar, try_enum
from collections import namedtuple

VALID_ICON_FORMATS = {"jpeg", "jpg", "webp", "png"}

class WidgetChannel(namedtuple('WidgetChannel', 'id name position')):
    """Represents a "partial" widget channel.

    Attributes
    -----------
    id: :class:`id`
        The channel's ID.
    name: :class:`str`
        The channel's name.
    position: :class:`int`
        The channel's position
    """
    __slots__ = ()

    def __str__(self):
        return self.name

    @property
    def mention(self):
        """:class:`str` : The string that allows you to mention the channel."""
        return '<#%s>' % self.id

    @property
    def created_at(self):
        """Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

class WidgetMember(namedtuple('WidgetMember', 'username status nick avatar discriminator id bot game deafened suppress '
                                              'muted connected_channel')):
    """Represents a "partial" member of the widget's guild.

    This model will always be given, as long as it is enabled.

    Attributes
    -----------
    id: :class:`int`
        The member's ID.
    username: :class:`str`
        The member's username.
    discriminator: :class:`str`
        The member's discriminator.
    bot: :class:`bool`
        Whether the member is a bot.
    status: :class:`Status`
        The member's status.
    nick: Optional[:class:`str`]
        The member's nickname.
    avatar: Optional[:class:`str`]
        The member's avatar hash.
    game: Optional[:class:`Game`]
        The member's activity.
    deafened: Optional[:class:`bool`]
        Whether the member is currently deafened.
    muted: Optional[:class:`bool`]
        Whether the member is currently muted.
    suppress: Optional[:class:`bool`]
        Whether the member is currently being suppressed.
    connected_channel: Optional[:class:`VoiceChannel`]
        Which channel the member is connected to.
    """
    __slots__ = ()

    def __str__(self):
        return '{}#{}'.format(self.username, self.discriminator)

    @property
    def mention(self):
        """:class:`str` : The string that allows you to mention the member."""
        return '<@%s>' % self.id

    @property
    def created_at(self):
        """Returns the member's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def display_name(self):
        """Returns the member's display name."""
        return self.nick if self.nick else self.username

    @property
    def avatar_url(self):
        """Returns the URL version of the member's avatar. Returns an empty string if it has no avatar."""
        return self.avatar_url_as()

    def avatar_url_as(self, *, format='webp', size=1024):
        """:class:`str`: The same operation as :meth:`User.avatar_url_as`."""
        if not valid_icon_size(size):
            raise InvalidArgument("size must be a power of 2 between 16 and 4096")
        if format not in VALID_ICON_FORMATS:
            raise InvalidArgument("format must be one of {}".format(VALID_ICON_FORMATS))

        if self.avatar is None:
            return self.default_avatar_url

        return 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.{1}?size={2}'.format(self, format, size)

    @property
    def default_avatar(self):
        """:class:`DefaultAvatar`: The same operation as :meth:`User.default_avatar`."""
        return DefaultAvatar(int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """Returns a URL for a user's default avatar."""
        return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(self.default_avatar.value)

class Widget:
    """Represents a :class:`Guild` widget.

    This model is always given, as long as it is enabled.

    Attributes
    -----------
    id: :class:`int`
        The guild's ID.
    name: :class:`str`
        The guild's name.
    channels: List[:class:`VoiceChannel`]
        The accessible voice channels in the guild.
    members: List[:class:`Member`]
        The online members in the server. Note: offline
        members do not appear in the widget.
    invite: Optional[:class:`Invite`]
        The invite set for the widget.
    """
    __slots__ = ('_state', 'channels', 'invite', 'id', 'members', 'name')

    def __init__(self, *, state, data, invite):
        self._state = state
        self.invite = invite
        self.name = data.get('name')
        self.id = int(data.get('id'))

        self.channels = []
        for channel in data.get('channels'):
            _id = int(channel['id'])
            self.channels.append(WidgetChannel(id=_id, name=channel['name'], position=channel['position']))

        self.members = []
        for member in data.get('members'):
            _id = int(member.get('id'))
            bot = bool(member.get('bot'))
            status = try_enum(Status, member.get('status'))
            deafened = bool(member.get('deaf')) or bool(member.get('self_deaf'))
            muted = bool(member.get('mute')) or bool(member.get('self_mute'))
            suppress = bool(member.get('mute'))

            game = None
            if member.get('game'):
                game = Game(**member.get('game'))

            connected_channel = None
            if member.get('channel_id'):
                connected_channel = get(self.channels, id=int(member.get('channel_id')))

            self.members.append(WidgetMember(id=_id,
                                             bot=bot,
                                             username=member.get('username'),
                                             discriminator=member.get('discriminator'),
                                             status=status,
                                             avatar=member.get('avatar'),
                                             nick=member.get('nick'),
                                             game=game,
                                             deafened=deafened,
                                             muted=muted,
                                             suppress=suppress,
                                             connected_channel=connected_channel))

    def __str__(self):
        return self.json_url

    def __repr__(self):
        return '<Widget id={0.id} name={0.name!r} invite={0.invite!r}>'.format(self)

    @property
    def created_at(self):
        """Returns the member's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def json_url(self):
        """The JSON URL of the widget."""
        return "https://discordapp.com/api/guilds/{0.id}/widget.json".format(self)
