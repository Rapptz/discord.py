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
from typing import TypedDict
from .types.snowflake import Snowflake


class ClanTagPayload(TypedDict):
    identity_guild_id: Snowflake
    identity_enabled: bool
    tag: str
    badge: str


class ClanTag:
    __slots__ = ("identity_guild_id", "identity_enabled", "tag", "badge")

    def __init__(self, data: ClanTagPayload):
        self.identity_guild_id: int = int(data["identity_guild_id"])
        self.identity_enabled: bool = data["identity_enabled"]
        self.tag: str = data["tag"]
        self.badge: str = data["badge"]

    def __repr__(self) -> str:
        return f"<ClanTag tag={self.tag!r} identity_guild_id={self.identity_guild_id}>"