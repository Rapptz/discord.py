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

from typing import TYPE_CHECKING, Optional, List, Union, Type


from .enums import AutoModRuleTriggerType, AutoModRuleActionType, AutoModRuleEventType, try_enum
from .flags import AutoModPresets
from . import utils

if TYPE_CHECKING:
    from typing_extensions import Self
    from .abc import GuildChannel
    from .threads import Thread
    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.automod import (
        AutoModerationRule as AutoModerationRulePayload,
        AutoModerationTriggerMetadata as AutoModerationTriggerMetadataPayload,
        AutoModerationAction as AutoModerationActionPayload,
        AutoModerationActionExecution as AutoModerationActionExecutionPayload,
    )
    from .user import User
    from .role import Role

__all__ = (
    'AutoModRuleAction',
    'AutoModTrigger',
    'AutoModRule',
    'AutoModRuleExecution',
)


class AutoModRuleAction:
    """Represents a rule action.

    Attributes
    -----------
    type: :class:`AutoModRuleActionType`
        The type of action to take.
    channel_id: Optional[int]
        The channel to send the alert message to, if any.
    duration_seconds: Optional[int]
        The duration of the timeout to apply, if any.

    Raises
    -------
    :exc:`ValueError`
        Provided arguments do not match the needed types.
    """

    __slots__ = ('type', 'channel_id', 'duration_seconds')

    def __init__(
        self, *, type: AutoModRuleActionType, channel_id: Optional[int] = None, duration_seconds: Optional[int] = None
    ) -> None:
        self.type: AutoModRuleActionType = type
        self.channel_id: Optional[int] = channel_id
        self.duration_seconds: Optional[int] = duration_seconds

        if self.type is AutoModRuleActionType.timeout and self.duration_seconds is None:
            raise ValueError('duration_seconds must be set if type is timeout.')
        elif self.type is AutoModRuleActionType.send_alert_message and self.channel_id is None:
            raise ValueError('channel_id must be set if type is send_alert_message.')

    @classmethod
    def from_data(cls, data: AutoModerationActionPayload) -> Self:
        type_ = try_enum(AutoModRuleActionType, data['type'])
        if data['type'] == AutoModRuleActionType.block_message.value:
            return cls(type=type_)
        elif data['type'] == AutoModRuleActionType.timeout.value:
            duration_seconds = data['metadata']['duration_seconds']
            return cls(type=type_, duration_seconds=duration_seconds)
        elif data['type'] == AutoModRuleActionType.send_alert_message.value:
            channel_id = int(data['metadata']['channel_id'])
            return cls(type=type_, channel_id=channel_id)
        return cls(type=type_)

    def to_dict(self) -> AutoModerationActionPayload:
        ret: AutoModerationActionPayload = {'type': self.type.value, 'metadata': {}}
        if self.type is AutoModRuleActionType.timeout:
            ret['metadata'] = {'duration_seconds': self.duration_seconds}  # type: ignore # guarded by type check
        elif self.type is AutoModRuleActionType.send_alert_message:
            ret['metadata'] = {'channel_id': str(self.channel_id)}  # type: ignore # guarded by type check
        return ret


class AutoModTrigger:
    """Represents a trigger for an auto moderation rule.

    Attributes
    -----------
    type: :class:`AutoModRuleTriggerType`
        The type of trigger.
    keyword_filter: Optional[List[:class:`str`]]
        The list of strings that will trigger the keyword filter.
    presets: Optional[:class:`AutoModPresets`]
        The presets used with the preset keyword filter.

    .. versionadded:: 2.0
    """

    __slots__ = ('type', 'keyword_filter', 'presets')

    def __init__(
        self,
        *,
        type: AutoModRuleTriggerType,
        keyword_filter: Optional[List[str]] = None,
        presets: Optional[AutoModPresets] = None,
    ) -> None:
        self.type: AutoModRuleTriggerType = type
        self.keyword_filter: Optional[List[str]] = keyword_filter
        self.presets: Optional[AutoModPresets] = presets

        if self.type is AutoModRuleTriggerType.keyword and self.keyword_filter is None:
            raise ValueError('keyword_filter must be set if type is keyword.')
        elif self.type is AutoModRuleTriggerType.keyword_preset and self.presets is None:
            raise ValueError('presets must be set if type is keyword_preset.')

    @classmethod
    def from_data(cls: Type[Self], type: int, data: Optional[AutoModerationTriggerMetadataPayload]) -> Self:
        type_ = try_enum(AutoModRuleTriggerType, type)
        if type_ is AutoModRuleTriggerType.keyword:
            return cls(type=type_, keyword_filter=data['keyword_filter'])  # type: ignore # unable to typeguard due to outer payload
        elif type_ is AutoModRuleTriggerType.keyword_preset:
            return cls(type=type_, presets=AutoModPresets._from_value(data['presets']))  # type: ignore # unable to typeguard due to outer payload
        return cls(type=type_)

    def to_metadata_dict(self) -> AutoModerationTriggerMetadataPayload:
        if self.type is AutoModRuleTriggerType.keyword:
            return {'keyword_filter': self.keyword_filter}  # type: ignore # guarded by the type check
        elif self.type is AutoModRuleTriggerType.keyword_preset:
            return {'presets': self.presets.value}  # type: ignore # guarded by the type check

        return {}


