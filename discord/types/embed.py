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

from typing import List, Literal, TypedDict, Union
from typing_extensions import NotRequired, Required

from .components import ContainerComponent


PollResultFieldName = Literal[
    'poll_question_text',
    'victor_answer_votes',
    'total_votes',
    'victor_answer_id',
    'victor_answer_text',
    'victor_answer_emoji_id',
    'victor_answer_emoji_name',
    'victor_answer_emoji_animated',
]


class EmbedFooter(TypedDict):
    text: str
    icon_url: NotRequired[str]
    proxy_icon_url: NotRequired[str]


class EmbedField(TypedDict):
    name: str
    value: str
    inline: NotRequired[bool]


class EmbedMedia(TypedDict, total=False):
    url: Required[str]
    proxy_url: str
    height: int
    width: int
    flags: int


class EmbedProvider(TypedDict, total=False):
    name: str
    url: str


class EmbedAuthor(TypedDict, total=False):
    name: Required[str]
    url: str
    icon_url: str
    proxy_icon_url: str


EmbedType = Literal['rich', 'image', 'video', 'gifv', 'article', 'link', 'poll_result', 'components']


class _Embed(TypedDict, total=False):
    title: str
    type: EmbedType
    description: str
    url: str
    timestamp: str
    color: int
    footer: EmbedFooter
    image: EmbedMedia
    thumbnail: EmbedMedia
    video: EmbedMedia
    provider: EmbedProvider
    author: EmbedAuthor
    fields: List[EmbedField]
    flags: int


class PollResultField(TypedDict):
    name: PollResultFieldName
    value: Union[str, int, bool]


class _PollResultEmbed(_Embed):
    type: Literal['poll_result']
    fields: List[PollResultField]


class _EmbedWithComponents(_Embed):
    type: Literal['components']
    components: List[ContainerComponent]


Embed = Union[_Embed, _PollResultEmbed, _EmbedWithComponents]
