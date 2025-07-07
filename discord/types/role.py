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

from typing import TypedDict, Optional
from typing_extensions import NotRequired

from .snowflake import Snowflake


class Role(TypedDict):
    id: Snowflake
    name: str
    color: int
    hoist: bool
    position: int
    permissions: str
    managed: bool
    mentionable: bool
    flags: int
    icon: NotRequired[Optional[str]]
    unicode_emoji: NotRequired[Optional[str]]
    tags: NotRequired[RoleTags]


class RoleTags(TypedDict, total=False):
    bot_id: Snowflake
    integration_id: Snowflake
    subscription_listing_id: Snowflake
    premium_subscriber: None
    available_for_purchase: None
    guild_connections: None
