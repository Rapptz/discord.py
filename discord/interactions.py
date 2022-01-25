"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import Optional, TYPE_CHECKING

from .enums import InteractionType, try_enum

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.snowflake import Snowflake
    from .types.user import User as UserPayload
    from .user import BaseUser, ClientUser


class Interaction:
    """Represents an interaction.

    Attributes
    ------------
    id: :class:`int`
        The interaction ID.
    nonce: Optional[Union[:class:`int`, :class:`str`]]
        The interaction's nonce. Not always present.
    name: Optional[:class:`str`]
        The name of the application command, if applicable.
    type: :class:`InteractionType`
        The type of interaction.
    successful: Optional[:class:`bool`]
        Whether the interaction succeeded.
        If this is your interaction, this is not immediately available.
        It is filled when Discord notifies us about the outcome of the interaction.
    user: :class:`User`
        The user who initiated the interaction.
    """

    __slots__ = ('id', 'type', 'nonce', 'user', 'name', 'successful')

    def __init__(
        self,
        id: int,
        type: int,
        nonce: Optional[Snowflake] = None,
        *,
        user: BaseUser,
        name: Optional[str] = None,
    ) -> None:
        self.id = id
        self.nonce = nonce
        self.type = try_enum(InteractionType, type)
        self.user = user
        self.name = name
        self.successful: Optional[bool] = None

    @classmethod
    def _from_self(
        cls, *, id: Snowflake, type: int, nonce: Optional[Snowflake] = None, user: ClientUser, name: Optional[str]
    ) -> Interaction:
        return cls(int(id), type, nonce, user=user, name=name)

    @classmethod
    def _from_message(
        cls, state: ConnectionState, *, id: Snowflake, type: int, user: UserPayload, **data
    ) -> Interaction:
        name = data.get('name')
        user = state.store_user(user)
        inst = cls(int(id), type, user=user, name=name)
        inst.successful = True
        return inst

    def __repr__(self) -> str:
        s = self.successful
        return f'<Interaction id={self.id} type={self.type}{f" successful={s}" if s is not None else ""} user={self.user!r}>'

    def __bool__(self) -> bool:
        if self.successful is not None:
            return self.successful
        raise TypeError('Interaction has not been resolved yet')