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

from typing import TYPE_CHECKING, List, Literal, Optional, TypedDict, Union

from .snowflake import Snowflake
from .user import PartialUser

if TYPE_CHECKING:
    from typing_extensions import NotRequired

FormFieldType = Literal['TERMS', 'TEXT_INPUT', 'PARAGRAPH', 'MULTIPLE_CHOICE', 'VERIFICATION']
JoinRequestStatus = Literal['STARTED', 'SUBMITTED', 'REJECTED', 'APPROVED']
JoinRequestAction = Literal['APPROVED', 'REJECTED']


class MemberVerificationFormField(TypedDict):
    field_type: FormFieldType
    label: str
    choices: NotRequired[List[str]]
    values: NotRequired[Optional[List[str]]]
    response: NotRequired[Optional[Union[str, int, bool]]]
    required: bool
    description: Optional[str]
    placeholder: NotRequired[Optional[str]]


class MemberVerification(TypedDict):
    version: str
    form_fields: List[MemberVerificationFormField]
    description: Optional[str]


class JoinRequest(TypedDict):
    id: Snowflake
    join_request_id: Snowflake
    created_at: str
    application_status: JoinRequestStatus
    guild_id: Snowflake
    form_responses: NotRequired[Optional[List[MemberVerificationFormField]]]
    last_seen: Optional[str]
    reviewed_at: NotRequired[str]
    actioned_by_user: NotRequired[PartialUser]
    rejection_reason: Optional[str]
    user_id: Snowflake
    user: NotRequired[PartialUser]
    interview_channel_id: Optional[Snowflake]


class JoinRequestList(TypedDict):
    guild_join_requests: List[JoinRequest]
    total: NotRequired[int]
