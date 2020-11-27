# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz

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

from . import utils

class _MessageType:
    __slots__ = ()

class MessageReference(_MessageType):
    """Represents a reference to a :class:`~discord.Message`.

    .. versionadded:: 1.5

    Attributes
    -----------
    message_id: Optional[:class:`int`]
        The id of the message referenced.
    channel_id: :class:`int`
        The channel id of the message referenced.
    guild_id: Optional[:class:`int`]
        The guild id of the message referenced.
    """

    __slots__ = ('message_id', 'channel_id', 'guild_id', '_state')

    def __init__(self, state, **kwargs):
        self.message_id = utils._get_as_snowflake(kwargs, 'message_id')
        self.channel_id = int(kwargs.pop('channel_id'))
        self.guild_id = utils._get_as_snowflake(kwargs, 'guild_id')
        self._state = state

    @classmethod
    def from_message(cls, message):
        """Creates a :class:`MessageReference` from an existing :class:`~discord.Message`.

        .. versionadded:: 1.6

        Parameters
        ----------
        message: :class:`~discord.Message`
            The message to be converted into a reference.

        Returns
        -------
        :class:`MessageReference`
            A reference to the message.
        """
        return cls(message._state, message_id=message.id, channel_id=message.channel.id, guild_id=getattr(message.guild, 'id', None))

    @property
    def cached_message(self):
        """Optional[:class:`~discord.Message`]: The cached message, if found in the internal message cache."""
        return self._state._get_message(self.message_id)

    def __repr__(self):
        return '<MessageReference message_id={0.message_id!r} channel_id={0.channel_id!r} guild_id={0.guild_id!r}>'.format(self)

    def to_dict(self):
        result = {'message_id': self.message_id} if self.message_id is not None else {}
        result['channel_id'] = self.channel_id
        if self.guild_id is not None:
            result['guild_id'] = self.guild_id
        return result
