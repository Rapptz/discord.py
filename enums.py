"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import types
from collections import namedtuple
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, Union

__all__ = (
    "Enum",
    "ChannelType",
    "MessageType",
    "VoiceRegion",
    "SpeakingState",
    "VerificationLevel",
    "ContentFilter",
    "Status",
    "DefaultAvatar",
    "AuditLogAction",
    "AuditLogActionCategory",
    "UserFlags",
    "ActivityType",
    "NotificationLevel",
    "TeamMembershipState",
    "WebhookType",
    "ExpireBehaviour",
    "ExpireBehavior",
    "StickerType",
    "StickerFormatType",
    "InviteTarget",
    "VideoQualityMode",
    "ComponentType",
    "ButtonStyle",
    "StagePrivacyLevel",
    "InteractionType",
    "InteractionResponseType",
    "NSFWLevel",
    "EmbeddedActivity",
    "ScheduledEventStatus",
    "ScheduledEventPrivacyLevel",
    "ScheduledEventLocationType",
    "InputTextStyle",
    "SlashCommandOptionType",
    "AutoModTriggerType",
    "AutoModEventType",
    "AutoModActionType",
    "AutoModKeywordPresetType",
    "ApplicationRoleConnectionMetadataType",
)


def _create_value_cls(name, comparable):
    cls = namedtuple(f"_EnumValue_{name}", "name value")
    cls.__repr__ = lambda self: f"<{name}.{self.name}: {self.value!r}>"
    cls.__str__ = lambda self: f"{name}.{self.name}"
    if comparable:
        cls.__le__ = (
            lambda self, other: isinstance(other, self.__class__)
            and self.value <= other.value
        )
        cls.__ge__ = (
            lambda self, other: isinstance(other, self.__class__)
            and self.value >= other.value
        )
        cls.__lt__ = (
            lambda self, other: isinstance(other, self.__class__)
            and self.value < other.value
        )
        cls.__gt__ = (
            lambda self, other: isinstance(other, self.__class__)
            and self.value > other.value
        )
    return cls


def _is_descriptor(obj):
    return (
        hasattr(obj, "__get__") or hasattr(obj, "__set__") or hasattr(obj, "__delete__")
    )


class EnumMeta(type):
    if TYPE_CHECKING:
        __name__: ClassVar[str]
        _enum_member_names_: ClassVar[list[str]]
        _enum_member_map_: ClassVar[dict[str, Any]]
        _enum_value_map_: ClassVar[dict[Any, Any]]

    def __new__(cls, name, bases, attrs, *, comparable: bool = False):
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name, comparable)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == "_" and not is_descriptor:
                continue

            # Special case classmethod to just pass through
            if isinstance(value, classmethod):
                continue

            if is_descriptor:
                setattr(value_cls, key, value)
                del attrs[key]
                continue

            try:
                new_value = value_mapping[value]
            except KeyError:
                new_value = value_cls(name=key, value=value)
                value_mapping[value] = new_value
                member_names.append(key)

            member_mapping[key] = new_value
            attrs[key] = new_value

        attrs["_enum_value_map_"] = value_mapping
        attrs["_enum_member_map_"] = member_mapping
        attrs["_enum_member_names_"] = member_names
        attrs["_enum_value_cls_"] = value_cls
        actual_cls = super().__new__(cls, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls  # type: ignore
        return actual_cls

    def __iter__(cls):
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls):
        return (
            cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_)
        )

    def __len__(cls):
        return len(cls._enum_member_names_)

    def __repr__(cls):
        return f"<enum {cls.__name__}>"

    @property
    def __members__(cls):
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value):
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __getitem__(cls, key):
        return cls._enum_member_map_[key]

    def __setattr__(cls, name, value):
        raise TypeError("Enums are immutable.")

    def __delattr__(cls, attr):
        raise TypeError("Enums are immutable")

    def __instancecheck__(self, instance):
        # isinstance(x, Y)
        # -> __instancecheck__(Y, x)
        try:
            return instance._actual_enum_cls_ is self
        except AttributeError:
            return False


if TYPE_CHECKING:
    from enum import Enum
