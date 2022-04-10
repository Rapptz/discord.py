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

from typing import Dict, overload, Optional, TYPE_CHECKING

from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .enums import ChannelType
    from .types.snowflake import Snowflake
    from .state import ConnectionState

__all__ = (
    'ContextProperties',
    'Tracking',
)


class ContextProperties:  # Thank you Discord-S.C.U.M
    """Represents the Discord X-Context-Properties header.

    This header is essential for certain actions (e.g. joining guilds, friend requesting).

    .. versionadded:: 1.9

    .. container:: operations

        .. describe:: x == y

            Checks if two context properties are equal.

        .. describe:: x != y

            Checks if two context properties are not equal.

        .. describe:: hash(x)

            Return the context property's hash.

        .. describe:: str(x)

            Returns the context property's name.

    Attributes
    ----------
    value: :class:`str`
        The encoded header value.
    """

    __slots__ = ('_data', 'value')

    def __init__(self, data) -> None:
        self._data: Dict[str, Snowflake] = data
        self.value: str = self._encode_data(data)

    def _encode_data(self, data) -> str:
        library = {
            'None': 'e30=',
            # Locations
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
            # Sources
            'Chat Input Blocker - Lurker Mode': 'eyJzb3VyY2UiOiJDaGF0IElucHV0IEJsb2NrZXIgLSBMdXJrZXIgTW9kZSJ9',
            'Notice - Lurker Mode': 'eyJzb3VyY2UiOiJOb3RpY2UgLSBMdXJrZXIgTW9kZSJ9',
        }

        try:
            return library[self.target or 'None']
        except KeyError:
            return b64encode(json.dumps(data, separators=(',', ':')).encode()).decode('utf-8')

    @classmethod
    def _empty(cls) -> Self:
        return cls({})

    @classmethod
    def _from_friends_page(cls) -> Self:
        data = {'location': 'Friends'}
        return cls(data)

    @classmethod
    def _from_context_menu(cls) -> Self:
        data = {'location': 'ContextMenu'}
        return cls(data)

    @classmethod
    def _from_user_profile(cls) -> Self:
        data = {'location': 'User Profile'}
        return cls(data)

    @classmethod
    def _from_add_friend_page(cls) -> Self:
        data = {'location': 'Add Friend'}
        return cls(data)

    @classmethod
    def _from_guild_header_menu(cls) -> Self:
        data = {'location': 'Guild Header'}
        return cls(data)

    @classmethod
    def _from_group_dm(cls) -> Self:
        data = {'location': 'Group DM'}
        return cls(data)

    @classmethod
    def _from_new_group_dm(cls) -> Self:
        data = {'location': 'New Group DM'}
        return cls(data)

    @classmethod
    def _from_dm_channel(cls) -> Self:
        data = {'location': 'DM Channel'}
        return cls(data)

    @classmethod
    def _from_add_to_dm(cls) -> Self:
        data = {'location': 'Add Friends to DM'}
        return cls(data)

    @classmethod
    def _from_app(cls) -> Self:
        data = {'location': '/app'}
        return cls(data)

    @classmethod
    def _from_login(cls) -> Self:
        data = {'location': 'Login'}
        return cls(data)

    @classmethod
    def _from_register(cls) -> Self:
        data = {'location': 'Register'}
        return cls(data)

    @classmethod
    def _from_verification(cls) -> Self:
        data = {'location': 'Verify Email'}
        return cls(data)

    @classmethod
    def _from_accept_invite_page(
        cls,
        *,
        guild_id: Snowflake = MISSING,
        channel_id: Snowflake = MISSING,
        channel_type: ChannelType = MISSING,
    ) -> Self:
        data: Dict[str, Snowflake] = {
            'location': 'Accept Invite Page',
        }
        if guild_id is not MISSING:
            data['location_guild_id'] = str(guild_id)
        if channel_id is not MISSING:
            data['location_channel_id'] = str(channel_id)
        if channel_type is not MISSING:
            data['location_channel_type'] = int(channel_type)
        return cls(data)

    @classmethod
    def _from_join_guild_popup(
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
    def _from_invite_embed(
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
    def _from_lurking(cls, source: str = MISSING) -> Self:
        data = {'source': source or choice(('Chat Input Blocker - Lurker Mode', 'Notice - Lurker Mode'))}
        return cls(data)

    @property
    def target(self) -> Optional[str]:
        return self._data.get('location', self._data.get('source'))  # type: ignore

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
        return self._data.get('location_channel_type')  # type: ignore

    @property
    def message_id(self) -> Optional[int]:
        data = self._data.get('location_message_id')
        if data is not None:
            return int(data)

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

    def __hash__(self) -> int:
        return hash(self.value)


class Tracking:
    """Represents your Discord tracking settings.

    Attributes
    ----------
    personalization: :class:`bool`
        Whether you have consented to your data being used for personalization.
    usage_statistics: :class:`bool`
        Whether you have consented to your data being used for usage statistics.
    """

    __slots__ = ('_state', 'personalization', 'usage_statistics')

    def __init__(self, *, data: Dict[str, Dict[str, bool]], state: ConnectionState) -> None:
        self._state = state
        self._update(data)

    def __bool__(self) -> bool:
        return any({self.personalization, self.usage_statistics})

    def _update(self, data: Dict[str, Dict[str, bool]]):
        self.personalization = data.get('personalization', {}).get('consented', False)
        self.usage_statistics = data.get('usage_statistics', {}).get('consented', False)

    @overload
    async def edit(self) -> None:
        ...

    @overload
    async def edit(
        self,
        *,
        personalization: bool = ...,
        usage_statistics: bool = ...,
    ) -> None:
        ...

    async def edit(self, **kwargs) -> None:
        """|coro|

        Edits your tracking settings.

        Parameters
        ----------
        personalization: :class:`bool`
            Whether you have consented to your data being used for personalization.
        usage_statistics: :class:`bool`
            Whether you have consented to your data being used for usage statistics.
        """
        payload = {
            'grant': [k for k, v in kwargs.items() if v is True],
            'revoke': [k for k, v in kwargs.items() if v is False],
        }
        data = await self._state.http.edit_tracking(payload)
        self._update(data)
