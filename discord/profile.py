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

from typing import TYPE_CHECKING, List, Optional

from . import utils
from .application import ApplicationInstallParams
from .asset import Asset
from .connections import PartialConnection
from .enums import PremiumType, try_enum
from .flags import ApplicationFlags
from .member import Member
from .mixins import Hashable
from .user import User

if TYPE_CHECKING:
    from datetime import datetime

    from .guild import Guild
    from .state import ConnectionState
    from .types.profile import (
        Profile as ProfilePayload,
        ProfileApplication as ProfileApplicationPayload,
        MutualGuild as MutualGuildPayload,
    )
    from .types.user import PartialUser as PartialUserPayload

__all__ = (
    'ApplicationProfile',
    'MutualGuild',
    'UserProfile',
    'MemberProfile',
)


class Profile:
    if TYPE_CHECKING:
        id: int
        bot: bool
        _state: ConnectionState

    def __init__(self, **kwargs) -> None:
        data: ProfilePayload = kwargs.pop('data')
        user = data['user']
        mutual_friends: List[PartialUserPayload] = kwargs.pop('mutual_friends', None)

        member = data.get('guild_member')
        if member is not None:
            member['user'] = user
            kwargs['data'] = member
        else:
            kwargs['data'] = user

        # n.b. this class is subclassed by UserProfile and MemberProfile
        # which subclass either User or Member respectively
        # Because of this, we call super().__init__ here
        # after ensuring the data kwarg is set correctly
        super().__init__(**kwargs)
        state = self._state

        self.bio: Optional[str] = user['bio'] or None

        # We need to do a bit of a hack here because premium_since is massively overloaded
        guild_premium_since = getattr(self, 'premium_since', utils.MISSING)
        if guild_premium_since is not utils.MISSING:
            self.guild_premium_since = guild_premium_since

        self.premium_type: Optional[PremiumType] = (
            try_enum(PremiumType, data['premium_type']) if user.get('premium_type') else None
        )
        self.premium_since: Optional[datetime] = utils.parse_time(data['premium_since'])
        self.premium_guild_since: Optional[datetime] = utils.parse_time(data['premium_guild_since'])
        self.connections: List[PartialConnection] = [PartialConnection(d) for d in data['connected_accounts']]

        self.mutual_guilds: Optional[List[MutualGuild]] = (
            [MutualGuild(state=state, data=d) for d in data['mutual_guilds']] if 'mutual_guilds' in data else None
        )
        self.mutual_friends: Optional[List[User]] = self._parse_mutual_friends(mutual_friends)
        self._mutual_friends_count: Optional[int] = data.get('mutual_friends_count')

        application = data.get('application')
        self.application: Optional[ApplicationProfile] = ApplicationProfile(data=application) if application else None

    def _parse_mutual_friends(self, mutual_friends: List[PartialUserPayload]) -> Optional[List[User]]:
        if self.bot:
            # Bots don't have friends
            return []
        if mutual_friends is None:
            return

        state = self._state
        return [state.store_user(friend) for friend in mutual_friends]

    @property
    def mutual_friends_count(self) -> Optional[int]:
        """Optional[:class:`int`]: The number of mutual friends the user has with the client user."""
        if self.bot:
            # Bots don't have friends
            return 0
        if self._mutual_friends_count is not None:
            return self._mutual_friends_count
        if self.mutual_friends is not None:
            return len(self.mutual_friends)

    @property
    def premium(self) -> bool:
        """:class:`bool`: Indicates if the user is a premium user."""
        return self.premium_since is not None


class ApplicationProfile(Hashable):
    """Represents a Discord application profile.

    .. container:: operations

        .. describe:: x == y

            Checks if two applications are equal.

        .. describe:: x != y

            Checks if two applications are not equal.

        .. describe:: hash(x)

            Return the applications's hash.

    .. versionadded:: 2.0

    Attributes
    ------------
    id: :class:`int`
        The application's ID.
    verified: :class:`bool`
        Indicates if the application is verified.
    popular_application_command_ids: List[:class:`int`]
        A list of the IDs of the application's popular commands.
    primary_sku_id: Optional[:class:`int`]
        The application's primary SKU ID, if any.
        This can be an application's game SKU, subscription SKU, etc.
    custom_install_url: Optional[:class:`str`]
        The custom URL to use for authorizing the application, if specified.
    install_params: Optional[:class:`ApplicationInstallParams`]
        The parameters to use for authorizing the application, if specified.
    """

    __slots__ = (
        'id',
        'verified',
        'popular_application_command_ids',
        'primary_sku_id',
        '_flags',
        'custom_install_url',
        'install_params',
    )

    def __init__(self, data: ProfileApplicationPayload) -> None:
        self.id: int = int(data['id'])
        self.verified: bool = data.get('verified', False)
        self.popular_application_command_ids: List[int] = [int(id) for id in data.get('popular_application_command_ids', [])]
        self.primary_sku_id: Optional[int] = utils._get_as_snowflake(data, 'primary_sku_id')
        self._flags: int = data.get('flags', 0)

        params = data.get('install_params')
        self.custom_install_url: Optional[str] = data.get('custom_install_url')
        self.install_params: Optional[ApplicationInstallParams] = (
            ApplicationInstallParams.from_application(self, params) if params else None
        )

    def __repr__(self) -> str:
        return f'<ApplicationProfile id={self.id} verified={self.verified}>'

    @property
    def flags(self) -> ApplicationFlags:
        """:class:`ApplicationFlags`: The flags of this application."""
        return ApplicationFlags._from_value(self._flags)

    @property
    def install_url(self) -> Optional[str]:
        """:class:`str`: The URL to install the application."""
        return self.custom_install_url or self.install_params.url if self.install_params else None

    @property
    def primary_sku_url(self) -> Optional[str]:
        """:class:`str`: The URL to the primary SKU of the application, if any."""
        if self.primary_sku_id:
            return f'https://discord.com/store/skus/{self.primary_sku_id}/unknown'