else:

    class Enum(metaclass=EnumMeta):
        @classmethod
        def try_value(cls, value):
            try:
                return cls._enum_value_map_[value]
            except (KeyError, TypeError):
                return value


class ChannelType(Enum):
    """Channel type"""

    text = 0
    private = 1
    voice = 2
    group = 3
    category = 4
    news = 5
    news_thread = 10
    public_thread = 11
    private_thread = 12
    stage_voice = 13
    directory = 14
    forum = 15

    def __str__(self):
        return self.name


class MessageType(Enum):
    """Message type"""

    default = 0
    recipient_add = 1
    recipient_remove = 2
    call = 3
    channel_name_change = 4
    channel_icon_change = 5
    pins_add = 6
    new_member = 7
    premium_guild_subscription = 8
    premium_guild_tier_1 = 9
    premium_guild_tier_2 = 10
    premium_guild_tier_3 = 11
    channel_follow_add = 12
    guild_stream = 13
    guild_discovery_disqualified = 14
    guild_discovery_requalified = 15
    guild_discovery_grace_period_initial_warning = 16
    guild_discovery_grace_period_final_warning = 17
    thread_created = 18
    reply = 19
    application_command = 20
    thread_starter_message = 21
    guild_invite_reminder = 22
    context_menu_command = 23
    auto_moderation_action = 24
    role_subscription_purchase = 25
    interaction_premium_upsell = 26
    stage_start = 27
    stage_end = 28
    stage_speaker = 29
    stage_raise_hand = 30
    stage_topic = 31
    guild_application_premium_subscription = 32


class VoiceRegion(Enum):
    """Voice region"""

    us_west = "us-west"
    us_east = "us-east"
    us_south = "us-south"
    us_central = "us-central"
    eu_west = "eu-west"
    eu_central = "eu-central"
    singapore = "singapore"
    london = "london"
    sydney = "sydney"
    amsterdam = "amsterdam"
    frankfurt = "frankfurt"
    brazil = "brazil"
    hongkong = "hongkong"
    russia = "russia"
    japan = "japan"
    southafrica = "southafrica"
    south_korea = "south-korea"
    india = "india"
    europe = "europe"
    dubai = "dubai"
    vip_us_east = "vip-us-east"
    vip_us_west = "vip-us-west"
    vip_amsterdam = "vip-amsterdam"

    def __str__(self):
        return self.value


class SpeakingState(Enum):
    """Speaking state"""

    none = 0
    voice = 1
    soundshare = 2
    priority = 4

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


class VerificationLevel(Enum, comparable=True):
    """Verification level"""

    none = 0
    low = 1
    medium = 2
    high = 3
    highest = 4

    def __str__(self):
        return self.name


class SortOrder(Enum):
    """Forum Channel Sort Order"""

    latest_activity = 0
    creation_date = 1

    def __str__(self):
        return self.name


class ContentFilter(Enum, comparable=True):
    """Content Filter"""

    disabled = 0
    no_role = 1
    all_members = 2

    def __str__(self):
        return self.name


class Status(Enum):
    """Status"""

    online = "online"
    offline = "offline"
    idle = "idle"
    dnd = "dnd"
    do_not_disturb = "dnd"
    invisible = "invisible"
    streaming = "streaming"

    def __str__(self):
        return self.value


class DefaultAvatar(Enum):
    """Default avatar"""

    blurple = 0
    grey = 1
    gray = 1
    green = 2
    orange = 3
    red = 4

    def __str__(self):
        return self.name


class NotificationLevel(Enum, comparable=True):
    """Notification level"""

    all_messages = 0
    only_mentions = 1


class AuditLogActionCategory(Enum):
    """Audit log action category"""

    create = 1
    delete = 2
    update = 3


