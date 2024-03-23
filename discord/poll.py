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

from .enums import PollLayoutType, try_enum
from . import utils
from .emoji import PartialEmoji, Emoji

if TYPE_CHECKING:
    from typing_extensions import Self

    from .message import Message
    from .types.poll import (
        Poll as PollPayload,
        PollAnswer as PollAnswerPayload,
        PollAnswerMedia as PollAnswerMediaPayload,
        PollResult as PollResultPayload,
        PollAnswerCount as PollAnswerCountPayload,
    )


__all__ = (
    'Poll',
    'PollAnswer',
)

MISSING = utils.MISSING

PollDuration = Literal[1, 24, 72, 168]


class PollAnswer:
    """Represents a poll's answer.

    .. container:: operations

        .. describe:: str(x)

            Returns this answer's text, if any.

    Attributes
    ----------
    text: Optional[:class:`str`]
        The answers display text, or ``None`` if there
        isn't.
    emoji: Union[:class:`PartialEmoji`, :class:`Emoji`, :class:`str`]
        The emoji to show up with this answer.
    """

    __slots__ = ('text', 'emoji')

    def __init__(self, text: str, *, emoji: Union[PartialEmoji, Emoji, str] = MISSING) -> None:
        self.text: str = text
        self.emoji: Optional[Union[PartialEmoji, Emoji, str]] = emoji if emoji is not MISSING else None

    @classmethod
    def _from_data(cls, data: PollAnswerPayload) -> Self:
        media = data['poll_media']
        text = media['text']
        emoji = media.get('emoji', None)

        if emoji:
            partial_emoji = PartialEmoji(name=emoji['name'], id=emoji.get('id', None))

            return cls(text=text, emoji=partial_emoji)

        return cls(text=text)

    def _to_dict(self) -> PollAnswerMediaPayload:
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


class PollAnswerCount:
    """Represents a poll answer count.
    
    Attributes
    ----------
    id: :class:`int`
        The ID for the answer.
    count: :class:`int`
        The amount of votes this answer currently has.
    me_voted: :class:`bool`
        Whether the current user voted for this answer or not.
    """

    __slots__ = ('id', 'count', 'me_voted')

    def __init__(self, data: PollAnswerCountPayload) -> None:
        self.id: int = int(data.get('id'))
        self.count: int = int(data.get('count'))
        self.me_voted: bool = data.get('me_voted')


class PollResults:
    """Represents a poll result.
    
    Attributes
    ----------
    answers: List[:class:`PollAnswerCount`]
        The counts for each answer.
    finalized: :class:`bool`
        Whether the votes are precise or not.

        If this is ``False`` then the answer counts could be
        wrongly counted. This is a Discord issue.
    """

    __slots__ = (
        '_answers',
        'finalized'
    )

    def __init__(self, data: PollResultPayload) -> None:
        self._answers: List[PollAnswerCount] = [
            PollAnswerCount(count) # type: ignore # For some strange reason type checker thinks this is a str
            for count in data.get('answer_counts')
        ]
        self.finalized: bool = data.get('is_finalized')

    @property
    def answers(self) -> List[PollAnswerCount]:
        """List[:class:`PollAnswerCount`]: The counts for each answer"""
        return self._answers.copy()


class Poll:
    """Represents a message's Poll.

    .. container:: operations

        .. describe:: str(x)

            Returns the Poll's question

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
    )

    def __init__(
        self,
        question: str,
        duration: PollDuration,
        *,
        answers: Optional[List[PollAnswer]] = None,
        multiselect: bool = False,
        layout_type: PollLayoutType = PollLayoutType.default,
    ) -> None:
        if answers and len(answers) > 10:
            raise ValueError('max answers for polls are 10')

        self.question: str = question
        self._answers: List[PollAnswer] = answers or []
        self.duration: int = duration
        self.multiselect: bool = multiselect
        self.layout_type: PollLayoutType = layout_type
        self._message: Optional[Message] = None

    @property
    def answers(self) -> List[PollAnswer]:
        """List[:class:`PollAnswer`]: Returns a read-only copy of the answers"""
        return self._answers.copy()

    @classmethod
    def _from_data(cls, data: PollPayload, message: Message) -> Self:
        answers = [PollAnswer._from_data(answer) for answer in data.get('answers')]
        multiselect = data.get('allow_multiselect', False)
        duration = data.get('duration')
        layout_type = try_enum(PollLayoutType, data.get('layout_type', 1))
        question_data = data.get('question')
        question = question_data.get('text')

        self = cls(
            answers=answers,
            duration=duration,
            multiselect=multiselect,
            layout_type=layout_type,
            question=question,
        )
        self._message = message

        return self

    def __str__(self) -> str:
        return self.question

    def __repr__(self) -> str:
        return f"<Poll duration={self.duration} question=\"{self.question}\" answers={self.answers}>"

    def _to_dict(self) -> PollPayload:
        data = {}
        data['allow_multiselect'] = self.multiselect
        data['question'] = {'text': self.question}
        data['duration'] = self.duration
        data['layout_type'] = self.layout_type.value
        data['answers'] = [{'poll_media': answer._to_dict()} for answer in self.answers]

        return data  # type: ignore

    def add_answer(
        self,
        *,
        text: str,
        emoji: Union[PartialEmoji, Emoji, str] = MISSING
    ) -> Self:
        if len(self._answers) >= 10:
            raise ValueError('max answers for polls are 10')

        self._answers.append(
            PollAnswer(
                text=text,
                emoji=emoji
            )
        )

        return self
    
    @property
    def message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: Returns the message this poll is from.
        
        This can only be a value if it is accessed from ``Message.poll``.
        """

        return self._message
    
    async def end(self) -> None:
        """Ends the poll.
        
        This can only be called when the poll is accessed via ``Message.poll``.
        """

        if not self.message:
            raise RuntimeError(
                'This method can only be called when a message is present try using this via Message.poll.end()'
            )
        
        await self.message._state.http.end_poll(self.message.channel.id, self.message.id)

