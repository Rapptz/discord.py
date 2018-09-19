import datetime

from .guild import Guild
from .channel import TextChannel, DMChannel, GroupChannel, CategoryChannel, VoiceChannel
from .abc import Snowflake
from .enums import MessageType
from .member import Member
from .user import User
from .embeds import Embed
from .reaction import Reaction
from .emoji import Emoji, PartialEmoji
from .calls import CallMessage
from .role import Role

from typing import Any, Optional, List, Union, BinaryIO
from mypy_extensions import TypedDict

class Attachment:
    id: int
    size: int
    height: Optional[int]
    width: Optional[int]
    filename: str
    url: str
    proxy_url: str

    async def save(self, fp: Union[BinaryIO, str], *, seek_begin: bool = ...) -> int: ...

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
    reactions: List[Reaction]
    activity: Optional[MessageActivity]
    application: Optional[MessageApplication]

    def __repr__(self) -> str: ...

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def raw_mentions(self) -> List[int]: ...

    @property
    def raw_channel_mentions(self) -> List[int]: ...

    @property
    def raw_role_mentions(self) -> List[int]: ...

    @property
    def channel_mentions(self) -> List[Union[TextChannel, VoiceChannel, CategoryChannel]]: ...

    @property
    def clean_content(self) -> str: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    @property
    def edited_at(self) -> Optional[datetime.datetime]: ...

    @property
    def jump_url(self) -> str: ...

    @property
    def system_content(self) -> str: ...

    async def delete(self) -> None: ...

    async def edit(self, *, content: Optional[str] = ..., embed: Optional[Embed] = ...,
                   delete_after: Optional[float] = ...) -> None: ...

    async def pin(self) -> None: ...

    async def unpin(self) -> None: ...

    async def add_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str]) -> None: ...

    async def remove_reaction(self, emoji: Union[Emoji, Reaction, PartialEmoji, str], member: Member) -> None: ...

    async def clear_reactions(self) -> None: ...

    async def ack(self) -> None: ...
