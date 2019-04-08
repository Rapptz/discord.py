import datetime

from . import utils
from .channel import GroupChannel
from .enums import VoiceRegion
from .member import VoiceState
from .message import Message
from .types import RawVoiceStateDict
from .user import User, ClientUser

from typing import List, Optional, Union

class CallMessage:
    ended_timestamp: Optional[datetime.datetime]
    participants: Optional[List[User]]
    message: Message

    def __init__(self, message: Message, *, ended_timestamp: Optional[str] = ..., participants: List[User]) -> None: ...
    @property
    def call_ended(self) -> bool: ...
    @property
    def channel(self) -> GroupChannel: ...
    @property
    def duration(self) -> datetime.timedelta: ...

class GroupCall:
    call: CallMessage
    unavailable: Optional[bool]
    ringing: List[User]
    region: VoiceRegion

    def __init__(self, *, call: CallMessage, unavailable: bool, voice_states: List[RawVoiceStateDict] = ...,
                 region: VoiceRegion, ringing: List[int] = ...) -> None: ...
    @property
    def connected(self) -> List[Union[User, ClientUser]]: ...
    @property
    def channel(self) -> GroupChannel: ...
    def voice_state_for(self, user: Union[User, ClientUser]) -> Optional[VoiceState]: ...
