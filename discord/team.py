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

from datetime import datetime
from typing import TYPE_CHECKING, AsyncIterator, List, Optional, Union, overload

from . import utils
from .asset import Asset
from .enums import ApplicationMembershipState, PayoutAccountStatus, PayoutReportType, PayoutStatus, try_enum
from .metadata import Metadata
from .mixins import Hashable
from .object import Object
from .user import User, _UserTag

if TYPE_CHECKING:
    from datetime import date

    from .abc import Snowflake, SnowflakeTime
    from .application import Application, Company
    from .state import ConnectionState
    from .types.team import Team as TeamPayload, TeamMember as TeamMemberPayload, TeamPayout as TeamPayoutPayload
    from .types.user import PartialUser as PartialUserPayload

__all__ = (
    'Team',
    'TeamMember',
    'TeamPayout',
)

MISSING = utils.MISSING


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

    .. versionadded:: 2.0

    Attributes
    -------------
    id: :class:`int`
        The team ID.
    name: :class:`str`
        The team name.
    owner_id: :class:`int`
        The team's owner ID.
    members: List[:class:`TeamMember`]
        The team's members.

        .. note::

            In almost all cases, a call to :meth:`fetch_members`
            is required to populate this list past (sometimes) the owner.
    payout_account_status: Optional[:class:`PayoutAccountStatus`]
        The team's payout account status, if any and available.
    stripe_connect_account_id: Optional[:class:`str`]
        The account ID representing the Stripe Connect account the
        team's payout account is linked to, if any and available.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        '_icon',
        'owner_id',
        'members',
        'payout_account_status',
        'stripe_connect_account_id',
    )

    def __init__(self, state: ConnectionState, data: TeamPayload):
        self._state: ConnectionState = state

        self.members: List[TeamMember] = []
        self.payout_account_status: Optional[PayoutAccountStatus] = None
        self.stripe_connect_account_id: Optional[str] = None
        self._update(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

    def __str__(self) -> str:
        return self.name

    def _update(self, data: TeamPayload):
        state = self._state

        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data['icon']
        self.owner_id = owner_id = int(data['owner_user_id'])

        if 'members' in data:
            self.members = [TeamMember(self, state=state, data=member) for member in data.get('members', [])]

        if not self.owner:
            owner = self._state.get_user(owner_id)
            if owner:
                user: PartialUserPayload = owner._to_minimal_user_json()
                member: TeamMemberPayload = {
                    'user': user,
                    'team_id': self.id,
                    'membership_state': 2,
                    'permissions': ['*'],
                }
                self.members.append(TeamMember(self, self._state, member))

        if 'payout_account_status' in data:
            self.payout_account_status = try_enum(PayoutAccountStatus, data.get('payout_account_status'))
        if 'stripe_connect_account_id' in data:
            self.stripe_connect_account_id = data.get('stripe_connect_account_id')

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Retrieves the team's icon asset, if any."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='team')

    @property
    def default_icon(self) -> Asset:
        """:class:`Asset`: Returns the default icon for the team. This is calculated by the team's ID."""
        return Asset._from_default_avatar(self._state, int(self.id) % 5)

    @property
    def display_icon(self) -> Asset:
        """:class:`Asset`: Returns the team's display icon.

        For regular teams this is just their default icon or uploaded icon.
        """
        return self.icon or self.default_icon

    @property
    def owner(self) -> Optional[TeamMember]:
        """Optional[:class:`TeamMember`]: The team's owner, if available."""
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

        All parameters are optional.

        Parameters
        -----------
        name: :class:`str`
            The name of the team.
        icon: Optional[:class:`bytes`]
            The icon of the team.
        owner: :class:`User`
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

    async def applications(self) -> List[Application]:
        """|coro|

        Retrieves the team's applications.

        Returns
        --------
        List[:class:`TeamMember`]
            The team's applications.

        Raises
        -------
        Forbidden
            You do not have permissions to fetch the team's applications.
        HTTPException
            Retrieving the team applications failed.
        """
        from .application import Application

        state = self._state
        data = await state.http.get_team_applications(self.id)
        return [Application(state=state, data=app, team=self) for app in data]

    async def fetch_members(self) -> List[TeamMember]:
        """|coro|

        Retrieves and caches the team's members.

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
    async def invite_member(self, user: _UserTag, /) -> TeamMember:
        ...

    @overload
    async def invite_member(self, user: str, /) -> TeamMember:
        ...

    @overload
    async def invite_member(self, username: str, discriminator: str, /) -> TeamMember:
        ...

    async def invite_member(self, *args: Union[_UserTag, str]) -> TeamMember:
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
        :class:`TeamMember`
            The new member.
        """
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, _UserTag):
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

    async def create_company(self, name: str, /) -> Company:
        """|coro|

        Creates a company for the team.

        Parameters
        -----------
        name: :class:`str`
            The name of the company.

        Raises
        -------
        Forbidden
            You do not have permissions to create a company.
        HTTPException
            Creating the company failed.

        Returns
        -------
        :class:`.Company`
            The created company.
        """
        from .application import Company

        state = self._state
        data = await state.http.create_team_company(self.id, name)
        return Company(data=data)

    async def payouts(
        self,
        *,
        limit: Optional[int] = 96,
        before: Optional[SnowflakeTime] = None,
    ) -> AsyncIterator[TeamPayout]:
        """Returns an :term:`asynchronous iterator` that enables receiving your team payouts.

        .. versionadded:: 2.0

        Examples
        ---------

        Usage ::

            total = 0
            async for payout in team.payouts():
                if payout.period_end:
                    total += payout.amount

        Flattening into a list: ::

            payments = [payout async for payout in team.payouts(limit=123)]
            # payments is now a list of TeamPayout...

        All parameters are optional.

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of payouts to retrieve.
            If ``None``, retrieves every payout you have. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve payments before this date or payout.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

        Raises
        ------
        HTTPException
            The request to get team payouts failed.

        Yields
        -------
        :class:`~discord.TeamPayout`
            The payout received.
        """

        async def strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self._state.http.get_team_payouts(self.id, limit=retrieve, before=before_id)

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[-1]['id']))

            return data, before, limit

        if isinstance(before, datetime):
            before = Object(id=utils.time_snowflake(before, high=False))

        while True:
            retrieve = min(96 if limit is None else limit, 100)
            if retrieve < 1:
                return

            data, before, limit = await strategy(retrieve, before, limit)

            # Terminate loop on next iteration; there's no data left after this
            if len(data) < 96:
                limit = 0

            for payout in data:
                yield TeamPayout(data=payout, team=self)

    async def leave(self) -> None:
        """|coro|

        Leaves the team.

        .. note::

            You cannot leave a team that you own, you must delete it instead
            via :meth:`delete`.

        Raises
        -------
        Forbidden
            You do not have permissions to leave the team.
        HTTPException
            Leaving the team failed.
        """
        await self._state.http.remove_team_member(self.id, self._state.self_id)  # type: ignore

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


