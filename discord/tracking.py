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

from typing import Any, Dict, Optional

from .types.snowflake import Snowflake

__all__ = ('ContextProperties',)


class ContextProperties:  # Thank you Discord-S.C.U.M
    """Represents the Discord X-Context-Properties header.

    This header is essential for certain actions (e.g. joining guilds, friend requesting).
    """

    __slots__ = ('_data', 'value')

    def __init__(self, data) -> None:
        self._data: Dict[str, any] = data
        self.value: str = self._encode_data(data)

    def _encode_data(self, data) -> str:
        library = {
            'Friends': 'eyJsb2NhdGlvbiI6IkZyaWVuZHMifQ==',
            'ContextMenu': 'eyJsb2NhdGlvbiI6IkNvbnRleHRNZW51In0=',
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
            'None': 'e30='
        }

        try:
            return library[data.get('location', 'None')]
        except KeyError:
            return b64encode(json.dumps(data).encode()).decode('utf-8')

    @classmethod
    def _empty(cls) -> ContextProperties:
        return cls({})

    @classmethod
    def _from_friends_page(cls) -> ContextProperties:
        data = {
            'location': 'Friends'
        }
        return cls(data)

    @classmethod
    def _from_context_menu(cls) -> ContextProperties:
        data = {
            'location': 'ContextMenu'
        }
        return cls(data)

    @classmethod
    def _from_user_profile(cls) -> ContextProperties:
        data = {
            'location': 'User Profile'
        }
        return cls(data)

    @classmethod
    def _from_add_friend_page(cls) -> ContextProperties:
        data = {
            'location': 'Add Friend'
        }
        return cls(data)

    @classmethod
    def _from_guild_header_menu(cls) -> ContextProperties:
        data = {
            'location': 'Guild Header'
        }
        return cls(data)

    @classmethod
    def _from_group_dm(cls) -> ContextProperties:
        data = {
            'location': 'Group DM'
        }
        return cls(data)

    @classmethod
    def _from_new_group_dm(cls) -> ContextProperties:
        data = {
            'location': 'New Group DM'
        }
        return cls(data)

    @classmethod
    def _from_dm_channel(cls) -> ContextProperties:
        data = {
            'location': 'DM Channel'
        }
        return cls(data)

    @classmethod
    def _from_add_to_dm(cls) -> ContextProperties:
        data = {
            'location': 'Add Friends to DM'
        }
        return cls(data)

    @classmethod
    def _from_accept_invite_page_blank(cls) -> ContextProperties:
        data = {
            'location': 'Accept Invite Page'
        }
        return cls(data)

    @classmethod
    def _from_app(cls) -> ContextProperties:
        data = {
            'location': '/app'
        }
        return cls(data)

    @classmethod
    def _from_login(cls) -> ContextProperties:
        data = {
            'location': 'Login'
        }
        return cls(data)

    @classmethod
    def _from_register(cls) -> ContextProperties:
        data = {
            'location': 'Register'
        }
        return cls(data)

    @classmethod
    def _from_verification(cls) -> ContextProperties:
        data = {
            'location': 'Verify Email'
        }
        return cls(data)

    @classmethod
    def _from_accept_invite_page(
        cls, *, guild_id: Snowflake, channel_id: Snowflake, channel_type: int
    ) -> ContextProperties:
        data = {
            'location': 'Accept Invite Page',
            'location_guild_id': str(guild_id),
            'location_channel_id': str(channel_id),
            'location_channel_type': int(channel_type)
        }
        return cls(data)

    @classmethod
    def _from_join_guild_popup(
        cls, *, guild_id: Snowflake, channel_id: Snowflake, channel_type: int
    ) -> ContextProperties:
        data = {
            'location': 'Join Guild',
            'location_guild_id': str(guild_id),
            'location_channel_id': str(channel_id),
            'location_channel_type': int(channel_type)
        }
        return cls(data)

    @classmethod
    def _from_invite_embed(
        cls, *, guild_id: Snowflake, channel_id: Snowflake, message_id: Snowflake, channel_type: int
    ) -> ContextProperties:
        data = {
            'location': 'Invite Button Embed',
            'location_guild_id': str(guild_id),
            'location_channel_id': str(channel_id),
            'location_channel_type': int(channel_type),
            'location_message_id': str(message_id)
        }
        return cls(data)

    @property
    def location(self) -> Optional[str]:
        return self._data.get('location')

    @property
    def guild_id(self) -> Optional[int]:
        data = self._data.get('location_guild_id')
        if data is not None:
            return int(data)

    @property
    def channel_id(self) -> Optional[int]:
        data = self._data.get('location_channel_id')
        if data is not None:
            return int(data)

    @property
    def channel_type(self) -> Optional[int]:
        data = self._data.get('location_channel_type')
        if data is not None:
            return data

    @property
    def message_id(self) -> Optional[int]:
        data = self._data.get('location_message_id')
        if data is not None:
            return int(data)

    def __bool__(self) -> bool:
        return self.value is not None

    def __str__(self) -> str:
        return self._data.get('location', 'None')

    def __repr__(self) -> str:
        return '<ContextProperties location={0.location}>'.format(self)

    def __eq__(self, other) -> bool:
        return isinstance(other, ContextProperties) and self.value == other.value

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
