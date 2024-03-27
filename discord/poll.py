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


from typing import (
    Dict,
    Optional,
    List,
    TYPE_CHECKING,
    Literal,
    Union,
)
from datetime import timedelta, datetime

from .enums import PollLayoutType, try_enum
from . import utils
from .emoji import PartialEmoji, Emoji
from .user import User

if TYPE_CHECKING:
    from typing_extensions import Self

    from .message import Message
    from .abc import Snowflake
    from .state import ConnectionState

    from .types.poll import (
        Poll as PollPayload,
        PollMedia as PollMediaPayload,
        PollAnswerCount as PollAnswerCountPayload,
        PollWithExpiry as PollWithExpiryPayload,
        PollAnswerWithID as PollAnswerWithIDPayload,
    )


__all__ = (
    'Poll',
    'PollAnswer',
    'PollAnswerCount',
)

MISSING = utils.MISSING

PollDuration = Literal[1, 4, 8, 24, 72, 168]


class PollAnswerCount:
    """Represents a partial poll answer.
    
    This is not meant to be user-constructed and should be
    obtained in the `on_poll_vote_add` and `on_poll_vote_remove`
    events.

    Attributes
    ----------
    id: :class:`int`
        The answer ID.
    me_voted: :class:`bool`
        Whether the current client has voted for this answer or not.
    count: :class:`int`
        The number of votes for this answer.
    """

    __slots__ = (
        '_state',
        '_message',

        'id',
        'me_voted',
        'count',
    )

    def __init__(self, *, state: ConnectionState, message: Message, data: PollAnswerCountPayload) -> None:
        self._state: ConnectionState = state
        self._message: Message = message

        self.id: int = int(data.get('id'))
        self.me_voted: bool = data.get('me_voted')
        self.count: int = data.get('count')

    async def users(self, *, after: Snowflake = MISSING, limit: int = 25) -> List[User]:
        """|coro|
        
        Retrieves all the voters of this answer.

        .. warning::
        
            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Parameters
        ----------
        after: :class:`Snowflake`
            Fetches users after this ID.
        limit: :class:`int`
            The max number of users to return. Can be up to 100.

        Raises
        ------
        ~discord.HTTPException
            Retrieving the users failed.

        Returns
        -------
        List[:class:`User`]
            A list containing all the users that voted for this poll.
        """

        data = await self._state.http.get_poll_answer_voters(
            self._message.channel.id,
            self._message.id,
            self.id,
            after.id if after is not MISSING else MISSING,
            limit
        )

        return [User(state=self._state, data=user_data) for user_data in data.get('users')]


