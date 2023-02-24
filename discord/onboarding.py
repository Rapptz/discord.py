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
from typing import TYPE_CHECKING, Dict, List, Union

from .mixins import Hashable
from .object import Object
from .role import Role
from .enums import OnboardingPromptType, try_enum
from .partial_emoji import PartialEmoji
from .utils import SequenceProxy

if TYPE_CHECKING:
    from .abc import GuildChannel, PartialMessageable
    from .guild import Guild
    from .threads import Thread
    from .types.onboarding import (
        Onboarding as OnboardingPayload,
        OnboardingPrompt as OnboardingPromptPayload,
        OnboardingPromptOption as OnboardingPromptOptionPayload,
    )


class OnboardingPromptOption(Hashable):
    """Represents a guild's onboarding prompt's option.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    .. versionadded:: 2.2

    Attributes
    -----------
    id: :class:`int`
        The ID of the option.
    title: :class:`str`
        The title of the option.
    description: :class:`str`
        The description of the option.
    emoji: :class:`PartialEmoji`
        The emoji of the option.
    """

    __slots__ = ('id', 'title', 'description', 'emoji', '_channels', '_roles', '_onboarding')

    def __init__(self, *, onboarding: Onboarding, data: OnboardingPromptOptionPayload) -> None:
        self._onboarding: Onboarding = onboarding

        self._channels: Dict[int, Union[GuildChannel, Thread, PartialMessageable, Object]] = {}
        self._roles: Dict[int, Union[Role, Object]] = {}
        self._from_data(data)

    def _from_data(self, data: OnboardingPromptOptionPayload) -> None:
        guild = self._onboarding._guild
        state = guild._state

        self.id: int = int(data['id'])
        self.title: str = data['title']
        self.description: str = data['description']

        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = state
        self.emoji: PartialEmoji = emoji

        channel_ids = data.get('channel_ids', [])
        for channel_id in channel_ids:
            channel = guild.get_channel_or_thread(int(channel_id)) or state.get_channel(int(channel_id))
            self._channels[int(channel_id)] = channel or Object(id=channel_id)  # type: ignore # can't be PrivateChannel

        role_ids = data.get('role_ids', [])
        for role_id in role_ids:
            role = guild.get_role(int(role_id))

            self._roles[int(role_id)] = role or Object(id=role_id, type=Role)

    def __repr__(self) -> str:
        return f'<OnboardingPromptOption id={self.id} title={self.title!r} description={self.description!r} emoji={self.emoji!r}>'

    @property
    def channels(self) -> SequenceProxy[Union[GuildChannel, Thread, PartialMessageable, Object]]:
        """List[:class:`Union[GuildChannel, Thread, PartialMessageable, Object]`]: A list of channels that are opted into when this option is selected."""
        return SequenceProxy(self._channels.values())

    @property
    def roles(self) -> SequenceProxy[Union[Role, Object]]:
        """List[:class:`Union[Role, Object]`]: A list of roles that are assigned when this option is selected."""
        return SequenceProxy(self._roles.values())


class OnboardingPrompt(Hashable):
    """Represents a guild's onboarding prompt.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    .. versionadded:: 2.2


    Attributes
    -----------
    id: :class:`int`
        The ID of the prompt.
    title: :class:`str`
        The title of the prompt.
    single_select: :class:`bool`
        Whether only one option can be selected at a time.
    required: :class:`bool`
        Whether the prompt is required in the onboarding flow.
    in_onboarding: :class:`bool`
        Whether the prompt is in the onboarding flow.
    """

    __slots__ = ('id', 'title', 'single_select', 'required', 'in_onboarding', '_oboarding', '_options', '_type')

    def __init__(self, *, onboarding: Onboarding, data: OnboardingPromptPayload) -> None:
        self._oboarding: Onboarding = onboarding
        self._from_data(data)

    def _from_data(self, data: OnboardingPromptPayload) -> None:
        self.id: int = int(data['id'])
        self.title: str = data['title']
        self.single_select: bool = data['single_select']
        self.required: bool = data['required']
        self._type: OnboardingPromptType = try_enum(OnboardingPromptType, data['type'])
        self.in_onboarding: bool = data['in_onboarding']
        self._options: List[OnboardingPromptOption] = [
            OnboardingPromptOption(onboarding=self._oboarding, data=option) for option in data['options']
        ]

    def __repr__(self) -> str:
        return f'<OnboardingPrompt id={self.id} title={self.title!r} single_select={self.single_select} required={self.required} in_onboarding={self.in_onboarding} type={self.type!r}>'

    @property
    def type(self) -> OnboardingPromptType:
        """Optional[:class:`OnboardingPromptType`]: The type of the prompt."""
        return self._type

    @property
    def options(self) -> SequenceProxy[OnboardingPromptOption]:
        """List[:class:`OnboardingPromptOption`]: The options available to the prompt."""
        return SequenceProxy(self._options)


class Onboarding:
    """Represents a guild's onboarding.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    .. versionadded:: 2.2

    Attributes
    -----------
    enabled: :class:`bool`
        Whether guild onboarding is enabled.
    """

    __slots__ = ('enabled', '_guild', '_default_channel_ids', '_default_channels', '_prompts', '_guild_id')

    def __init__(self, *, guild: Guild, data: OnboardingPayload) -> None:
        self._guild = guild

        self._default_channels: Dict[int, Union[GuildChannel, Thread, PartialMessageable, Object]] = {}
        self._from_data(data)

    def _from_data(self, data: OnboardingPayload) -> None:
        guild = self._guild
        state = guild._state

        self.enabled: bool = data['enabled']
        self._guild_id: int = int(data['guild_id'])

        prompts = data.get('prompts', [])
        self._prompts: List[OnboardingPrompt] = [OnboardingPrompt(onboarding=self, data=prompt) for prompt in prompts]
        default_channel_ids = data.get('default_channel_ids', [])
        for channel_id in default_channel_ids:
            channel = guild.get_channel_or_thread(int(channel_id)) or state.get_channel(int(channel_id))
            self._default_channels[int(channel_id)] = channel or Object(id=channel_id)  # type: ignore # can't be a private channel

    def __repr__(self) -> str:
        return f'<Onboarding enabled={self.enabled}>'

    @property
    def default_channels(self) -> SequenceProxy[Union[GuildChannel, Thread, PartialMessageable, Object]]:
        """List[Union[:class:`GuildChannel`, :class:`Thread`, :class:`Object`]: The channels that new members get opted into automatically."""
        return SequenceProxy(self._default_channels.values())

    @property
    def prompts(self) -> SequenceProxy[OnboardingPrompt]:
        """List[:class:`GuildOnboardingPrompt`]: The prompts shown during onboarding and in costomize community."""
        return SequenceProxy(self._prompts)
