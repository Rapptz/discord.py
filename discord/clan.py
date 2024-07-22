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

from typing import TYPE_CHECKING, Dict, List, Optional

from .enums import ClanBannerStyle, ClanPlayStyle, try_enum, ClanBadgeType
from .mixins import Hashable
from .state import ConnectionState
from .object import Object
from .colour import Colour
from .asset import Asset
from .member_verification import MemberVerification
from .utils import MISSING
from .abc import Snowflake

if TYPE_CHECKING:
    from typing_extensions import Self

    from .guild import Guild

    from .types.clan import (
        PartialClan as PartialClanPayload,
        Clan as ClanPayload,
        ClanSettings as ClanSettingsPayload,
        UserClan as UserClanPayload,
    )

__all__ = ('UserClan', 'PartialClan', 'Clan')


class UserClan:
    """Represents a partial clan accessible via a user.

    .. container:: operations

        .. describe:: x == y

            Checks if two user clans are equal.

        .. describe:: x != y

            Checks if two user clans are not equal.

    .. versionadded:: 2.5

    Attributes
    ----------
    guild_id: :class:`int`
        The guild ID the clan is from.
    enabled: :class:`bool`
        Whether the user is displaying their clan tag.
    tag: :class:`str`
        The clan tag.
    """

    __slots__ = (
        '_state',
        'guild_id',
        'enabled',
        'tag',
        '_badge_hash',
    )

    def __init__(self, *, data: UserClanPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.guild_id: int = int(data['identity_guild_id'])
        self.enabled: bool = data['identity_enabled']
        self.tag: str = data['tag']
        self._badge_hash: str = data['badge']

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.tag == other.tag and self.guild_id == other.guild_id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __repr__(self) -> str:
        return f'<UserClan guild_id={self.guild_id} tag={self.tag!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: Returns the cached guild this clan is from."""
        return self._state._get_guild(self.guild_id)

    @property
    def badge(self) -> Asset:
        """:class:`Asset`: Returns the clan badge asset."""
        return Asset._from_clan_badge(self._state, self.guild_id, self._badge_hash)


class PartialClan:
    """Represents a partial clan.

    .. versionadded:: 2.5

    Attributes
    ----------
    tag: :class:`str`
        The clan tag.
    badge_type: Optional[:class:`ClanBadgeType`]
        The clan badge type, or ``None``.
    """

    __slots__ = (
        '_state',
        'tag',
        'badge_type',
    )

    def __init__(self, *, data: PartialClanPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.tag: str = data['tag']
        try:
            self.badge_type: Optional[ClanBadgeType] = try_enum(ClanBadgeType, data['badge'])
        except KeyError:
            self.badge_type = None


class Clan(Hashable, PartialClan):
    """Represents a clan.

    .. container:: operations

        .. describe:: x == y

            Checks if two clans are equal.

        .. describe:: x != y

            Checks if two clans are not equal.

        .. describe:: hash(x)

            Returns the clan's hash.

        .. describe:: str(x)

            Returns the clan's name.

    .. versionadded:: 2.5

    Attributes
    ----------
    id: :class:`int`
        The guild ID.
    name: :class:`str`
        The guild name.
    tag: :class:`str`
        The clan tag.
    description: :class:`str`
        The clan description.

        .. note::

            This can be different than the guild's description.
    member_count: Optional[:class:`int`]
        An approximate count of the total members in the guild, or ``None``.
    play_style: :class:`ClanPlayStyle`
        The clan play style.
    badge_type: Optional[:class:`ClanBadgeType`]
        The clan badge type, or ``None``.
    banner_style: Optional[:class:`ClanBannerStyle`]
        The clan banner type, or ``None``.
    """

    __slots__ = (
        'id',
        'name',
        'description',
        'play_style',
        'member_count',
        'banner_style',
        '_games',
        '_search_terms',
        '_badge_hash',
        '_banner_hash',
        '_badge_primary_colour',
        '_badge_secondary_colour',
        '_banner_primary_colour',
        '_banner_secondary_colour',
        '_wildcard_descriptors',
        '_verification_form',
    )

    if TYPE_CHECKING:
        id: int
        name: str
        description: str
        play_style: ClanPlayStyle
        member_count: Optional[int]
        banner_style: Optional[ClanBannerStyle]
        _games: Dict[int, Object]
        _search_terms: List[str]
        _badge_hash: Optional[str]
        _banner_hash: Optional[str]
        _badge_primary_colour: Optional[str]
        _badge_secondary_colour: Optional[str]
        _banner_primary_colour: Optional[str]
        _banner_secondary_colour: Optional[str]
        _verification_form: Optional[MemberVerification]

    def __init__(self, *, data: ClanPayload, state: ConnectionState) -> None:
        super().__init__(data=data, state=state)

        self.id: int = int(data['id'])
        self._update(data)

    def _update(self, data: ClanPayload) -> None:
        self.name: str = data['name']
        self.description: str = data['description']
        self.member_count: Optional[int] = data.get('member_count')
        self.play_style: ClanPlayStyle = try_enum(ClanPlayStyle, data.get('play_style', 0))

        try:
            self.banner_style: Optional[ClanBannerStyle] = try_enum(
                ClanBannerStyle, data['banner']
            )
        except KeyError:
            self.banner_style = None

        self._games: Dict[int, Object] = {
            int(g): Object(int(g)) for g in data.get('game_application_ids', [])
        }
        self._search_terms: List[str] = data.get('search_terms', [])
        self._badge_hash: Optional[str] = data.get('badge_hash')
        self._banner_hash: Optional[str] = data.get('banner_hash')
        self._badge_primary_colour: Optional[str] = data.get('badge_color_primary')
        self._badge_secondary_colour: Optional[str] = data.get('badge_color_secondary')
        self._banner_primary_colour: Optional[str] = data.get('brand_color_primary')
        self._banner_secondary_colour: Optional[str] = data.get('brand_color_secondary')
        self._wildcard_descriptors: List[str] = data.get('wildcard_descriptors', [])
        try:
            self._verification_form: Optional[MemberVerification] = MemberVerification._from_data(
                data=data['verification_form'],
                state=self._state,
                guild=self.guild,
            )
        except KeyError:
            self._verification_form = None

    def _update_from_clan_settings(self, data: ClanSettingsPayload) -> None:
        self.tag = data['tag']
        self._games = {int(g): Object(int(g)) for g in data.get('game_application_ids', [])}
        self._search_terms = data['search_terms']
        self.play_style = try_enum(ClanPlayStyle, data['play_style'])
        self.description = data['description']
        self._wildcard_descriptors = data['wildcard_descriptors']
        self.badge_type = try_enum(ClanBadgeType, data['badge'])
        self.banner_style = try_enum(ClanBannerStyle, data['banner'])
        self._badge_primary_colour = data['badge_color_primary']
        self._badge_secondary_colour = data['badge_color_secondary']
        self._banner_primary_colour = data['brand_color_primary']
        self._banner_secondary_colour = data['brand_color_secondary']
        self._verification_form = MemberVerification._from_data(
            data=data['verification_form'],
            state=self._state,
            guild=self.guild,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Clan id={self.id} tag={self.tag!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: Returns the respective guild of this clan."""
        return self._state._get_guild(self.id)

    @property
    def games(self) -> List[Object]:
        """List[:class:`Object`]: Returns a list of objects that represent the games
        the clan plays.
        """
        return list(self._games.values())

    @property
    def search_terms(self) -> List[str]:
        """List[:class:`str`]: Returns a read-only list of the interests, topics,
        or traits for the clan.
        """
        return self._search_terms.copy()

    @property
    def wildcard_descriptors(self) -> List[str]:
        """List[:class:`str`]: Returns a read-only list of the terms that describe the
        clan.
        """
        return self._wildcard_descriptors.copy()

    @property
    def badge_primary_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan badge primary colour.

        There is an alias for this named :attr:`badge_primary_color`.
        """

        if self._badge_primary_colour is None:
            return None
        return Colour.from_str(self._badge_primary_colour)

    @property
    def badge_secondary_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan badge secondary colour.

        There is an alias for this named :attr:`badge_secondary_color`.
        """

        if self._badge_secondary_colour is None:
            return None
        return Colour.from_str(self._badge_secondary_colour)

    @property
    def badge_primary_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan badge primary color.

        There is an alias for this named :attr:`badge_primary_colour`.
        """
        return self.badge_primary_colour

    @property
    def badge_secondary_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan badge secondary color.

        There is an alias for this named :attr:`badge_secondary_colour`.
        """
        return self.badge_secondary_colour

    @property
    def banner_primary_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan banner primary colour.

        There is an alias for this named :attr:`banner_primary_color`.
        """

        if self._banner_primary_colour is None:
            return None
        return Colour.from_str(self._banner_primary_colour)

    @property
    def banner_secondary_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan banner secondary colour.

        There is an alias for this named :attr:`banner_secondary_color`.
        """

        if self._banner_secondary_colour is None:
            return None
        return Colour.from_str(self._banner_secondary_colour)

    @property
    def banner_primary_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan banner primary color.

        There is an alias for this named :attr:`banner_primary_colour`.
        """
        return self.banner_primary_colour

    @property
    def banner_secondary_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: A property that returns the clan banner secondary color.

        There is an alias for this named :attr:`banner_secondary_colour`.
        """
        return self.banner_secondary_colour

    @property
    def badge(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the badge asset, or ``None``."""
        if self._badge_hash is None:
            return None
        return Asset._from_clan_badge(self._state, self.id, self._badge_hash)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the banner asset, or ``None``."""
        if self._banner_hash is None:
            return None
        return Asset._from_clan_banner(self._state, self.id, self._banner_hash)

    @property
    def verification_form(self) -> Optional[MemberVerification]:
        """Optional[:class:`MemberVerification`]: The member verification shown to applicants,
        or ``None``.
        """
        return self._verification_form

    async def fetch_settings(self) -> Self:
        """|coro|

        Fetches this clan settings.

        Raises
        ------
        HTTPException
            An error occurred while fetching the clan settings.

        Returns
        -------
        :class:`Clan`
            The updated class with the settings up-to-date.
        """

        data = await self._state.http.get_clan_settings(self.id)
        self._update_from_clan_settings(data)
        return self

    async def edit(
        self,
        *,
        tag: str = MISSING,
        games: List[Snowflake] = MISSING,
        search_terms: List[str] = MISSING,
        play_style: ClanPlayStyle = MISSING,
        description: str = MISSING,
        wildcard_descriptors: List[str] = MISSING,
        badge_type: ClanBadgeType = MISSING,
        banner_style: ClanBannerStyle = MISSING,
        badge_primary_colour: Colour = MISSING,
        badge_secondary_colour: Colour = MISSING,
        badge_primary_color: Colour = MISSING,
        badge_secondary_color: Colour = MISSING,
        banner_primary_colour: Colour = MISSING,
        banner_secondary_colour: Colour = MISSING,
        banner_primary_color: Colour = MISSING,
        banner_secondary_color: Colour = MISSING,
        verification_form: MemberVerification = MISSING,
    ) -> None:
        """|coro|

        Edits this clan.

        Parameters
        ----------
        tag: :class:`str`
            The new tag of the clan. Must be between 2 to 4 characters long.
        games: List[:class`abc.Snowflake`]
            A list of objects that meet the :class:`abc.Snowflake` ABC representing
            the games this clan plays.
        search_terms: List[:class:`str`]
            The interests, topics, or traits for the clan. Can have up to 30 items, and
            each one can be up to 24 characters.
        play_style: :class:`ClanPlayStyle`
            The play style of the clan.
        description: :class:`str`
            The clan description.
        wildcard_descriptors: List[:class:`str`]
            The terms that describe the clan. Can have up to 3 items, and each one can be
            up to 12 characters.
        badge_type: :class:`ClanBadgeType`
            The badge type shown on the clan tag.
        banner_style: :class:`ClannBannerStyle`
            The banner style representing the clan.
        badge_primary_colour: :class:`Colour`
            The primary colour of the badge.
        badge_secondary_colour: :class:`Colour`
            The secondary colour of the badge.
        badge_primary_color: :class:`Colour`
            An alias for ``badge_primary_colour``.
        badge_secondary_color: :class:`Colour`
            An alias for ``badge_secondary_colour``.
        banner_primary_colour: :class:`Colour`
            The banner primary colour.
        banner_secondary_colour: :class:`Colour`
            The banner secondary colour.
        banner_primary_color: :class:`Colour`
            An alias for ``banner_primary_colour``.
        banner_secondary_color: :class:`Color`
            An alias for ``banner_secondary_colour``.
        verification_form: :class:`MemberVerification`
            The member verification shown to applicants.
        """

        # TODO: finish this