class AuditLogAction(Enum):
    """Audit log action"""

    guild_update = 1
    channel_create = 10
    channel_update = 11
    channel_delete = 12
    overwrite_create = 13
    overwrite_update = 14
    overwrite_delete = 15
    kick = 20
    member_prune = 21
    ban = 22
    unban = 23
    member_update = 24
    member_role_update = 25
    member_move = 26
    member_disconnect = 27
    bot_add = 28
    role_create = 30
    role_update = 31
    role_delete = 32
    invite_create = 40
    invite_update = 41
    invite_delete = 42
    webhook_create = 50
    webhook_update = 51
    webhook_delete = 52
    emoji_create = 60
    emoji_update = 61
    emoji_delete = 62
    message_delete = 72
    message_bulk_delete = 73
    message_pin = 74
    message_unpin = 75
    integration_create = 80
    integration_update = 81
    integration_delete = 82
    stage_instance_create = 83
    stage_instance_update = 84
    stage_instance_delete = 85
    sticker_create = 90
    sticker_update = 91
    sticker_delete = 92
    scheduled_event_create = 100
    scheduled_event_update = 101
    scheduled_event_delete = 102
    thread_create = 110
    thread_update = 111
    thread_delete = 112
    application_command_permission_update = 121
    auto_moderation_rule_create = 140
    auto_moderation_rule_update = 141
    auto_moderation_rule_delete = 142
    auto_moderation_block_message = 143

    @property
    def category(self) -> AuditLogActionCategory | None:
        lookup: dict[AuditLogAction, AuditLogActionCategory | None] = {
            AuditLogAction.guild_update: AuditLogActionCategory.update,
            AuditLogAction.channel_create: AuditLogActionCategory.create,
            AuditLogAction.channel_update: AuditLogActionCategory.update,
            AuditLogAction.channel_delete: AuditLogActionCategory.delete,
            AuditLogAction.overwrite_create: AuditLogActionCategory.create,
            AuditLogAction.overwrite_update: AuditLogActionCategory.update,
            AuditLogAction.overwrite_delete: AuditLogActionCategory.delete,
            AuditLogAction.kick: None,
            AuditLogAction.member_prune: None,
            AuditLogAction.ban: None,
            AuditLogAction.unban: None,
            AuditLogAction.member_update: AuditLogActionCategory.update,
            AuditLogAction.member_role_update: AuditLogActionCategory.update,
            AuditLogAction.member_move: None,
            AuditLogAction.member_disconnect: None,
            AuditLogAction.bot_add: None,
            AuditLogAction.role_create: AuditLogActionCategory.create,
            AuditLogAction.role_update: AuditLogActionCategory.update,
            AuditLogAction.role_delete: AuditLogActionCategory.delete,
            AuditLogAction.invite_create: AuditLogActionCategory.create,
            AuditLogAction.invite_update: AuditLogActionCategory.update,
            AuditLogAction.invite_delete: AuditLogActionCategory.delete,
            AuditLogAction.webhook_create: AuditLogActionCategory.create,
            AuditLogAction.webhook_update: AuditLogActionCategory.update,
            AuditLogAction.webhook_delete: AuditLogActionCategory.delete,
            AuditLogAction.emoji_create: AuditLogActionCategory.create,
            AuditLogAction.emoji_update: AuditLogActionCategory.update,
            AuditLogAction.emoji_delete: AuditLogActionCategory.delete,
            AuditLogAction.message_delete: AuditLogActionCategory.delete,
            AuditLogAction.message_bulk_delete: AuditLogActionCategory.delete,
            AuditLogAction.message_pin: None,
            AuditLogAction.message_unpin: None,
            AuditLogAction.integration_create: AuditLogActionCategory.create,
            AuditLogAction.integration_update: AuditLogActionCategory.update,
            AuditLogAction.integration_delete: AuditLogActionCategory.delete,
            AuditLogAction.stage_instance_create: AuditLogActionCategory.create,
            AuditLogAction.stage_instance_update: AuditLogActionCategory.update,
            AuditLogAction.stage_instance_delete: AuditLogActionCategory.delete,
            AuditLogAction.sticker_create: AuditLogActionCategory.create,
            AuditLogAction.sticker_update: AuditLogActionCategory.update,
            AuditLogAction.sticker_delete: AuditLogActionCategory.delete,
            AuditLogAction.scheduled_event_create: AuditLogActionCategory.create,
            AuditLogAction.scheduled_event_update: AuditLogActionCategory.update,
            AuditLogAction.scheduled_event_delete: AuditLogActionCategory.delete,
            AuditLogAction.thread_create: AuditLogActionCategory.create,
            AuditLogAction.thread_update: AuditLogActionCategory.update,
            AuditLogAction.thread_delete: AuditLogActionCategory.delete,
            AuditLogAction.application_command_permission_update: (
                AuditLogActionCategory.update
            ),
            AuditLogAction.auto_moderation_rule_create: AuditLogActionCategory.create,
            AuditLogAction.auto_moderation_rule_update: AuditLogActionCategory.update,
            AuditLogAction.auto_moderation_rule_delete: AuditLogActionCategory.delete,
            AuditLogAction.auto_moderation_block_message: None,
        }
        return lookup[self]

    @property
    def target_type(self) -> str | None:
        v = self.value
        if v == -1:
            return "all"
        elif v < 10:
            return "guild"
        elif v < 20:
            return "channel"
        elif v < 30:
            return "user"
        elif v < 40:
            return "role"
        elif v < 50:
            return "invite"
        elif v < 60:
            return "webhook"
        elif v < 70:
            return "emoji"
        elif v == 73:
            return "channel"
        elif v < 80:
            return "message"
        elif v < 83:
            return "integration"
        elif v < 90:
            return "stage_instance"
        elif v < 93:
            return "sticker"
        elif v < 103:
            return "scheduled_event"
        elif v < 113:
            return "thread"
        elif v < 122:
            return "application_command_permission"
        elif v < 144:
            return "auto_moderation_rule"


