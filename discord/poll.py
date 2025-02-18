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


from typing import Optional, List, TYPE_CHECKING, Union, AsyncIterator, Dict

import datetime

from .enums import PollLayoutType, try_enum, MessageType
from . import utils
from .emoji import PartialEmoji, Emoji
from .user import User
from .object import Object
from .errors import ClientException

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

    .. versionadded:: 2.4

    Attributes
    ----------
    text: :class:`str`
        The displayed text.
    emoji: Optional[Union[:class:`PartialEmoji`, :class:`Emoji`]]
        The attached emoji for this media. This is only valid for poll answers.
    """

    __slots__ = ('text', 'emoji')

    def __init__(self, /, text: str, emoji: Optional[PollMediaEmoji] = None) -> None:
        self.text: str = text
        self.emoji: Optional[Union[PartialEmoji, Emoji]] = PartialEmoji.from_str(emoji) if isinstance(emoji, str) else emoji

    def __repr__(self) -> str:
        return f'<PollMedia text={self.text!r} emoji={self.emoji!r}>'

    def to_dict(self) -> PollMediaPayload:
        payload: PollMediaPayload = {'text': self.text}

        if self.emoji is not None:
            payload['emoji'] = self.emoji._to_partial().to_dict()

        return payload

    @classmethod
    def from_dict(cls, *, data: PollMediaPayload) -> Self:
        emoji = data.get('emoji')

        if emoji:
            return cls(text=data['text'], emoji=PartialEmoji.from_dict(emoji))
        return cls(text=data['text'])


class PollAnswer:
    """Represents a poll's answer.

    .. container:: operations

        .. describe:: str(x)

            Returns this answer's text, if any.

    .. versionadded:: 2.4

    Attributes
    ----------
    id: :class:`int`
        The ID of this answer.
    media: :class:`PollMedia`
        The display data for this answer.
    self_voted: :class:`bool`
        Whether the current user has voted to this answer or not.
    """

    __slots__ = (
        'media',
        'id',
        '_state',
        '_message',
        '_vote_count',
        'self_voted',
        '_poll',
        '_victor',
    )

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
        self._victor: bool = False

    def _handle_vote_event(self, added: bool, self_voted: bool) -> None:
        if added:
            self._vote_count += 1
        else:
            self._vote_count -= 1
        self.self_voted = self_voted

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
        if emoji is not None:
            emoji = PartialEmoji.from_str(emoji) if isinstance(emoji, str) else emoji._to_partial()
            emoji_data = emoji.to_dict()
            # No need to remove animated key as it will be ignored
            poll_media['emoji'] = emoji_data

        payload: PollAnswerWithIDPayload = {'answer_id': id, 'poll_media': poll_media}

        return cls(data=payload, message=message, poll=poll)

    @property
    def text(self) -> str:
        """:class:`str`: Returns this answer's displayed text."""
        return self.media.text

    @property
    def emoji(self) -> Optional[Union[PartialEmoji, Emoji]]:
        """Optional[Union[:class:`Emoji`, :class:`PartialEmoji`]]: Returns this answer's displayed
        emoji, if any.
        """
        return self.media.emoji

    @property
    def vote_count(self) -> int:
        """:class:`int`: Returns an approximate count of votes for this answer.

        If the poll is finished, the count is exact.
        """
        return self._vote_count

    @property
    def poll(self) -> Poll:
        """:class:`Poll`: Returns the parent poll of this answer."""
        return self._poll

    def _to_dict(self) -> PollAnswerPayload:
        return {
            'poll_media': self.media.to_dict(),
        }

    @property
    def victor(self) -> bool:
        """:class:`bool`: Whether the answer is the one that had the most
        votes when the poll ended.

        .. versionadded:: 2.5

        .. note::

            If the poll has not ended, this will always return ``False``.
        """
        return self._victor

    async def voters(
        self, *, limit: Optional[int] = None, after: Optional[Snowflake] = None
    ) -> AsyncIterator[Union[User, Member]]:
        """Returns an :term:`asynchronous iterator` representing the users that have voted on this answer.

        The ``after`` parameter must represent a user
        and meet the :class:`abc.Snowflake` abc.

        This can only be called when the parent poll was sent to a message.

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
            voted on this poll answer.
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
            on this poll answer. The case where it can be a :class:`Member`
            is in a guild message context. Sometimes it can be a :class:`User`
            if the member has left the guild or if the member is not cached.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise ClientException('You cannot fetch users to a poll not sent with a message')

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
                # No more voters to fetch, terminate loop
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

    .. versionadded:: 2.4

    Parameters
    ----------
    question: Union[:class:`PollMedia`, :class:`str`]
        The poll's displayed question. The text can be up to 300 characters.
    duration: :class:`datetime.timedelta`
        The duration of the poll. Duration must be in hours.
    multiple: :class:`bool`
        Whether users are allowed to select more than one answer.
        Defaults to ``False``.
    layout_type: :class:`PollLayoutType`
        The layout type of the poll. Defaults to :attr:`PollLayoutType.default`.

    Attributes
    -----------
    duration: :class:`datetime.timedelta`
        The duration of the poll.
    multiple: :class:`bool`
        Whether users are allowed to select more than one answer.
    layout_type: :class:`PollLayoutType`
        The layout type of the poll.
    """

    __slots__ = (
        'multiple',
        '_answers',
        'duration',
        'layout_type',
        '_question_media',
        '_message',
        '_expiry',
        '_finalized',
        '_state',
        '_total_votes',
        '_victor_answer_id',
    )

    def __init__(
        self,
        question: Union[PollMedia, str],
        duration: datetime.timedelta,
        *,
        multiple: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        self._question_media: PollMedia = PollMedia(text=question, emoji=None) if isinstance(question, str) else question
        self._answers: Dict[int, PollAnswer] = {}
        self.duration: datetime.timedelta = duration

        self.multiple: bool = multiple
        self.layout_type: PollLayoutType = layout_type

        # NOTE: These attributes are set manually when calling
        # _from_data, so it should be ``None`` now.
        self._message: Optional[Message] = None
        self._state: Optional[ConnectionState] = None
        self._finalized: bool = False
        self._expiry: Optional[datetime.datetime] = None
        self._total_votes: Optional[int] = None
        self._victor_answer_id: Optional[int] = None

    def _update(self, message: Message) -> None:
        self._state = message._state
        self._message = message

        if not message.poll:
            return

        # The message's poll contains the more up to date data.
        self._expiry = message.poll.expires_at
        self._finalized = message.poll._finalized
        self._answers = message.poll._answers
        self._update_results_from_message(message)

    def _update_results_from_message(self, message: Message) -> None:
        if message.type != MessageType.poll_result or not message.embeds:
            return

        result_embed = message.embeds[0]  # Will always have 1 embed
        fields: Dict[str, str] = {field.name: field.value for field in result_embed.fields}  # type: ignore

        total_votes = fields.get('total_votes')

        if total_votes is not None:
            self._total_votes = int(total_votes)

        victor_answer = fields.get('victor_answer_id')

        if victor_answer is None:
            return  # Can't do anything else without the victor answer

        self._victor_answer_id = int(victor_answer)

        victor_answer_votes = fields['victor_answer_votes']

        answer = self._answers[self._victor_answer_id]
        answer._victor = True
        answer._vote_count = int(victor_answer_votes)
        self._answers[answer.id] = answer  # Ensure update

    def _update_results(self, data: PollResultPayload) -> None:
        self._finalized = data['is_finalized']

        for count in data['answer_counts']:
            answer = self.get_answer(int(count['id']))
            if not answer:
                continue

            answer._update_with_results(count)

    def _handle_vote(self, answer_id: int, added: bool, self_voted: bool = False):
        answer = self.get_answer(answer_id)
        if not answer:
            return

        answer._handle_vote_event(added, self_voted)

    @classmethod
    def _from_data(cls, *, data: PollPayload, message: Message, state: ConnectionState) -> Self:
        multiselect = data.get('allow_multiselect', False)
        layout_type = try_enum(PollLayoutType, data.get('layout_type', 1))
        question_data = data.get('question')
        question = question_data.get('text')
        expiry = utils.parse_time(data['expiry'])  # If obtained via API, then expiry is set.
        # expiry - message.created_at may be a few nanos away from the actual duration
        duration = datetime.timedelta(hours=round((expiry - message.created_at).total_seconds() / 3600))
        # self.created_at = message.created_at

        self = cls(
            duration=duration,
            multiple=multiselect,
            layout_type=layout_type,
            question=question,
        )
        self._answers = {
            int(answer['answer_id']): PollAnswer(data=answer, message=message, poll=self) for answer in data['answers']
        }
        self._message = message
        self._state = state
        self._expiry = expiry

        try:
            self._update_results(data['results'])
        except KeyError:
            pass

        return self

    def _to_dict(self) -> PollCreatePayload:
        data: PollCreatePayload = {
            'allow_multiselect': self.multiple,
            'question': self._question_media.to_dict(),
            'duration': self.duration.total_seconds() / 3600,
            'layout_type': self.layout_type.value,
            'answers': [answer._to_dict() for answer in self.answers],
        }
        return data

    def __repr__(self) -> str:
        return f"<Poll duration={self.duration} question=\"{self.question}\" answers={self.answers}>"

    @property
    def question(self) -> str:
        """:class:`str`: Returns this poll's question string."""
        return self._question_media.text

    @property
    def answers(self) -> List[PollAnswer]:
        """List[:class:`PollAnswer`]: Returns a read-only copy of the answers."""
        return list(self._answers.values())

    @property
    def victor_answer_id(self) -> Optional[int]:
        """Optional[:class:`int`]: The victor answer ID.

        .. versionadded:: 2.5

        .. note::

            This will **always** be ``None`` for polls that have not yet finished.
        """
        return self._victor_answer_id

    @property
    def victor_answer(self) -> Optional[PollAnswer]:
        """Optional[:class:`PollAnswer`]: The victor answer.

        .. versionadded:: 2.5

        .. note::

            This will **always** be ``None`` for polls that have not yet finished.
        """
        if self.victor_answer_id is None:
            return None
        return self.get_answer(self.victor_answer_id)

    @property
    def expires_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: A datetime object representing the poll expiry.

        .. note::

            This will **always** be ``None`` for stateless polls.
        """
        return self._expiry

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the poll's creation time.

        .. note::

            This will **always** be ``None`` for stateless polls.
        """

        if not self._message:
            return
        return self._message.created_at

    @property
    def message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: The message this poll is from."""
        return self._message

    @property
    def total_votes(self) -> int:
        """:class:`int`: Returns the sum of all the answer votes.

        If the poll has not yet finished, this is an approximate vote count.

        .. versionchanged:: 2.5
            This now returns an exact vote count when updated from its poll results message.
        """
        if self._total_votes is not None:
            return self._total_votes
        return sum([answer.vote_count for answer in self.answers])

    def is_finalised(self) -> bool:
        """:class:`bool`: Returns whether the poll has finalised.

        This always returns ``False`` for stateless polls.
        """
        return self._finalized

    is_finalized = is_finalised

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
        ClientException
            Cannot append answers to a poll that is active.

        Returns
        -------
        :class:`Poll`
            This poll with the new answer appended. This allows fluent-style chaining.
        """

        if self._message:
            raise ClientException('Cannot append answers to a poll that is active')

        answer = PollAnswer.from_params(id=len(self.answers) + 1, text=text, emoji=emoji, message=self._message, poll=self)
        self._answers[answer.id] = answer
        return self

    def get_answer(
        self,
        /,
        id: int,
    ) -> Optional[PollAnswer]:
        """Returns the answer with the provided ID or ``None`` if not found.

        Parameters
        ----------
        id: :class:`int`
            The ID of the answer to get.

        Returns
        -------
        Optional[:class:`PollAnswer`]
            The answer.
        """

        return self._answers.get(id)

    async def end(self) -> Self:
        """|coro|

        Ends the poll.

        Raises
        ------
        ClientException
            This poll has no attached message.
        HTTPException
            Ending the poll failed.

        Returns
        -------
        :class:`Poll`
            The updated poll.
        """

        if not self._message or not self._state:  # Make type checker happy
            raise ClientException('This poll has no attached message.')

        message = await self._message.end_poll()
        self._update(message)

        return self
