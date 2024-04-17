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


from typing import Dict, Optional, List, TYPE_CHECKING, Union, AsyncIterator, NamedTuple

import datetime

from .enums import PollLayoutType, try_enum
from . import utils
from .emoji import PartialEmoji, Emoji
from .user import User
from .object import Object

if TYPE_CHECKING:
    from typing_extensions import Self

    from .message import Message
    from .abc import Snowflake
    from .state import ConnectionState
    from .member import Member

    from .types.poll import (
        PollCreate as PollCreatePayload,
        PollMedia as PollMediaPayload,
        PollAnswerCount as PollAnswerCountPayload,
        Poll as PollPayload,
        PollAnswerWithID as PollAnswerWithIDPayload,
    )


__all__ = (
    'Poll',
    'PollAnswer',
    'PollAnswerCount',
    'PollMedia',
)

MISSING = utils.MISSING
PollMediaEmoji = Union[PartialEmoji, Emoji, str]


class PollMedia(NamedTuple):
    """Represents the poll media for a poll item.

    Attributes
    ----------
    text: :class:`str`
        The displayed text
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]]
        The attached emoji for this media. This will always be ignored for a poll
        question media.
    """

    text: str
    emoji: Optional[PollMediaEmoji] = None

    def to_dict(self) -> PollMediaPayload:
        """Returns an API valid payload for this tuple."""

        payload = {'text': self.text}

        if self.emoji:
            if isinstance(self.emoji, Emoji):
                payload['emoji'] = {'name': self.emoji.name, 'id': self.emoji.id}  # type: ignore

            elif isinstance(self.emoji, PartialEmoji):
                payload['emoji'] = self.emoji.to_dict()  # type: ignore

            else:
                payload['emoji'] = {'name': str(self.emoji)}  # type: ignore

        return payload  # type: ignore

    @classmethod
    def from_dict(cls, *, data: PollMediaPayload) -> PollMedia:
        """Returns a new instance of this class from a payload."""

        emoji = data.get('emoji')

        if emoji:
            return cls(text=data['text'], emoji=PartialEmoji.from_dict(emoji))
        return cls(text=data['text'])