class UserFlags(Enum):
    """User flags"""

    staff = 1
    partner = 2
    hypesquad = 4
    bug_hunter = 8
    mfa_sms = 16
    premium_promo_dismissed = 32
    hypesquad_bravery = 64
    hypesquad_brilliance = 128
    hypesquad_balance = 256
    early_supporter = 512
    team_user = 1024
    partner_or_verification_application = 2048
    system = 4096
    has_unread_urgent_messages = 8192
    bug_hunter_level_2 = 16384
    underage_deleted = 32768
    verified_bot = 65536
    verified_bot_developer = 131072
    discord_certified_moderator = 262144
    bot_http_interactions = 524288
    spammer = 1048576
    active_developer = 4194304


class ActivityType(Enum):
    """Activity type"""

    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

    def __int__(self):
        return self.value


class TeamMembershipState(Enum):
    """Team membership state"""

    invited = 1
    accepted = 2


class WebhookType(Enum):
    """Webhook Type"""

    incoming = 1
    channel_follower = 2
    application = 3


class ExpireBehaviour(Enum):
    """Expire Behaviour"""

    remove_role = 0
    kick = 1


ExpireBehavior = ExpireBehaviour


class StickerType(Enum):
    """Sticker type"""

    standard = 1
    guild = 2


class StickerFormatType(Enum):
    """Sticker format Type"""

    png = 1
    apng = 2
    lottie = 3
    gif = 4

    @property
    def file_extension(self) -> str:
        lookup: dict[StickerFormatType, str] = {
            StickerFormatType.png: "png",
            StickerFormatType.apng: "png",
            StickerFormatType.lottie: "json",
            StickerFormatType.gif: "gif",
        }
        # TODO: Improve handling of unknown sticker format types if possible
        return lookup.get(self, "png")


class InviteTarget(Enum):
    """Invite target"""

    unknown = 0
    stream = 1
    embedded_application = 2


class InteractionType(Enum):
    """Interaction type"""

    ping = 1
    application_command = 2
    component = 3
    auto_complete = 4
    modal_submit = 5


class InteractionResponseType(Enum):
    """Interaction response type"""

    pong = 1
    # ack = 2 (deprecated)
    # channel_message = 3 (deprecated)
    channel_message = 4  # (with source)
    deferred_channel_message = 5  # (with source)
    deferred_message_update = 6  # for components
    message_update = 7  # for components
    auto_complete_result = 8  # for autocomplete interactions
    modal = 9  # for modal dialogs


class VideoQualityMode(Enum):
    """Video quality mode"""

    auto = 1
    full = 2

    def __int__(self):
        return self.value


class ComponentType(Enum):
    """Component type"""

    action_row = 1
    button = 2
    string_select = 3
    select = string_select  # (deprecated) alias for string_select
    input_text = 4
    user_select = 5
    role_select = 6
    mentionable_select = 7
    channel_select = 8

    def __int__(self):
        return self.value


