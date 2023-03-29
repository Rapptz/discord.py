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
from .user import Note, User

if TYPE_CHECKING:
    from datetime import datetime

    from .guild import Guild
    from .state import ConnectionState

__all__ = (
    'ApplicationProfile',
    'UserProfile',
    'MemberProfile',
)


class Profile:
    if TYPE_CHECKING:
        id: int
        application_id: Optional[int]
        _state: ConnectionState

    def __init__(self, **kwargs) -> None:  # TODO: type data
        data = kwargs.pop('data')
        user = data['user']

        if (member := data.get('guild_member')) is not None:
            member['user'] = user
            kwargs['data'] = member
        else:
            kwargs['data'] = user

        super().__init__(**kwargs)

        self.bio: Optional[str] = user.pop('bio', None) or None
        self.note: Note = Note(kwargs['state'], self.id, user=getattr(self, '_user', self))  # type: ignore

        # We need to do a bit of a hack here because premium_since is massively overloaded
        guild_premium_since = getattr(self, 'premium_since', utils.MISSING)
        if guild_premium_since is not utils.MISSING:
            self.guild_premium_since = guild_premium_since

        self.premium_type: Optional[PremiumType] = (
            try_enum(PremiumType, user.pop('premium_type')) if user.get('premium_type') else None
        )
        self.premium_since: Optional[datetime] = utils.parse_time(data['premium_since'])
        self.boosting_since: Optional[datetime] = utils.parse_time(data['premium_guild_since'])
        self.connections: List[PartialConnection] = [PartialConnection(d) for d in data['connected_accounts']]

        self.mutual_guilds: Optional[List[Guild]] = self._parse_mutual_guilds(data.get('mutual_guilds'))
        self.mutual_friends: Optional[List[User]] = self._parse_mutual_friends(data.get('mutual_friends'))

        application = data.get('application', {})
        self.application: Optional[ApplicationProfile] = ApplicationProfile(data=application) if application else None

    def _parse_mutual_guilds(self, mutual_guilds) -> Optional[List[Guild]]:
        if mutual_guilds is None:
            return

        state = self._state

        def get_guild(guild):
            return state._get_or_create_unavailable_guild(int(guild['id']))

        return list(map(get_guild, mutual_guilds))

    def _parse_mutual_friends(self, mutual_friends) -> Optional[List[User]]:
        if mutual_friends is None:
            return

        state = self._state
        return [state.store_user(friend) for friend in mutual_friends]

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

    def __init__(self, data: dict) -> None:
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
        The application profile of the user, if a bot.
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
    premium_type: Optional[:class:`PremiumType`]
        Specifies the type of premium a user has (i.e. Nitro, Nitro Classic, or Nitro Basic). Could be None if the user is not premium.
    premium_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies how long a user has been premium (had Nitro).
        ``None`` if the user is not a premium user.
    boosting_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies when a user first boosted a guild.
    connections: Optional[List[:class:`PartialConnection`]]
        The connected accounts that show up on the profile.
    note: :class:`Note`
        Represents the note on the profile.
    mutual_guilds: Optional[List[:class:`Guild`]]
        A list of guilds that you share with the user.
        ``None`` if you didn't fetch mutuals.
    mutual_friends: Optional[List[:class:`User`]]
        A list of friends that you share with the user.
        ``None`` if you didn't fetch mutuals.
    """

    def __repr__(self) -> str:
        return f'<UserProfile id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot} system={self.system} premium={self.premium}>'


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
        The application profile of the user, if a bot.
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
    boosting_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies when a user first boosted any guild.
    connections: Optional[List[:class:`PartialConnection`]]
        The connected accounts that show up on the profile.
    note: :class:`Note`
        Represents the note on the profile.
    mutual_guilds: Optional[List[:class:`Guild`]]
        A list of guilds that you share with the user.
        ``None`` if you didn't fetch mutuals.
    mutual_friends: Optional[List[:class:`User`]]
        A list of friends that you share with the user.
        ``None`` if you didn't fetch mutuals.
    """

    def __init__(self, *, state: ConnectionState, data: dict, guild: Guild):
        super().__init__(state=state, guild=guild, data=data)
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
