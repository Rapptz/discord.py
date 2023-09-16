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

from typing import Any, Optional, TYPE_CHECKING, List
from .utils import parse_time, _bytes_to_base64_data, MISSING
from .guild import Guild

# fmt: off
__all__ = (
    'Template',
)
# fmt: on

if TYPE_CHECKING:
    import datetime
    from .types.template import Template as TemplatePayload
    from .state import ConnectionState
    from .user import User


class _FriendlyHttpAttributeErrorHelper:
    __slots__ = ()

    def __getattr__(self, attr):
        raise AttributeError('PartialTemplateState does not support http methods.')


class _PartialTemplateState:
    def __init__(self, *, state) -> None:
        self.__state = state
        self.http = _FriendlyHttpAttributeErrorHelper()

    @property
    def shard_count(self):
        return self.__state.shard_count

    @property
    def user(self):
        return self.__state.user

    @property
    def self_id(self):
        return self.__state.user.id

    @property
    def member_cache_flags(self):
        return self.__state.member_cache_flags

    @property
    def cache_guild_expressions(self):
        return False

    def store_emoji(self, guild, packet) -> None:
        return None

    def _get_voice_client(self, id) -> None:
        return None

    def _get_message(self, id) -> None:
        return None

    def _get_guild(self, id):
        return self.__state._get_guild(id)

    async def query_members(self, **kwargs: Any) -> List[Any]:
        return []

    def __getattr__(self, attr):
        raise AttributeError(f'PartialTemplateState does not support {attr!r}.')


class Template:
    """Represents a Discord template.

    .. versionadded:: 1.4

    Attributes
    -----------
    code: :class:`str`
        The template code.
    uses: :class:`int`
        How many times the template has been used.
    name: :class:`str`
        The name of the template.
    description: :class:`str`
        The description of the template.
    creator: :class:`User`
        The creator of the template.
    created_at: :class:`datetime.datetime`
        An aware datetime in UTC representing when the template was created.
    updated_at: :class:`datetime.datetime`
        An aware datetime in UTC representing when the template was last updated.
        This is referred to as "last synced" in the official Discord client.
    source_guild: :class:`Guild`
        The guild snapshot that represents the data that this template currently holds.
    is_dirty: Optional[:class:`bool`]
        Whether the template has unsynced changes.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'code',
        'uses',
        'name',
        'description',
        'creator',
        'created_at',
        'updated_at',
        'source_guild',
        'is_dirty',
        '_state',
    )

    def __init__(self, *, state: ConnectionState, data: TemplatePayload) -> None:
        self._state = state
        self._store(data)

    def _store(self, data: TemplatePayload) -> None:
        self.code: str = data['code']
        self.uses: int = data['usage_count']
        self.name: str = data['name']
        self.description: Optional[str] = data['description']
        creator_data = data.get('creator')
        self.creator: Optional[User] = None if creator_data is None else self._state.create_user(creator_data)

        self.created_at: Optional[datetime.datetime] = parse_time(data.get('created_at'))
        self.updated_at: Optional[datetime.datetime] = parse_time(data.get('updated_at'))

        source_serialised = data['serialized_source_guild']
        source_serialised['id'] = int(data['source_guild_id'])
        state = _PartialTemplateState(state=self._state)
        # Guild expects a ConnectionState, we're passing a _PartialTemplateState
        self.source_guild = Guild(data=source_serialised, state=state)  # type: ignore

        self.is_dirty: Optional[bool] = data.get('is_dirty', None)

    def __repr__(self) -> str:
        return (
            f'<Template code={self.code!r} uses={self.uses} name={self.name!r}'
            f' creator={self.creator!r} source_guild={self.source_guild!r} is_dirty={self.is_dirty}>'
        )

    async def create_guild(self, name: str, icon: bytes = MISSING) -> Guild:
        """|coro|

        Creates a :class:`.Guild` using the template.

        Bot accounts in more than 10 guilds are not allowed to create guilds.

        .. versionchanged:: 2.0
            The ``region`` parameter has been removed.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        icon: :class:`bytes`
            The :term:`py:bytes-like object` representing the icon. See :meth:`.ClientUser.edit`
            for more details on what is expected.

        Raises
        ------
        HTTPException
            Guild creation failed.
        ValueError
            Invalid icon image format given. Must be PNG or JPG.

        Returns
        -------
        :class:`.Guild`
            The guild created. This is not the same guild that is
            added to cache.
        """
        base64_icon = None
        if icon is not MISSING:
            base64_icon = _bytes_to_base64_data(icon)

        data = await self._state.http.create_from_template(self.code, name, base64_icon)
        return Guild(data=data, state=self._state)

    async def sync(self) -> Template:
        """|coro|

        Sync the template to the guild's current state.

        You must have :attr:`~Permissions.manage_guild` in the source guild to do this.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            The template is no longer edited in-place, instead it is returned.

        Raises
        -------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.

        Returns
        --------
        :class:`Template`
            The newly edited template.
        """

        data = await self._state.http.sync_template(self.source_guild.id, self.code)
        return Template(state=self._state, data=data)

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: Optional[str] = MISSING,
    ) -> Template:
        """|coro|

        Edit the template metadata.

        You must have :attr:`~Permissions.manage_guild` in the source guild to do this.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            The template is no longer edited in-place, instead it is returned.

        Parameters
        ------------
        name: :class:`str`
            The template's new name.
        description: Optional[:class:`str`]
            The template's new description.

        Raises
        -------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.

        Returns
        --------
        :class:`Template`
            The newly edited template.
        """
        payload = {}

        if name is not MISSING:
            payload['name'] = name
        if description is not MISSING:
            payload['description'] = description

        data = await self._state.http.edit_template(self.source_guild.id, self.code, payload)
        return Template(state=self._state, data=data)

    async def delete(self) -> None:
        """|coro|

        Delete the template.

        You must have :attr:`~Permissions.manage_guild` in the source guild to do this.

        .. versionadded:: 1.7

        Raises
        -------
        HTTPException
            Editing the template failed.
        Forbidden
            You don't have permissions to edit the template.
        NotFound
            This template does not exist.
        """
        await self._state.http.delete_template(self.source_guild.id, self.code)

    @property
    def url(self) -> str:
        """:class:`str`: The template url.

        .. versionadded:: 2.0
        """
        return f'https://discord.new/{self.code}'
