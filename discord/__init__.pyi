from typing import NamedTuple
from typing_extensions import Final
from .client import Client as Client
from .appinfo import AppInfo as AppInfo
from .user import User as User, ClientUser as ClientUser, Profile as Profile
from .emoji import Emoji as Emoji, PartialEmoji as PartialEmoji
from .activity import *
from .channel import *
from .guild import Guild as Guild
from .relationship import Relationship as Relationship
from .member import Member as Member, VoiceState as VoiceState
from .message import Message as Message, Attachment as Attachment
from .asset import Asset as Asset
from .errors import *
from .calls import CallMessage as CallMessage, GroupCall as GroupCall
from .permissions import Permissions as Permissions, PermissionOverwrite as PermissionOverwrite
from .role import Role as Role
from .file import File as File
from .colour import Color as Color, Colour as Colour
from .invite import Invite as Invite
from .widget import Widget as Widget, WidgetMember as WidgetMember, WidgetChannel as WidgetChannel
from .object import Object as Object
from .reaction import Reaction as Reaction
from . import utils as utils, opus as opus, abc as abc
from .enums import *
from .embeds import Embed as Embed
from .shard import AutoShardedClient as AutoShardedClient
from .player import *
from .webhook import *
from .voice_client import VoiceClient as VoiceClient
from .audit_logs import AuditLogChanges as AuditLogChanges, AuditLogEntry as AuditLogEntry, AuditLogDiff as AuditLogDiff
from .raw_models import *

class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int

__title__: Final[str] = ...
__author__: Final[str] = ...
__license__: Final[str] = ...
__copyright__: Final[str] = ...
__version__: Final[str] = ...
version_info: Final[VersionInfo] = ...