class PollAnswer:
    """Represents a poll's answer.

    .. container:: operations

        .. describe:: str(x)

            Returns this answer's text, if any.

    Attributes
    ----------
    id: :class:`int`
        The ID of this answer.
    text: :class:`str`
        The answers display text. Can be up to 55 characters.
    emoji: :class:`PartialEmoji`
        The emoji to show up with this answer.
    """

    __slots__ = ('text', 'emoji', 'id', '_state', '_message')

    def __init__(
        self,
        *,
        data: PollAnswerWithIDPayload,
        message: Optional[Message] = None,
    ) -> None:
        self._state: Optional[ConnectionState] = message._state if message else None
        self._message: Optional[Message] = message

        media = data['poll_media']

        self.id: int = int(data['answer_id'])
        self.text: str = media['text']

        emoji = media.get('emoji', None)

        if emoji:
            emoji_id = int(emoji.get('id')) if emoji.get('id', None) is not None else None # type: ignore

            partial = PartialEmoji(
                name=emoji['name'],
                id=emoji_id
            )

        else:
            partial = None

        self.emoji: Optional[PartialEmoji] = partial

    @classmethod
    def from_params(
        cls,
        id: int,
        text: str,
        emoji: Optional[Union[Emoji, PartialEmoji, str]] = None,
        *,
        message: Optional[Message] = None
    ) -> Self:
        
        poll_media: PollMediaPayload = {'text': text}
        if emoji:
            poll_media.update({'emoji': {'id': emoji.id if isinstance(emoji, (PartialEmoji, Emoji)) else None, 'name': str(emoji)}})

        payload: PollAnswerWithIDPayload = {'answer_id': id, 'poll_media': poll_media}

        return cls(data=payload, message=message)


    def _to_dict(self) -> PollMediaPayload:
        data: Dict[str, Union[str, Dict[str, Union[str, int]]]] = {}  # Needed to add type hint to make type checker happy
        data['text'] = self.text

        if self.emoji is not None:
            if isinstance(self.emoji, str):
                data['emoji'] = {'name': self.emoji}

            elif isinstance(self.emoji, (PartialEmoji, Emoji)):
                data['emoji'] = {'name': self.emoji.name}

                if self.emoji.id:
                    data['emoji']['id'] = self.emoji.id

        return data  # type: ignore # Type Checker complains that this dict's type ain't PollAnswerMediaPayload
    
    async def users(self, *, after: Snowflake = MISSING, limit: int = 25) -> List[User]:
        """|coro|
        
        Retrieves all the voters of this answer.

        .. warning::
        
            This method can only be used if it has a message attached.
            That is, only accessible via :attr:`Message.poll`

        Parameters
        ----------
        after: :class:`Snowflake`
            Fetches users after this ID.
        limit: :class:`int`
            The max number of users to return. Can be up to 100.

        Raises
        ------
        RuntimeError
            The poll doesn't have an attached message.
        ~discord.HTTPException
            Retrieving the users failed.

        Returns
        -------
        List[:class:`User`]
            A list containing all the users that voted for this poll.
        """

        if not self._message or not self._state:
            raise RuntimeError(
                'You cannot fetch users in a non-message-attached poll'
            )

        if 0 > limit or limit > 100:
            raise ValueError(
                'limit can only be within 0 and 100'
            )


        data = await self._state.http.get_poll_answer_voters(
            self._message.channel.id,
            self._message.id,
            self.id,
            after.id if after is not MISSING else MISSING,
            limit
        )

        return [User(state=self._state, data=user_data) for user_data in data.get('users')]


