import datetime

from .mixins import Hashable
from .guild import Guild
from .user import User
from .channel import TextChannel, VoiceChannel
from .enums import ChannelType, VerificationLevel

from typing import Optional, Union, NamedTuple, List, Set
from typing_extensions import Literal

VALID_ICON_FORMATS: Set[str] = ...
_VALID_ICON_FORMATS = Literal['jpeg', 'jpg', 'webp', 'png']


class PartialInviteChannel(NamedTuple):
    id: int
    name: str
    type: ChannelType

    @property
    def mention(self) -> str: ...

    @property
    def created_at(self) -> datetime.datetime: ...


class PartialInviteGuild(NamedTuple):
    features: List[str]
    icon: Optional[str]
    banner: Optional[str]
    id: int
    name: str
    splash: Optional[str]
    verification_level: VerificationLevel

    @property
    def created_at(self) -> datetime.datetime: ...

    @property
    def icon_url(self) -> str: ...

    def icon_url_as(self, *, format: _VALID_ICON_FORMATS = ..., size: int = ...) -> str: ...

    @property
    def banner_url(self) -> str: ...

    def banner_url_as(self, *, format: _VALID_ICON_FORMATS = ..., size: int = ...) -> str: ...

    @property
    def splash_url(self) -> str: ...

    def splash_url_as(self, *, format: _VALID_ICON_FORMATS = ..., size: int = ...) -> str: ...


class Invite(Hashable):
    max_age: int
    code: str
    guild: Union[Guild, PartialInviteGuild]
    revoked: bool
    created_at: datetime.datetime
    temporary: bool
    uses: int
    max_uses: int
    inviter: User
    approximate_member_count: Optional[int]
    approximate_presence_count: Optional[int]
    channel: Union[TextChannel, VoiceChannel, PartialInviteChannel]

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    def __hash__(self) -> int: ...

    @property
    def id(self) -> str: ...

    @property
    def url(self) -> str: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...
