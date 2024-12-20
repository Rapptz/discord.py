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
from .utils import _get_as_snowflake, _RawReprMixin

if TYPE_CHECKING:
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .guild import Guild
    from .state import ConnectionState
    from .types.activity import ClientStatus as ClientStatusPayload, PartialPresenceUpdate


__all__ = ('RawPresenceUpdateEvent',)


class _ClientStatus:
    __slots__ = ('_status', 'desktop', 'mobile', 'web')

    def __init__(self):
        self._status: str = 'offline'

        self.desktop: Optional[str] = None
        self.mobile: Optional[str] = None
        self.web: Optional[str] = None

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
        return try_enum(Status, self._status)

    @property
    def raw_status(self) -> str:
        return self._status

    @property
    def mobile_status(self) -> Status:
        return try_enum(Status, self.mobile or 'offline')

    @property
    def desktop_status(self) -> Status:
        return try_enum(Status, self.desktop or 'offline')

    @property
    def web_status(self) -> Status:
        return try_enum(Status, self.web or 'offline')


class RawPresenceUpdateEvent(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_presence_update` event.

    .. versionadded:: 2.5

    Attributes
    ----------
    user_id: :class:`int`
        The ID of the user that triggered the presence update.
    guild_id: Optional[:class:`int`]
        The guild ID for the users presence update. Could be ``None``.
    """

    __slots__ = ('user_id', 'guild_id', 'guild', 'client_status', '_activities')

    def __init__(self, *, data: PartialPresenceUpdate, state: ConnectionState) -> None:
        self.user_id: int = int(data["user"]["id"])

        self.client_status: _ClientStatus = _ClientStatus()
        self.client_status._update(data["status"], data["client_status"])
        self._activities: Tuple[ActivityTypes, ...] | None = None

        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.guild: Guild | None = state._get_guild(self.guild_id)

    def _create_activities(self, data: PartialPresenceUpdate, state: ConnectionState) -> None:
        self._activities = tuple(create_activity(d, state) for d in data['activities'])

    @property
    def activities(self) -> Tuple[ActivityTypes, ...]:
        """Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]: The activities the user is currently doing.

        .. note::

            Due to a Discord API limitation, a user's Spotify activity may not appear
            if they are listening to a song with a title longer
            than ``128`` characters. See :issue:`1738` for more information.
        """
        return self._activities or ()

    @property
    def status(self) -> Status:
        """:class:`Status`: The member's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return self.client_status.status

    @property
    def raw_status(self) -> str:
        """:class:`str`: The member's overall status as a string value.

        .. versionadded:: 1.5
        """
        return self.client_status._status

    @property
    def mobile_status(self) -> Status:
        """:class:`Status`: The member's status on a mobile device, if applicable."""
        return self.client_status.mobile_status

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The member's status on the desktop client, if applicable."""
        return self.client_status.desktop_status

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The member's status on the web client, if applicable."""
        return self.client_status.web_status

    def is_on_mobile(self) -> bool:
        """A helper function that determines if a member is active on a mobile device.

        Returns
        -------
        :class:`bool`
        """
        return self.client_status.mobile is not None
