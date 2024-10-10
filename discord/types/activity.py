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

from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired
from .user import User
from .snowflake import Snowflake


StatusType = Literal['idle', 'dnd', 'online', 'offline']


class PartialPresenceUpdate(TypedDict):
    user: User
    guild_id: Snowflake
    status: StatusType
    activities: List[Activity]
    client_status: ClientStatus


class ClientStatus(TypedDict, total=False):
    desktop: StatusType
    mobile: StatusType
    web: StatusType


class ActivityTimestamps(TypedDict, total=False):
    start: int
    end: int


class ActivityParty(TypedDict, total=False):
    id: str
    size: List[int]


class ActivityAssets(TypedDict, total=False):
    large_image: str
    large_text: str
    small_image: str
    small_text: str


class ActivitySecrets(TypedDict, total=False):
    join: str
    spectate: str
    match: str


class ActivityEmoji(TypedDict):
    name: str
    id: NotRequired[Snowflake]
    animated: NotRequired[bool]


ActivityType = Literal[0, 1, 2, 4, 5]


class SendableActivity(TypedDict):
    name: str
    type: ActivityType
    url: NotRequired[Optional[str]]


class _BaseActivity(SendableActivity):
    created_at: int


class Activity(_BaseActivity, total=False):
    state: Optional[str]
    details: Optional[str]
    timestamps: ActivityTimestamps
    platform: Optional[str]
    assets: ActivityAssets
    party: ActivityParty
    application_id: Snowflake
    flags: int
    emoji: Optional[ActivityEmoji]
    secrets: ActivitySecrets
    session_id: Optional[str]
    instance: bool
    buttons: List[str]
    sync_id: str
