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

from . import utils
from .user import BaseUser
from .asset import Asset
from .enums import TeamMemberRole, TeamMembershipState, try_enum

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from .state import ConnectionState

    from .types.team import (
        Team as TeamPayload,
        TeamMember as TeamMemberPayload,
    )

__all__ = (
    'Team',
    'TeamMember',
)


class Team:
    """Represents an application team for a bot provided by Discord.

    Attributes
    -------------
    id: :class:`int`
        The team ID.
    name: :class:`str`
        The team name
    owner_id: :class:`int`
        The team's owner ID.
    members: List[:class:`TeamMember`]
        A list of the members in the team

        .. versionadded:: 1.3
    """

    __slots__ = ('_state', 'id', 'name', '_icon', 'owner_id', 'members')

    def __init__(self, state: ConnectionState, data: TeamPayload) -> None:
        self._state: ConnectionState = state

        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data['icon']
        self.owner_id: Optional[int] = utils._get_as_snowflake(data, 'owner_user_id')
        self.members: List[TeamMember] = [TeamMember(self, self._state, member) for member in data['members']]

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the team's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='team')

    @property
    def owner(self) -> Optional[TeamMember]:
        """Optional[:class:`TeamMember`]: The team's owner."""
        return utils.get(self.members, id=self.owner_id)


class TeamMember(BaseUser):
    """Represents a team member in a team.

    .. container:: operations

        .. describe:: x == y

            Checks if two team members are equal.

        .. describe:: x != y

            Checks if two team members are not equal.

        .. describe:: hash(x)

            Return the team member's hash.

        .. describe:: str(x)

            Returns the team member's handle (e.g. ``name`` or ``name#discriminator``).

    .. versionadded:: 1.3

    Attributes
    -------------
    name: :class:`str`
        The team member's username.
    id: :class:`int`
        The team member's unique ID.
    discriminator: :class:`str`
        The team member's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The team member's global nickname, taking precedence over the username in display.

        .. versionadded:: 2.3
    bot: :class:`bool`
        Specifies if the user is a bot account.
    team: :class:`Team`
        The team that the member is from.
    membership_state: :class:`TeamMembershipState`
        The membership state of the member (e.g. invited or accepted)
    role: :class:`TeamMemberRole`
        The role of the member within the team.

        .. versionadded:: 2.4
    """

    __slots__ = ('team', 'membership_state', 'permissions', 'role')

    def __init__(self, team: Team, state: ConnectionState, data: TeamMemberPayload) -> None:
        self.team: Team = team
        self.membership_state: TeamMembershipState = try_enum(TeamMembershipState, data['membership_state'])
        self.permissions: List[str] = data.get('permissions', [])
        self.role: TeamMemberRole = try_enum(TeamMemberRole, data['role'])
        super().__init__(state=state, data=data['user'])

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'global_name={self.global_name!r} membership_state={self.membership_state!r}>'
        )
