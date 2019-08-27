import abc
import datetime

from .channel import CategoryChannel
from .context_managers import Typing
from .embeds import Embed
from .file import File
from .guild import Guild
from .invite import Invite
from .iterators import HistoryIterator
from .member import Member
from .message import Message
from .permissions import Permissions, PermissionOverwrite
from .role import Role
from .user import ClientUser
from .voice_client import VoiceClient

from typing import Any, Optional, Union, List, Dict, TypeVar, overload
from typing_extensions import Protocol, runtime

_GC = TypeVar('_GC', bound=GuildChannel)

@runtime
class Snowflake(Protocol):
    id: int

    @property
    @abc.abstractmethod
    def created_at(self) -> datetime.datetime: ...

@runtime
class User(Protocol):
    name: str
    discriminator: str
    avatar: Optional[str]
    bot: bool

    @property
    @abc.abstractmethod
    def display_name(self) -> str: ...
    @property
    @abc.abstractmethod
    def mention(self) -> str: ...

@runtime
class PrivateChannel(Protocol):
    me: ClientUser

class GuildChannel:
    id: int
    name: str
    guild: Guild
    position: int
    category_id: Optional[int]

    @property
    def changed_roles(self) -> List[Role]: ...
    @property
    def mention(self) -> str: ...
    @property
    def created_at(self) -> datetime.datetime: ...
    def overwrites_for(self, obj: Union[Role, User]) -> PermissionOverwrite: ...
    @property
    def overwrites(self) -> Dict[Union[Role, Member], PermissionOverwrite]: ...
    @property
    def category(self) -> Optional[CategoryChannel]: ...
    @property
    def permissions_synced(self) -> bool: ...
    def permissions_for(self, member: Member) -> Permissions: ...
    async def delete(self, *, reason: Optional[str] = ...) -> None: ...
    @overload
    async def set_permissions(self, target: Union[Member, Role], *, overwrite: Optional[PermissionOverwrite] = ...,
                              reason: Optional[str] = ...) -> None: ...
    @overload
    async def set_permissions(self, target: Union[Member, Role], *, reason: Optional[str] = ...,
                              create_instant_invite: Optional[bool] = ..., kick_members: Optional[bool] = ...,
                              ban_members: Optional[bool] = ..., administrator: Optional[bool] = ...,
                              manage_channels: Optional[bool] = ..., manage_guild: Optional[bool] = ...,
                              add_reactions: Optional[bool] = ..., view_audit_log: Optional[bool] = ...,
                              priority_speaker: Optional[bool] = ..., stream: Optional[bool] = ...,
                              read_messages: Optional[bool] = ..., send_messages: Optional[bool] = ...,
                              send_tts_messages: Optional[bool] = ..., manage_messages: Optional[bool] = ...,
                              embed_links: Optional[bool] = ..., attach_files: Optional[bool] = ...,
                              read_message_history: Optional[bool] = ..., mention_everyone: Optional[bool] = ...,
                              external_emojis: Optional[bool] = ..., connect: Optional[bool] = ...,
                              speak: Optional[bool] = ..., mute_members: Optional[bool] = ...,
                              deafen_members: Optional[bool] = ..., move_members: Optional[bool] = ...,
                              use_voice_activation: Optional[bool] = ..., change_nickname: Optional[bool] = ...,
                              manage_nicknames: Optional[bool] = ..., manage_roles: Optional[bool] = ...,
                              manage_webhooks: Optional[bool] = ..., manage_emojis: Optional[bool] = ...) -> None: ...
    async def clone(self: _GC, *, name: Optional[str] = ..., reason: Optional[str] = ...) -> _GC: ...
    async def create_invite(self, *, reason: Optional[str] = ..., max_age: int = ..., max_uses: int = ...,
                            temporary: bool = ..., unique: bool = ...) -> Invite: ...
    async def invites(self) -> List[Invite]: ...

class Messageable(metaclass=abc.ABCMeta):
    async def send(self, content: Optional[str] = ..., *, tts: bool = ..., embed: Optional[Embed] = ...,
                   file: Optional[File] = ..., files: Optional[List[File]] = ...,
                   delete_after: Optional[float] = ..., nonce: Optional[int] = ...) -> Message: ...
    async def trigger_typing(self) -> None: ...
    def typing(self) -> Typing: ...
    async def fetch_message(self, id: int) -> Message: ...
    async def pins(self) -> List[Message]: ...
    def history(self, *, limit: Optional[int] = ...,
                before: Optional[Union[Snowflake, datetime.datetime]] = ...,
                after: Optional[Union[Snowflake, datetime.datetime]] = ...,
                around: Optional[Union[Snowflake, datetime.datetime]] = ...,
                oldest_first: Optional[bool] = ...) -> HistoryIterator: ...

class Connectable(metaclass=abc.ABCMeta):
    async def connect(self, *, timeout: float = ..., reconnect: bool = ...) -> VoiceClient: ...
