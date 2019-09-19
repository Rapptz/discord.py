# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from .iterators import ReactionIterator

class Reaction:
    """Represents a reaction to a message.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two reactions are equal. This works by checking if the emoji
            is the same. So two messages with the same reaction will be considered
            "equal".

        .. describe:: x != y

            Checks if two reactions are not equal.

        .. describe:: hash(x)

            Returns the reaction's hash.

        .. describe:: str(x)

            Returns the string form of the reaction's emoji.

    Attributes
    -----------
    emoji: Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]
        The reaction emoji. May be a custom emoji, or a unicode emoji.
    count: :class:`int`
        Number of times this reaction was made
    me: :class:`bool`
        If the user sent this reaction.
    message: :class:`Message`
        Message this reaction is for.
    """
    __slots__ = ('message', 'count', 'emoji', 'me')

    def __init__(self, *, message, data, emoji=None):
        self.message = message
        self.emoji = emoji or message._state.get_reaction_emoji(data['emoji'])
        self.count = data.get('count', 1)
        self.me = data.get('me')

    @property
    def custom_emoji(self):
        """:class:`bool`: If this is a custom emoji."""
        return not isinstance(self.emoji, str)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self):
        return hash(self.emoji)

    def __str__(self):
        return str(self.emoji)

    def __repr__(self):
        return '<Reaction emoji={0.emoji!r} me={0.me} count={0.count}>'.format(self)

    async def remove(self, user):
        """|coro|

        Remove the reaction by the provided :class:`User` from the message.

        If the reaction is not your own (i.e. ``user`` parameter is not you) then
        the :attr:`~Permissions.manage_messages` permission is needed.

        The ``user`` parameter must represent a user or member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
             The user or member from which to remove the reaction.

        Raises
        -------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The user you specified, or the reaction's message was not found.
        """

        await self.message.remove_reaction(self.emoji, user)

    def users(self, limit=None, after=None):
        """Returns an :class:`AsyncIterator` representing the users that have reacted to the message.

        The ``after`` parameter must represent a member
        and meet the :class:`abc.Snowflake` abc.

        Examples
        ---------

        Usage ::

            # I do not actually recommend doing this.
            async for user in reaction.users():
                await channel.send('{0} has reacted with {1.emoji}!'.format(user, reaction))

        Flattening into a list: ::

            users = await reaction.users().flatten()
            # users is now a list of User...
            winner = random.choice(users)
            await channel.send('{} has won the raffle.'.format(winner))

        Parameters
        ------------
        limit: :class:`int`
            The maximum number of results to return.
            If not provided, returns all the users who
            reacted to the message.
        after: :class:`abc.Snowflake`
            For pagination, reactions are sorted by member.

        Raises
        --------
        HTTPException
            Getting the users for the reaction failed.

        Yields
        --------
        Union[:class:`User`, :class:`Member`]
            The member (if retrievable) or the user that has reacted
            to this message. The case where it can be a :class:`Member` is
            in a guild message context. Sometimes it can be a :class:`User`
            if the member has left the guild.
        """

        if self.custom_emoji:
            emoji = '{0.name}:{0.id}'.format(self.emoji)
        else:
            emoji = self.emoji

        if limit is None:
            limit = self.count

        return ReactionIterator(self.message, emoji, limit, after)