class TeamMember(User):
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
    membership_state: :class:`ApplicationMembershipState`
        The membership state of the member (i.e. invited or accepted)
    permissions: List[:class:`str`]
        The permissions of the team member. This is always "*".
    """

    __slots__ = ('team', 'membership_state', 'permissions')

    def __init__(self, team: Team, state: ConnectionState, data: TeamMemberPayload):
        self.team: Team = team
        self.membership_state: ApplicationMembershipState = try_enum(ApplicationMembershipState, data['membership_state'])
        self.permissions: List[str] = data.get('permissions', ['*'])
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


class TeamPayout(Hashable):
    """Represents a team payout.

    .. container:: operations

        .. describe:: x == y

            Checks if two team payouts are equal.

        .. describe:: x != y

            Checks if two team payouts are not equal.

        .. describe:: hash(x)

            Return the team payout's hash.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The ID of the payout.
    user_id: :class:`int`
        The ID of the user who is to be receiving the payout.
    status: :class:`PayoutStatus`
        The status of the payout.
    amount: :class:`int`
        The amount of the payout.
    period_start: :class:`datetime.date`
        The start of the payout period.
    period_end: Optional[:class:`datetime.date`]
        The end of the payout period, if ended.
    payout_date: Optional[:class:`datetime.date`]
        The date the payout was made, if made.
    tipalti_submission_response: Optional[:class:`Metadata`]
        The latest response from Tipalti, if exists.
    """

    def __init__(self, *, data: TeamPayoutPayload, team: Team):
        self.team: Team = team

        self.id: int = int(data['id'])
        self.user_id: int = int(data['user_id'])
        self.status: PayoutStatus = try_enum(PayoutStatus, data['status'])
        self.amount: int = data['amount']
        self.period_start: date = utils.parse_date(data['period_start'])
        self.period_end: Optional[date] = utils.parse_date(data.get('period_end'))
        self.payout_date: Optional[date] = utils.parse_date(data.get('payout_date'))
        self.tipalti_submission_response: Optional[Metadata] = (
            Metadata(data['latest_tipalti_submission_response']) if 'latest_tipalti_submission_response' in data else None
        )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} status={self.status!r}>'

    async def report(self, type: PayoutReportType) -> bytes:
        """|coro|

        Returns the report for the payout in CSV format.

        Parameters
        -----------
        type: :class:`PayoutReportType`
            The type of report to get the URL for.

        Raises
        -------
        Forbidden
            You do not have permissions to get the report URL.
        HTTPException
            Getting the report URL failed.

        Returns
        -------
        :class:`bytes`
            The report content.
        """
        return await self.team._state.http.get_team_payout_report(self.team.id, self.id, str(type))
