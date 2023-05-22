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

from __future__ import annotations

from typing import Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .snowflake import Snowflake

ReadStateType = Literal[0, 1, 2, 3, 4]


class ReadState(TypedDict):
    id: Snowflake
    read_state_type: NotRequired[ReadStateType]
    last_message_id: NotRequired[Snowflake]
    last_acked_id: NotRequired[Snowflake]
    last_pin_timestamp: NotRequired[str]
    mention_count: NotRequired[int]
    badge_count: NotRequired[int]
    flags: NotRequired[int]
    last_viewed: NotRequired[Optional[int]]


class BulkReadState(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    read_state_type: ReadStateType


class AcknowledgementToken(TypedDict):
    token: Optional[str]
