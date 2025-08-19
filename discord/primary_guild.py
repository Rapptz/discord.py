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

from typing import Optional, TYPE_CHECKING
from datetime import datetime

from .asset import Asset
from .utils import snowflake_time, _get_as_snowflake

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.user import PrimaryGuild as PrimaryGuildPayload
    from typing_extensions import Self


class PrimaryGuild:
    """Represents the primary guild identity of a :class:`User`

    .. versionadded:: 2.6

    Attributes
    -----------
    id: Optional[:class:`int`]
        The ID of the user's primary guild, if any.
    tag: Optional[:class:`str`]
        The primary guild's tag.
    identity_enabled: Optional[:class:`bool`]
        Whether the user has their primary guild publicly displayed. If ``None``, the user has a public guild but has not reaffirmed the guild identity after a change

        .. warning::

            Users can have their primary guild publicly displayed while still having an :attr:`id` of ``None``. Be careful when checking this attribute!
    """

    __slots__ = ('id', 'identity_enabled', 'tag', '_badge', '_state')

    def __init__(self, *, state: ConnectionState, data: PrimaryGuildPayload) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: PrimaryGuildPayload):
        self.id = _get_as_snowflake(data, 'identity_guild_id')
        self.identity_enabled = data['identity_enabled']
        self.tag = data.get('tag', None)
        self._badge = data.get('badge')

    @property
    def badge(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the primary guild's asset"""
        if self._badge is not None and self.id is not None:
            return Asset._from_primary_guild(self._state, self.id, self._badge)
        return None

    @property
    def created_at(self) -> Optional[datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the primary guild's creation time in UTC."""
        if self.id is not None:
            return snowflake_time(self.id)
        return None

    @classmethod
    def _default(cls, state: ConnectionState) -> Self:
        payload: PrimaryGuildPayload = {'identity_enabled': False}  # type: ignore
        return cls(state=state, data=payload)

    def __repr__(self) -> str:
        return f'<PrimaryGuild id={self.id} identity_enabled={self.identity_enabled} tag={self.tag!r}>'
