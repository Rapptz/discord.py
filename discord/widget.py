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

from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING, Union

from .utils import snowflake_time, _get_as_snowflake, resolve_invite
from .user import BaseUser
from .activity import BaseActivity, Spotify, create_activity
from .invite import Invite
from .enums import Status, try_enum
from .errors import HTTPException, NotFound

if TYPE_CHECKING:
    import datetime
    from .state import ConnectionState
    from .types.widget import (
        WidgetMember as WidgetMemberPayload,
        Widget as WidgetPayload,
        WidgetChannel as WidgetChannelPayload,
    )

__all__ = (
    'WidgetChannel',
    'WidgetMember',
    'Widget',
)

_log = logging.getLogger(__name__)


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

    def __init__(self, *, id: int, name: str, position: int) -> None:
        self.id: int = id
        self.name: str = name
        self.position: int = position

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<WidgetChannel id={self.id} name={self.name!r} position={self.position}>'

    def __eq__(self, other: object) -> bool:
        """Check if two WidgetChannel objects are equal."""
        if not isinstance(other, WidgetChannel):
            return NotImplemented
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        """Check if two WidgetChannel objects are not equal."""
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        """Return the hash of the channel."""
        return hash(self.id)

    @classmethod
    def from_data(cls, data: WidgetChannelPayload) -> WidgetChannel:
        """Create a WidgetChannel from raw data."""
        return cls(
            id=int(data['id']),
            name=data['name'],
            position=data['position']
        )

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

    def is_voice_channel(self) -> bool:
        """:class:`bool`: Whether this is a voice channel (always True for widget channels)."""
        return True


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

            Returns the widget member's handle (e.g. ``name`` or ``name#discriminator``).

    Attributes
    -----------
    id: :class:`int`
        The member's ID.
    name: :class:`str`
        The member's username.
    discriminator: :class:`str`
        The member's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The member's global nickname, taking precedence over the username in display.

        .. versionadded:: 2.3
    bot: :class:`bool`
        Whether the member is a bot.
    status: :class:`Status`
        The member's status.
    nick: Optional[:class:`str`]
        The member's guild-specific nickname. Takes precedence over the global name.
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
    connected_channel: Optional[:class:`WidgetChannel`]
        Which channel the member is connected to.
    """

    __slots__ = (
        'status',
        'nick',
        'avatar',
        'activity',
        'deafened',
        'suppress',
        'muted',
        'connected_channel',
    )

    if TYPE_CHECKING:
        activity: Optional[Union[BaseActivity, Spotify]]

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: WidgetMemberPayload,
        connected_channel: Optional[WidgetChannel] = None,
    ) -> None:
        super().__init__(state=state, data=data)
        self.nick: Optional[str] = data.get('nick')
        self.status: Status = try_enum(Status, data.get('status', 'offline'))
        
        # Improved deafened/muted status calculation
        self.deafened: bool = data.get('deaf', False) or data.get('self_deaf', False)
        self.muted: bool = data.get('mute', False) or data.get('self_mute', False)
        self.suppress: bool = data.get('suppress', False)

        # Better activity handling with error logging
        activity = None
        try:
            game = data.get('game')
            if game is not None:
                activity = create_activity(game, state)
        except Exception as e:
            _log.warning(f"Failed to create activity for member {self.id}: {e}")
            activity = None

        self.activity: Optional[Union[BaseActivity, Spotify]] = activity
        self.connected_channel: Optional[WidgetChannel] = connected_channel

    def __repr__(self) -> str:
        return (
            f"<WidgetMember id={self.id} name={self.name!r} global_name={self.global_name!r} "
            f"bot={self.bot} nick={self.nick!r} status={self.status}>"
        )

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the member's display name."""
        return self.nick or self.global_name or self.name

    @property
    def is_online(self) -> bool:
        """:class:`bool`: Whether the member is online."""
        return self.status != Status.offline

    @property
    def is_in_voice(self) -> bool:
        """:class:`bool`: Whether the member is connected to a voice channel."""
        return self.connected_channel is not None

    def get_voice_state_info(self) -> Dict[str, Union[bool, Optional[str]]]:
        """Get detailed voice state information.
        
        Returns
        -------
        Dict[str, Union[bool, Optional[str]]]
            A dictionary containing voice state information.
        """
        return {
            'connected': self.is_in_voice,
            'channel_name': self.connected_channel.name if self.connected_channel else None,
            'deafened': self.deafened,
            'muted': self.muted,
            'suppressed': self.suppress,
        }


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
    channels: List[:class:`WidgetChannel`]
        The accessible voice channels in the guild.
    members: List[:class:`WidgetMember`]
        The online members in the guild. Offline members
        do not appear in the widget.

        .. note::

            Due to a Discord limitation, if this data is available
            the users will be "anonymized" with linear IDs and discriminator
            information being incorrect. Likewise, the number of members
            retrieved is capped.
    presence_count: :class:`int`
        The approximate number of online members in the guild.
        Offline members are not included in this count.

        .. versionadded:: 2.0
    """

    __slots__ = ('_state', 'channels', '_invite', 'id', 'members', 'name', 'presence_count', '_channels_dict')

    def __init__(self, *, state: ConnectionState, data: WidgetPayload) -> None:
        self._state = state
        self._invite = data.get('instant_invite')
        self.name: str = data['name']
        self.id: int = int(data['id'])
        self.presence_count: int = data.get('presence_count', 0)

        # Build channels list and dictionary for faster lookups
        self.channels: List[WidgetChannel] = []
        self._channels_dict: Dict[int, WidgetChannel] = {}
        
        for channel_data in data.get('channels', []):
            channel = WidgetChannel.from_data(channel_data)
            self.channels.append(channel)
            self._channels_dict[channel.id] = channel

        # Sort channels by position
        self.channels.sort(key=lambda c: c.position)

        # Build members list with better error handling
        self.members: List[WidgetMember] = []
        for member_data in data.get('members', []):
            try:
                connected_channel = None
                channel_id = _get_as_snowflake(member_data, 'channel_id')
                
                if channel_id is not None:
                    connected_channel = self._channels_dict.get(channel_id)
                    if connected_channel is None:
                        # Create a placeholder channel if not found in the widget data
                        connected_channel = WidgetChannel(
                            id=channel_id, 
                            name='Unknown Channel', 
                            position=0
                        )

                member = WidgetMember(
                    state=self._state, 
                    data=member_data, 
                    connected_channel=connected_channel
                )
                self.members.append(member)
                
            except Exception as e:
                _log.warning(f"Failed to create WidgetMember from data: {e}")
                continue

    def __str__(self) -> str:
        return self.json_url

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Widget):
            return NotImplemented
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f'<Widget id={self.id} name={self.name!r} '
            f'channels={len(self.channels)} members={len(self.members)} '
            f'invite_url={self.invite_url!r}>'
        )

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def json_url(self) -> str:
        """:class:`str`: The JSON URL of the widget."""
        return f"https://discord.com/api/guilds/{self.id}/widget.json"

    @property
    def invite_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The invite URL for the guild, if available."""
        return self._invite

    @property
    def member_count(self) -> int:
        """:class:`int`: The number of members currently shown in the widget."""
        return len(self.members)

    @property
    def online_members(self) -> List[WidgetMember]:
        """List[:class:`WidgetMember`]: A list of online members."""
        return [member for member in self.members if member.is_online]

    @property
    def voice_members(self) -> List[WidgetMember]:
        """List[:class:`WidgetMember`]: A list of members connected to voice channels."""
        return [member for member in self.members if member.is_in_voice]

    def get_channel(self, channel_id: int) -> Optional[WidgetChannel]:
        """Get a channel by its ID.
        
        Parameters
        ----------
        channel_id: :class:`int`
            The ID of the channel to get.
            
        Returns
        -------
        Optional[:class:`WidgetChannel`]
            The channel if found, otherwise None.
        """
        return self._channels_dict.get(channel_id)

    def get_member(self, member_id: int) -> Optional[WidgetMember]:
        """Get a member by their ID.
        
        Parameters
        ----------
        member_id: :class:`int`
            The ID of the member to get.
            
        Returns
        -------
        Optional[:class:`WidgetMember`]
            The member if found, otherwise None.
        """
        for member in self.members:
            if member.id == member_id:
                return member
        return None

    def get_members_in_channel(self, channel_id: int) -> List[WidgetMember]:
        """Get all members connected to a specific voice channel.
        
        Parameters
        ----------
        channel_id: :class:`int`
            The ID of the channel.
            
        Returns
        -------
        List[:class:`WidgetMember`]
            A list of members in the specified channel.
        """
        return [
            member for member in self.members 
            if member.connected_channel and member.connected_channel.id == channel_id
        ]

    async def fetch_invite(self, *, with_counts: bool = True, with_expiration: bool = True) -> Optional[Invite]:
        """|coro|

        Retrieves an :class:`Invite` from the widget's invite URL.
        This is the same as :meth:`Client.fetch_invite`; the invite
        code is abstracted away.

        Parameters
        -----------
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`Invite.approximate_member_count` and :attr:`Invite.approximate_presence_count`
            fields.
        with_expiration: :class:`bool`
            Whether to include expiration information in the invite.

        Returns
        --------
        Optional[:class:`Invite`]
            The invite from the widget's invite URL, if available.
            
        Raises
        ------
        HTTPException
            Fetching the invite failed.
        NotFound
            The invite is invalid or expired.
        """
        if not self._invite:
            return None
            
        try:
            resolved = resolve_invite(self._invite)
            data = await self._state.http.get_invite(
                resolved.code, 
                with_counts=with_counts,
                with_expiration=with_expiration
            )
            return Invite.from_incomplete(state=self._state, data=data)
        except (HTTPException, NotFound) as e:
            _log.warning(f"Failed to fetch invite for widget {self.id}: {e}")
            raise

    def to_dict(self) -> Dict[str, Union[int, str, List[Dict], Optional[str]]]:
        """Convert the widget to a dictionary representation.
        
        Returns
        -------
        Dict[str, Union[int, str, List[Dict], Optional[str]]]
            A dictionary representation of the widget.
        """
        return {
            'id': self.id,
            'name': self.name,
            'presence_count': self.presence_count,
            'invite_url': self.invite_url,
            'channels': [
                {
                    'id': channel.id,
                    'name': channel.name,
                    'position': channel.position
                }
                for channel in self.channels
            ],
            'members': [
                {
                    'id': member.id,
                    'name': member.name,
                    'discriminator': member.discriminator,
                    'global_name': member.global_name,
                    'nick': member.nick,
                    'status': member.status.name,
                    'bot': member.bot,
                    'connected_channel_id': member.connected_channel.id if member.connected_channel else None,
                    'deafened': member.deafened,
                    'muted': member.muted,
                    'suppressed': member.suppress,
                }
                for member in self.members
            ]
        }
