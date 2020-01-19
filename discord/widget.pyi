from .enums import Status
from .invite import Invite
from .user import BaseUser
from .activity import BaseActivity, Spotify
from .channel import VoiceChannel
from .invite import Invite

from datetime import datetime
from typing import Any, Optional, Union, List, Set, NamedTuple

class WidgetChannel(NamedTuple):
    id: int
    name: str
    position: int

    @property
    def mention(self) -> str: ...
    @property
    def created_at(self) -> datetime: ...

class WidgetMember(BaseUser):
    id: int
    status: Status
    nick: Optional[str]
    activity: Optional[Union[BaseActivity, Spotify]]
    deafened: Optional[bool]
    muted: Optional[bool]
    suppress: Optional[bool]
    connected_channel: Optional[VoiceChannel]

    @property
    def display_name(self) -> str: ...

class Widget:
    id: int
    name: str
    channels: Optional[List[WidgetChannel]]
    members: Optional[List[WidgetMember]]

    def __eq__(self, other: Any) -> bool: ...
    @property
    def created_at(self) -> datetime: ...
    @property
    def json_url(self) -> str: ...
    @property
    def invite_url(self) -> Optional[str]: ...
    async def fetch_invite(self, *, with_counts: bool = ...) -> Optional[Invite]: ...