class ButtonStyle(Enum):
    """Button style"""

    primary = 1
    secondary = 2
    success = 3
    danger = 4
    link = 5

    # Aliases
    blurple = 1
    grey = 2
    gray = 2
    green = 3
    red = 4
    url = 5

    def __int__(self):
        return self.value
class Locale(Enum):
    american_english = 'en-US'
    british_english = 'en-GB'
    bulgarian = 'bg'
    chinese = 'zh-CN'
    taiwan_chinese = 'zh-TW'
    croatian = 'hr'
    czech = 'cs'
    indonesian = 'id'
    danish = 'da'
    dutch = 'nl'
    finnish = 'fi'
    french = 'fr'
    german = 'de'
    greek = 'el'
    hindi = 'hi'
    hungarian = 'hu'
    italian = 'it'
    japanese = 'ja'
    korean = 'ko'
    lithuanian = 'lt'
    norwegian = 'no'
    polish = 'pl'
    brazil_portuguese = 'pt-BR'
    romanian = 'ro'
    russian = 'ru'
    spain_spanish = 'es-ES'
    swedish = 'sv-SE'
    thai = 'th'
    turkish = 'tr'
    ukrainian = 'uk'
    vietnamese = 'vi'

    def __str__(self) -> str:
        return self.value

class InputTextStyle(Enum):
    """Input text style"""

    short = 1
    singleline = 1
    paragraph = 2
    multiline = 2
    long = 2


class ApplicationType(Enum):
    """Application type"""

    game = 1
    music = 2
    ticketed_events = 3
    guild_role_subscriptions = 4

class AppCommandOptionType(Enum):
    subcommand = 1
    subcommand_group = 2
    string = 3
    integer = 4
    boolean = 5
    user = 6
    channel = 7
    role = 8
    mentionable = 9
    number = 10
    attachment = 11
    
class AppCommandPermissionType(Enum):
    role = 1
    user = 2
    channel = 3
    
class StagePrivacyLevel(Enum):
    """Stage privacy level"""

    # public = 1 (deprecated)
    closed = 2
    guild_only = 2

class AppCommandType(Enum):
    chat_input = 1
    user = 2
    message = 3

class NSFWLevel(Enum, comparable=True):
    """NSFW level"""

    default = 0
    explicit = 1
    safe = 2
    age_restricted = 3


class SlashCommandOptionType(Enum):
    """Slash command option type"""

    sub_command = 1
    sub_command_group = 2
    string = 3
    integer = 4
    boolean = 5
    user = 6
    channel = 7
    role = 8
    mentionable = 9
    number = 10
    attachment = 11

    @classmethod
    def from_datatype(cls, datatype):
        if isinstance(datatype, tuple):  # typing.Union has been used
            datatypes = [cls.from_datatype(op) for op in datatype]
            if all(x == cls.channel for x in datatypes):
                return cls.channel
            elif set(datatypes) <= {cls.role, cls.user}:
                return cls.mentionable
            else:
                raise TypeError("Invalid usage of typing.Union")

        py_3_10_union_type = hasattr(types, "UnionType") and isinstance(
            datatype, types.UnionType
        )

        if py_3_10_union_type or getattr(datatype, "__origin__", None) is Union:
            # Python 3.10+ "|" operator or typing.Union has been used. The __args__ attribute is a tuple of the types.
            # Type checking fails for this case, so ignore it.
            return cls.from_datatype(datatype.__args__)  # type: ignore

        if datatype.__name__ in ["Member", "User"]:
            return cls.user
        if datatype.__name__ in [
            "GuildChannel",
            "TextChannel",
            "VoiceChannel",
            "StageChannel",
            "CategoryChannel",
            "ThreadOption",
            "Thread",
            "ForumChannel",
            "DMChannel",
        ]:
            return cls.channel
        if datatype.__name__ == "Role":
            return cls.role
        if datatype.__name__ == "Attachment":
            return cls.attachment
        if datatype.__name__ == "Mentionable":
            return cls.mentionable

        if issubclass(datatype, str):
            return cls.string
        if issubclass(datatype, bool):
            return cls.boolean
        if issubclass(datatype, int):
            return cls.integer
        if issubclass(datatype, float):
            return cls.number

        from .commands.context import ApplicationContext

        if not issubclass(
            datatype, ApplicationContext
        ):  # TODO: prevent ctx being passed here in cog commands
            raise TypeError(
                f"Invalid class {datatype} used as an input type for an Option"
            )  # TODO: Improve the error message


