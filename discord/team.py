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
from .asset import Asset
from .enums import TeamMembershipState, try_enum
from .mixins import Hashable
from .user import BaseUser

from typing import TYPE_CHECKING, Optional, overload, List, Union

if TYPE_CHECKING:
    from .abc import Snowflake
    from .state import ConnectionState

    from .types.team import (
        Team as TeamPayload,
        TeamMember as TeamMemberPayload,
    )
    from .types.user import User as UserPayload

MISSING = utils.MISSING

__all__ = (
    'Team',
    'TeamMember',
)


class Team(Hashable):
    """Represents an application team.

    .. container:: operations

        .. describe:: x == y

            Checks if two teams are equal.

        .. describe:: x != y

            Checks if two teams are not equal.

        .. describe:: hash(x)

            Return the team's hash.

        .. describe:: str(x)

            Returns the team's name.

    Attributes
    -------------
    id: :class:`int`
        The team ID.
    name: :class:`str`
        The team name.
    owner_id: :class:`int`
        The team's owner ID.
    members: List[:class:`TeamMember`]
        A list of the members in the team.
        A call to :meth:`fetch_members` may be required to populate this past the owner.
    """

    if TYPE_CHECKING:
        owner_id: int
        members: List[TeamMember]

    __slots__ = ('_state', 'id', 'name', '_icon', 'owner_id', 'members')

    def __init__(self, state: ConnectionState, data: TeamPayload):
        self._state: ConnectionState = state
        self._update(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

    def __str__(self) -> str:
        return self.name

    def _update(self, data: TeamPayload):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data['icon']
        self.owner_id = owner_id = int(data['owner_user_id'])
        self.members = members = [TeamMember(self, self._state, member) for member in data.get('members', [])]
        if owner_id not in members and owner_id == self._state.self_id:  # Discord moment
            user: UserPayload = self._state.user._to_minimal_user_json()  # type: ignore
            member: TeamMemberPayload = {
                'user': user,
                'team_id': self.id,
                'membership_state': 2,
                'permissions': ['*'],
            }
            members.append(TeamMember(self, self._state, member))

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

    async def edit(
        self,
        *,
        name: str = MISSING,
        icon: Optional[bytes] = MISSING,
        owner: Snowflake = MISSING,
    ) -> None:
        """|coro|

        Edits the team.

        Parameters
        -----------
        name: :class:`str`
            The name of the team.
        icon: Optional[:class:`bytes`]
            The icon of the team.
        owner: :class:`~abc.Snowflake`
            The team's owner.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the team.
        HTTPException
            Editing the team failed.
        """
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if icon is not MISSING:
            if icon is not None:
                payload['icon'] = utils._bytes_to_base64_data(icon)
            else:
                payload['icon'] = ''
        if owner is not MISSING:
            payload['owner_user_id'] = owner.id

        data = await self._state.http.edit_team(self.id, payload)
        self._update(data)

    async def fetch_members(self) -> List[TeamMember]:
        """|coro|

        Retrieves the team's members.

        Returns
        --------
        List[:class:`TeamMember`]
            The team's members.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch the team's members.
        HTTPException
            Retrieving the team members failed.
        """
        data = await self._state.http.get_team_members(self.id)
        members = [TeamMember(self, self._state, member) for member in data]
        self.members = members
        return members

    @overload
    async def invite_member(self, user: BaseUser, /) -> TeamMember:
        ...

    @overload
    async def invite_member(self, user: str, /) -> TeamMember:
        ...

    @overload
    async def invite_member(self, username: str, discriminator: str, /) -> TeamMember:
        ...

    async def invite_member(self, *args: Union[BaseUser, str]) -> TeamMember:
        """|coro|

        Invites a member to the team.

        This function can be used in multiple ways.

        .. code-block:: python

            # Passing a user object:
            await team.invite_member(user)

            # Passing a stringified user:
            await team.invite_member('Jake#0001')

            # Passing a username and discriminator:
            await team.invite_member('Jake', '0001')

        Parameters
        -----------
        user: Union[:class:`User`, :class:`str`]
            The user to invite.
        username: :class:`str`
            The username of the user to invite.
        discriminator: :class:`str`
            The discriminator of the user to invite.

        Raises
        -------
        Forbidden
            You do not have permissions to invite the user.
        HTTPException
            Inviting the user failed.
        TypeError
            More than 2 parameters or less than 1 parameter were passed.

        Returns
        -------
        :class:`.TeamMember`
            The new member.
        """
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, BaseUser):
                user = str(user)
            username, discrim = user.split('#')
        elif len(args) == 2:
            username, discrim = args  # type: ignore
        else:
            raise TypeError(f'invite_member() takes 1 or 2 arguments but {len(args)} were given')

        state = self._state
        data = await state.http.invite_team_member(self.id, username, discrim)
        member = TeamMember(self, state, data)
        self.members.append(member)
        return member

    async def delete(self) -> None:
        """|coro|

        Deletes the team.

        Raises
        -------
        Forbidden
            You do not have permissions to delete the team.
        HTTPException
            Deleting the team failed.
        """
        await self._state.http.delete_team(self.id)


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

            Returns the team member's name with discriminator.

    .. versionadded:: 1.3

    Attributes
    -------------
    team: :class:`Team`
        The team that the member is from.
    membership_state: :class:`TeamMembershipState`
        The membership state of the member (i.e. invited or accepted)
    """

    __slots__ = ('team', 'membership_state', 'permissions')

    def __init__(self, team: Team, state: ConnectionState, data: TeamMemberPayload):
        self.team: Team = team
        self.membership_state: TeamMembershipState = try_enum(TeamMembershipState, data['membership_state'])
        self.permissions: List[str] = data['permissions']
        super().__init__(state=state, data=data['user'])

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id} name={self.name!r} '
            f'discriminator={self.discriminator!r} membership_state={self.membership_state!r}>'
        )

    async def remove(self) -> None:
        """|coro|

        Removes the member from the team.

        Raises
        -------
        Forbidden
            You do not have permissions to remove the member.
        HTTPException
            Removing the member failed.
        """
        await self._state.http.remove_team_member(self.team.id, self.id)
