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

from base64 import b64encode
import json
from random import choice

from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING

from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .enums import ChannelType
    from .types.snowflake import Snowflake

# fmt: off
__all__ = (
    'ContextProperties',
)
# fmt: on


class ContextPropertiesMeta(type):
    if TYPE_CHECKING:

        def __getattribute__(self, name: str) -> Callable[[], Self]:
            ...

    def __new__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]):
        cls = super().__new__(cls, name, bases, attrs)
        locations = attrs.get('LOCATIONS', {})
        sources = attrs.get('SOURCES', {})

        def build_location(location: str) -> classmethod:
            def f(cls) -> Self:
                data = {'location': location}
                return cls(data)

            return classmethod(f)

        def build_source(source: str) -> classmethod:
            def f(cls) -> Self:
                data = {'source': source}
                return cls(data)

            return classmethod(f)

        for location in locations:
            if location:
                setattr(cls, f'from_{location.lower().replace(" ", "_").replace("/", "")}', build_location(location))

        for source in sources:
            if source:
                setattr(cls, f'from_{source.lower().replace(" ", "_")}', build_source(source))

        return cls


class ContextProperties(metaclass=ContextPropertiesMeta):
    """Represents the Discord X-Context-Properties header.

    This header is essential for certain actions (e.g. joining guilds, friend requesting).
    """

    __slots__ = ('_data',)

    LOCATIONS = {
        None: 'e30=',
        'Friends': 'eyJsb2NhdGlvbiI6IkZyaWVuZHMifQ==',
        'ContextMenu': 'eyJsb2NhdGlvbiI6IkNvbnRleHRNZW51In0=',
        'Context Menu': 'eyJsb2NhdGlvbiI6IkNvbnRleHQgTWVudSJ9',
        'User Profile': 'eyJsb2NhdGlvbiI6IlVzZXIgUHJvZmlsZSJ9',
        'Add Friend': 'eyJsb2NhdGlvbiI6IkFkZCBGcmllbmQifQ==',
        'Guild Header': 'eyJsb2NhdGlvbiI6Ikd1aWxkIEhlYWRlciJ9',
        'Group DM': 'eyJsb2NhdGlvbiI6Ikdyb3VwIERNIn0=',
        'DM Channel': 'eyJsb2NhdGlvbiI6IkRNIENoYW5uZWwifQ==',
        '/app': 'eyJsb2NhdGlvbiI6ICIvYXBwIn0=',
        'Login': 'eyJsb2NhdGlvbiI6IkxvZ2luIn0=',
        'Register': 'eyJsb2NhdGlvbiI6IlJlZ2lzdGVyIn0=',
        'Verify Email': 'eyJsb2NhdGlvbiI6IlZlcmlmeSBFbWFpbCJ9',
        'New Group DM': 'eyJsb2NhdGlvbiI6Ik5ldyBHcm91cCBETSJ9',
        'Add Friends to DM': 'eyJsb2NhdGlvbiI6IkFkZCBGcmllbmRzIHRvIERNIn0=',
        'Group DM Invite Create': 'eyJsb2NhdGlvbiI6Ikdyb3VwIERNIEludml0ZSBDcmVhdGUifQ==',
        'Stage Channel': 'eyJsb2NhdGlvbiI6IlN0YWdlIENoYW5uZWwifQ==',
    }

    SOURCES = {
        None: 'e30=',
        'Chat Input Blocker - Lurker Mode': 'eyJzb3VyY2UiOiJDaGF0IElucHV0IEJsb2NrZXIgLSBMdXJrZXIgTW9kZSJ9',
        'Notice - Lurker Mode': 'eyJzb3VyY2UiOiJOb3RpY2UgLSBMdXJrZXIgTW9kZSJ9',
    }

    def __init__(self, data: dict) -> None:
        self._data: Dict[str, Snowflake] = data

    def _encode_data(self) -> str:
        try:
            target = self.target
            return self.LOCATIONS.get(target, self.SOURCES[target])
        except KeyError:
            return b64encode(json.dumps(self._data, separators=(',', ':')).encode()).decode('utf-8')

    @classmethod
    def empty(cls) -> Self:
        return cls({})

    @classmethod
    def from_accept_invite_page(
        cls,
        *,
        guild_id: Optional[Snowflake] = None,
        channel_id: Optional[Snowflake] = None,
        channel_type: Optional[ChannelType] = None,
    ) -> Self:
        data: Dict[str, Snowflake] = {
            'location': 'Accept Invite Page',
        }
        if guild_id:
            data['location_guild_id'] = str(guild_id)
        if channel_id:
            data['location_channel_id'] = str(channel_id)
        if channel_type:
            data['location_channel_type'] = int(channel_type)
        return cls(data)

    @classmethod
    def from_join_guild(
        cls,
        *,
        guild_id: Snowflake = MISSING,
        channel_id: Snowflake = MISSING,
        channel_type: ChannelType = MISSING,
    ) -> Self:
        data: Dict[str, Snowflake] = {
            'location': 'Join Guild',
        }
        if guild_id is not MISSING:
            data['location_guild_id'] = str(guild_id)
        if channel_id is not MISSING:
            data['location_channel_id'] = str(channel_id)
        if channel_type is not MISSING:
            data['location_channel_type'] = int(channel_type)
        return cls(data)

    @classmethod
    def from_invite_button_embed(
        cls,
        *,
        guild_id: Optional[Snowflake],
        channel_id: Snowflake,
        message_id: Snowflake,
        channel_type: Optional[ChannelType],
    ) -> Self:
        data = {
            'location': 'Invite Button Embed',
            'location_guild_id': str(guild_id) if guild_id else None,
            'location_channel_id': str(channel_id),
            'location_channel_type': int(channel_type) if channel_type else None,
            'location_message_id': str(message_id),
        }
        return cls(data)

    @classmethod
    def from_lurking(cls, source: str = MISSING) -> Self:
        data = {'source': source or choice(('Chat Input Blocker - Lurker Mode', 'Notice - Lurker Mode'))}
        return cls(data)

    @property
    def target(self) -> Optional[str]:
        return self._data.get('location', self._data.get('source'))  # type: ignore

    @property
    def value(self) -> str:
        return self._encode_data()

    def __str__(self) -> str:
        return self.target or 'None'

    def __repr__(self) -> str:
        return f'<ContextProperties target={self.target!r}>'

    def __eq__(self, other) -> bool:
        return isinstance(other, ContextProperties) and self.value == other.value

    def __ne__(self, other) -> bool:
        if isinstance(other, ContextProperties):
            return self.value != other.value
        return True
