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
from typing import TYPE_CHECKING, Iterable, Optional, Set, List, Union

from .mixins import Hashable
from .enums import OnboardingMode, OnboardingPromptType, try_enum
from .partial_emoji import PartialEmoji
from .utils import cached_slot_property, MISSING
from . import utils

__all__ = (
    'Onboarding',
    'OnboardingPrompt',
    'OnboardingPromptOption',
)


if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import GuildChannel, Snowflake
    from .emoji import Emoji
    from .guild import Guild
    from .partial_emoji import PartialEmoji
    from .role import Role
    from .threads import Thread
    from .types.onboarding import (
        Prompt as PromptPayload,
        PromptOption as PromptOptionPayload,
        CreatePromptOption as CreatePromptOptionPayload,
        Onboarding as OnboardingPayload,
    )
    from .state import ConnectionState


class OnboardingPromptOption(Hashable):
    """Represents a onboarding prompt option.

    This can be manually created for :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.6

    Parameters
    -----------
    title: :class:`str`
        The title of this prompt option.
    emoji: Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]
        The emoji tied to this option. May be a custom emoji, or a unicode emoji. I
        f this is a string, it will be converted to a :class:`PartialEmoji`.
    description: Optional[:class:`str`]
        The description of this prompt option.
    channels: Iterable[Union[:class:`abc.Snowflake`, :class:`int`]]
        The channels the user will be added to if this option is selected.
    roles: Iterable[Union[:class:`abc.Snowflake`, :class:`int`]]
        The roles the user will be given if this option is selected.

    Attributes
    -----------
    id: :class:`int`
        The ID of this prompt option. If this was manually created then the ID will be ``0``.
    title: :class:`str`
        The title of this prompt option.
    description: Optional[:class:`str`]
        The description of this prompt option.
    emoji: Optional[Union[:class:`Emoji`, :class:`PartialEmoji`]]
        The emoji tied to this option. May be a custom emoji, or a unicode emoji.
    channel_ids: Set[:class:`int`]
        The IDs of the channels the user will be added to if this option is selected.
    role_ids: Set[:class:`int`]
        The IDs of the roles the user will be given if this option is selected.
    """

    __slots__ = (
        'title',
        'emoji',
        'description',
        'id',
        'channel_ids',
        'role_ids',
        '_guild',
        '_cs_channels',
        '_cs_roles',
    )

    def __init__(
        self,
        *,
        title: str,
        emoji: Union[Emoji, PartialEmoji, str] = MISSING,
        description: Optional[str] = None,
        channels: Iterable[Union[Snowflake, int]] = MISSING,
        roles: Iterable[Union[Snowflake, int]] = MISSING,
    ) -> None:
        self.id: int = 0
        self.title: str = title
        self.description: Optional[str] = description
        self.emoji: Optional[Union[Emoji, PartialEmoji]] = (
            PartialEmoji.from_str(emoji) if isinstance(emoji, str) else emoji if emoji is not MISSING else None
        )

        self.channel_ids: Set[int] = (
            {c.id if not isinstance(c, int) else c for c in channels} if channels is not MISSING else set()
        )
        self.role_ids: Set[int] = {c.id if not isinstance(c, int) else c for c in roles} if roles is not MISSING else set()
        self._guild: Optional[Guild] = None

    def __repr__(self) -> str:
        return f'<OnboardingPromptOption id={self.id!r} title={self.title!r} emoji={self.emoji!r}>'

    @classmethod
    def from_dict(cls, *, data: PromptOptionPayload, state: ConnectionState, guild: Guild) -> Self:
        instance = cls(
            title=data['title'],
            description=data['description'],
            emoji=state.get_emoji_from_partial_payload(data['emoji']) if 'emoji' in data else MISSING,
            channels=[int(id) for id in data['channel_ids']],
            roles=[int(id) for id in data['role_ids']],
        )
        instance._guild = guild
        instance.id = int(data['id'])
        return instance

    def to_dict(
        self,
    ) -> CreatePromptOptionPayload:
        res: CreatePromptOptionPayload = {
            'title': self.title,
            'description': self.description,
            'channel_ids': list(self.channel_ids),
            'role_ids': list(self.role_ids),
        }
        if self.emoji:
            res.update((self.emoji._to_partial())._to_onboarding_prompt_option_payload())  # type: ignore
        return res

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild this prompt option is related to.

        Raises
        -------
        ValueError
            If the prompt option was created manually.
        """
        if self._guild is None:
            raise ValueError('This prompt does not have an associated guild because it was created manually.')
        return self._guild

    @cached_slot_property('_cs_channels')
    def channels(self) -> List[Union[GuildChannel, Thread]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The list of channels which will be made visible if this option is selected.

        Raises
        -------
        ValueError
            IF the prompt option is manually created, therefore has no guild.
        """
        it = filter(None, map(self.guild._resolve_channel, self.channel_ids))
        return utils._unique(it)

    @cached_slot_property('_cs_roles')
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: The list of roles given to the user if this option is selected.

        Raises
        -------
        ValueError
            If the prompt option is manually created, therefore has no guild.
        """
        it = filter(None, map(self.guild.get_role, self.role_ids))
        return utils._unique(it)


class OnboardingPrompt:
    """Represents a onboarding prompt.

    This can be manually created for :meth:`Guild.edit_onboarding`.

    .. versionadded:: 2.6

    Parameters
    -----------
    type: :class:`OnboardingPromptType`
        The type of this prompt.
    title: :class:`str`
        The title of this prompt.
    options: List[:class:`OnboardingPromptOption`]
        The options of this prompt.
    single_select: :class:`bool`
        Whether this prompt is single select.
        Defaults to ``True``.
    required: :class:`bool`
        Whether this prompt is required.
        Defaults to ``True``.
    in_onboarding: :class:`bool`
        Whether this prompt is in the onboarding flow.
        Defaults to ``True``.

    Attributes
    -----------
    id: :class:`int`
        The ID of this prompt. If this was manually created then the ID will be ``0``.
    type: :class:`OnboardingPromptType`
        The type of this prompt.
    title: :class:`str`
        The title of this prompt.
    options: List[:class:`OnboardingPromptOption`]
        The options of this prompt.
    single_select: :class:`bool`
        Whether this prompt is single select.
    required: :class:`bool`
        Whether this prompt is required.
    in_onboarding: :class:`bool`
        Whether this prompt is in the onboarding flow.
    """

    __slots__ = (
        'id',
        'type',
        'title',
        'options',
        'single_select',
        'required',
        'in_onboarding',
        '_guild',
    )

    def __init__(
        self,
        *,
        type: OnboardingPromptType,
        title: str,
        options: List[OnboardingPromptOption],
        single_select: bool = True,
        required: bool = True,
        in_onboarding: bool = True,
    ) -> None:
        self.id: int = 0
        self.type: OnboardingPromptType = type
        self.title: str = title
        self.options: List[OnboardingPromptOption] = options
        self.single_select: bool = single_select
        self.required: bool = required
        self.in_onboarding: bool = in_onboarding

        self._guild: Optional[Guild] = None

    def __repr__(self) -> str:
        return f'<OnboardingPrompt id={self.id!r} title={self.title!r}, type={self.type!r}>'

    @classmethod
    def from_dict(cls, *, data: PromptPayload, state: ConnectionState, guild: Guild) -> Self:
        instance = cls(
            type=try_enum(OnboardingPromptType, data['type']),
            title=data['title'],
            options=[
                OnboardingPromptOption.from_dict(data=option_data, state=state, guild=guild)  # type: ignore
                for option_data in data['options']
            ],
            single_select=data['single_select'],
            required=data['required'],
            in_onboarding=data['in_onboarding'],
        )
        instance.id = int(data['id'])
        return instance

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

    @property
    def guild(self) -> Guild:
        """:class:`Guild`: The guild this prompt is related to.

        Raises
        ------
        ValueError
            If the prompt was created manually.
        """
        if self._guild is None:
            raise ValueError('This prompt does not have an associated guild because it was created manually.')
        return self._guild

    def get_option(self, option_id: int, /) -> Optional[OnboardingPromptOption]:
        """Optional[:class:`OnboardingPromptOption`]: The option with the given ID, if found."""
        return next((option for option in self.options if option.id == option_id), None)


class Onboarding:
    """Represents a guild's onboarding configuration.

    .. versionadded:: 2.6

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
            OnboardingPrompt.from_dict(data=prompt_data, state=state, guild=guild) for prompt_data in data['prompts']
        ]
        self.enabled: bool = data['enabled']
        self.mode: OnboardingMode = try_enum(OnboardingMode, data.get('mode', 0))

    def __repr__(self) -> str:
        return f'<Onboarding guild={self.guild!r} enabled={self.enabled!r} mode={self.mode!r}>'

    @cached_slot_property('_cs_default_channels')
    def default_channels(self) -> List[Union[GuildChannel, Thread]]:
        """List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]: The list of channels exposed to a new user by default."""
        it = filter(None, map(self.guild._resolve_channel, self.default_channel_ids))
        return utils._unique(it)

    def get_prompt(self, prompt_id: int, /) -> Optional[OnboardingPrompt]:
        """Optional[:class:`OnboardingPrompt`]: The prompt with the given ID, if found."""
        return next((prompt for prompt in self.prompts if prompt.id == prompt_id), None)
