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

import datetime
from typing import Optional, TYPE_CHECKING, overload
from .utils import _get_as_snowflake, get, parse_time
from .user import User
from .errors import InvalidArgument
from .enums import try_enum, ExpireBehaviour

__all__ = (
    'IntegrationAccount',
    'Integration',
)

if TYPE_CHECKING:
    from .types.integration import (
        IntegrationAccount as IntegrationAccountPayload,
        Integration as IntegrationPayload,
    )
    from .guild import Guild


class IntegrationAccount:
    """Represents an integration account.

    .. versionadded:: 1.4

    Attributes
    -----------
    id: :class:`int`
        The account ID.
    name: :class:`str`
        The account name.
    """

    __slots__ = ('id', 'name')

    def __init__(self, data: IntegrationAccountPayload) -> None:
        self.id: Optional[int] = _get_as_snowflake(data, 'id')
        self.name: str = data.pop('name')

    def __repr__(self) -> str:
        return f'<IntegrationAccount id={self.id} name={self.name!r}>'


class Integration:
    """Represents a guild integration.

    .. versionadded:: 1.4

    Attributes
    -----------
    id: :class:`int`
        The integration ID.
    name: :class:`str`
        The integration name.
    guild: :class:`Guild`
        The guild of the integration.
    type: :class:`str`
        The integration type (i.e. Twitch).
    enabled: :class:`bool`
        Whether the integration is currently enabled.
    syncing: :class:`bool`
        Where the integration is currently syncing.
    role: :class:`Role`
        The role which the integration uses for subscribers.
    enable_emoticons: Optional[:class:`bool`]
        Whether emoticons should be synced for this integration (currently twitch only).
    expire_behaviour: :class:`ExpireBehaviour`
        The behaviour of expiring subscribers. Aliased to ``expire_behavior`` as well.
    expire_grace_period: :class:`int`
        The grace period (in days) for expiring subscribers.
    user: :class:`User`
        The user for the integration.
    account: :class:`IntegrationAccount`
        The integration account information.
    synced_at: :class:`datetime.datetime`
        An aware UTC datetime representing when the integration was last synced.
    """

    __slots__ = (
        'id',
        '_state',
        'guild',
        'name',
        'enabled',
        'type',
        'syncing',
        'role',
        'expire_behaviour',
        'expire_behavior',
        'expire_grace_period',
        'synced_at',
        'user',
        'account',
        'enable_emoticons',
        '_role_id',
    )

    def __init__(self, *, data: IntegrationPayload, guild: Guild) -> None:
        self.guild = guild
        self._state = guild._state
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<Integration id={self.id} name={self.name!r} type={self.type!r}>'

    def _from_data(self, integ: IntegrationPayload):
        self.id = _get_as_snowflake(integ, 'id')
        self.name = integ['name']
        self.type = integ['type']
        self.enabled = integ['enabled']
        self.syncing = integ['syncing']
        self._role_id = _get_as_snowflake(integ, 'role_id')
        self.role = get(self.guild.roles, id=self._role_id)
        self.enable_emoticons = integ.get('enable_emoticons')
        self.expire_behaviour = try_enum(ExpireBehaviour, integ['expire_behavior'])
        self.expire_behavior = self.expire_behaviour
        self.expire_grace_period = integ['expire_grace_period']
        self.synced_at = parse_time(integ['synced_at'])

        self.user = User(state=self._state, data=integ['user'])
        self.account = IntegrationAccount(integ['account'])

    @overload
    async def edit(
        self,
        *,
        expire_behaviour: Optional[ExpireBehaviour] = ...,
        expire_grace_period: Optional[int] = ...,
        enable_emoticons: Optional[bool] = ...,
    ) -> None:
        ...

    @overload
    async def edit(self, **fields) -> None:
        ...

    async def edit(self, **fields) -> None:
        """|coro|

        Edits the integration.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Parameters
        -----------
        expire_behaviour: :class:`ExpireBehaviour`
            The behaviour when an integration subscription lapses. Aliased to ``expire_behavior`` as well.
        expire_grace_period: :class:`int`
            The period (in days) where the integration will ignore lapsed subscriptions.
        enable_emoticons: :class:`bool`
            Where emoticons should be synced for this integration (currently twitch only).

        Raises
        -------
        Forbidden
            You do not have permission to edit the integration.
        HTTPException
            Editing the guild failed.
        InvalidArgument
            ``expire_behaviour`` did not receive a :class:`ExpireBehaviour`.
        """
        try:
            expire_behaviour = fields['expire_behaviour']
        except KeyError:
            expire_behaviour = fields.get('expire_behavior', self.expire_behaviour)

        if not isinstance(expire_behaviour, ExpireBehaviour):
            raise InvalidArgument('expire_behaviour field must be of type ExpireBehaviour')

        expire_grace_period = fields.get('expire_grace_period', self.expire_grace_period)

        payload = {
            'expire_behavior': expire_behaviour.value,
            'expire_grace_period': expire_grace_period,
        }

        enable_emoticons = fields.get('enable_emoticons')

        if enable_emoticons is not None:
            payload['enable_emoticons'] = enable_emoticons

        await self._state.http.edit_integration(self.guild.id, self.id, **payload)

        self.expire_behaviour = expire_behaviour
        self.expire_behavior = self.expire_behaviour
        self.expire_grace_period = expire_grace_period
        self.enable_emoticons = enable_emoticons

    async def sync(self) -> None:
        """|coro|

        Syncs the integration.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Raises
        -------
        Forbidden
            You do not have permission to sync the integration.
        HTTPException
            Syncing the integration failed.
        """
        await self._state.http.sync_integration(self.guild.id, self.id)
        self.synced_at = datetime.datetime.now(datetime.timezone.utc)

    async def delete(self) -> None:
        """|coro|

        Deletes the integration.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Raises
        -------
        Forbidden
            You do not have permission to delete the integration.
        HTTPException
            Deleting the integration failed.
        """
        await self._state.http.delete_integration(self.guild.id, self.id)
