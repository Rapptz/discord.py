import discord.abc
import datetime

from .asset import Asset
from .enums import ChannelType
from .guild import Guild
from .member import Member
from .message import Message
from .mixins import Hashable
from .permissions import Permissions, PermissionOverwrite
from .role import Role
from .types import RawChannelDict
from .user import BaseUser, User, ClientUser
from .voice_client import VoiceClient
from .webhook import Webhook

from typing import Any, Optional, Union, List, Tuple, Dict, Iterable, Callable, Type

class TextChannel(discord.abc.Messageable, discord.abc.GuildChannel, Hashable):
    id: int
    name: str
    guild: Guild
    category_id: Optional[int]
    topic: Optional[str]
    position: int
    last_message_id: Optional[int]
    slowmode_delay: int
    nsfw: bool

    @property
    def type(self) -> ChannelType: ...
    def permissions_for(self, member: Member) -> Permissions: ...
    @property
    def members(self) -> List[Member]: ...
    def is_nsfw(self) -> bool: ...
    def is_news(self) -> bool: ...
    @property
    def last_message(self) -> Optional[Message]: ...
    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., topic: str = ..., position: int = ...,
                   nsfw: bool = ..., sync_permissions: bool = ..., category: Optional[CategoryChannel] = ...,
                   slowmode_delay: int = ...) -> None: ...
    async def delete_messages(self, messages: Iterable[Message]) -> None: ...
    async def purge(self, *, limit: Optional[int] = ..., check: Optional[Callable[[Message], bool]] = ...,
                    before: Optional[Union[datetime.datetime, Message]] = ...,
                    after: Optional[Union[datetime.datetime, Message]] = ...,
                    around: Optional[Union[datetime.datetime, Message]] = ...,
                    oldest_first: Optional[bool] = ..., bulk: bool = ...) -> List[Message]: ...
    async def webhooks(self) -> List[Webhook]: ...
    async def create_webhook(self, *, name: str, avatar: Optional[Union[bytes, bytearray]] = ...,
                             reason: Optional[str] = ...) -> Webhook: ...

class VoiceChannel(discord.abc.Connectable, discord.abc.GuildChannel, Hashable):
    id: int
    name: str
    guild: Guild
    category_id: Optional[int]
    position: int
    bitrate: int
    user_limit: int

    @property
    def type(self) -> ChannelType: ...
    @property
    def members(self) -> List[Member]: ...
    def permissions_for(self, member: Member) -> Permissions: ...
    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., bitrate: int = ...,
                   user_limit: int = ..., position: int = ..., sync_permissions: bool = ...,
                   category: Optional[CategoryChannel] = ...) -> None: ...

class CategoryChannel(discord.abc.GuildChannel, Hashable):
    id: int
    guild: Guild
    name: str
    category_id: Optional[int]
    position: int

    @property
    def type(self) -> ChannelType: ...
    def is_nsfw(self) -> bool: ...
    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., position: int = ...,
                   nsfw: bool = ...) -> None: ...
    @property
    def channels(self) -> List[Union[TextChannel, VoiceChannel, StoreChannel]]: ...
    @property
    def text_channels(self) -> List[TextChannel]: ...
    @property
    def voice_channels(self) -> List[VoiceChannel]: ...
    async def create_text_channel(self, name: str, *,
                                  overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                  position: int = ..., topic: str = ..., slowmode_delay: int = ..., nsfw: bool = ...,
                                  reason: Optional[str] = ...) -> TextChannel: ...
    async def create_voice_channel(self, name: str, *,
                                   overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                   bitrate: int = ..., position: int = ..., user_limit: int = ...,
                                   reason: Optional[str] = ...) -> VoiceChannel: ...

class StoreChannel(discord.abc.GuildChannel, Hashable):
    id: int
    name: str
    guild: Guild
    category_id: Optional[int]
    position: int
    nsfw: bool

    @property
    def type(self) -> ChannelType: ...
    def permissions_for(self, member: Member) -> Permissions: ...
    def is_nsfw(self) -> bool: ...
    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., position: int = ...,
                   nsfw: bool = ..., sync_permissions: bool = ..., category: Optional[CategoryChannel] = ...) -> None: ...

class DMChannel(discord.abc.Messageable, Hashable):
    id: int
    recipient: User
    me: ClientUser

    @property
    def type(self) -> ChannelType: ...
    @property
    def created_at(self) -> datetime.datetime: ...
    def permissions_for(self, user: Optional[BaseUser] = ...) -> Permissions: ...

class GroupChannel(discord.abc.Messageable, Hashable):
    id: int
    me: ClientUser
    owner: User
    icon: Optional[str]
    name: Optional[str]

    @property
    def type(self) -> ChannelType: ...
    @property
    def icon_url(self) -> Asset: ...
    @property
    def created_at(self) -> datetime.datetime: ...
    def permissions_for(self, user: BaseUser) -> Permissions: ...
    async def add_recipients(self, *recipients: User) -> None: ...
    async def remove_recipients(self, *recipients: User) -> None: ...
    async def edit(self, name: Optional[str] = ..., icon: Optional[bytes] = ...) -> None: ...
    async def leave(self) -> None: ...
