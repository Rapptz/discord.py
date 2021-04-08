# -*- coding: utf-8 -*-

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

from . import utils
from .enums import try_enum, InteractionType

__all__ = (
    'Interaction',
)

class Interaction:
    """Represents a Discord interaction.

    An interaction happens when a user does an action that needs to
    be notified. Current examples are slash commands but future examples
    include forms and buttons.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The interaction type.
    guild_id: Optional[:class:`int`]
        The guild ID the interaction was sent from.
    channel_id: Optional[:class:`int`]
        The channel ID the interaction was sent from.
    application_id: :class:`int`
        The application ID that the interaction was for.
    user: Optional[Union[:class:`User`, :class:`Member`]]
        The user or member that sent the interaction.
    token: :class:`str`
        The token to continue the interaction. These are valid
        for 15 minutes.
    """
    __slots__ = (
        'id',
        'type',
        'guild_id',
        'channel_id',
        'data',
        'application_id',
        'user',
        'token',
        'version',
        '_state',
    )

    def __init__(self, *, data, state=None):
        self._state = state
        self._from_data(data)

    def _from_data(self, data):
        self.id = int(data['id'])
        self.type = try_enum(InteractionType, data['type'])
        self.data = data.get('data')
        self.token = data['token']
        self.version = data['version']
        self.channel_id = utils._get_as_snowflake(data, 'channel_id')
        self.guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.application_id = utils._get_as_snowflake(data, 'application_id')

    @property
    def guild(self):
        """Optional[:class:`Guild`]: The guild the interaction was sent from."""
        return self._state and self._state.get_guild(self.guild_id)

    @property
    def channel(self):
        """Optional[:class:`abc.GuildChannel`]: The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels are not resolved since there is
        no data to complete them.
        """
        guild = self.guild
        return guild and guild.get_channel(self.channel_id)