class MutualGuild(Hashable):
    """Represents a mutual guild between a user and the client user.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

    .. versionadded:: 2.0

    Attributes
    ------------
    id: :class:`int`
        The guild's ID.
    nick: Optional[:class:`str`]
        The guild specific nickname of the user.
    """

    __slots__ = ('id', 'nick', '_state')

    def __init__(self, *, state: ConnectionState, data: MutualGuildPayload) -> None:
        self._state = state
        self.id: int = int(data['id'])
        self.nick: Optional[str] = data.get('nick')

    def __repr__(self) -> str:
        return f'<MutualGuild guild={self.guild!r} nick={self.nick!r}>'

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild that the user is mutual with."""
        return self._state._get_or_create_unavailable_guild(self.id)


class UserProfile(Profile, User):
    """Represents a Discord user's profile.

    This is a :class:`User` with extended attributes.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: Optional[:class:`ApplicationProfile`]
        The application profile of the user, if it is a bot.
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
    premium_type: Optional[:class:`PremiumType`]
        Specifies the type of premium a user has (i.e. Nitro, Nitro Classic, or Nitro Basic). Could be None if the user is not premium.
    premium_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies how long a user has been premium (had Nitro).
        ``None`` if the user is not a premium user.
    premium_guild_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies when a user first Nitro boosted a guild.
    connections: Optional[List[:class:`PartialConnection`]]
        The connected accounts that show up on the profile.
    mutual_guilds: Optional[List[:class:`MutualGuild`]]
        A list of guilds that you share with the user.
        ``None`` if you didn't fetch mutual guilds.
    mutual_friends: Optional[List[:class:`User`]]
        A list of friends that you share with the user.
        ``None`` if you didn't fetch mutual friends.
    """

    __slots__ = (
        'bio',
        'premium_type',
        'premium_since',
        'premium_guild_since',
        'connections',
        'mutual_guilds',
        'mutual_friends',
        '_mutual_friends_count',
        'application',
    )

    def __repr__(self) -> str:
        return f'<UserProfile id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot} system={self.system} premium={self.premium}>'

    @property
    def display_bio(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the user's display bio.

        This is the same as :attr:`bio` and is here for compatibility.
        """
        return self.bio


class MemberProfile(Profile, Member):
    """Represents a Discord member's profile.

    This is a :class:`Member` with extended attributes.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's name with the discriminator.

    .. versionadded:: 2.0

    Attributes
    -----------
    application: Optional[:class:`ApplicationProfile`]
        The application profile of the user, if it is a bot.
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
    guild_bio: Optional[:class:`str`]
        The user's "about me" field for the guild. Could be ``None``.
    guild_premium_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC when the member used their
        "Nitro boost" on the guild, if available. This could be ``None``.

        .. note::

            This is renamed from :attr:`Member.premium_since` because of name collisions.
    premium_type: Optional[:class:`PremiumType`]
        Specifies the type of premium a user has (i.e. Nitro, Nitro Classic, or Nitro Basic). Could be ``None`` if the user is not premium.
    premium_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies how long a user has been premium (had Nitro).
        ``None`` if the user is not a premium user.

        .. note::

            This is not the same as :attr:`Member.premium_since`. That is renamed to :attr:`guild_premium_since`.
    premium_guild_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies when a user first Nitro boosted a guild.
    connections: Optional[List[:class:`PartialConnection`]]
        The connected accounts that show up on the profile.
    mutual_guilds: Optional[List[:class:`MutualGuild`]]
        A list of guilds that you share with the user.
        ``None`` if you didn't fetch mutuals.
    mutual_friends: Optional[List[:class:`User`]]
        A list of friends that you share with the user.
        ``None`` if you didn't fetch mutuals.
    """

    __slots__ = (
        'bio',
        'guild_premium_since',
        'premium_type',
        'premium_since',
        'premium_guild_since',
        'connections',
        'mutual_guilds',
        'mutual_friends',
        '_mutual_friends_count',
        'application',
        '_banner',
        'guild_bio',
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        data = kwargs['data']
        member = data['guild_member']
        self._banner: Optional[str] = member.get('banner')
        self.guild_bio: Optional[str] = member.get('bio') or None

    def __repr__(self) -> str:
        return (
            f'<MemberProfile id={self._user.id} name={self._user.name!r} discriminator={self._user.discriminator!r}'
            f' bot={self._user.bot} nick={self.nick!r} premium={self.premium} guild={self.guild!r}>'
        )

    @property
    def display_banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the member's display banner.

        For regular members this is just their banner (if available), but
        if they have a guild specific banner then that
        is returned instead.
        """
        return self.guild_banner or self._user.banner

    @property
    def guild_banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the guild banner
        the member has. If unavailable, ``None`` is returned.
        """
        if self._banner is None:
            return None
        return Asset._from_guild_banner(self._state, self.guild.id, self.id, self._banner)

    @property
    def display_bio(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the member's display bio.

        For regular members this is just their bio (if available), but
        if they have a guild specific bio then that
        is returned instead.
        """
        return self.guild_bio or self.bio
