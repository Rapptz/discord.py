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

from typing import TYPE_CHECKING, Optional, Tuple

from .activity import create_activity
from .enums import Status, try_enum
from .utils import MISSING, _get_as_snowflake, _RawReprMixin

if TYPE_CHECKING:
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .guild import Guild
    from .state import ConnectionState
    from .types.activity import ClientStatus as ClientStatusPayload, PartialPresenceUpdate


__all__ = (
    'RawPresenceUpdateEvent',
    'ClientStatus',
)


class ClientStatus:
    """Represents the :ddocs:`Client Status Object <events/gateway-events#client-status-object>` from Discord,
    which holds information about the status of the user on various clients/platforms, with additional helpers.

    .. versionadded:: 2.5
    """

    __slots__ = ('_status', 'desktop', 'mobile', 'web')

    def __init__(self, *, status: str = MISSING, data: ClientStatusPayload = MISSING) -> None:
        self._status: str = status or 'offline'

        data = data or {}
        self.desktop: Optional[str] = data.get('desktop')
        self.mobile: Optional[str] = data.get('mobile')
        self.web: Optional[str] = data.get('web')

    def __repr__(self) -> str:
        attrs = [
            ('_status', self._status),
            ('desktop', self.desktop),
            ('mobile', self.mobile),
            ('web', self.web),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'

    def _update(self, status: str, data: ClientStatusPayload, /) -> None:
        self._status = status

        self.desktop = data.get('desktop')
        self.mobile = data.get('mobile')
        self.web = data.get('web')

    @classmethod
    def _copy(cls, client_status: Self, /) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self._status = client_status._status

        self.desktop = client_status.desktop
        self.mobile = client_status.mobile
        self.web = client_status.web

        return self

    @property
    def status(self) -> Status:
        """:class:`Status`: The user's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return try_enum(Status, self._status)

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value."""
        return self._status

    @property
    def mobile_status(self) -> Status:
        """:class:`Status`: The user's status on a mobile device, if applicable."""
        return try_enum(Status, self.mobile or 'offline')

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The user's status on the desktop client, if applicable."""
        return try_enum(Status, self.desktop or 'offline')

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The user's status on the web client, if applicable."""
        return try_enum(Status, self.web or 'offline')

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if a user is active on a mobile device."""
        return self.mobile is not None


class RawPresenceUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_presence_update` event.

    .. versionadded:: 2.5

    Attributes
    ----------
    user_id: :class:`int`
        The ID of the user that triggered the presence update.
    guild_id: Optional[:class:`int`]
        The guild ID for the users presence update. Could be ``None``.
    guild: Optional[:class:`Guild`]
        The guild associated with the presence update and user. Could be ``None``.
    client_status: :class:`ClientStatus`
        The :class:`~.ClientStatus` model which holds information about the status of the user on various clients.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities the user is currently doing. Due to a Discord API limitation, a user's Spotify activity may not appear
        if they are listening to a song with a title longer than ``128`` characters. See :issue:`1738` for more information.
    """

    __slots__ = ('user_id', 'guild_id', 'guild', 'client_status', 'activities')

    def __init__(self, *, data: PartialPresenceUpdate, state: ConnectionState) -> None:
        self.user_id: int = int(data['user']['id'])
        self.client_status: ClientStatus = ClientStatus(status=data['status'], data=data['client_status'])
        self.activities: Tuple[ActivityTypes, ...] = tuple(create_activity(d, state) for d in data['activities'])
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.guild: Optional[Guild] = state._get_guild(self.guild_id)
