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

from typing import TYPE_CHECKING
from datetime import datetime

from .asset import Asset
from .utils import snowflake_time
from .types.clan import Clan as ClanPayload

if TYPE_CHECKING:
    from .state import ConnectionState


class Clan:
    __slots__ = (
        'guild_id',
        'identity_enabled',
        'tag',
        '_badge',
        '_state'
    )

    if TYPE_CHECKING:
        guild_id: int
        identity_enabled: bool
        tag: str
        _badge: str
        _state: ConnectionState
    
    def __init__(self, *, state, data: ClanPayload) -> None:
        self._state = state
        self._update(data)

    def _update(self, data: ClanPayload):
        self.guild_id = data["identity_guild_id"]
        self.identity_enabled = data['identity_enabled']
        self.tag = data['tag']
        self._badge = data['badge']
    
    @property
    def badge(self) -> Asset:
        """:class:`Asset`: Returns the clan's asset"""
        return Asset._from_clan(self._state, self.guild_id, self._badge)
    
    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the clan's guild creation time in UTC.

        This is when the guild, of that clan tag, was created.
        """
        return snowflake_time(self.guild_id)
    
    def __repr__(self) -> str:
        return (
            f"<guild_id={self.guild_id} identity_enabled={self.identity_enabled} tag={self.tag}"
            f" badge={self.badge}>"
        )
