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
from typing import TYPE_CHECKING, AsyncIterator, Union, Optional

from .user import User
from .object import Object
from .enums import ReactionType

# fmt: off
__all__ = (
    'Reaction',
)
# fmt: on

if TYPE_CHECKING:
    from .member import Member
    from .types.message import Reaction as ReactionPayload
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .emoji import Emoji
    from .abc import Snowflake


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
        Number of times this reaction was made. This is a sum of :attr:`normal_count` and :attr:`burst_count`.
    me: :class:`bool`
        If the user sent this reaction.
    message: :class:`Message`
        Message this reaction is for.
    me_burst: :class:`bool`
        If the user sent this super reaction.

        .. versionadded:: 2.4
    normal_count: :class:`int`
        The number of times this reaction was made using normal reactions.
        This is not available in the gateway events such as :func:`on_reaction_add`
        or :func:`on_reaction_remove`.

        .. versionadded:: 2.4
    burst_count: :class:`int`
        The number of times this reaction was made using super reactions.
        This is not available in the gateway events such as :func:`on_reaction_add`
        or :func:`on_reaction_remove`.

        .. versionadded:: 2.4
    """

    __slots__ = ('message', 'count', 'emoji', 'me', 'me_burst', 'normal_count', 'burst_count')

    def __init__(self, *, message: Message, data: ReactionPayload, emoji: Optional[Union[PartialEmoji, Emoji, str]] = None):
        self.message: Message = message
        self.emoji: Union[PartialEmoji, Emoji, str] = emoji or message._state.get_emoji_from_partial_payload(data['emoji'])
        self.count: int = data.get('count', 1)
        self.me: bool = data['me']
        details = data.get('count_details', {})
        self.normal_count: int = details.get('normal', 0)
        self.burst_count: int = details.get('burst', 0)
        self.me_burst: bool = data.get('me_burst', False)

    def is_custom_emoji(self) -> bool:
        """:class:`bool`: If this is a custom emoji."""
        return not isinstance(self.emoji, str)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self) -> int:
        return hash(self.emoji)

    def __str__(self) -> str:
        return str(self.emoji)

    def __repr__(self) -> str:
        return f'<Reaction emoji={self.emoji!r} me={self.me} count={self.count}>'

    async def remove(self, user: Snowflake) -> None:
        """|coro|

        Remove the reaction by the provided :class:`User` from the message.

        If the reaction is not your own (i.e. ``user`` parameter is not you) then
        :attr:`~Permissions.manage_messages` is needed.

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

    async def clear(self) -> None:
        """|coro|

        Clears this reaction from the message.

        You must have :attr:`~Permissions.manage_messages` to do this.

        .. versionadded:: 1.3

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Raises
        --------
        HTTPException
            Clearing the reaction failed.
        Forbidden
            You do not have the proper permissions to clear the reaction.
        NotFound
            The emoji you specified was not found.
        TypeError
            The emoji parameter is invalid.
        """
        await self.message.clear_reaction(self.emoji)

    async def users(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None, type: Optional[ReactionType] = None
    ) -> AsyncIterator[Union[Member, User]]:
        """Returns an :term:`asynchronous iterator` representing the users that have reacted to the message.

        The ``after`` parameter must represent a member
        and meet the :class:`abc.Snowflake` abc.

        .. versionchanged:: 2.0

            ``limit`` and ``after`` parameters are now keyword-only.

        Examples
        ---------

        Usage ::

            # I do not actually recommend doing this.
            async for user in reaction.users():
                await channel.send(f'{user} has reacted with {reaction.emoji}!')

        Flattening into a list: ::

            users = [user async for user in reaction.users()]
            # users is now a list of User...
            winner = random.choice(users)
            await channel.send(f'{winner} has won the raffle.')

        Parameters
        ------------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
            If not provided, returns all the users who
            reacted to the message.
        after: Optional[:class:`abc.Snowflake`]
            For pagination, reactions are sorted by member.
        type: Optional[:class:`ReactionType`]
            The type of reaction to return users from.
            If not provided, Discord only returns users of reactions with type ``normal``.

            .. versionadded:: 2.4

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

        if not isinstance(self.emoji, str):
            emoji = f'{self.emoji.name}:{self.emoji.id}'
        else:
            emoji = self.emoji

        if limit is None:
            limit = self.count

        while limit > 0:
            retrieve = min(limit, 100)

            message = self.message
            guild = message.guild
            state = message._state
            after_id = after.id if after else None

            data = await state.http.get_reaction_users(
                message.channel.id,
                message.id,
                emoji,
                retrieve,
                after=after_id,
                type=type.value if type is not None else None,
            )

            if data:
                limit -= len(data)
                after = Object(id=int(data[-1]['id']))
            else:
                # Terminate loop if we received no data
                limit = 0

            if guild is None or isinstance(guild, Object):
                for raw_user in reversed(data):
                    yield User(state=state, data=raw_user)

                continue

            for raw_user in reversed(data):
                member_id = int(raw_user['id'])
                member = guild.get_member(member_id)

                yield member or User(state=state, data=raw_user)
