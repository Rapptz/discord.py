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
from typing import Any, Dict, Optional, TYPE_CHECKING, overload, Type, Tuple
from .utils import _get_as_snowflake, parse_time, MISSING
from .user import User
from .errors import InvalidArgument
from .enums import try_enum, ExpireBehaviour

__all__ = (
    'IntegrationAccount',
    'IntegrationApplication',
    'Integration',
    'StreamIntegration',
    'BotIntegration',
)

if TYPE_CHECKING:
    from .types.integration import (
        IntegrationAccount as IntegrationAccountPayload,
        Integration as IntegrationPayload,
        StreamIntegration as StreamIntegrationPayload,
        BotIntegration as BotIntegrationPayload,
        IntegrationType,
        IntegrationApplication as IntegrationApplicationPayload,
    )
    from .guild import Guild
    from .role import Role


class IntegrationAccount:
    """Represents an integration account.

    .. versionadded:: 1.4

    Attributes
    -----------
    id: :class:`str`
        The account ID.
    name: :class:`str`
        The account name.
    """

    __slots__ = ('id', 'name')

    def __init__(self, data: IntegrationAccountPayload) -> None:
        self.id: str = data['id']
        self.name: str = data['name']

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
    account: :class:`IntegrationAccount`
        The account linked to this integration.
    user: :class:`User`
        The user that added this integration.
    """

    __slots__ = (
        'guild',
        'id',
        '_state',
        'type',
        'name',
        'account',
        'user',
        'enabled',
    )

    def __init__(self, *, data: IntegrationPayload, guild: Guild) -> None:
        self.guild = guild
        self._state = guild._state
        self._from_data(data)

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id} name={self.name!r}>"

    def _from_data(self, data: IntegrationPayload) -> None:
        self.id: int = int(data['id'])
        self.type: IntegrationType = data['type']
        self.name: str = data['name']
        self.account: IntegrationAccount = IntegrationAccount(data['account'])

        user = data.get('user')
        self.user = User(state=self._state, data=user) if user else None
        self.enabled: bool = data['enabled']

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the integration.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        Parameters
        -----------
        reason: :class:`str`
            The reason the integration was deleted. Shows up on the audit log.

            .. versionadded:: 2.0

        Raises
        -------
        Forbidden
            You do not have permission to delete the integration.
        HTTPException
            Deleting the integration failed.
        """
        await self._state.http.delete_integration(self.guild.id, self.id, reason=reason)


class StreamIntegration(Integration):
    """Represents a stream integration for Twitch or YouTube.

    .. versionadded:: 2.0

    Attributes
    ----------
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
        'revoked',
        'expire_behaviour',
        'expire_grace_period',
        'synced_at',
        '_role_id',
        'syncing',
        'enable_emoticons',
        'subscriber_count',
    )

    def _from_data(self, data: StreamIntegrationPayload) -> None:
        super()._from_data(data)
        self.revoked: bool = data['revoked']
        self.expire_behaviour: ExpireBehaviour = try_enum(ExpireBehaviour, data['expire_behavior'])
        self.expire_grace_period: int = data['expire_grace_period']
        self.synced_at: datetime.datetime = parse_time(data['synced_at'])
        self._role_id: Optional[int] = _get_as_snowflake(data, 'role_id')
        self.syncing: bool = data['syncing']
        self.enable_emoticons: bool = data['enable_emoticons']
        self.subscriber_count: int = data['subscriber_count']

    @property
    def expire_behavior(self) -> ExpireBehaviour:
        """:class:`ExpireBehaviour`: An alias for :attr:`expire_behaviour`."""
        return self.expire_behaviour

    @property
    def role(self) -> Optional[Role]:
        """Optional[:class:`Role`] The role which the integration uses for subscribers."""
        return self.guild.get_role(self._role_id)  # type: ignore

    async def edit(
        self,
        *,
        expire_behaviour: ExpireBehaviour = MISSING,
        expire_grace_period: int = MISSING,
        enable_emoticons: bool = MISSING,
    ) -> None:
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
        payload: Dict[str, Any] = {}
        if expire_behaviour is not MISSING:
            if not isinstance(expire_behaviour, ExpireBehaviour):
                raise InvalidArgument('expire_behaviour field must be of type ExpireBehaviour')

            payload['expire_behavior'] = expire_behaviour.value

        if expire_grace_period is not MISSING:
            payload['expire_grace_period'] = expire_grace_period

        if enable_emoticons is not MISSING:
            payload['enable_emoticons'] = enable_emoticons

        # This endpoint is undocumented.
        # Unsure if it returns the data or not as a result
        await self._state.http.edit_integration(self.guild.id, self.id, **payload)

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


class IntegrationApplication:
    """Represents an application for a bot integration.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The ID for this application.
    name: :class:`str`
        The application's name.
    icon: Optional[:class:`str`]
        The application's icon hash.
    description: :class:`str`
        The application's description. Can be an empty string.
    summary: :class:`str`
        The summary of the application. Can be an empty string.
    user: Optional[:class:`User`]
        The bot user on this application.
    """

    __slots__ = (
        'id',
        'name',
        'icon',
        'description',
        'summary',
        'user',
    )

    def __init__(self, *, data: IntegrationApplicationPayload, state):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.icon: Optional[str] = data['icon']
        self.description: str = data['description']
        self.summary: str = data['summary']
        user = data.get('bot')
        self.user: Optional[User] = User(state=state, data=user) if user else None


class BotIntegration(Integration):
    """Represents a bot integration on discord.

    .. versionadded:: 2.0

    Attributes
    ----------
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
    user: :class:`User`
        The user that added this integration.
    account: :class:`IntegrationAccount`
        The integration account information.
    application: :class:`IntegrationApplication`
        The application tied to this integration.
    """

    __slots__ = ('application',)

    def _from_data(self, data: BotIntegrationPayload) -> None:
        super()._from_data(data)
        self.application = IntegrationApplication(data=data['application'], state=self._state)


def _integration_factory(value: str) -> Tuple[Type[Integration], str]:
    if value == 'discord':
        return BotIntegration, value
    elif value in ('twitch', 'youtube'):
        return StreamIntegration, value
    else:
        return Integration, value
