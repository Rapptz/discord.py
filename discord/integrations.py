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

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Type

from .enums import ExpireBehaviour, try_enum
from .user import User
from .utils import MISSING, _get_as_snowflake, parse_time, utcnow

__all__ = (
    'IntegrationAccount',
    'Integration',
    'StreamIntegration',
    'BotIntegration',
)

if TYPE_CHECKING:
    from datetime import datetime

    from .application import IntegrationApplication
    from .guild import Guild
    from .role import Role
    from .state import ConnectionState
    from .types.integration import (
        BotIntegration as BotIntegrationPayload,
        Integration as IntegrationPayload,
        IntegrationAccount as IntegrationAccountPayload,
        IntegrationType,
        StreamIntegration as StreamIntegrationPayload,
    )


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
        The integration type.
    enabled: :class:`bool`
        Whether the integration is currently enabled.
    account: :class:`IntegrationAccount`
        The account linked to this integration.
    user: Optional[:class:`User`]
        The user that added this integration, if available.
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
        self.guild: Guild = guild
        self._state: ConnectionState = guild._state
        self._from_data(data)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} name={self.name!r}>"

    def _from_data(self, data: IntegrationPayload) -> None:
        self.id: int = int(data['id'])
        self.type: IntegrationType = data['type']
        self.name: str = data['name']
        self.account: IntegrationAccount = IntegrationAccount(data['account'])

        user = data.get('user')
        self.user: Optional[User] = User(state=self._state, data=user) if user else None
        self.enabled: bool = data.get('enabled', True)

    async def delete(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Deletes the integration.

        You must have :attr:`~Permissions.manage_guild` to do this.

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
        self.enabled = False


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
    enable_emoticons: :class:`bool`
        Whether emoticons should be synced for this integration (currently twitch only).
    expire_behaviour: :class:`ExpireBehaviour`
        The behaviour of expiring subscribers. Aliased to ``expire_behavior`` as well.
    expire_grace_period: :class:`int`
        The grace period (in days) for expiring subscribers.
    user: Optional[:class:`User`]
        The user for the integration, if available.
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
        self.revoked: bool = data.get('revoked', False)
        self.expire_behaviour: ExpireBehaviour = try_enum(ExpireBehaviour, data.get('expire_behaviour', 0))
        self.expire_grace_period: int = data.get('expire_grace_period', 1)
        self.synced_at: datetime = parse_time(data['synced_at']) if 'synced_at' in data else utcnow()
        self._role_id: Optional[int] = _get_as_snowflake(data, 'role_id')
        self.syncing: bool = data.get('syncing', False)
        self.enable_emoticons: bool = data.get('enable_emoticons', True)
        self.subscriber_count: int = data.get('subscriber_count', 0)

    @property
    def expire_behavior(self) -> ExpireBehaviour:
        """:class:`ExpireBehaviour`: An alias for :attr:`expire_behaviour`."""
        return self.expire_behaviour

    @property
    def role(self) -> Optional[Role]:
        """Optional[:class:`Role`] The role which the integration uses for subscribers."""
        # The key is `int` but `int | None` will return `None` anyway.
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

        You must have :attr:`~Permissions.manage_guild` to do this.

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
        """
        payload: Dict[str, Any] = {}
        if expire_behaviour is not MISSING:
            payload['expire_behavior'] = int(expire_behaviour)

        if expire_grace_period is not MISSING:
            payload['expire_grace_period'] = expire_grace_period

        if enable_emoticons is not MISSING:
            payload['enable_emoticons'] = enable_emoticons

        await self._state.http.edit_integration(self.guild.id, self.id, **payload)

    async def sync(self) -> None:
        """|coro|

        Syncs the integration.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Raises
        -------
        Forbidden
            You do not have permission to sync the integration.
        HTTPException
            Syncing the integration failed.
        """
        await self._state.http.sync_integration(self.guild.id, self.id)
        self.synced_at = utcnow()

    async def disable(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Disables the integration.

        This is an alias of :meth:`Integration.delete`.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Parameters
        -----------
        reason: :class:`str`
            The reason the integration was disabled. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permission to disable the integration.
        HTTPException
            Disabling the integration failed.
        """
        await self.delete(reason=reason)

    async def enable(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Enables the integration.

        You must have :attr:`~Permissions.manage_guild` to do this.

        Parameters
        -----------
        reason: :class:`str`
            The reason the integration was enabled. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permission to enable the integration.
        HTTPException
            Enabling the integration failed.
        """
        await self._state.http.create_integration(self.guild.id, self.type, self.id, reason=reason)
        self.enabled = True


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
        The integration type (i.e. Discord).
    enabled: :class:`bool`
        Whether the integration is currently enabled.
    user: Optional[:class:`User`]
        The user that added this integration, if available.
    account: :class:`IntegrationAccount`
        The integration account information.
    application_id: :class:`int`
        The application ID of the integration.
    application: Optional[:class:`IntegrationApplication`]
        The application tied to this integration. Not available in some contexts.
    scopes: List[:class:`str`]
        The scopes the integration is authorized for.
    """

    __slots__ = ('application', 'application_id', 'scopes')

    def _from_data(self, data: BotIntegrationPayload) -> None:
        super()._from_data(data)
        self.application: Optional[IntegrationApplication] = (
            self._state.create_integration_application(data['application']) if 'application' in data else None
        )
        self.application_id = self.application.id if self.application else int(data['application_id'])  # type: ignore # One or the other
        self.scopes: List[str] = data.get('scopes', [])


def _integration_factory(value: str) -> Tuple[Type[Integration], str]:
    if value == 'discord':
        return BotIntegration, value
    elif value in ('twitch', 'youtube'):
        return StreamIntegration, value
    else:
        return Integration, value
