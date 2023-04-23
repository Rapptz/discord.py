"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

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

from typing import Literal, Optional, TypedDict

from .member import Member
from .snowflake import Snowflake
from .user import User

ScheduledEventStatus = Literal[1, 2, 3, 4]
ScheduledEventLocationType = Literal[1, 2, 3]
ScheduledEventPrivacyLevel = Literal[2]


class ScheduledEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    channel_id: Snowflake
    creator_id: Snowflake
    name: str
    description: str
    image: Optional[str]
    scheduled_start_time: str
    scheduled_end_time: Optional[str]
    privacy_level: ScheduledEventPrivacyLevel
    status: ScheduledEventStatus
    entity_type: ScheduledEventLocationType
    entity_id: Snowflake
    entity_metadata: ScheduledEventEntityMetadata
    creator: User
    user_count: Optional[int]


class ScheduledEventEntityMetadata(TypedDict):
    location: str


class ScheduledEventSubscriber(TypedDict):
    guild_scheduled_event_id: Snowflake
    user: User
    member: Optional[Member]
