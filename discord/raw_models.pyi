from .emoji import PartialEmoji
from .http import _MessageDict, _PartialEmojiDict
from .message import Message

from typing import Any, Optional, Dict, Set, List
from typing_extensions import TypedDict, Literal

class _BaseBulkMessageDeleteDict(TypedDict, total=False):
    guild_id: str

class _BulkMessageDeleteDict(_BaseBulkMessageDeleteDict):
    ids: List[str]
    channel_id: str

class _BaseReactionActionDict(TypedDict):
    message_id: str
    channel_id: str
    user_id: str
    emoji: _PartialEmojiDict

class _ReactionActionDict(_BaseReactionActionDict, total=False):
    guild_id: str

class _BaseReactionClearDict(TypedDict):
    channel_id: int
    message_id: int

class _ReactionClearDict(_BaseReactionClearDict, total=False):
    guild_id: int

class RawMessageDeleteEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[int]
    cached_message: Optional[Message]

    def __init__(self, data: _MessageDict) -> None: ...

class RawBulkMessageDeleteEvent:
    message_ids: Set[int]
    channel_id: int
    guild_id: Optional[int]
    cached_messages: List[Message]

    def __init__(self, data: _BulkMessageDeleteDict) -> None: ...

class RawMessageUpdateEvent:
    message_id: int
    channel_id: int
    data: _MessageDict
    cached_message: Optional[Message]

    def __init__(self, data: _MessageDict) -> None: ...

class RawReactionActionEvent:
    message_id: int
    channel_id: int
    user_id: int
    emoji: PartialEmoji
    event_type: Literal['REACTION_ADD', 'REACTION_REMOVE']
    guild_id: Optional[int]

    def __init__(self, data: _ReactionActionDict, emoji: PartialEmoji) -> None: ...

class RawReactionClearEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[int]

    def __init__(self, data: _ReactionClearDict) -> None: ...
