import datetime

from .mixins import Hashable
from .guild import Guild
from .user import User
from .channel import TextChannel, VoiceChannel

from typing import Optional, Union

class Invite(Hashable):
    max_age: int
    code: str
    guild: Guild
    revoked: bool
    created_at: datetime.datetime
    temporary: bool
    uses: int
    max_uses: int
    inviter: User
    channel: Union[TextChannel, VoiceChannel]

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    def __hash__(self) -> int: ...

    @property
    def id(self) -> str: ...

    @property
    def url(self) -> str: ...

    async def delete(self, *, reason: Optional[str] = ...) -> None: ...
