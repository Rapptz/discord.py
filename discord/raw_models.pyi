from .emoji import PartialEmoji
from .types import RawMessageDict, RawPartialEmojiDict, RawBulkMessageDeleteDict, RawReactionActionDict, RawReactionClearDict
from .message import Message

from typing import Any, Optional, Dict, Set, List

class RawMessageDeleteEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[int]
    cached_message: Optional[Message]

    def __init__(self, data: RawMessageDict) -> None: ...

class RawBulkMessageDeleteEvent:
    message_ids: Set[int]
    channel_id: int
    guild_id: Optional[int]
    cached_messages: List[Message]

    def __init__(self, data: RawBulkMessageDeleteDict) -> None: ...

class RawMessageUpdateEvent:
    message_id: int
    data: RawMessageDict

    def __init__(self, data: RawMessageDict) -> None: ...

class RawReactionActionEvent:
    message_id: int
    channel_id: int
    user_id: int
    emoji: PartialEmoji
    guild_id: Optional[int]

    def __init__(self, data: RawReactionActionDict, emoji: PartialEmoji) -> None: ...

class RawReactionClearEvent:
    message_id: int
    channel_id: int
    guild_id: Optional[int]

    def __init__(self, data: RawReactionClearDict) -> None: ...
