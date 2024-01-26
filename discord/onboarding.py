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

import os
from typing import TYPE_CHECKING, Iterable, Optional, Set, List, Union

from discord.utils import MISSING

from . import utils
from .mixins import Hashable
from .enums import OnboardingMode, OnboardingPromptType, try_enum
from .utils import cached_slot_property, MISSING

__all__ = (
    'Onboarding',
    'PartialOnboardingPrompt',
    'OnboardingPrompt',
    'OnboardingPromptOption',
    'PartialOnboardingPromptOption',
)


if TYPE_CHECKING:
    from .abc import GuildChannel
    from .emoji import Emoji
    from .guild import Guild
    from .partial_emoji import PartialEmoji
    from .role import Role
    from .threads import Thread
    from .types.onboarding import (
        Prompt as PromptPayload,
        PromptOption as PromptOptionPayload,
        Onboarding as OnboardingPayload,
    )
    from .state import ConnectionState


class PartialOnboardingPromptOption:
    """Represents a partial onboarding prompt option, these are used in the creation
    of an :class:`OnboardingPrompt` via :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.4

    Attributes
    -----------
    title: :class:`str`
        The title of this prompt option.
    description: Optional[:class:`str`]
        The description of this prompt option.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
        The emoji tied to this option. May be a custom emoji, or a unicode emoji.
    channel_ids: Set[:class:`int`]
        The IDs of the channels that will be made visible if this option is selected.
    role_ids: Set[:class:`int`]
        The IDs of the roles given to the user if this option is selected.
    """

    __slots__ = (
        'title',
        'emoji',
        'description',
        'channel_ids',
        'role_ids',
    )

    def __init__(
        self,
        title: str,
        emoji: Union[Emoji, PartialEmoji, str],
        description: Optional[str] = None,
        channel_ids: Iterable[int] = MISSING,
        role_ids: Iterable[int] = MISSING,
    ) -> None:
        self.title: str = title
        self.description: Optional[str] = description
        self.emoji: Union[PartialEmoji, Emoji, str] = emoji
        self.channel_ids: Set[int] = set(channel_ids or [])
        self.role_ids: Set[int] = set(role_ids or [])

    def to_dict(self, *, id: int = MISSING) -> PromptOptionPayload:
        if isinstance(self.emoji, str):
            emoji_payload = {"emoji_name": self.emoji}
        else:
            emoji_payload = {
                "emoji_id": self.emoji.id,
                "emoji_name": self.emoji.name,
                "emoji_animated": self.emoji.animated,
            }

        return {
            'id': id or os.urandom(16).hex(),
            'title': self.title,
            'description': self.description,
            'channel_ids': list(self.channel_ids),
            'role_ids': list(self.role_ids),
            **emoji_payload,
        }  # type: ignore


