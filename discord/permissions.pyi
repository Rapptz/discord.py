from typing import Any, Iterator, Tuple, TypeVar, Optional, Type, ClassVar, Set

_T = TypeVar('_T', bound=Permissions)

class Permissions:
    value: int

    create_instant_invite: bool
    kick_members: bool
    ban_members: bool
    administrator: bool
    manage_channels: bool
    manage_guild: bool
    add_reactions: bool
    view_audit_log: bool
    priority_speaker: bool
    read_messages: bool
    send_messages: bool
    send_tts_messages: bool
    manage_messages: bool
    embed_links: bool
    attach_files: bool
    read_message_history: bool
    mention_everyone: bool
    external_emojis: bool
    connect: bool
    speak: bool
    mute_members: bool
    deafen_members: bool
    move_members: bool
    use_voice_activation: bool
    change_nickname: bool
    manage_nickname: bool
    manage_roles: bool
    manage_webhooks: bool
    manage_emojis: bool

    def __init__(self, permissions: int = ...) -> None: ...

    def __eq__(self, other: Any) -> bool: ...

    def __ne__(self, other: Any) -> bool: ...

    def __hash__(self) -> int: ...

    def __repr__(self) -> str: ...

    def __iter__(self) -> Iterator[Tuple[str, bool]]: ...

    def is_subset(self, other: Any) -> bool: ...

    def is_superset(self, other: Any) -> bool: ...

    def is_strict_subset(self, other: Any) -> bool: ...

    def is_strict_superset(self, other: Any) -> bool: ...

    def __le__(self, other: Any) -> bool: ...

    def __ge__(self, other: Any) -> bool: ...

    def __lt__(self, other: Any) -> bool: ...

    def __gt__(self, other: Any) -> bool: ...

    @classmethod
    def none(cls: Type[_T]) -> _T: ...

    @classmethod
    def all(cls: Type[_T]) -> _T: ...

    @classmethod
    def all_channel(cls: Type[_T]) -> _T: ...

    @classmethod
    def general(cls: Type[_T]) -> _T: ...

    @classmethod
    def text(cls: Type[_T]) -> _T: ...

    @classmethod
    def voice(cls: Type[_T]) -> _T: ...

    def update(self, **kwargs: Any) -> None: ...

    def handle_overwrite(self, allow: int, deny: int) -> None: ...

_OT = TypeVar('_OT', bound=PermissionOverwrite)

class PermissionOverwrite:
    VALID_NAMES: ClassVar[Set[str]]
    create_instant_invite: Optional[bool]
    kick_members: Optional[bool]
    ban_members: Optional[bool]
    administrator: Optional[bool]
    manage_channels: Optional[bool]
    manage_guild: Optional[bool]
    add_reactions: Optional[bool]
    view_audit_log: Optional[bool]
    priority_speaker: Optional[bool]
    read_messages: Optional[bool]
    send_messages: Optional[bool]
    send_tts_messages: Optional[bool]
    manage_messages: Optional[bool]
    embed_links: Optional[bool]
    attach_files: Optional[bool]
    read_message_history: Optional[bool]
    mention_everyone: Optional[bool]
    external_emojis: Optional[bool]
    connect: Optional[bool]
    speak: Optional[bool]
    mute_members: Optional[bool]
    deafen_members: Optional[bool]
    move_members: Optional[bool]
    use_voice_activation: Optional[bool]
    change_nickname: Optional[bool]
    manage_nickname: Optional[bool]
    manage_roles: Optional[bool]
    manage_webhooks: Optional[bool]
    manage_emojis: Optional[bool]

    def __init__(self, **kwargs: Any) -> None: ...

    def pair(self) -> Tuple[Permissions, Permissions]: ...

    @classmethod
    def from_pair(cls: Type[_OT], allow: Permissions, deny: Permissions) -> _OT: ...

    def is_empty(self) -> bool: ...

    def update(self, **kwargs: Any) -> None: ...

    def __iter__(self) -> Iterator[Tuple[str, Optional[bool]]]: ...
