"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from .utils import snowflake_time, _get_as_snowflake, resolve_invite
from .user import BaseUser
from .activity import create_activity
from .invite import Invite
from .enums import Status, try_enum

__all__ = (
    'WidgetChannel',
    'WidgetMember',
    'Widget',
)

class WidgetChannel:
    """Represents a "partial" widget channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two partial channels are the same.

        .. describe:: x != y

            Checks if two partial channels are not the same.

        .. describe:: hash(x)

            Return the partial channel's hash.

        .. describe:: str(x)

            Returns the partial channel's name.

    Attributes
    -----------
    id: :class:`int`
        The channel's ID.
    name: :class:`str`
        The channel's name.
    position: :class:`int`
        The channel's position
    """
    __slots__ = ('id', 'name', 'position')


    def __init__(self, **kwargs):
        self.id = kwargs.pop('id')
        self.name = kwargs.pop('name')
        self.position = kwargs.pop('position')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'<WidgetChannel id={self.id} name={self.name!r} position={self.position!r}>'

    @property
    def mention(self):
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

class WidgetMember(BaseUser):
    """Represents a "partial" member of the widget's guild.

    .. container:: operations

        .. describe:: x == y

            Checks if two widget members are the same.

        .. describe:: x != y

            Checks if two widget members are not the same.

        .. describe:: hash(x)

            Return the widget member's hash.

        .. describe:: str(x)

            Returns the widget member's `name#discriminator`.

    Attributes
    -----------
    id: :class:`int`
        The member's ID.
    name: :class:`str`
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
    activity: Optional[Union[:class:`BaseActivity`, :class:`Spotify`]]
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
    __slots__ = ('name', 'status', 'nick', 'avatar', 'discriminator',
                 'id', 'bot', 'activity', 'deafened', 'suppress', 'muted',
                 'connected_channel')

    def __init__(self, *, state, data, connected_channel=None):
        super().__init__(state=state, data=data)
        self.nick = data.get('nick')
        self.status = try_enum(Status, data.get('status'))
        self.deafened = data.get('deaf', False) or data.get('self_deaf', False)
        self.muted = data.get('mute', False) or data.get('self_mute', False)
        self.suppress = data.get('suppress', False)

        try:
            game = data['game']
        except KeyError:
            self.activity = None
        else:
            self.activity = create_activity(game)

        self.connected_channel = connected_channel

    def __repr__(self):
        return (
            f"<WidgetMember name={self.name!r} discriminator={self.discriminator!r}"
            f" bot={self.bot} nick={self.nick!r}>"
        )

    @property
    def display_name(self):
        """:class:`str`: Returns the member's display name."""
        return self.nick or self.name

class Widget:
    """Represents a :class:`Guild` widget.

    .. container:: operations

        .. describe:: x == y

            Checks if two widgets are the same.

        .. describe:: x != y

            Checks if two widgets are not the same.

        .. describe:: str(x)

            Returns the widget's JSON URL.

    Attributes
    -----------
    id: :class:`int`
        The guild's ID.
    name: :class:`str`
        The guild's name.
    channels: Optional[List[:class:`WidgetChannel`]]
        The accessible voice channels in the guild.
    members: Optional[List[:class:`Member`]]
        The online members in the server. Offline members
        do not appear in the widget.

        .. note::

            Due to a Discord limitation, if this data is available
            the users will be "anonymized" with linear IDs and discriminator
            information being incorrect. Likewise, the number of members
            retrieved is capped.

    """
    __slots__ = ('_state', 'channels', '_invite', 'id', 'members', 'name')

    def __init__(self, *, state, data):
        self._state = state
        self._invite = data['instant_invite']
        self.name = data['name']
        self.id = int(data['id'])

        self.channels = []
        for channel in data.get('channels', []):
            _id = int(channel['id'])
            self.channels.append(WidgetChannel(id=_id, name=channel['name'], position=channel['position']))

        self.members = []
        channels = {channel.id: channel for channel in self.channels}
        for member in data.get('members', []):
            connected_channel = _get_as_snowflake(member, 'channel_id')
            if connected_channel in channels:
                connected_channel = channels[connected_channel]
            elif connected_channel:
                connected_channel = WidgetChannel(id=connected_channel, name='', position=0)

            self.members.append(WidgetMember(state=self._state, data=member, connected_channel=connected_channel))

    def __str__(self):
        return self.json_url

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return f'<Widget id={self.id} name={self.name!r} invite_url={self.invite_url!r}>'

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the member's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def json_url(self):
        """:class:`str`: The JSON URL of the widget."""
        return f"https://discord.com/api/guilds/{self.id}/widget.json"

    @property
    def invite_url(self):
        """Optional[:class:`str`]: The invite URL for the guild, if available."""
        return self._invite

    async def fetch_invite(self, *, with_counts=True):
        """|coro|

        Retrieves an :class:`Invite` from a invite URL or ID.
        This is the same as :meth:`Client.fetch_invite`; the invite
        code is abstracted away.

        Parameters
        -----------
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`Invite.approximate_member_count` and :attr:`Invite.approximate_presence_count`
            fields.

        Returns
        --------
        :class:`Invite`
            The invite from the URL/ID.
        """
        if self._invite:
            invite_id = resolve_invite(self._invite)
            data = await self._state.http.get_invite(invite_id, with_counts=with_counts)
            return Invite.from_incomplete(state=self._state, data=data)