class Poll:
    """Represents a message's Poll.

    .. container:: operations

        .. describe:: str(x)

            Returns the Poll's question

    .. versionadded:: 2.4

    Parameters
    ----------
    question: :class:`str`
        The poll's question. Can be up to 300 characters.
    duration: :class:`int`
        The duration in hours of the poll.
    answers: Optional[List[:class:`PollAnswer`]]
        The possible answers for this poll. If ``None``
        is passed, then this answers must be added through
        :meth:`add_answer`
    multiselect: :class:`bool`
        Whether users are allowed to select more than
        one answer.
    layout_type: :class:`PollLayoutType`
        The layout type of the poll.
    """

    __slots__ = (
        'multiselect',
        '_answers',
        'duration',
        'layout_type',
        'question',
        '_message',
        '_results',
        '_expiry',
        '_finalized',
        '_state',
        '_counts',
    )

    def __init__(
        self,
        question: str,
        duration: PollDuration,
        *,
        multiselect: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        self.question: str = question
        # Automatically order the answers
        self._answers: List[PollAnswer] = []
        self.duration: int = duration
        self.multiselect: bool = multiselect
        self.layout_type: PollLayoutType = layout_type

        # NOTE: These attributes are set manually when calling
        # _from_data, so it should be ``None`` now.
        self._message: Optional[Message] = None
        self._state: Optional[ConnectionState] = None
        self._finalized: bool = False
        self._counts: Optional[List[PollAnswerCount]] = None

        # We set the expiry using utils.utcnow()

        now = utils.utcnow()

        self._expiry = now + timedelta(hours=duration)

    @classmethod
    def _from_data(cls, data: PollWithExpiryPayload, message: Message, state: ConnectionState) -> Self:
        answers = [PollAnswer(data=answer, message=message) for answer in data.get('answers')]
        multiselect = data.get('allow_multiselect', False)
        expiry = data.get('expiry')
        layout_type = try_enum(PollLayoutType, data.get('layout_type', 1))
        question_data = data.get('question')
        question = question_data.get('text')

        self = cls(
            duration=1, # Set to 1 so we can set the expiry manually
            multiselect=multiselect,
            layout_type=layout_type,
            question=question,
        )
        self._answers = answers
        self._message = message
        self._state = state
        self._expiry = datetime.fromisoformat(expiry)

        results = data.get('results', None)
        if results:
            self._finalized = results.get('is_finalized')
            self._counts = [PollAnswerCount(state=state, message=message, data=count) for count in results.get('answer_counts')]

        return self

    def _to_dict(self) -> PollPayload:
        data = {}
        data['allow_multiselect'] = self.multiselect
        data['question'] = {'text': self.question}
        data['duration'] = self.duration
        data['layout_type'] = self.layout_type.value
        data['answers'] = [{'poll_media': answer._to_dict()} for answer in self.answers]

        return data  # type: ignore
    
    def __str__(self) -> str:
        return self.question

    def __repr__(self) -> str:
        return f"<Poll duration={self.duration} question=\"{self.question}\" answers={self.answers}>"

    @property
    def answers(self) -> List[PollAnswer]:
        """List[:class:`PollAnswer`]: Returns a read-only copy of the answers"""
        return self._answers.copy()
    
    @property
    def expiry(self) -> datetime:
        """:class:`datetime.datetime`: A datetime object representing the poll expiry"""

        # This is autocalculated when created manually, set with the expiry
        # returned in the data when created from data.
        return self._expiry
    
    @property
    def answer_counts(self) -> Optional[List[PollAnswerCount]]:
        """Optional[List[:class:`PollAnswerCount`]]: Returns a read-only copy of the
        answer counts, or ``None`` if this is user-constructed."""

        if self._counts:
            return self._counts.copy()
        return None

    def is_finalized(self) -> bool:
        """:class:`bool`: Returns whether the poll has finalized.
        
        It always returns ``False`` if the poll is not part of a
        fetched message. You should consider accesing this method
        via :attr:`Message.poll`
        """

        return self._finalized

    def add_answer(
        self,
        *,
        text: str,
        emoji: Optional[Union[PartialEmoji, Emoji, str]] = None,
    ) -> Self:
        """Appends a new answer to this poll.

        Parameters
        ----------
        text: :class:`str`
            The text label for this poll answer. Can be up to 55
            characters.
        emoji: Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]
            The emoji to display along the text.

        Returns
        -------
        :class:`Poll`
            This poll with the new answer appended.
        """

        answer = PollAnswer.from_params(
            id=len(self.answers)+1, # Auto ID
            text=text,
            emoji=emoji,
            message=self._message
        )

        self._answers.append(answer)
        return self
    
    def get_answer(
        self,
        /,
        id: int,
    ) -> Optional[PollAnswer]:
        """Returns the answer with the provided ID or ``None`` if not found.
        
        Note that the ID, as Discord says, it is the index / row where the answer
        is located in the poll.

        Returns
        -------
        Optional[:class:`PollAnswer`]
            The answer.
        """

        if id > len(self.answers):
            return None
        
        try:
            return self.answers[id-1]
        except IndexError: # Though we added a checker we should try to not raise errors.
            return


    async def end(self) -> None:
        """|coro|
        
        Ends the poll.
        
        .. warning::
        
            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Raises
        ------
        RuntimeError
            This poll has no attached message.
        HTTPError
            Ending the poll failed.
        """

        if not self._message:
            raise RuntimeError(
                'This method can only be called when a message is present, try using this via Message.poll.end()'
            )
        
        await self._message._state.http.end_poll(self._message.channel.id, self._message.id)
