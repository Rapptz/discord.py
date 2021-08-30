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
from typing import Any, Iterator, List, Optional, TYPE_CHECKING, Tuple

from .asset import Asset, AssetMixin
from .utils import SnowflakeList, snowflake_time, MISSING
from .partial_emoji import _EmojiTag, PartialEmoji
from .user import User

__all__ = (
    'Emoji',
)

if TYPE_CHECKING:
    from .types.emoji import Emoji as EmojiPayload
    from .guild import Guild
    from .state import ConnectionState
    from .abc import Snowflake
    from .role import Role
    from datetime import datetime


class Emoji(_EmojiTag, AssetMixin):
    """Represents a custom emoji.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    -----------
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    guild_id: :class:`int`
        The guild ID the emoji belongs to.
    available: :class:`bool`
        Whether the emoji is available for use.
    user: Optional[:class:`User`]
        The user that created the emoji. This can only be retrieved using :meth:`Guild.fetch_emoji` and
        having the :attr:`~Permissions.manage_emojis` permission.
    """

    __slots__: Tuple[str, ...] = (
        'require_colons',
        'animated',
        'managed',
        'id',
        'name',
        '_roles',
        'guild_id',
        '_state',
        'user',
        'available',
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: EmojiPayload):
        self.guild_id: int = guild.id
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, emoji: EmojiPayload):
        self.require_colons: bool = emoji.get('require_colons', False)
        self.managed: bool = emoji.get('managed', False)
        self.id: int = int(emoji['id'])  # type: ignore
        self.name: str = emoji['name']  # type: ignore
        self.animated: bool = emoji.get('animated', False)
        self.available: bool = emoji.get('available', True)
        self._roles: SnowflakeList = SnowflakeList(map(int, emoji.get('roles', [])))
        user = emoji.get('user')
        self.user: Optional[User] = User(state=self._state, data=user) if user else None

    def _to_partial(self) -> PartialEmoji:
        return PartialEmoji(name=self.name, animated=self.animated, id=self.id)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        for attr in self.__slots__:
            if attr[0] != '_':
                value = getattr(self, attr, None)
                if value is not None:
                    yield (attr, value)

    def __str__(self) -> str:
        if self.animated:
            return f'<a:{self.name}:{self.id}>'
        return f'<:{self.name}:{self.id}>'

    def __repr__(self) -> str:
        return f'<Emoji id={self.id} name={self.name!r} animated={self.animated} managed={self.managed}>'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _EmojiTag) and self.id == other.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the emoji's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the URL of the emoji."""
        fmt = 'gif' if self.animated else 'png'
        return f'{Asset.BASE}/emojis/{self.id}.{fmt}'

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: A :class:`list` of roles that is allowed to use this emoji.

        If roles is empty, the emoji is unrestricted.
        """
        guild = self.guild
        if guild is None:
            return []

        return [role for role in guild.roles if self._roles.has(role.id)]

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild this emoji belongs to."""
        return self._state._get_guild(self.guild_id)

    def is_usable(self) -> bool:
        """:class:`bool`: Whether the bot can use this emoji.

        .. versionadded:: 1.3
        """
        if not self.available:
            return False
        if not self._roles:
            return True
        emoji_roles, my_roles = self._roles, self.guild.me._roles
        return any(my_roles.has(role_id) for role_id in emoji_roles)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_custom_emoji(self.guild.id, self.id, reason=reason)

    async def edit(self, *, name: str = MISSING, roles: List[Snowflake] = MISSING, reason: Optional[str] = None) -> Emoji:
        r"""|coro|

        Edits the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        .. versionchanged:: 2.0
            The newly updated emoji is returned.

        Parameters
        -----------
        name: :class:`str`
            The new emoji name.
        roles: Optional[List[:class:`~discord.abc.Snowflake`]]
            A list of roles that can use this emoji. An empty list can be passed to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for editing this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.

        Returns
        --------
        :class:`Emoji`
            The newly updated emoji.
        """

        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if roles is not MISSING:
            payload['roles'] = [role.id for role in roles]

        data = await self._state.http.edit_custom_emoji(self.guild.id, self.id, payload=payload, reason=reason)
        return Emoji(guild=self.guild, data=data, state=self._state)
