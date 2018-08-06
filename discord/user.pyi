import discord.abc

from .channel import DMChannel, GroupChannel
from .enums import DefaultAvatar
from .guild import Guild
from .permissions import Permissions
from .message import Message
from .relationship import Relationship

import datetime
from typing import Any, Optional, NamedTuple, List, Set

VALID_STATIC_FORMATS: Set[str]
VALID_AVATAR_FORMATS: Set[str]

class Profile(NamedTuple):
    flags: int
    user: User
    mutual_guilds: List[Guild]
    connected_accounts: List[Any]
    premium_since: Optional[datetime.datetime]

    @property
    def nitro(self) -> bool: ...

    premium: bool

    @property
    def staff(self) -> bool: ...

    @property
    def hypesquad(self) -> bool: ...

    @property
    def partner(self) -> bool: ...


_BaseUser = discord.abc.User

class BaseUser(_BaseUser):
    name: str
    id: int
    discriminator: str
    avatar: Optional[str]
    bot: bool

    def __str__(self) -> str: ...

    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...

    def __hash__(self) -> int: ...

    @property
    def avatar_url(self) -> str: ...

    def is_avatar_animated(self) -> bool: ...

    def avatar_url_as(self, *, format: Optional[str] = ..., static_format: str = ...,
                      size: int = ...) -> str: ...

    @property
    def default_avatar(self) -> DefaultAvatar: ...

    @property
    def default_avatar_url(self) -> str: ...

    @property
    def mention(self) -> str: ...

    def permissions_in(self, channel: discord.abc.GuildChannel) -> Permissions: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    @property
    def display_name(self) -> str: ...

    def mentioned_in(self, message: Message) -> bool: ...


class ClientUser(BaseUser):
    verified: bool
    email: Optional[str]
    mfa_enabled: bool
    premium: bool

    def __repr__(self) -> str: ...

    def get_relationship(self, user_id: int) -> Optional[Relationship]: ...

    @property
    def relationships(self) -> List[Relationship]: ...

    @property
    def friends(self) -> List['User']: ...

    @property
    def blocked(self) -> List['User']: ...

    async def edit(self, *, password: str = ..., new_password: str = ..., email: str = ...,
                   username: str = ..., avatar: bytes = ...) -> None: ...

    async def create_group(self, *recipients: 'User') -> GroupChannel: ...


class User(BaseUser, discord.abc.Messageable):
    def __repr__(self) -> str: ...

    @property
    def dm_channel(self) -> Optional[DMChannel]: ...

    async def create_dm(self) -> DMChannel: ...

    @property
    def relationship(self) -> Optional['Relationship']: ...

    def is_friend(self) -> bool: ...

    def is_blocked(self) -> bool: ...

    async def block(self) -> None: ...

    async def unblock(self) -> None: ...

    async def remove_friend(self) -> None: ...

    async def send_friend_request(self) -> None: ...

    async def profile(self) -> Profile: ...
