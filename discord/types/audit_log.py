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

from typing import Any, List, Literal, Optional, TypedDict
from .webhook import Webhook
from .integration import PartialIntegration
from .user import User
from .snowflake import Snowflake

AuditLogEvent = Literal[
    1,
    10,
    11,
    12,
    13,
    14,
    15,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    30,
    31,
    32,
    40,
    41,
    42,
    50,
    51,
    52,
    60,
    61,
    62,
    72,
    73,
    74,
    75,
    80,
    81,
    82,
]


class AuditLogChange(TypedDict):
    key: str
    new_value: Any
    old_value: Any


class AuditEntryInfo(TypedDict):
    delete_member_days: str
    members_removed: str
    channel_id: Snowflake
    message_id: Snowflake
    count: str
    id: Snowflake
    type: Literal['0', '1']
    role_name: str


class _AuditLogEntryOptional(TypedDict, total=False):
    changes: List[AuditLogChange]
    options: AuditEntryInfo
    reason: str


class AuditLogEntry(_AuditLogEntryOptional):
    target_id: Optional[str]
    user_id: Snowflake
    id: Snowflake
    action_type: AuditLogEvent


class AuditLog(TypedDict):
    webhooks: List[Webhook]
    users: List[User]
    audit_log_entries: List[AuditLogEntry]
    integrations: List[PartialIntegration]
