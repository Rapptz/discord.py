import datetime

from .mixins import Hashable
from .abc import Snowflake
from .channel import VoiceChannel, TextChannel, CategoryChannel
from .member import Member
from .voice_client import VoiceClient
from .role import Role
from .emoji import Emoji
from .enums import VoiceRegion, VerificationLevel, ContentFilter, NotificationLevel, AuditLogAction
from .permissions import PermissionOverwrite
from .user import User
from .webhook import Webhook
from .invite import Invite
from .iterators import AuditLogIterator
from .colour import Colour
from .permissions import Permissions

from typing import List, Optional, Tuple, Dict, Union, NamedTuple, Set, Any

VALID_ICON_FORMATS: Set[str] = ...

class BanEntry(NamedTuple):
    user: User
    reason: str

class Guild(Hashable):
    name: str
    emojis: Tuple[Emoji]
    region: VoiceRegion
    afk_timeout: int
    afk_channel: Optional[VoiceChannel]
    icon: Optional[str]
    id: int
    owner_id: int
    unavailable: bool
    mfa_level: int
    verification_level: VerificationLevel
    default_notifications: NotificationLevel
    explicit_content_filter: ContentFilter
    features: List[str]
    splash: Optional[str]

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    @property
    def channels(self) -> List[Union[TextChannel, VoiceChannel, CategoryChannel]]: ...

    @property
    def large(self) -> bool: ...

    @property
    def voice_channels(self) -> List[VoiceChannel]: ...

    @property
    def me(self) -> Member: ...

    @property
    def voice_client(self) -> VoiceClient: ...

    @property
    def text_channels(self) -> List[TextChannel]: ...

    @property
    def categories(self) -> List[CategoryChannel]: ...

    def by_category(self) -> List[Tuple[Optional[CategoryChannel], List[Union[TextChannel, VoiceChannel]]]]: ...

    def get_channel(self, channel_id: int) -> Optional[Union[TextChannel, VoiceChannel, CategoryChannel]]: ...

    @property
    def system_channel(self) -> Optional[TextChannel]: ...

    @property
    def members(self) -> List[Member]: ...

    def get_member(self, user_id: int) -> Optional[Member]: ...

    @property
    def roles(self) -> List[Role]: ...

    def get_role(self, role_id: int) -> Optional[Role]: ...

    @property
    def default_role(self) -> Role: ...

    @property
    def owner(self) -> Member: ...

    @property
    def icon_url(self) -> str: ...

    def icon_url_as(self, *, format: str = ..., size: int = ...) -> str: ...

    @property
    def splash_url(self) -> str: ...

    def splash_url_as(self, *, format: str = ..., size: int = ...) -> str: ...

    @property
    def member_count(self) -> int: ...

    @property
    def chunked(self) -> bool: ...

    @property
    def shard_id(self) -> Optional[int]: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    def get_member_named(self, name: str) -> Optional[Member]: ...

    async def create_text_channel(self, name: str, *,
                                  overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                  category: Optional[CategoryChannel] = ...,
                                  reason: Optional[str] = ...) -> TextChannel: ...

    async def create_voice_channel(self, name: str, *,
                                   overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                                   category: Optional[CategoryChannel] = ...,
                                   reason: Optional[str] = ...) -> VoiceChannel: ...

    async def create_category(self, name: str, *,
                              overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = ...,
                              reason: Optional[str] = ...) -> CategoryChannel: ...

    async def leave(self) -> None: ...

    async def delete(self) -> None: ...

    async def edit(self, *, reason: Optional[str] = ..., name: str = ..., icon: Optional[bytes] = ...,
                   splash: Optional[bytes] = ..., region: VoiceRegion = ...,
                   afk_channel: Optional[VoiceChannel] = ..., afk_timeout: int = ...,
                   owner: Member = ..., verification_level: VerificationLevel = ...,
                   default_notifications: NotificationLevel = ...,
                   vanity_code: str = ..., system_channel: Optional[TextChannel] = ...) -> None: ...

    async def get_ban(self, user: Snowflake) -> BanEntry: ...

    async def bans(self) -> List[BanEntry]: ...

    async def prune_members(self, *, days: int, reason: Optional[str] = ...) -> int: ...

    async def webhooks(self) -> List[Webhook]: ...

    async def estimate_pruned_members(self, *, days: int) -> int: ...

    async def invites(self) -> List[Invite]: ...

    async def create_custom_emoji(self, *, name: str, image: Union[bytes, bytearray], reason: Optional[str] = ...) -> Emoji: ...

    async def create_role(self, *, name: str, permissions: Permissions = ..., colour: Colour = ...,
                          color: Colour = ..., hoist: bool = ..., mentionable: bool = ...,
                          reason: Optional[str] = ...) -> Role: ...

    async def kick(self, user: Snowflake, *, reason: Optional[str] = ...) -> None: ...

    async def ban(self, user: Snowflake, *, reason: Optional[str] = ..., delete_message_days: int = ...) -> None: ...

    async def unban(self, user: Snowflake, *, reason: Optional[str] = ...) -> None: ...

    async def vanity_invite(self) -> Invite: ...

    def ack(self) -> Any: ...

    def audit_logs(self, *, limit: int = ..., before: Optional[Union[Snowflake, datetime.datetime]] = ...,
                   after: Optional[Union[Snowflake, datetime.datetime]] = ...,
                   reverse: Optional[bool] = ..., user: Optional[Snowflake] = ...,
                   action: Optional[AuditLogAction] = ...) -> AuditLogIterator: ...
