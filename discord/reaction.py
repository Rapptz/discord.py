# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

import asyncio

from .user import User

class Reaction:
    """Represents a reaction to a message.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    Similar to members, the same reaction to a different message are equal.

    Supported Operations:

    +-----------+-------------------------------------------+
    | Operation |               Description                 |
    +===========+===========================================+
    | x == y    | Checks if two reactions are the same.     |
    +-----------+-------------------------------------------+
    | x != y    | Checks if two reactions are not the same. |
    +-----------+-------------------------------------------+
    | hash(x)   | Return the emoji's hash.                  |
    +-----------+-------------------------------------------+

    Attributes
    -----------
    emoji: :class:`Emoji` or str
        The reaction emoji. May be a custom emoji, or a unicode emoji.
    count: int
        Number of times this reaction was made
    me: bool
        If the user sent this reaction.
    message: :class:`Message`
        Message this reaction is for.
    """
    __slots__ = ('message', 'count', 'emoji', 'me')

    def __init__(self, *, message, data, emoji=None):
        self.message = message
        self.emoji = message._state.get_reaction_emoji(data['emoji']) if emoji is None else emoji
        self.count = data.get('count', 1)
        self.me = data.get('me')

    @property
    def custom_emoji(self):
        """bool: If this is a custom emoji."""
        return not isinstance(self.emoji, str)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self):
        return hash(self.emoji)

    def __repr__(self):
        return '<Reaction emoji={0.emoji!r} me={0.me} count={0.count}>'.format(self)

    @asyncio.coroutine
    def users(self, limit=100, after=None):
        """|coro|

        Get the users that added this reaction.

        The ``after`` parameter must represent a member
        and meet the :class:`abc.Snowflake` abc.

        Parameters
        ------------
        limit: int
            The maximum number of results to return.
        after: :class:`abc.Snowflake`
            For pagination, reactions are sorted by member.

        Raises
        --------
        HTTPException
            Getting the users for the reaction failed.

        Returns
        --------
        List[:class:`User`]
            A list of users who reacted to the message.
        """

        # TODO: Return an iterator a la `Messageable.history`?

        if self.custom_emoji:
            emoji = '{0.name}:{0.id}'.format(self.emoji)
        else:
            emoji = self.emoji

        if after:
            after = after.id

        msg = self.message
        state = msg._state
        data = yield from state.http.get_reaction_users(msg.id, msg.channel.id, emoji, limit, after=after)
        return [User(state=state, data=user) for user in data]
