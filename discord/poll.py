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


from typing import Optional, List, TYPE_CHECKING, Union, AsyncIterator

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
        PollResult as PollResultPayload,
        PollAnswer as PollAnswerPayload,
    )


__all__ = (
    'Poll',
    'PollAnswer',
    'PollMedia',
)

MISSING = utils.MISSING
PollMediaEmoji = Union[PartialEmoji, Emoji, str]


class PollMedia:
    """Represents the poll media for a poll item.

    .. container:: operations

        .. describe:: str(x)

            Returns this Poll Media\'s text.

    Attributes
    ----------
    text: :class:`str`
        The displayed text
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]]
        The attached emoji for this media. This will always be ignored for a poll
        question media.
    """

    __slots__ = ('text', 'emoji')

    def __init__(self, /, text: str, emoji: Optional[PollMediaEmoji] = None) -> None:
        self.text: str = text
        self.emoji: Optional[PollMediaEmoji] = emoji

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f'<PollMedia text={self.text!r} emoji={self.emoji!r}>'

    def to_dict(self) -> PollMediaPayload:
        """Returns an API valid payload for this instance."""

        payload: PollMediaPayload = {'text': self.text}

        if isinstance(self.emoji, str):
            payload['emoji'] = {"id": None, "name": self.emoji}
        elif self.emoji is not None:
            payload['emoji'] = {"id": self.emoji.id, "name": self.emoji.name}

        return payload

    @classmethod
    def from_dict(cls, *, data: PollMediaPayload) -> Self:
        """Returns a new instance of this class from a payload.

        Parameters
        ----------
        data: :class:`dict`
            The dictionary to convert into a poll media.
        """

        emoji = data.get('emoji')

        if emoji:
            return cls(text=data['text'], emoji=PartialEmoji.from_dict(emoji))
        return cls(text=data['text'])


class PollAnswer:
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
    self_voted: :class:`bool`
        Whether the current user has voted to this answer or not.
    """

    __slots__ = ('media', 'id', '_state', '_message', '_vote_count', 'self_voted', '_poll')

    def __init__(
        self,
        *,
        message: Optional[Message],
        poll: Poll,
        data: PollAnswerWithIDPayload,
    ) -> None:
        self.media: PollMedia = PollMedia.from_dict(data=data['poll_media'])
        self.id: int = int(data['answer_id'])
        self._message: Optional[Message] = message
        self._state: Optional[ConnectionState] = message._state if message else None
        self._vote_count: int = 0
        self.self_voted: bool = False
        self._poll: Poll = poll

    def _handle_vote_event(self, added: bool) -> None:
        if added:
            self._vote_count += 1
        else:
            self._vote_count -= 1

    def _update_with_results(self, payload: PollAnswerCountPayload) -> None:
        self._vote_count = int(payload['count'])
        self.self_voted = payload['me_voted']

    def __str__(self) -> str:
        return self.media.text

    def __repr__(self) -> str:
        return f'<PollAnswer id={self.id} media={self.media!r}>'

    @classmethod
    def from_params(
        cls,
        id: int,
        text: str,
        emoji: Optional[PollMediaEmoji] = None,
        *,
        poll: Poll,
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

        return cls(data=payload, message=message, poll=poll)

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

    @property
    def vote_count(self) -> int:
        """:class:`int`: Returns an approximate votes of this answer. If the poll
        has finalized, it returns the exact amount of votes.
        """
        return self._vote_count

    @property
    def poll(self) -> Poll:
        """:class:`Poll`: Returns the parent poll of this answer"""
        return self._poll

    def _to_dict(self) -> PollAnswerPayload:
        return {
            'poll_media': self.media.to_dict(),
        }

    async def voters(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """Returns an :term:`asynchronous iterator` representing the users that have voted to this answer.

        The ``after`` parameter must represent a user
        and meet the :class:`abc.Snowflake` abc.

        .. note::

            This can only be called when the parent poll has an attached message.

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
                limit = self.vote_count or 100

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

            limit -= len(users)
            after = Object(id=int(users[-1]['id']))

            if not guild or isinstance(guild, Object):
                for raw_user in reversed(users):
                    yield User(state=self._state, data=raw_user)
                continue

            for raw_member in reversed(users):
                member_id = int(raw_member['id'])
                member = guild.get_member(member_id)

                yield member or User(state=self._state, data=raw_member)


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
        'layout_type',
        '_question_media',
        '_message',
        '_expiry',
        '_finalized',
        '_state',
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

        self.multiselect: bool = multiselect
        self.layout_type: PollLayoutType = layout_type

        # NOTE: These attributes are set manually when calling
        # _from_data, so it should be ``None`` now.
        self._message: Optional[Message] = None
        self._state: Optional[ConnectionState] = None
        self._finalized: bool = False
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

    def _handle_vote(self, answer_id: int, added: bool, self_voted: bool = False):
        answer = self.get_answer(answer_id)
        if not answer:
            return

        answer._handle_vote_event(added)
        answer.self_voted = self_voted

    @classmethod
    def _from_data(cls, *, data: PollPayload, message: Message, state: ConnectionState) -> Self:
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
        self._answers = [PollAnswer(data=answer, message=message, poll=self) for answer in data['answers']]
        self._message = message
        self._state = state
        self._expiry = expiry

        try:
            self._results = data['results']
        except KeyError:
            self._results = None

        return self

    def _to_dict(self) -> PollCreatePayload:
        data: PollCreatePayload = {
            'allow_multiselect': self.multiselect,
            'question': self._question_media.to_dict(),
            'duration': self.duration.total_seconds() / 3600,
            'layout_type': self.layout_type.value,
            'answers': [answer._to_dict() for answer in self.answers],
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
        """Optional[:class:`datetime.datetime`]: A datetime object representing the poll expiry.

        .. note::

            This will **always** return ``None`` if the poll is not part of a message.
        """
        return self._expiry

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
        return sum([answer.vote_count for answer in self.answers])

    def is_finalized(self) -> bool:
        """:class:`bool`: Returns whether the poll has finalized.

        It always returns ``False`` for stateless polls.
        """
        if not self._results:
            return False
        return self._results['is_finalized']

    is_finalised = is_finalized

    def copy(self) -> Self:
        """Returns a stateless copy of this poll.

        This is meant to be used when you want to edit a stateful poll.

        Returns
        -------
        :class:`Poll`
            The copy of the poll.
        """

        new = self.__class__(question=self.question, duration=self.duration)
        # We want to return a stateless copy of the poll, so we should not
        # override new._answers as our answers may contain a state

        for answer in self.answers:
            new.add_answer(text=answer.text, emoji=answer.emoji)

        return new

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

        Raises
        ------
        RuntimeError
            Cannot append answers to a poll recieved via message.

        Returns
        -------
        :class:`Poll`
            This poll with the new answer appended.
        """

        if self._message:
            raise RuntimeError('Cannot append answers to a poll recieved via message.')

        answer = PollAnswer.from_params(id=len(self.answers) + 1, text=text, emoji=emoji, message=self._message, poll=self)

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

    async def end(self) -> Self:
        """|coro|

        Ends the poll.

        Raises
        ------
        RuntimeError
            This poll has no attached message.
        HTTPException
            Ending the poll failed.

        Returns
        -------
        :class:`Poll`
            The updated poll.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise RuntimeError('This poll has no attached message.')

        self._message = await self._message.end_poll()

        return self
