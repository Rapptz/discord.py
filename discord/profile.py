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

from typing import List, Optional, TYPE_CHECKING

from .connections import PartialConnection
from .flags import PrivateUserFlags
from .member import Member
from .user import Note, User
from .utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .guild import Guild
    from .state import ConnectionState


class Profile:
    """Represents a Discord profile.

    Attributes
    ----------
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
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

    if TYPE_CHECKING:
        id: int
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

        self._flags: int = user.pop('flags', 0)
        self.bio: Optional[str] = user.pop('bio') or None
        self.note: Note = Note(kwargs['state'], self.id, user=self)

        self.premium_since: Optional[datetime] = parse_time(data['premium_since'])
        self.boosting_since: Optional[datetime] = parse_time(data['premium_guild_since'])
        self.connections: List[PartialConnection] = [PartialConnection(d) for d in data['connected_accounts']]  # TODO: parse these

        self.mutual_guilds: Optional[List[Guild]] = self._parse_mutual_guilds(data.get('mutual_guilds'))
        self.mutual_friends: Optional[List[User]] = self._parse_mutual_friends(data.get('mutual_friends'))

    def _parse_mutual_guilds(self, mutual_guilds) -> Optional[List[Guild]]:
        if mutual_guilds is None:
            return

        state = self._state

        def get_guild(guild) -> Optional[Guild]:
            return state._get_guild(int(guild['id']))

        # Potential data loss if the gateway is not connected
        return list(filter(None, map(get_guild, mutual_guilds)))

    def _parse_mutual_friends(self, mutual_friends) -> Optional[List[User]]:
        if mutual_friends is None:
            return

        state = self._state
        return [state.store_user(friend) for friend in mutual_friends]

    @property
    def flags(self) -> PrivateUserFlags:
        """:class:`PrivateUserFlags`: The flags the user has."""
        return PrivateUserFlags._from_value(self._flags)

    @property
    def premium(self) -> bool:
        """:class:`bool`: Indicates if the user is a premium user.

        There is an alias for this named :attr:`nitro`.
        """
        return self.premium_since is not None

    @property
    def nitro(self) -> bool:
        """:class:`bool`: Indicates if the user is a premium user.

        This is an alias for :attr:`premium`.
        """
        return self.premium


class UserProfile(Profile, User):
    def __repr__(self) -> str:
        return f'<UserProfile id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot} system={self.system} premium={self.premium}>'


class MemberProfile(Profile, Member):
    def __repr__(self) -> str:
        return (
            f'<MemberProfile id={self._user.id} name={self._user.name!r} discriminator={self._user.discriminator!r}'
            f' bot={self._user.bot} nick={self.nick!r} premium={self.premium} guild={self.guild!r}>'
        )
