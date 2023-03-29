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

from typing import List, Optional, TYPE_CHECKING, Union

from .object import Object
from .partial_emoji import PartialEmoji
from .utils import _get_as_snowflake, MISSING

if TYPE_CHECKING:
    from .abc import Snowflake
    from .emoji import Emoji
    from .guild import Guild
    from .invite import PartialInviteGuild
    from .state import ConnectionState
    from .types.welcome_screen import (
        WelcomeScreen as WelcomeScreenPayload,
        WelcomeScreenChannel as WelcomeScreenChannelPayload,
    )

__all__ = (
    'WelcomeChannel',
    'WelcomeScreen',
)


class WelcomeChannel:
    """Represents a channel shown on a :class:`WelcomeScreen`.

    .. versionadded:: 2.0

    Attributes
    -----------
    channel: :class:`abc.Snowflake`
        The channel that is being shown.
    description: :class:`str`
        The description of the channel.
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`]
        The emoji shown under the description.
    """

    def __init__(
        self, *, channel: Snowflake, description: str, emoji: Optional[Union[PartialEmoji, Emoji, str]] = None
    ) -> None:
        self.channel = channel
        self.description = description

        if isinstance(emoji, str):
            emoji = PartialEmoji(name=emoji)
        self.emoji = emoji

    def __repr__(self) -> str:
        return f'<WelcomeChannel channel={self.channel!r} description={self.description} emoji={self.emoji!r}>'

    @classmethod
    def _from_dict(cls, *, data: WelcomeScreenChannelPayload, state: ConnectionState) -> WelcomeChannel:
        channel_id = int(data['channel_id'])
        channel = state.get_channel(channel_id) or Object(id=channel_id)

        emoji = None
        if (emoji_id := _get_as_snowflake(data, 'emoji_id')) is not None:
            emoji = state.get_emoji(emoji_id)
        elif (emoji_name := data.get('emoji_name')) is not None:
            emoji = PartialEmoji(name=emoji_name)

        return cls(channel=channel, description=data.get('description', ''), emoji=emoji)

    def _to_dict(self) -> WelcomeScreenChannelPayload:
        data: WelcomeScreenChannelPayload = {
            'channel_id': self.channel.id,
            'description': self.description,
            'emoji_id': None,
            'emoji_name': None,
        }
        if (emoji := self.emoji) is not None:
            data['emoji_id'] = emoji.id
            data['emoji_name'] = emoji.name

        return data


class WelcomeScreen:
    """Represents a :class:`Guild`'s welcome screen.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: bool(b)

            Returns whether the welcome screen is enabled.

    Attributes
    -----------
    guild: Union[:class:`Guild`, :class:`PartialInviteGuild`]
        The guild the welcome screen is for.
    description: :class:`str`
        The text shown on the welcome screen.
    welcome_channels: List[:class:`WelcomeChannel`]
        The channels shown on the welcome screen.
    """

    def __init__(self, *, data: WelcomeScreenPayload, guild: Union[Guild, PartialInviteGuild]) -> None:
        self.guild = guild
        self._update(data)

    def _update(self, data: WelcomeScreenPayload) -> None:
        state = self.guild._state
        channels = data.get('welcome_channels', [])

        self.welcome_channels: List[WelcomeChannel] = [
            WelcomeChannel._from_dict(data=channel, state=state) for channel in channels
        ]
        self.description: str = data.get('description', '')

    def __repr__(self) -> str:
        return f'<WelcomeScreen enabled={self.enabled} description={self.description} welcome_channels={self.welcome_channels!r}>'

    def __bool__(self) -> bool:
        return self.enabled

    @property
    def enabled(self) -> bool:
        """:class:`bool`: Whether the welcome screen is displayed."""
        return 'WELCOME_SCREEN_ENABLED' in self.guild.features

    async def edit(
        self,
        *,
        description: str = MISSING,
        welcome_channels: List[WelcomeChannel] = MISSING,
        enabled: bool = MISSING,
        reason: Optional[str] = None,
    ):
        """|coro|

        Edit the welcome screen.

        Welcome channels can only accept custom emojis if :attr:`Guild.premium_tier` is level 2 or above.

        You must have :attr:`~Permissions.manage_guild` in the guild to do this.

        All parameters are optional.

        Usage: ::

            rules_channel = guild.get_channel(12345678)
            announcements_channel = guild.get_channel(87654321)

            custom_emoji = utils.get(guild.emojis, name='loudspeaker')

            await welcome_screen.edit(
                description='This is a very cool community server!',
                welcome_channels=[
                    WelcomeChannel(channel=rules_channel, description='Read the rules!', emoji='👨‍🏫'),
                    WelcomeChannel(channel=announcements_channel, description='Watch out for announcements!', emoji=custom_emoji),
                ]
            )

        Parameters
        ------------
        enabled: :class:`bool`
            Whether the welcome screen will be shown.
        description: :class:`str`
            The welcome screen's description.
        welcome_channels: Optional[List[:class:`WelcomeChannel`]]
            The welcome channels (in order).
        reason: Optional[:class:`str`]
            The reason for editing the welcome screen. Shows up on the audit log.

        Raises
        -------
        HTTPException
            Editing the welcome screen failed failed.
        Forbidden
            You don't have permissions to edit the welcome screen.
        """
        payload = {}

        if enabled is not MISSING:
            payload['enabled'] = enabled
        if description is not MISSING:
            payload['description'] = description
        if welcome_channels is not MISSING:
            channels = [channel._to_dict() for channel in welcome_channels] if welcome_channels else []
            payload['welcome_channels'] = channels

        if payload:
            guild = self.guild
            data = await guild._state.http.edit_welcome_screen(guild.id, payload, reason=reason)
            self._update(data)
