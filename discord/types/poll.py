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


from typing import List, TypedDict, Optional, Literal, TYPE_CHECKING
from typing_extensions import NotRequired

from .snowflake import Snowflake

if TYPE_CHECKING:
    from .user import User
    from .emoji import PartialEmoji


LayoutType = Literal[1]  # 1 = Default


class PollMedia(TypedDict):
    text: str
    emoji: NotRequired[Optional[PartialEmoji]]


class PollAnswer(TypedDict):
    poll_media: PollMedia


class PollAnswerWithID(PollAnswer):
    answer_id: int


class PollAnswerCount(TypedDict):
    id: Snowflake
    count: int
    me_voted: bool


class PollAnswerVoters(TypedDict):
    users: List[User]


class PollResult(TypedDict):
    is_finalized: bool
    answer_counts: List[PollAnswerCount]


class PollCreate(TypedDict):
    allow_multiselect: bool
    answers: List[PollAnswer]
    duration: float
    layout_type: LayoutType
    question: PollMedia


# We don't subclass Poll as it will
# still have the duration field, which
# is converted into expiry when poll is
# fetched from a message or returned
# by a `send` method in a Messageable
class Poll(TypedDict):
    allow_multiselect: bool
    answers: List[PollAnswerWithID]
    expiry: str
    layout_type: LayoutType
    question: PollMedia
    results: PollResult