class PollAnswerBase:
    def __init__(self, *, id: int, message: Optional[Message], state: Optional[ConnectionState]) -> None:
        self.id: int = id
        self._message: Optional[Message] = message
        self._state: Optional[ConnectionState] = state

    def _update(self, message: Message) -> None:
        self._message = message
        self._state = message._state

    async def voters(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """Returns an :term:`asynchronous iterator` representing the users that have voted to this answer.

        The ``after`` parameter must represent a user
        and meet the :class:`abc.Snowflake` abc.

        .. warning::

            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Examples
        --------

        Usage ::

            async for voter in poll_answer.voters():
                print(f'{voter} has voted for {poll_answer}!')

        Flattening into a list: ::

            voters = [voter async for voter in poll_answer.voters()]
            # voters is now a list of User

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The maximum number of results to return.
            If not provided, returns all the users who
            voted to this poll answer.
        after: Optional[:class:`abc.Snowflake`]
            For pagination, voters are sorted by member.

        Raises
        ------
        HTTPException
            Retrieving the users failed.

        Yields
        ------
        Union[:class:`User`, :class:`Member`]
            The member (if retrievable) or the user that has voted
            to this poll answer. The case where it can be a :class:`Member`
            is in a guild message context. Sometimes it can be a :class:`User`
            if the member has left the guild.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise RuntimeError('You cannot fetch users in a non-message-attached poll')

        if limit is None:
            if not self._message.poll:
                limit = 100
            else:
                answer_count = self._message.poll.get_answer_count(self.id)

                limit = answer_count.count if answer_count else 100

        while limit > 0:
            retrieve = min(limit, 100)

            message = self._message
            guild = self._message.guild
            state = self._state
            after_id = after.id if after else None

            data = await state.http.get_poll_answer_voters(
                message.channel.id, message.id, self.id, after=after_id, limit=retrieve
            )
            users = data['users']

            if len(users) == 0:
                # No more voters to fetch, terminate process
                break

            after = Object(id=int((users[len(users)-1])['id']))

            if not guild or isinstance(guild, Object):
                for raw_user in reversed(users):
                    yield User(state=self._state, data=raw_user)
                continue

            for raw_member in reversed(users):
                member_id = int(raw_member['id'])
                member = guild.get_member(member_id)

                yield member or User(state=self._state, data=raw_member)


class PollAnswerCount(PollAnswerBase):
    """Represents a poll answer count.

    This is not meant to be user-constructed but instead obtained by the results in
    :attr:`Poll.answer_counts`

    Attributes
    ----------
    id: :class:`int`
        The answer ID.
    self_voted: :class:`bool`
        Whether the current client has voted for this answer or not.
    count: :class:`int`
        The number of votes for this answer.
    """

    __slots__ = (
        '_state',
        '_message',
        'id',
        'self_voted',
        'count',
    )

    def __init__(self, *, state: ConnectionState, message: Message, data: PollAnswerCountPayload) -> None:
        self.self_voted: bool = data.get('me_voted')
        self.count: int = data.get('count')

        super().__init__(id=int(data['id']), message=message, state=state)

    def __repr__(self) -> str:
        return f'<PollAnswerCount id={self.id} resolved={self.resolved!r}> self_voted={self.self_voted}'

    @property
    def original_message(self) -> Message:
        """:class:`Message`: Returns the original message the poll of this answer is in."""
        return self._message  # type: ignore # Here will always be a value

    @property
    def resolved(self) -> Optional[PollAnswer]:
        """Optional[:class:`PollAnswer`]: Returns the resolved poll answer of this count or ``None``
        if not found.
        """
        if not self.original_message.poll:
            return
        return self.original_message.poll.get_answer(self.id)

    @property
    def poll(self) -> Poll:
        """:class:`Poll`: Returns the poll that this answer belongs to."""
        return self._message.poll  # type: ignore


class PollAnswer(PollAnswerBase):
    """Represents a poll's answer.

    .. container:: operations

        .. describe:: str(x)

            Returns this answer's text, if any.

    Attributes
    ----------
    id: :class:`int`
        The ID of this answer.
    media: :class:`PollMedia`
        A :class:`NamedTuple` containing the raw data of this answers media.
    """

    __slots__ = ('media', 'id', '_state', '_message')

    def __init__(
        self,
        *,
        message: Optional[Message],
        data: PollAnswerWithIDPayload,
    ) -> None:
        self.media: PollMedia = PollMedia.from_dict(data=data['poll_media'])

        super().__init__(id=int(data['answer_id']), message=message, state=message._state if message else None)

    def __str__(self) -> str:
        return self.media.text

    def __repr__(self) -> str:
        return f'<PollAnswer id={self.id} media={self.media}>'

    @classmethod
    def from_params(
        cls,
        id: int,
        text: str,
        emoji: Optional[PollMediaEmoji] = None,
        *,
        message: Optional[Message],
    ) -> Self:
        poll_media: PollMediaPayload = {'text': text}
        if emoji:
            if isinstance(emoji, Emoji):
                poll_media['emoji'] = {'name': emoji.name}  # type: ignore

                if emoji.id:
                    poll_media['emoji']['id'] = emoji.id  # type: ignore
            elif isinstance(emoji, PartialEmoji):
                poll_media['emoji'] = emoji.to_dict()
            else:
                poll_media['emoji'] = {'name': str(emoji)}  # type: ignore

        payload: PollAnswerWithIDPayload = {'answer_id': id, 'poll_media': poll_media}

        return cls(data=payload, message=message)

    @property
    def text(self) -> str:
        """:class:`str`: Returns this answer display text."""
        return self.media.text

    @property
    def emoji(self) -> Optional[Union[PartialEmoji, Emoji]]:
        """Optional[:class:`PartialEmoji`]: Returns this answer display emoji, is any."""
        if isinstance(self.media.emoji, str):
            return PartialEmoji.from_str(self.media.emoji)
        return self.media.emoji

    def get_count(self) -> Optional[PollAnswerCount]:
        """Returns this answer's count data, if available.

        .. warning::

            This will **always** return ``None`` if the parent poll is user-constructed.

        Returns
        -------
        Optional[:class:`PollAnswerCount`]
            This poll's answer count, or ``None`` if not available.
        """

        if not self._message or not self._message.poll:
            return None
        return self._message.poll.get_answer_count(id=self.id)

    def _to_dict(self) -> PollMediaPayload:
        data: PollMediaPayload = {'text': self.text}

        if self.emoji is not None:
            if isinstance(self.emoji, PartialEmoji):
                data['emoji'] = self.emoji.to_dict()
            else:
                data['emoji'] = {'name': str(self.emoji)}  # type: ignore

                if hasattr(self.emoji, 'id'):
                    data['emoji']['id'] = int(self.emoji.id)  # type: ignore

        return data


class Poll:
    """Represents a message's Poll.

    .. container:: operations

        .. describe:: str(x)

            Returns the Poll's question

        .. describe:: len(x)

            Returns the Poll's answer amount.

    .. versionadded:: 2.4

    Parameters
    ----------
    question: Union[:class:`PollMedia`, :class:`str`]
        The poll's question media. Text can be up to 300 characters.
    duration: :class:`datetime.timedelta`
        The duration of the poll.
    multiselect: :class:`bool`
        Whether users are allowed to select more than one answer. Defaults
        to ``True``
    layout_type: :class:`PollLayoutType`
        The layout type of the poll. Defaults to :attr:`PollLayoutType.default`
    """

    __slots__ = (
        'multiselect',
        '_answers',
        'duration',
        '_hours_duration',
        'layout_type',
        '_question_media',
        '_message',
        '_results',
        '_expiry',
        '_finalized',
        '_state',
        '_counts',
    )

    def __init__(
        self,
        question: Union[PollMedia, str],
        duration: datetime.timedelta,
        *,
        multiselect: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        if isinstance(question, str):
            self._question_media: PollMedia = PollMedia(text=question, emoji=None)
        else:
            self._question_media: PollMedia = (
                question  # At the moment this only supports text, so no need to add emoji support
            )
        self._answers: List[PollAnswer] = []
        self.duration: datetime.timedelta = duration
        self._hours_duration: float = duration.total_seconds() / 3600

        self.multiselect: bool = multiselect
        self.layout_type: PollLayoutType = layout_type

        # NOTE: These attributes are set manually when calling
        # _from_data, so it should be ``None`` now.
        self._message: Optional[Message] = None
        self._state: Optional[ConnectionState] = None
        self._finalized: bool = False
        self._counts: Optional[Dict[int, PollAnswerCount]] = None  # {answer_id: answer_count}
        self._expiry: Optional[datetime.datetime] = None

    def _update(self, message: Message) -> None:
        self._state = message._state
        self._message = message

        if not message.poll:
            # Something should go very wrong for this if block to be called
            return
        # These attributes are accessed via message.poll as there
        # is where all the data is stored
        self._expiry = message.poll.expiry
        self._finalized = message.poll._finalized
        self._counts = message.poll._counts

        for answer in self._answers:
            answer._update(message)

    @classmethod
    def _from_data(cls, *, data: PollPayload, message: Message, state: ConnectionState) -> Self:
        answers = [
            PollAnswer(data=answer, message=message) for answer in data.get('answers')
        ]  # 'message' will always have the 'poll' attr
        multiselect = data.get('allow_multiselect', False)
        layout_type = try_enum(PollLayoutType, data.get('layout_type', 1))
        question_data = data.get('question')
        question = question_data.get('text')
        expiry = utils.parse_time(data['expiry'])  # If obtained via API, then expiry is set.
        duration = expiry - message.created_at
        # self.created_at = message.created_at
        # duration = self.created_at - expiry

        if (duration.total_seconds() / 3600) > 168:  # As the duration may exceed little milliseconds then we fix it
            duration = datetime.timedelta(days=7)

        self = cls(
            duration=duration,
            multiselect=multiselect,
            layout_type=layout_type,
            question=question,
        )
        self._answers = answers
        self._message = message
        self._state = state
        self._expiry = expiry

        results = data.get('results', None)
        if results:
            self._finalized = results.get('is_finalized')
            self._counts = {
                int(count['id']): PollAnswerCount(state=state, message=message, data=count)
                for count in results.get('answer_counts')
            }

        return self

    def _to_dict(self) -> PollCreatePayload:
        data: PollCreatePayload = {
            'allow_multiselect': self.multiselect,
            'question': self._question_media.to_dict(),
            'duration': self._hours_duration,
            'layout_type': self.layout_type.value,
            'answers': [{'poll_media': answer._to_dict()} for answer in self.answers],
        }
        return data

    def __str__(self) -> str:
        return self._question_media.text

    def __repr__(self) -> str:
        return f"<Poll duration={self.duration} question=\"{self.question}\" answers={self.answers}>"

    def __len__(self) -> int:
        return len(self.answers)

    @property
    def question(self) -> str:
        """:class:`str`: Returns this poll answer question string."""
        return self._question_media.text

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`PartialEmoji`]: Returns the emoji for this poll's question."""

        return None  # As of now, polls questions don't support emojis

    @property
    def answers(self) -> List[PollAnswer]:
        """List[:class:`PollAnswer`]: Returns a read-only copy of the answers"""
        return self._answers.copy()

    @property
    def expiry(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: A datetime object representing the poll expiry, this is autocalculated using a UTC :class:`datetime.datetime` object
        and adding the poll duration.

        .. note::

            This will **always** return ``None`` if the poll is not part of a message.
        """
        return self._expiry

    @property
    def answer_counts(self) -> Optional[List[PollAnswerCount]]:
        """Optional[List[:class:`PollAnswerCount`]]: Returns a read-only copy of the
        answer counts, or ``None`` if this is user-constructed."""

        if not self._counts:
            return
        return list(self._counts.values())

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """:class:`datetime.datetime`: Returns the poll's creation time, or ``None`` if user-created."""

        if not self._message:
            return
        return self._message.created_at

    @property
    def message(self) -> Optional[Message]:
        """:class:`Message`: The message this poll is from."""
        return self._message

    @property
    def total_votes(self) -> int:
        """:class:`int`: Returns the sum of all the answer votes."""

        if not self.answer_counts:
            return 0
        return sum([count.count for count in self.answer_counts])

    def is_finalized(self) -> bool:
        """:class:`bool`: Returns whether the poll has finalized.

        It always returns ``False`` if the poll is not part of a
        fetched message. You should consider accessing this method
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

        if self._message:
            raise RuntimeError('Cannot append answers a poll recieved via a message')

        answer = PollAnswer.from_params(id=len(self.answers) + 1, text=text, emoji=emoji, message=self._message)

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

        Parameters
        ----------
        id: :class:`int`
            The ID of the answer to get.

        Returns
        -------
        Optional[:class:`PollAnswer`]
            The answer.
        """

        return utils.get(self.answers, id=id)

    def get_answer_count(
        self,
        /,
        id: int,
    ) -> Optional[PollAnswerCount]:
        """Returns the answer count with the provided ID or ``None`` if not found.

        Note that the ID, as Discord says, is the index or row where the answer is
        located in the poll UI.

        .. warning::

            This will **always** return ``None`` for user-created poll objects.

        Parameters
        ----------
        id: :class:`int`
            The ID of the answer to get the count of.

        Returns
        -------
        Optional[:class:`PollAnswerCount`]
            The answer count.
        """

        if not self._counts:
            return None
        return self._counts.get(id)

    async def end(self) -> Message:
        """|coro|

        Ends the poll.

        .. warning::

            This can only be called when the poll is accessed via :attr:`Message.poll`.

        Raises
        ------
        RuntimeError
            This poll has no attached message.
        HTTPException
            Ending the poll failed.

        Returns
        -------
        :class:`Message`
            The updated message with the poll ended and with accurate results.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise RuntimeError(
                'This method can only be called when a message is present, try using this via Message.poll.end()'
            )

        data = await self._state.http.end_poll(self._message.channel.id, self._message.id)

        self._message = Message(state=self._state, channel=self._message.channel, data=data)

        return self._message
