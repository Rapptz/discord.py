# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from . import utils
from .user import BaseUser
from .asset import Asset
from .enums import TeamMembershipState, try_enum

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
    icon: Optional[:class:`str`]
        The icon hash, if it exists.
    owner_id: :class:`int`
        The team's owner ID.
    members: List[:class:`TeamMember`]
        A list of the members in the team
    """
    __slots__ = ('_state', 'id', 'name', 'icon', 'owner_id', 'members')

    def __init__(self, state, data):
        self._state = state

        self.id = utils._get_as_snowflake(data, 'id')
        self.name = data['name']
        self.icon = data['icon']
        self.owner_id = utils._get_as_snowflake(data, 'owner_user_id')
        self.members = [TeamMember(self, self._state, member) for member in data['members']]

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name}>'.format(self)

    @property
    def icon_url(self):
        """:class:`.Asset`: Retrieves the team's icon asset."""
        return Asset._from_icon(self._state, self, 'team')

    @property
    def owner(self):
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

            Returns the team member's name with discriminator.

    Attributes
    -------------
    name: :class:`str`
        The team member's username.
    id: :class:`int`
        The team member's unique ID.
    discriminator: :class:`str`
        The team member's discriminator. This is given when the username has conflicts.
    avatar: Optional[:class:`str`]
        The avatar hash the team member has. Could be None.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    team: :class:`Team`
        The team that the member is from.
    membership_state: :class:`TeamMembershipState`
        The membership state of the member (e.g. invited or accepted)
    """
    __slots__ = BaseUser.__slots__ + ('team', 'membership_state', 'permissions')

    def __init__(self, team, state, data):
        self.team = team
        self.membership_state = try_enum(TeamMembershipState, data['membership_state'])
        self.permissions = data['permissions']
        super().__init__(state=state, data=data['user'])

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r} ' \
               'discriminator={0.discriminator!r} membership_state={0.membership_state!r}>'.format(self)
