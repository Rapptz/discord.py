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
from typing import TYPE_CHECKING, ClassVar, List, Optional, Sequence

__all__ = (
    'AppInstallationType',
    'AppCommandContext',
)

if TYPE_CHECKING:
    from typing_extensions import Self
    from ..types.interactions import InteractionContextType, InteractionInstallationType


class AppInstallationType:
    r"""Represents the installation location of an application command.

    .. versionadded:: 2.4

    Parameters
    -----------
    guild: Optional[:class:`bool`]
        Whether the integration is a guild install.
    user: Optional[:class:`bool`]
        Whether the integration is a user install.
    """

    __slots__ = ('_guild', '_user')

    GUILD: ClassVar[int] = 0
    USER: ClassVar[int] = 1

    def __init__(self, *, guild: Optional[bool] = None, user: Optional[bool] = None):
        self._guild: Optional[bool] = guild
        self._user: Optional[bool] = user

    @property
    def guild(self) -> bool:
        """:class:`bool`: Whether the integration is a guild install."""
        return bool(self._guild)

    @guild.setter
    def guild(self, value: bool) -> None:
        self._guild = bool(value)

    @property
    def user(self) -> bool:
        """:class:`bool`: Whether the integration is a user install."""
        return bool(self._user)

    @user.setter
    def user(self, value: bool) -> None:
        self._user = bool(value)

    def merge(self, other: AppInstallationType) -> AppInstallationType:
        # Merging is similar to AllowedMentions where `self` is the base
        # and the `other` is the override preference
        guild = self._guild if other._guild is None else other._guild
        user = self._user if other._user is None else other._user
        return AppInstallationType(guild=guild, user=user)

    def _is_unset(self) -> bool:
        return all(x is None for x in (self._guild, self._user))

    def _merge_to_array(self, other: Optional[AppInstallationType]) -> Optional[List[InteractionInstallationType]]:
        result = self.merge(other) if other is not None else self
        if result._is_unset():
            return None
        return result.to_array()

    @classmethod
    def _from_value(cls, value: Sequence[InteractionInstallationType]) -> Self:
        self = cls()
        for x in value:
            if x == cls.GUILD:
                self._guild = True
            elif x == cls.USER:
                self._user = True
        return self

    def to_array(self) -> List[InteractionInstallationType]:
        values = []
        if self._guild:
            values.append(self.GUILD)
        if self._user:
            values.append(self.USER)
        return values


class AppCommandContext:
    r"""Wraps up the Discord :class:`~discord.app_commands.Command` execution context.

    .. versionadded:: 2.4

    Parameters
    -----------
    guild: Optional[:class:`bool`]
        Whether the context allows usage in a guild.
    dm_channel: Optional[:class:`bool`]
        Whether the context allows usage in a DM channel.
    private_channel: Optional[:class:`bool`]
        Whether the context allows usage in a DM or a GDM channel.
    """

    GUILD: ClassVar[int] = 0
    DM_CHANNEL: ClassVar[int] = 1
    PRIVATE_CHANNEL: ClassVar[int] = 2

    __slots__ = ('_guild', '_dm_channel', '_private_channel')

    def __init__(
        self,
        *,
        guild: Optional[bool] = None,
        dm_channel: Optional[bool] = None,
        private_channel: Optional[bool] = None,
    ):
        self._guild: Optional[bool] = guild
        self._dm_channel: Optional[bool] = dm_channel
        self._private_channel: Optional[bool] = private_channel

    @property
    def guild(self) -> bool:
        """:class:`bool`: Whether the context allows usage in a guild."""
        return bool(self._guild)

    @guild.setter
    def guild(self, value: bool) -> None:
        self._guild = bool(value)

    @property
    def dm_channel(self) -> bool:
        """:class:`bool`: Whether the context allows usage in a DM channel."""
        return bool(self._dm_channel)

    @dm_channel.setter
    def dm_channel(self, value: bool) -> None:
        self._dm_channel = bool(value)

    @property
    def private_channel(self) -> bool:
        """:class:`bool`: Whether the context allows usage in a DM or a GDM channel."""
        return bool(self._private_channel)

    @private_channel.setter
    def private_channel(self, value: bool) -> None:
        self._private_channel = bool(value)

    def merge(self, other: AppCommandContext) -> AppCommandContext:
        guild = self._guild if other._guild is None else other._guild
        dm_channel = self._dm_channel if other._dm_channel is None else other._dm_channel
        private_channel = self._private_channel if other._private_channel is None else other._private_channel
        return AppCommandContext(guild=guild, dm_channel=dm_channel, private_channel=private_channel)

    def _is_unset(self) -> bool:
        return all(x is None for x in (self._guild, self._dm_channel, self._private_channel))

    def _merge_to_array(self, other: Optional[AppCommandContext]) -> Optional[List[InteractionContextType]]:
        result = self.merge(other) if other is not None else self
        if result._is_unset():
            return None
        return result.to_array()

    @classmethod
    def _from_value(cls, value: Sequence[InteractionContextType]) -> Self:
        self = cls()
        for x in value:
            if x == cls.GUILD:
                self._guild = True
            elif x == cls.DM_CHANNEL:
                self._dm_channel = True
            elif x == cls.PRIVATE_CHANNEL:
                self._private_channel = True
        return self

    def to_array(self) -> List[InteractionContextType]:
        values = []
        if self._guild:
            values.append(self.GUILD)
        if self._dm_channel:
            values.append(self.DM_CHANNEL)
        if self._private_channel:
            values.append(self.PRIVATE_CHANNEL)
        return values
