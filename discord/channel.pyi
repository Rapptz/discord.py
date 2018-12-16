import discord.abc
import datetime

from .enums import ChannelType
from .guild import Guild
from .member import Member
from .message import Message
from .mixins import Hashable
from .permissions import Permissions
from .types import RawChannelDict
from .user import User, ClientUser
from .voice_client import VoiceClient
from .webhook import Webhook

from typing import Any, Optional, Union, List, Tuple, Iterable, Callable, Type

class TextChannel(discord.abc.Messageable, discord.abc.GuildChannel, Hashable):
    id: int
    name: str
    guild: Guild
    category_id: Optional[int]
    topic: Optional[str]
    position: int
    slowmode_delay: int
    nsfw: bool

    def __repr__(self) -> str: ...

    def permissions_for(self, member: Member) -> Permissions: ...

    @property
    def members(self) -> List[Member]: ...

    def is_nsfw(self) -> bool: ...

    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., topic: str = ..., position: int = ...,
                   nsfw: bool = ..., sync_permissions: bool = ..., category: Optional[CategoryChannel] = ...,
                   slowmode_delay: int = ...) -> None: ...

    async def delete_messages(self, messages: Iterable[Message]) -> None: ...

    async def purge(self, *, limit: int = ..., check: Optional[Callable[[Message], bool]] = ...,
                    before: Optional[Union[datetime.datetime, Message]] = ...,
                    after: Optional[Union[datetime.datetime, Message]] = ...,
                    around: Optional[Union[datetime.datetime, Message]] = ...,
                    reverse: bool = ..., bulk: bool = ...) -> List[Message]: ...

    async def webhooks(self) -> List[Webhook]: ...

    async def create_webhook(self, *, name: str, avatar: Optional[Union[bytes, bytearray]] = ...) -> Webhook: ...


class VoiceChannel(discord.abc.Connectable, discord.abc.GuildChannel, Hashable):
    id: int
    name: str
    guild: Guild
    category_id: Optional[int]
    topic: Optional[str]
    position: int
    bitrate: int
    user_limit: int

    def __repr__(self) -> str: ...

    @property
    def members(self) -> List[Member]: ...

    def permissions_for(self, member: Member) -> Permissions: ...

    async def edit(self, *, reason: Optional[str] = ..., **options: Any) -> None: ...


class CategoryChannel(discord.abc.GuildChannel, Hashable):
    id: int
    guild: Guild
    name: str
    category_id: Optional[int]
    nsfw: bool
    position: int

    def __repr__(self) -> str: ...

    def is_nsfw(self) -> bool: ...

    async def edit(self, *, reason: Optional[str] = ..., **options: Any) -> None: ...

    @property
    def channels(self) -> List[Union[TextChannel, VoiceChannel]]: ...


class DMChannel(discord.abc.Messageable, Hashable):
    id: int
    recipient: User
    me: ClientUser

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    def permissions_for(self, user: Optional[User] = ...) -> Permissions: ...


class GroupChannel(discord.abc.Messageable, Hashable):
    id: int
    me: ClientUser

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    @property
    def icon_url(self) -> str: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    def permissions_for(self, user: User) -> Permissions: ...

    async def add_recipients(self, *recipients: User) -> None: ...

    async def remove_recipients(self, *recipients: User) -> None: ...

    async def edit(self, **fields: Any) -> None: ...

    async def leave(self) -> None: ...

def _channel_factory(channel_type: Union[int, ChannelType]) -> Tuple[Optional[Type[Union[TextChannel, VoiceChannel, DMChannel, CategoryChannel, GroupChannel]]], ChannelType]: ...
