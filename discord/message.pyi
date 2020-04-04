import datetime

from .guild import Guild
from .channel import TextChannel, DMChannel, GroupChannel
from .abc import Snowflake, User as _BaseUser
from .enums import MessageType
from .member import Member
from .user import User
from .embeds import Embed
from .reaction import Reaction
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .calls import CallMessage
from .role import Role
from .flags import MessageFlags
from .file import File

from typing import Any, Optional, List, Union, BinaryIO
from typing_extensions import TypedDict
from os import PathLike

class Attachment:
    id: int
    size: int
    height: Optional[int]
    width: Optional[int]
    filename: str
    url: str
    proxy_url: str

    def is_spoiler(self) -> bool: ...
    async def save(self, fp: Union[BinaryIO, PathLike[str], str], *, seek_begin: bool = ...,
                   use_cached: bool = ...) -> int: ...
    async def read(self, *, use_cached: bool = ...) -> bytes: ...
    async def to_file(self, use_cached: bool = ...) -> File: ...

class MessageActivity(TypedDict, total=False):
    type: int
    party_id: str

class MessageApplication(TypedDict):
    id: str
    name: str
    description: str
    icon: str
    cover_image: str

class Message:
    id: int
    tts: bool
    type: MessageType
    author: Union[User, Member]
    content: str
    embeds: List[Embed]
    channel: Union[TextChannel, DMChannel, GroupChannel]
    call: Optional[CallMessage]
    mention_everyone: bool
    mentions: List[Union[User, Member]]
    role_mentions: List[Role]
    webhook_id: Optional[int]
    attachments: List[Attachment]
    pinned: bool
    flags: MessageFlags
    reactions: List[Reaction]
    activity: Optional[MessageActivity]
    application: Optional[MessageApplication]

    @property
    def guild(self) -> Optional[Guild]: ...
    @property
    def raw_mentions(self) -> List[int]: ...
    @property
    def raw_channel_mentions(self) -> List[int]: ...
    @property
    def raw_role_mentions(self) -> List[int]: ...
    @property
    def channel_mentions(self) -> List[TextChannel]: ...
    @property
    def clean_content(self) -> str: ...
    @property
    def created_at(self) -> datetime.datetime: ...
    @property
    def edited_at(self) -> Optional[datetime.datetime]: ...
    @property
    def jump_url(self) -> str: ...
    def is_system(self) -> bool: ...
    @property
    def system_content(self) -> str: ...
    async def delete(self, *, delay: Optional[float] = ...) -> None: ...
    async def edit(self, *, content: Optional[str] = ..., embed: Optional[Embed] = ...,
                   suppress: bool = ..., delete_after: Optional[float] = ...) -> None: ...
    async def publish(self) -> None: ...
    async def pin(self) -> None: ...
    async def unpin(self) -> None: ...
    async def add_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str]) -> None: ...
    async def remove_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str], member: _BaseUser) -> None: ...
    async def clear_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str]) -> None: ...
    async def clear_reactions(self) -> None: ...
    async def ack(self) -> None: ...
