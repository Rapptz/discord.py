"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import Dict, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired

from .guild import PartialGuild, _GuildCounts
from .scheduled_event import ExternalScheduledEvent, StageInstanceScheduledEvent, VoiceScheduledEvent
from .snowflake import Snowflake


class _DirectoryScheduledEvent(TypedDict):
    guild: PartialGuild
    user_rsvp: bool
    user_count: int


class _DirectoryStageInstanceScheduledEvent(_DirectoryScheduledEvent, StageInstanceScheduledEvent):
    ...


class _DirectoryVoiceScheduledEvent(_DirectoryScheduledEvent, VoiceScheduledEvent):
    ...


class _DirectoryExternalScheduledEvent(_DirectoryScheduledEvent, ExternalScheduledEvent):
    ...


DirectoryScheduledEvent = Union[
    _DirectoryStageInstanceScheduledEvent, _DirectoryVoiceScheduledEvent, _DirectoryExternalScheduledEvent
]


class DirectoryGuild(PartialGuild, _GuildCounts):
    featurable_in_directory: bool


DirectoryEntryType = Literal[0, 1]
DirectoryCategory = Literal[0, 1, 2, 3, 5]
DirectoryCounts = Dict[DirectoryCategory, int]


class PartialDirectoryEntry(TypedDict):
    type: DirectoryEntryType
    primary_category_id: NotRequired[DirectoryCategory]
    directory_channel_id: Snowflake
    author_id: Snowflake
    entity_id: Snowflake
    created_at: str
    description: Optional[str]


class DirectoryEntry(PartialDirectoryEntry):
    guild: NotRequired[DirectoryGuild]
    guild_scheduled_event: NotRequired[DirectoryScheduledEvent]


class DirectoryBroadcast(TypedDict):
    can_broadcast: bool