class AutoModRule:
    """Represents an auto moderation rule.

    Attributes
    -----------
    id: :class:`int`
        The ID of the rule.
    guild: :class:`Guild`
        The guild the rule is for.
    name: :class:`str`
        The name of the rule.
    creator_id: :class:`int`
        The ID of the user that created the rule.
    trigger: :class:`AutoModTrigger`
        The rule's trigger.
    enabled: :class:`bool`
        Whether the rule is enabled.
    raw_exempt_roles: List[:class:`int`]
        The IDs of the roles that are exempt from the rule.
    raw_exempt_channels: List[:class:`int`]
        The IDs of the channels that are exempt from the rule.

    .. versionadded:: 2.0
    """

    __slots__ = (
        '_state',
        'id',
        'guild',
        'name',
        'creator_id',
        'event_type',
        'trigger',
        'enabled',
        'raw_exempt_roles',
        'raw_exempt_channels',
        '_actions',
    )

    def __init__(self, *, data: AutoModerationRulePayload, guild: Guild, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.creator_id = int(data['creator_id'])
        self.event_type: AutoModRuleEventType = try_enum(AutoModRuleEventType, data['event_type'])
        self.trigger: AutoModTrigger = AutoModTrigger.from_data(data['trigger_type'], data=data.get('trigger_metadata'))
        self.enabled: bool = data['enabled']
        self.raw_exempt_roles: List[int] = [int(role_id) for role_id in data['exempt_roles']]
        self.raw_exempt_channels: List[int] = [int(channel_id) for channel_id in data['exempt_channels']]
        self._actions: List[AutoModerationActionPayload] = data['actions']

    def __repr__(self) -> str:
        return f'<AutoModRule id={self.id} name={self.name!r}>'

    def to_dict(self) -> AutoModerationRulePayload:
        ret: AutoModerationRulePayload = {
            'id': str(self.id),
            'guild_id': str(self.guild.id),
            'name': self.name,
            'creator_id': str(self.creator_id),
            'event_type': self.event_type.value,
            'trigger_type': self.trigger.type.value,
            'trigger_metadata': self.trigger.to_metadata_dict(),
            'actions': [action.to_dict() for action in self.actions],
            'enabled': self.enabled,
            'exempt_roles': [str(role_id) for role_id in self.raw_exempt_roles],
            'exempt_channels': [str(channel_id) for channel_id in self.raw_exempt_channels],
        }  # type: ignore # trigger types break the flow here.

        return ret

    @property
    def creator(self) -> Optional[User]:
        """Optional[:class:`User`]: The user that created this rule."""
        return self._state.get_user(self.creator_id)

    @property
    def exempt_roles(self) -> List[Role]:
        """List[:class:`Role`]: The roles that are exempt from this rule."""
        it = [role for role in (self.guild.get_role(role_id) for role_id in self.raw_exempt_roles) if role is not None]
        return utils._unique(it)

    @property
    def exempt_channels(self) -> List[Union[GuildChannel, Thread]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The channels that are exempt from this rule."""
        it = filter(None, map(self.guild._resolve_channel, self.raw_exempt_channels))
        return utils._unique(it)

    @property
    def actions(self) -> List[AutoModRuleAction]:
        """List[:class:`AutoModRuleAction`]: The actions that are taken when this rule is triggered."""
        return [AutoModRuleAction.from_data(action) for action in self._actions]

    async def edit(
        self,
        *,
        name: Optional[str] = None,
        event_type: Optional[AutoModRuleEventType] = None,
        actions: List[AutoModRuleAction],
        enabled: Optional[bool] = None,
        exempt_roles: Optional[List[Role]] = None,
        exempt_channels: Optional[List[Union[GuildChannel, Thread]]] = None,
    ) -> Self:
        """|coro|

        This method will alter an existing auto moderation rule.

        Parameters
        -----------
        name: Optional[:class:`str`]
            The name to change to, if any.
        event_type: Optional[:class:`AutoModRuleEventType`]
            The event type to change to, if any.
        actions: List[:class:`AutoModRuleAction`]
            The rule actions to update, if any.
        enabled: Optional[:class:`bool`]
            Whether the rule should be enabled or not.
        exempt_roles: Optional[List[:class:`Role`]]
            The roles to exempt from the rule, if any.
        exempt_channels: Optional[List[Union[:class:`abc.GuildChannel`], :class:`Thread`]]
            The channels to exempt from the rule, if any.

        Raises
        -------
        :exc:`Forbidden`
            You are not authorised to perform this action.
        :exc:`NotFound`
            The rule was not found.

        Returns
        --------
        :class:`AutoModRule`
            The updated auto moderation rule.
        """
        transformed_actions = None
        if actions:
            transformed_actions = [action.to_dict() for action in actions]

        data = await self._state.http.modify_auto_moderation_rule(
            self.guild.id,
            self.id,
            name=name,
            event_type=event_type,
            actions=transformed_actions,
            enabled=enabled,
            exempt_roles=exempt_roles,
            exempt_channels=exempt_channels,
        )

        return self.__class__(data=data, guild=self.guild, state=self._state)

    async def delete(self) -> None:
        """|coro|

        This method will delete the auto moderation rule.

        Raises
        -------
        :exc:`Forbidden`
            You are not authorised to perform this action.
        :exc:`NotFound`
            The rule was not found.
        """
        await self._state.http.delete_auto_moderation_rule(self.guild.id, self.id)


class AutoModRuleExecution:
    """Represents an auto moderation rule execution.

    Attributes
    -----------
    """

    __slots__ = (
        '_state',
        '_guild_id',
        '_channel_id',
        'action',
        'rule_id',
        'rule_trigger_type',
        'user_id',
        'message_id',
        'alert_system_message_id',
        'content',
        'matched_keyword',
        'matched_content',
    )

    def __init__(self, *, data: AutoModerationActionExecutionPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._guild_id: int = int(data['guild_id'])
        self._channel_id: Optional[int] = utils._get_as_snowflake(data, 'channel_id')
        self.message_id: Optional[int] = utils._get_as_snowflake(data, 'message_id')
        self.action: AutoModRuleAction = AutoModRuleAction.from_data(data['action'])
        self.rule_id: int = int(data['rule_id'])
        self.rule_trigger_type: AutoModRuleTriggerType = try_enum(AutoModRuleTriggerType, data['rule_trigger_type'])
        self.user_id: int = int(data['user_id'])
        self.alert_system_message_id: Optional[int] = utils._get_as_snowflake(data, 'alert_system_message_id')
        self.content: str = data['content']
        self.matched_keyword: Optional[str] = data['matched_keyword']
        self.matched_content: Optional[str] = data['matched_content']

    @property
    def guild(self) -> Guild:
        """Optional[:class:`Guild`]: The guild this rule was executed in."""
        return self._state._get_guild(self._guild_id)  # type: ignore # this should never be None here

    @property
    def channel(self) -> Optional[Union[GuildChannel, Thread]]:
        """Optional[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The channel this rule was executed in."""
        if self._channel_id:
            return self.guild and self.guild.get_channel(self._channel_id)
        return None

    @property
    def member(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this rule was executed on/who triggered this rule."""
        return self.guild and self.guild.get_member(self.user_id)

    async def fetch_rule(self) -> AutoModRule:
        """|coro|

        This method will fetch the rule that was executed.

        Returns
        --------
        :class:`AutoModRule`
            The rule that was executed.
        """

        data = await self._state.http.get_auto_moderation_rule(self.guild.id, self.rule_id)
        return AutoModRule(data=data, guild=self.guild, state=self._state)
