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
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from .asset import Asset
from .permissions import Permissions
from .colour import Colour
from .mixins import Hashable
from .utils import snowflake_time, _get_as_snowflake, MISSING, _bytes_to_base64_data

__all__ = (
    'RoleTags',
    'Role',
)

if TYPE_CHECKING:
    import datetime
    from .types.role import (
        Role as RolePayload,
        RoleTags as RoleTagPayload,
    )
    from .types.guild import RolePositionUpdate
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .abc import Snowflake


class RoleTags:
    """Represents tags on a role.

    A role tag is a piece of extra information attached to a managed role
    that gives it context for the reason the role is managed.

    While this can be accessed, a useful interface is also provided in the
    :class:`Role` and :class:`Guild` classes as well.

    .. versionadded:: 1.6

    Attributes
    ------------
    bot_id: Optional[:class:`int`]
        The bot's user ID that manages this role.
    integration_id: Optional[:class:`int`]
        The integration ID that manages the role.
    subscription_listing_id: Optional[:class:`int`]
        The ID of this role's subscription SKU and listing.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'bot_id',
        'integration_id',
        '_premium_subscriber',
        '_available_for_purchase',
        'subscription_listing_id',
        '_guild_connections',
    )

    def __init__(self, data: RoleTagPayload):
        self.bot_id: Optional[int] = _get_as_snowflake(data, 'bot_id')
        self.integration_id: Optional[int] = _get_as_snowflake(data, 'integration_id')
        self.subscription_listing_id: Optional[int] = _get_as_snowflake(data, 'subscription_listing_id')

        # NOTE: The API returns "null" for this if it's valid, which corresponds to None.
        # This is different from other fields where "null" means "not there".
        # So in this case, a value of None is the same as True.
        # Which means we would need a different sentinel.
        self._premium_subscriber: bool = data.get('premium_subscriber', MISSING) is None
        self._available_for_purchase: bool = data.get('available_for_purchase', MISSING) is None
        self._guild_connections: bool = data.get('guild_connections', MISSING) is None

    def is_bot_managed(self) -> bool:
        """:class:`bool`: Whether the role is associated with a bot."""
        return self.bot_id is not None

    def is_premium_subscriber(self) -> bool:
        """:class:`bool`: Whether the role is the premium subscriber, AKA "boost", role for the guild."""
        return self._premium_subscriber

    def is_integration(self) -> bool:
        """:class:`bool`: Whether the role is managed by an integration."""
        return self.integration_id is not None

    def is_available_for_purchase(self) -> bool:
        """:class:`bool`: Whether the role is available for purchase.

        .. versionadded:: 2.0
        """
        return self._available_for_purchase

    def is_guild_connection(self) -> bool:
        """:class:`bool`: Whether the role is a guild's linked role.

        .. versionadded:: 2.0
        """
        return self._guild_connections

    def __repr__(self) -> str:
        return (
            f'<RoleTags bot_id={self.bot_id} integration_id={self.integration_id} '
            f'premium_subscriber={self.is_premium_subscriber()}>'
        )


class Role(Hashable):
    """Represents a Discord role in a :class:`Guild`.

    .. container:: operations

        .. describe:: x == y

            Checks if two roles are equal.

        .. describe:: x != y

            Checks if two roles are not equal.

        .. describe:: x > y

            Checks if a role is higher than another in the hierarchy.

        .. describe:: x < y

            Checks if a role is lower than another in the hierarchy.

        .. describe:: x >= y

            Checks if a role is higher or equal to another in the hierarchy.

        .. describe:: x <= y

            Checks if a role is lower or equal to another in the hierarchy.

        .. describe:: hash(x)

            Return the role's hash.

        .. describe:: str(x)

            Returns the role's name.

    Attributes
    ----------
    id: :class:`int`
        The ID for the role.
    name: :class:`str`
        The name of the role.
    guild: :class:`Guild`
        The guild the role belongs to.
    hoist: :class:`bool`
         Indicates if the role will be displayed separately from other members.
    position: :class:`int`
        The position of the role. This number is usually positive. The bottom
        role has a position of 0.

        .. warning::

            Multiple roles can have the same position number. As a consequence
            of this, comparing via role position is prone to subtle bugs if
            checking for role hierarchy. The recommended and correct way to
            compare for roles in the hierarchy is using the comparison
            operators on the role objects themselves.

    unicode_emoji: Optional[:class:`str`]
        The role's unicode emoji, if available.

        .. note::

            If :attr:`icon` is not ``None``, it is displayed as role icon
            instead of the unicode emoji under this attribute.

            If you want the icon that a role has displayed, consider using :attr:`display_icon`.

        .. versionadded:: 2.0

    managed: :class:`bool`
        Indicates if the role is managed by the guild through some form of
        integrations such as Twitch.
    mentionable: :class:`bool`
        Indicates if the role can be mentioned by users.
    tags: Optional[:class:`RoleTags`]
        The role tags associated with this role.
    """

    __slots__ = (
        'id',
        'name',
        '_permissions',
        '_colour',
        'position',
        '_icon',
        'unicode_emoji',
        'managed',
        'mentionable',
        'hoist',
        'guild',
        'tags',
        '_state',
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: RolePayload):
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Role id={self.id} name={self.name!r}>'

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Role) or not isinstance(self, Role):
            return NotImplemented

        if self.guild != other.guild:
            raise RuntimeError('cannot compare roles from two different guilds.')

        # the @everyone role is always the lowest role in hierarchy
        guild_id = self.guild.id
        if self.id == guild_id:
            # everyone_role < everyone_role -> False
            return other.id != guild_id

        if self.position < other.position:
            return True

        if self.position == other.position:
            return self.id > other.id

        return False

    def __le__(self, other: Any) -> bool:
        r = Role.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __gt__(self, other: Any) -> bool:
        return Role.__lt__(other, self)

    def __ge__(self, other: object) -> bool:
        r = Role.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def _update(self, data: RolePayload):
        self.name: str = data['name']
        self._permissions: int = int(data.get('permissions', 0))
        self.position: int = data.get('position', 0)
        self._colour: int = data.get('color', 0)
        self.hoist: bool = data.get('hoist', False)
        self._icon: Optional[str] = data.get('icon')
        self.unicode_emoji: Optional[str] = data.get('unicode_emoji')
        self.managed: bool = data.get('managed', False)
        self.mentionable: bool = data.get('mentionable', False)
        self.tags: Optional[RoleTags]

        try:
            self.tags = RoleTags(data['tags'])
        except KeyError:
            self.tags = None

    def is_default(self) -> bool:
        """:class:`bool`: Checks if the role is the default role."""
        return self.guild.id == self.id

    def is_bot_managed(self) -> bool:
        """:class:`bool`: Whether the role is associated with a bot.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_bot_managed()

    def is_premium_subscriber(self) -> bool:
        """:class:`bool`: Whether the role is the premium subscriber, AKA "boost", role for the guild.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_premium_subscriber()

    def is_integration(self) -> bool:
        """:class:`bool`: Whether the role is managed by an integration.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_integration()

    def is_assignable(self) -> bool:
        """:class:`bool`: Whether the role is able to be assigned or removed by the bot.

        .. versionadded:: 2.0
        """
        me = self.guild.me
        return not self.is_default() and not self.managed and (me.top_role > self or me.id == self.guild.owner_id)  # type: ignore # Should just error ATP

    @property
    def permissions(self) -> Permissions:
        """:class:`Permissions`: Returns the role's permissions."""
        return Permissions(self._permissions)

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: Returns the role colour. An alias exists under ``color``."""
        return Colour(self._colour)

    @property
    def color(self) -> Colour:
        """:class:`Colour`: Returns the role color. An alias exists under ``colour``."""
        return self.colour

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Returns the role's icon asset, if available.

        .. note::
            If this is ``None``, the role might instead have unicode emoji as its icon
            if :attr:`unicode_emoji` is not ``None``.

            If you want the icon that a role has displayed, consider using :attr:`display_icon`.

        .. versionadded:: 2.0
        """
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='role')

    @property
    def display_icon(self) -> Optional[Union[Asset, str]]:
        """Optional[Union[:class:`.Asset`, :class:`str`]]: Returns the role's display icon, if available.

        .. versionadded:: 2.0
        """
        return self.icon or self.unicode_emoji

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the role's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention a role."""
        if self.id == self.guild.id:
            return '@everyone'
        return f'<@&{self.id}>'

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all the members with this role."""
        all_members = list(self.guild._members.values())
        if self.is_default():
            return all_members

        role_id = self.id
        return [member for member in all_members if member._roles.has(role_id)]

    async def _move(self, position: int, reason: Optional[str]) -> None:
        if position <= 0:
            raise ValueError("Cannot move role to position 0 or below")

        if self.is_default():
            raise ValueError("Cannot move default role")

        if self.position == position:
            return  # Save Discord the extra request

        http = self._state.http

        change_range = range(min(self.position, position), max(self.position, position) + 1)
        roles = [r.id for r in self.guild.roles[1:] if r.position in change_range and r.id != self.id]

        if self.position > position:
            roles.insert(0, self.id)
        else:
            roles.append(self.id)

        payload: List[RolePositionUpdate] = [{"id": z[0], "position": z[1]} for z in zip(roles, change_range)]
        await http.move_role_position(self.guild.id, payload, reason=reason)

    async def fetch_members(self, *, subscribe: bool = False) -> List[Member]:
        """|coro|

        Retrieves all members with this role.
        This is a partial websocket operation.

        .. versionadded:: 2.0

        .. note::
            This can only return up to 100 of the first members, and cannot be used on the default role.

        Parameters
        ----------
        subscribe: :class:`bool`
            Whether to subscribe to the resulting members. This will keep their info and presence updated.
            This requires another request, and defaults to ``False``.

        Raises
        ------
        HTTPException
            Fetching the members failed.
        TypeError
            This role is the default role.
        asyncio.TimeoutError
            The operation timed out.

        Returns
        -------
        List[:class:`Member`]
            The members with this role.
        """
        if self.is_default():
            raise TypeError('Cannot fetch the default role\'s members')

        guild = self.guild
        data = await self._state.http.get_role_members(guild.id, self.id)
        if data:
            return await guild.query_members(user_ids=data, subscribe=subscribe)  # type: ignore # user_ids is cast to str anyway
        return []

    async def add_members(self, *members: Snowflake, reason: Optional[str] = None) -> List[Member]:
        r"""|coro|

        Adds a number of :class:`Member`\s to this role.

        You must have :attr:`~Permissions.manage_roles` to use this,
        and the current :class:`Role` must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*members: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Member`
            to add to the role.
        reason: Optional[:class:`str`]
            The reason for adding these members. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to add these members.
        HTTPException
            Adding members failed.
        TypeError
            The role is the default role.

        Returns
        --------
        List[:class:`Member`]
            The list of members that were added to the role.
        """
        if self.is_default():
            raise TypeError('Cannot add members to the default role')

        from .member import Member  # Circular import

        state = self._state
        guild = self.guild

        data = await state.http.add_members_to_role(guild.id, self.id, [m.id for m in members], reason=reason)
        return [Member(data=m, state=state, guild=guild) for m in data.values()]

    async def remove_members(self, *members: Snowflake, reason: Optional[str] = None) -> None:
        r"""|coro|

        Removes :class:`Member`\s from this role.

        You must have :attr:`~Permissions.manage_roles` to use this,
        and the current :class:`Role` must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*members: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Member`
            to remove from the role.
        reason: Optional[:class:`str`]
            The reason for adding these members. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these members.
        HTTPException
            Removing the members failed.
        TypeError
            The role is the default role.
        """
        if self.is_default():
            raise TypeError('Cannot remove members from the default role')

        req = self._state.http.remove_role
        guild_id = self.guild.id
        role_id = self.id
        for member in members:
            await req(guild_id, member.id, role_id, reason=reason)

    async def edit(
        self,
        *,
        name: str = MISSING,
        permissions: Permissions = MISSING,
        colour: Union[Colour, int] = MISSING,
        color: Union[Colour, int] = MISSING,
        hoist: bool = MISSING,
        display_icon: Optional[Union[bytes, str]] = MISSING,
        icon: Optional[bytes] = MISSING,
        unicode_emoji: Optional[str] = MISSING,
        mentionable: bool = MISSING,
        position: int = MISSING,
        reason: Optional[str] = MISSING,
    ) -> Optional[Role]:
        """|coro|

        Edits the role.

        You must have :attr:`~Permissions.manage_roles` to do this.

        All fields are optional.

        .. versionchanged:: 1.4
            Can now pass ``int`` to ``colour`` keyword-only parameter.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited role is returned instead.

        .. versionadded:: 2.0
            The ``display_icon``, ``icon``, and ``unicode_emoji`` keyword-only parameters were added.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        name: :class:`str`
            The new role name to change to.
        permissions: :class:`Permissions`
            The new permissions to change to.
        colour: Union[:class:`Colour`, :class:`int`]
            The new colour to change to. (aliased to color as well)
        hoist: :class:`bool`
            Indicates if the role should be shown separately in the member list.
        display_icon: Optional[Union[:class:`bytes`, :class:`str`]]
            A :term:`py:bytes-like object` representing the icon
            or :class:`str` representing unicode emoji that should be used as a role icon.
            Could be ``None`` to denote removal of the icon.
            Only PNG/JPEG is supported.
            This is only available to guilds that contain ``ROLE_ICONS`` in :attr:`Guild.features`.
        icon: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the icon that should be used as a role icon.
            Could be ``None`` to denote removal of the icon.
            Only PNG/JPEG is supported.
            This is only available to guilds that contain ``ROLE_ICONS`` in :attr:`Guild.features`.
        unicode_emoji: Optional[:class:`str`]
            A unicode emoji that should be used as a role icon.
            :attr:`icon` takes precedence over this, but both can be set.
            This is only available to guilds that contain ``ROLE_ICONS`` in :attr:`Guild.features`.
        mentionable: :class:`bool`
            Indicates if the role should be mentionable by others.
        position: :class:`int`
            The new role's position. This must be below your top role's
            position or it will fail.
        reason: Optional[:class:`str`]
            The reason for editing this role. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to change the role.
        HTTPException
            Editing the role failed.
        ValueError
            An invalid position was given, the default
            role was asked to be moved, or both ``display_icon``
            and ``icon``/``unicode_emoji`` were set.

        Returns
        --------
        :class:`Role`
            The newly edited role.
        """
        if display_icon and (icon or unicode_emoji):
            raise ValueError('Cannot set both icon/unicode_emoji and display_icon')

        if position is not MISSING:
            await self._move(position, reason=reason)

        payload: Dict[str, Any] = {}
        if color is not MISSING:
            colour = color

        if colour is not MISSING:
            if isinstance(colour, int):
                payload['color'] = colour
            else:
                payload['color'] = colour.value

        if name is not MISSING:
            payload['name'] = name

        if permissions is not MISSING:
            payload['permissions'] = permissions.value

        if hoist is not MISSING:
            payload['hoist'] = hoist

        if display_icon is not MISSING:
            if isinstance(display_icon, bytes):
                payload['icon'] = _bytes_to_base64_data(display_icon)
            elif display_icon:
                payload['unicode_emoji'] = display_icon
            else:
                payload['icon'] = None
                payload['unicode_emoji'] = None

        if icon is not MISSING:
            if icon is None:
                payload['icon'] = icon
            else:
                payload['icon'] = _bytes_to_base64_data(icon)

        if unicode_emoji is not MISSING:
            if unicode_emoji is None:
                payload['unicode_emoji'] = None
            else:
                payload['unicode_emoji'] = unicode_emoji

        if mentionable is not MISSING:
            payload['mentionable'] = mentionable

        data = await self._state.http.edit_role(self.guild.id, self.id, reason=reason, **payload)
        return Role(guild=self.guild, data=data, state=self._state)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the role.

        You must have :attr:`~Permissions.manage_roles` to do this.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for deleting this role. Shows up on the audit log.

        Raises
        --------
        Forbidden
            You do not have permissions to delete the role.
        HTTPException
            Deleting the role failed.
        """

        await self._state.http.delete_role(self.guild.id, self.id, reason=reason)