class EmbeddedActivity(Enum):
    """Embedded activity"""

    ask_away = 976052223358406656
    awkword = 879863881349087252
    awkword_dev = 879863923543785532
    bash_out = 1006584476094177371
    betrayal = 773336526917861400
    blazing_8s = 832025144389533716
    blazing_8s_dev = 832013108234289153
    blazing_8s_qa = 832025114077298718
    blazing_8s_staging = 832025061657280566
    bobble_league = 947957217959759964
    checkers_in_the_park = 832013003968348200
    checkers_in_the_park_dev = 832012682520428625
    checkers_in_the_park_qa = 832012894068801636
    checkers_in_the_park_staging = 832012938398400562
    chess_in_the_park = 832012774040141894
    chess_in_the_park_dev = 832012586023256104
    chess_in_the_park_qa = 832012815819604009
    chess_in_the_park_staging = 832012730599735326
    decoders_dev = 891001866073296967
    doodle_crew = 878067389634314250
    doodle_crew_dev = 878067427668275241
    fishington = 814288819477020702
    know_what_i_meme = 950505761862189096
    land = 903769130790969345
    letter_league = 879863686565621790
    letter_league_dev = 879863753519292467
    poker_night = 755827207812677713
    poker_night_dev = 763133495793942528
    poker_night_qa = 801133024841957428
    poker_night_staging = 763116274876022855
    putt_party = 945737671223947305
    putt_party_dev = 910224161476083792
    putt_party_qa = 945748195256979606
    putt_party_staging = 945732077960188005
    putts = 832012854282158180
    sketch_heads = 902271654783242291
    sketch_heads_dev = 902271746701414431
    sketchy_artist = 879864070101172255
    sketchy_artist_dev = 879864104980979792
    spell_cast = 852509694341283871
    spell_cast_staging = 893449443918086174
    watch_together = 880218394199220334
    watch_together_dev = 880218832743055411
    word_snacks = 879863976006127627
    word_snacks_dev = 879864010126786570
    youtube_together = 755600276941176913


class ScheduledEventStatus(Enum):
    """Scheduled event status"""

    scheduled = 1
    active = 2
    completed = 3
    canceled = 4
    cancelled = 4

    def __int__(self):
        return self.value


class ScheduledEventPrivacyLevel(Enum):
    """Scheduled event privacy level"""

    guild_only = 2

    def __int__(self):
        return self.value


class ScheduledEventLocationType(Enum):
    """Scheduled event location type"""

    stage_instance = 1
    voice = 2
    external = 3


class AutoModTriggerType(Enum):
    """Automod trigger type"""

    keyword = 1
    harmful_link = 2
    spam = 3
    keyword_preset = 4
    mention_spam = 5


class AutoModEventType(Enum):
    """Automod event type"""

    message_send = 1


class AutoModActionType(Enum):
    """Automod action type"""

    block_message = 1
    send_alert_message = 2
    timeout = 3


class AutoModKeywordPresetType(Enum):
    """Automod keyword preset type"""

    profanity = 1
    sexual_content = 2
    slurs = 3


class ApplicationRoleConnectionMetadataType(Enum):
    """Application role connection metadata type"""

    integer_less_than_or_equal = 1
    integer_greater_than_or_equal = 2
    integer_equal = 3
    integer_not_equal = 4
    datetime_less_than_or_equal = 5
    datetime_greater_than_or_equal = 6
    boolean_equal = 7
    boolean_not_equal = 8


T = TypeVar("T")


def create_unknown_value(cls: type[T], val: Any) -> T:
    value_cls = cls._enum_value_cls_  # type: ignore
    name = f"unknown_{val}"
    return value_cls(name=name, value=val)


def try_enum(cls: type[T], val: Any) -> T:
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns a proxy invalid value instead.
    """

    try:
        return cls._enum_value_map_[val]  # type: ignore
    except (KeyError, TypeError, AttributeError):
        return create_unknown_value(cls, val)
