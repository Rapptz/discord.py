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
    from .types.primary_guild import PrimaryGuild as PrimaryGuildPayload


class PrimaryGuild:
    """Represents the primary guild (formally known as a clan) of a :class:`User`"""

    __slots__ = ('id', 'identity_enabled', 'tag', '_badge', '_state')

    if TYPE_CHECKING:
        id: Optional[int]
        identity_enabled: bool
        tag: Optional[str]
        _badge: str
        _state: ConnectionState

    def __init__(self, *, state, data: PrimaryGuildPayload) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: PrimaryGuildPayload):
        self.id = _get_as_snowflake(data, 'identity_guild_id')
        self.identity_enabled = data['identity_enabled']
        self.tag = data.get('tag', None)
        self._badge = data.get('badge')

    @property
    def badge(self) -> Optional[Asset]:
        """:class:`Asset`: Returns the primary guild's asset"""
        if self._badge and self.id:
            return Asset._from_primary_guild(self._state, self.id, self._badge)
        return None

    @property
    def created_at(self) -> Optional[datetime]:
        """:class:`datetime.datetime`: Returns the primary guild's creation time in UTC."""
        if self.id:
            return snowflake_time(self.id)
        return None

    def __repr__(self) -> str:
        return f'<PrimaryGuild id={self.id} identity_enabled={self.identity_enabled} tag={self.tag}' f' badge={self.badge}>'
