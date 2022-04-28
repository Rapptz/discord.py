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

import copy
from typing import Optional, TYPE_CHECKING

from .enums import RelationshipAction, RelationshipType, try_enum
from .object import Object
from .utils import MISSING

if TYPE_CHECKING:
    from .state import ConnectionState
    from .user import User

# fmt: off
__all__ = (
    'Relationship',
)
# fmt: on


class Relationship:
    """Represents a relationship in Discord.

    A relationship is like a friendship, a person who is blocked, etc.

    .. container:: operations

        .. describe:: x == y

            Checks if two relationships are equal.

        .. describe:: x != y

            Checks if two relationships are not equal.

        .. describe:: hash(x)

            Return the relationship's hash.

    Attributes
    -----------
    nick: Optional[:class:`str`]
        The user's friend nickname (if applicable).

        .. versionchanged:: 2.0
            Renamed ``nickname`` to :attr:`nick`.
    user: :class:`User`
        The user you have the relationship with.
    type: :class:`RelationshipType`
        The type of relationship you have.
    """

    __slots__ = ('nick', 'type', 'user', '_state')

    def __init__(self, *, state: ConnectionState, data) -> None:  # TODO: type data
        self._state = state
        self._update(data)

    def _update(self, data: dict) -> None:
        self.type: RelationshipType = try_enum(RelationshipType, data['type'])
        self.nick: Optional[str] = data.get('nickname')

        self.user: User
        if (user := data.get('user')) is not None:
            self.user = self._state.store_user(user)
        elif self.user:
            return
        else:
            user_id = int(data['id'])
            self.user = self._state.get_user(user_id) or Object(id=user_id)  # type: ignore # Lying for better developer UX

    def __repr__(self) -> str:
        return f'<Relationship user={self.user!r} type={self.type!r} nick={self.nick!r}>'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Relationship) and other.user.id == self.user.id

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Relationship):
            return other.user.id != self.user.id
        return True

    def __hash__(self) -> int:
        return self.user.__hash__()

    async def delete(self) -> None:
        """|coro|

        Deletes the relationship.

        Depending on the type, this could mean unfriending or unblocking the user,
        denying an incoming friend request, or discarding an outgoing friend request.

        Raises
        ------
        HTTPException
            Deleting the relationship failed.
        """
        action = RelationshipAction.deny_request
        if self.type is RelationshipType.friend:
            action = RelationshipAction.unfriend
        elif self.type is RelationshipType.blocked:
            action = RelationshipAction.unblock
        elif self.type is RelationshipType.incoming_request:
            action = RelationshipAction.deny_request
        elif self.type is RelationshipType.outgoing_request:
            action = RelationshipAction.remove_pending_request

        await self._state.http.remove_relationship(self.user.id, action=action)

    async def accept(self) -> Relationship:
        """|coro|

        Accepts the relationship request. Only applicable for
        type :class:`RelationshipType.incoming_request`.

        .. versionchanged:: 2.0
            Changed the return type to :class:`Relationship`.

        Raises
        -------
        HTTPException
            Accepting the relationship failed.

        Returns
        -------
        :class:`Relationship`
            The new relationship.
        """
        data = await self._state.http.add_relationship(self.user.id, action=RelationshipAction.accept_request)
        return Relationship(state=self._state, data=data)

    async def edit(self, nick: Optional[str] = MISSING) -> Relationship:
        """|coro|

        Edits the relationship.

        .. versionadded:: 1.9

        .. versionchanged:: 2.0
            Changed the name of the method to :meth:`edit`.
            The edit is no longer in-place.

        Parameters
        ----------
        nick: Optional[:class:`str`]
            The nickname to change to. Can be ``None`` to denote no nickname.

        Raises
        -------
        HTTPException
            Changing the nickname failed.

        Returns
        -------
        :class:`Relationship`
            The new relationship.
        """
        payload = {}
        if nick is not MISSING:
            payload['nick'] = nick

        await self._state.http.edit_relationship(self.user.id, **payload)

        # Emulate the return for consistency
        new = copy.copy(self)
        new.nick = nick if nick is not MISSING else self.nick
        return new