class OnboardingPromptOption(PartialOnboardingPromptOption, Hashable):
    """Represents an onboarding prompt option.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The ID of this prompt option.
    guild: :class:`Guild`
        The guild the onboarding prompt option is related to.
    title: :class:`str`
        The title of this prompt option.
    description: Optional[:class:`str`]
        The description of this prompt option.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]]
        The emoji tied to this option. May be a custom emoji, or a unicode emoji.
    channel_ids: Set[:class:`int`]
        The IDs of the channels that will be made visible if this option is selected.
    role_ids: Set[:class:`int`]
        The IDs of the roles given to the user if this option is selected.
    """

    __slots__ = (
        '_state',
        '_cs_channels',
        '_cs_roles',
        'guild',
        'id',
    )

    def __init__(self, *, data: PromptOptionPayload, state: ConnectionState, guild: Guild) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        super().__init__(
            title=data['title'],
            description=data['description'],
            emoji=self._state.get_emoji_from_partial_payload(data['emoji']),
            channel_ids=[int(id) for id in data['channel_ids']],
            role_ids=[int(id) for id in data['role_ids']],
        )

    def __repr__(self) -> str:
        return f'<OnboardingPromptOption id={self.id} title={self.title}>'

    @cached_slot_property('_cs_channels')
    def channels(self) -> List[Union[GuildChannel, Thread]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The list of channels which will be made visible if this option is selected."""
        it = filter(None, map(self.guild._resolve_channel, self.channel_ids))
        return utils._unique(it)

    @cached_slot_property('_cs_roles')
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: The list of roles given to the user if this option is selected."""
        it = filter(None, map(self.guild.get_role, self.role_ids))
        return utils._unique(it)

    def to_dict(self) -> PromptOptionPayload:
        return super().to_dict(id=self.id)


class PartialOnboardingPrompt:
    """Represents a partial onboarding prompt, these are used in the creation
    of an :class:`Onboarding` via :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.4

    Attributes
    -----------
    type: :class:`OnboardingPromptType`
        The type of this prompt.
    title: :class:`str`
        The title of this prompt.
    options: List[:class:`PartialOnboardingPromptOption`]
        The options of this prompt.
    single_select: :class:`bool`
        Whether this prompt is single select.
    required: :class:`bool`
        Whether this prompt is required.
    in_onboarding: :class:`bool`
        Whether this prompt is in the onboarding flow.
    """

    __slots__ = (
        'type',
        'title',
        'options',
        'single_select',
        'required',
        'in_onboarding',
    )

    def __init__(
        self,
        *,
        type: OnboardingPromptType,
        title: str,
        options: List[PartialOnboardingPromptOption],
        single_select: bool = True,
        required: bool = True,
        in_onboarding: bool = True,
    ) -> None:
        self.type: OnboardingPromptType = try_enum(OnboardingPromptType, type)
        self.title: str = title
        self.options: List[PartialOnboardingPromptOption] = options
        self.single_select: bool = single_select
        self.required: bool = required
        self.in_onboarding: bool = in_onboarding

    def to_dict(self, *, id: int) -> PromptPayload:
        return {
            'id': id,
            'type': self.type.value,
            'title': self.title,
            'options': [option.to_dict() for option in self.options],
            'single_select': self.single_select,
            'required': self.required,
            'in_onboarding': self.in_onboarding,
        }


class OnboardingPrompt(PartialOnboardingPrompt, Hashable):
    """Represents an onboarding prompt.

    .. versionadded:: 2.4

    Attributes
    -----------
    id: :class:`int`
        The ID of this prompt.
    guild: :class:`Guild`
        The guild the onboarding prompt is related to.
    type: :class:`OnboardingPromptType`
        The type of onboarding prompt.
    title: :class:`str`
        The title of this prompt.
    options: List[:class:`OnboardingPromptOption`]
        The list of options the user can select from.
    single_select: :class:`bool`
        Whether only one option can be selected.
    required: :class:`bool`
        Whether this prompt is required to complete the onboarding flow.
    in_onboarding: :class:`bool`
        Whether this prompt is part of the onboarding flow.
    """

    options: List[OnboardingPromptOption]

    __slots__ = (
        '_state',
        'guild',
        'id',
        'title',
        'options',
        'single_select',
        'required',
        'in_onboarding',
        'type',
    )

    def __init__(self, *, data: PromptPayload, state: ConnectionState, guild: Guild):
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.id: int = int(data['id'])
        super().__init__(
            type=try_enum(OnboardingPromptType, data['type']),
            title=data['title'],
            options=[OnboardingPromptOption(data=option_data, state=state, guild=guild) for option_data in data['options']],
            single_select=data['single_select'],
            required=data['required'],
            in_onboarding=data['in_onboarding'],
        )

    def __repr__(self) -> str:
        return f'<OnboardingPrompt id={self.id} title={self.title}, type={self.type}>'


class Onboarding:
    """Represents a guild's onboarding configuration.

    .. versionadded:: 2.4

    Attributes
    -----------
    guild: :class:`Guild`
        The guild the onboarding configuration is for.
    prompts: List[:class:`OnboardingPrompt`]
        The list of prompts shown during the onboarding and customize community flows.
    default_channel_ids: Set[:class:`int`]
        The IDs of the channels exposed to a new user by default.
    enabled: :class:`bool`:
        Whether onboarding is enabled in this guild.
    mode: :class:`OnboardingMode`
        The mode of onboarding for this guild.
    """

    __slots__ = (
        '_state',
        '_cs_default_channels',
        'guild',
        'prompts',
        'default_channel_ids',
        'enabled',
        'mode',
    )

    def __init__(self, *, data: OnboardingPayload, guild: Guild, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self.default_channel_ids: Set[int] = {int(channel_id) for channel_id in data['default_channel_ids']}
        self.prompts: List[OnboardingPrompt] = [
            OnboardingPrompt(data=prompt_data, state=state, guild=guild) for prompt_data in data['prompts']
        ]
        self.enabled: bool = data['enabled']
        self.mode: OnboardingMode = try_enum(OnboardingMode, data.get('mode', 0))

    def __repr__(self) -> str:
        return f'<Onboarding guild={self.guild!r} enabled={self.enabled}>'

    @cached_slot_property('_cs_default_channels')
    def default_channels(self) -> List[Union[GuildChannel, Thread]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The list of channels exposed to a new user by default."""
        it = filter(None, map(self.guild._resolve_channel, self.default_channel_ids))
        return utils._unique(it)
