"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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
from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, Iterator, Mapping

__all__ = (
    'Enum',
    'ChannelType',
    'MessageType',
    'SpeakingState',
    'VerificationLevel',
    'ContentFilter',
    'Status',
    'DefaultAvatar',
    'AuditLogAction',
    'AuditLogActionCategory',
    'UserFlags',
    'ActivityType',
    'NotificationLevel',
    'HighlightLevel',
    'ApplicationMembershipState',
    'PayoutAccountStatus',
    'PayoutStatus',
    'PayoutReportType',
    'WebhookType',
    'ExpireBehaviour',
    'ExpireBehavior',
    'StickerType',
    'StickerFormatType',
    'InviteTarget',
    'VideoQualityMode',
    'ComponentType',
    'ButtonStyle',
    'TextStyle',
    'GiftStyle',
    'PrivacyLevel',
    'InteractionType',
    'NSFWLevel',
    'MFALevel',
    'Locale',
    'EntityType',
    'EventStatus',
    'AppCommandType',
    'AppCommandOptionType',
    'RelationshipType',
    'HypeSquadHouse',
    'PremiumType',
    'UserContentFilter',
    'Theme',
    'StickerAnimationOptions',
    'SpoilerRenderOptions',
    'InboxTab',
    'EmojiPickerSection',
    'StickerPickerSection',
    'RequiredActionType',
    'ReportType',
    'ApplicationVerificationState',
    'StoreApplicationState',
    'RPCApplicationState',
    'ApplicationDiscoverabilityState',
    'InviteType',
    'ScheduledEventStatus',
    'ScheduledEventEntityType',
    'ApplicationType',
    'EmbeddedActivityPlatform',
    'EmbeddedActivityOrientation',
    'ConnectionType',
    'ClientType',
    'PaymentSourceType',
    'PaymentGateway',
    'SubscriptionType',
    'SubscriptionStatus',
    'SubscriptionInvoiceStatus',
    'SubscriptionDiscountType',
    'SubscriptionInterval',
    'SubscriptionPlanPurchaseType',
    'PaymentStatus',
    'ApplicationAssetType',
    'SKUType',
    'SKUAccessLevel',
    'SKUFeature',
    'SKUGenre',
    'OperatingSystem',
    'ContentRatingAgency',
    'Distributor',
    'EntitlementType',
    'AutoModRuleTriggerType',
    'AutoModRuleEventType',
    'AutoModRuleActionType',
    'ForumLayoutType',
    'ForumOrderType',
)

if TYPE_CHECKING:
    from typing_extensions import Self


def _create_value_cls(name: str, comparable: bool):
    # All the type ignores here are due to the type checker being unable to recognise
    # Runtime type creation without exploding.
    cls = namedtuple('_EnumValue_' + name, 'name value')
    cls.__repr__ = lambda self: f'<{name}.{self.name}: {self.value!r}>'  # type: ignore
    cls.__str__ = lambda self: f'{name}.{self.name}'  # type: ignore
    if comparable:
        cls.__le__ = lambda self, other: isinstance(other, self.__class__) and self.value <= other.value  # type: ignore
        cls.__ge__ = lambda self, other: isinstance(other, self.__class__) and self.value >= other.value  # type: ignore
        cls.__lt__ = lambda self, other: isinstance(other, self.__class__) and self.value < other.value  # type: ignore
        cls.__gt__ = lambda self, other: isinstance(other, self.__class__) and self.value > other.value  # type: ignore
    return cls


def _is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')


class EnumMeta(type):
    if TYPE_CHECKING:
        __name__: ClassVar[str]
        _enum_member_names_: ClassVar[List[str]]
        _enum_member_map_: ClassVar[Dict[str, Any]]
        _enum_value_map_: ClassVar[Dict[Any, Any]]

    def __new__(cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any], *, comparable: bool = False) -> Self:
        value_mapping = {}
        member_mapping = {}
        member_names = []

        value_cls = _create_value_cls(name, comparable)
        for key, value in list(attrs.items()):
            is_descriptor = _is_descriptor(value)
            if key[0] == '_' and not is_descriptor:
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

        attrs['_enum_value_map_'] = value_mapping
        attrs['_enum_member_map_'] = member_mapping
        attrs['_enum_member_names_'] = member_names
        attrs['_enum_value_cls_'] = value_cls
        actual_cls = super().__new__(cls, name, bases, attrs)
        value_cls._actual_enum_cls_ = actual_cls  # type: ignore # Runtime attribute isn't understood
        return actual_cls

    def __iter__(cls) -> Iterator[Any]:
        return (cls._enum_member_map_[name] for name in cls._enum_member_names_)

    def __reversed__(cls) -> Iterator[Any]:
        return (cls._enum_member_map_[name] for name in reversed(cls._enum_member_names_))

    def __len__(cls) -> int:
        return len(cls._enum_member_names_)

    def __repr__(cls) -> str:
        return f'<enum {cls.__name__}>'

    @property
    def __members__(cls) -> Mapping[str, Any]:
        return types.MappingProxyType(cls._enum_member_map_)

    def __call__(cls, value: str) -> Any:
        try:
            return cls._enum_value_map_[value]
        except (KeyError, TypeError):
            raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    def __getitem__(cls, key: str) -> Any:
        return cls._enum_member_map_[key]

    def __setattr__(cls, name: str, value: Any) -> None:
        raise TypeError('Enums are immutable')

    def __delattr__(cls, attr: str) -> None:
        raise TypeError('Enums are immutable')

    def __instancecheck__(self, instance: Any) -> bool:
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
    text = 0
    private = 1
    voice = 2
    group = 3
    category = 4
    news = 5
    store = 6
    news_thread = 10
    public_thread = 11
    private_thread = 12
    stage_voice = 13
    forum = 15

    def __str__(self) -> str:
        return self.name

    def __int__(self):
        return self.value


class MessageType(Enum):
    default = 0
    recipient_add = 1
    recipient_remove = 2
    call = 3
    channel_name_change = 4
    channel_icon_change = 5
    channel_pinned_message = 6
    pins_add = 6
    member_join = 7
    user_join = 7
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
    chat_input_command = 20
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


class SpeakingState(Enum):
    none = 0
    voice = 1
    soundshare = 2
    priority = 4

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return self.value


class VerificationLevel(Enum, comparable=True):
    none = 0
    low = 1
    medium = 2
    high = 3
    highest = 4

    def __str__(self) -> str:
        return self.name


class ContentFilter(Enum, comparable=True):
    disabled = 0
    no_role = 1
    all_members = 2

    def __str__(self) -> str:
        return self.name


class UserContentFilter(Enum):
    disabled = 0
    non_friends = 1
    all_messages = 2

    def __int__(self) -> int:
        return self.value


class StickerAnimationOptions(Enum):
    always = 0
    on_interaction = 1
    never = 2

    def __int__(self) -> int:
        return self.value


class SpoilerRenderOptions(Enum):
    always = 'ALWAYS'
    on_click = 'ON_CLICK'
    if_moderator = 'IF_MODERATOR'

    def __str__(self) -> str:
        return self.value


class InboxTab(Enum):
    default = 0
    mentions = 1
    unreads = 2
    todos = 3
    for_you = 4

    def __int__(self) -> int:
        return self.value


class EmojiPickerSection(Enum):
    favorite = 'FAVORITES'
    top_emojis = 'TOP_GUILD_EMOJI'
    recent = 'RECENT'
    people = 'people'
    nature = 'nature'
    food = 'food'
    activity = 'activity'
    travel = 'travel'
    objects = 'objects'
    symbols = 'symbols'
    flags = 'flags'

    def __str__(self) -> str:
        return self.value


class StickerPickerSection(Enum):
    favorite = 'FAVORITE'
    recent = 'RECENT'

    def __str__(self) -> str:
        return self.value


class Theme(Enum):
    light = 'light'
    dark = 'dark'

    @classmethod
    def from_int(cls, value: int) -> Theme:
        return cls.light if value == 2 else cls.dark

    def to_int(self) -> int:
        return 2 if self is Theme.light else 1

    def __int__(self) -> int:
        return self.to_int()


class Status(Enum):
    online = 'online'
    offline = 'offline'
    idle = 'idle'
    dnd = 'dnd'
    do_not_disturb = 'dnd'
    invisible = 'invisible'
    unknown = 'unknown'

    def __str__(self) -> str:
        return self.value


class DefaultAvatar(Enum):
    blurple = 0
    grey = 1
    gray = 1
    green = 2
    orange = 3
    red = 4
    pink = 5

    def __str__(self) -> str:
        return self.name


class RelationshipType(Enum):
    none = 0  # :husk:
    friend = 1
    blocked = 2
    incoming_request = 3
    outgoing_request = 4
    implicit = 5
    suggestion = 6


class NotificationLevel(Enum, comparable=True):
    all_messages = 0
    all = 0
    only_mentions = 1
    nothing = 2
    none = 2
    server_default = 3
    default = 3

    def __int__(self):
        return self.value


class HighlightLevel(Enum):
    default = 0
    disabled = 1
    enabled = 2


class AuditLogActionCategory(Enum):
    create = 1
    delete = 2
    update = 3


class AuditLogAction(Enum):
    # fmt: off
    guild_update                  = 1
    channel_create                = 10
    channel_update                = 11
    channel_delete                = 12
    overwrite_create              = 13
    overwrite_update              = 14
    overwrite_delete              = 15
    kick                          = 20
    member_prune                  = 21
    ban                           = 22
    unban                         = 23
    member_update                 = 24
    member_role_update            = 25
    member_move                   = 26
    member_disconnect             = 27
    bot_add                       = 28
    role_create                   = 30
    role_update                   = 31
    role_delete                   = 32
    invite_create                 = 40
    invite_update                 = 41
    invite_delete                 = 42
    webhook_create                = 50
    webhook_update                = 51
    webhook_delete                = 52
    emoji_create                  = 60
    emoji_update                  = 61
    emoji_delete                  = 62
    message_delete                = 72
    message_bulk_delete           = 73
    message_pin                   = 74
    message_unpin                 = 75
    integration_create            = 80
    integration_update            = 81
    integration_delete            = 82
    stage_instance_create         = 83
    stage_instance_update         = 84
    stage_instance_delete         = 85
    sticker_create                = 90
    sticker_update                = 91
    sticker_delete                = 92
    scheduled_event_create        = 100
    scheduled_event_update        = 101
    scheduled_event_delete        = 102
    thread_create                 = 110
    thread_update                 = 111
    thread_delete                 = 112
    app_command_permission_update = 121
    automod_rule_create           = 140
    automod_rule_update           = 141
    automod_rule_delete           = 142
    automod_block_message         = 143
    automod_flag_message          = 144
    automod_timeout_member        = 145
    # fmt: on

    @property
    def category(self) -> Optional[AuditLogActionCategory]:
        # fmt: off
        lookup: Dict[AuditLogAction, Optional[AuditLogActionCategory]] = {
            AuditLogAction.guild_update:                  AuditLogActionCategory.update,
            AuditLogAction.channel_create:                AuditLogActionCategory.create,
            AuditLogAction.channel_update:                AuditLogActionCategory.update,
            AuditLogAction.channel_delete:                AuditLogActionCategory.delete,
            AuditLogAction.overwrite_create:              AuditLogActionCategory.create,
            AuditLogAction.overwrite_update:              AuditLogActionCategory.update,
            AuditLogAction.overwrite_delete:              AuditLogActionCategory.delete,
            AuditLogAction.kick:                          None,
            AuditLogAction.member_prune:                  None,
            AuditLogAction.ban:                           None,
            AuditLogAction.unban:                         None,
            AuditLogAction.member_update:                 AuditLogActionCategory.update,
            AuditLogAction.member_role_update:            AuditLogActionCategory.update,
            AuditLogAction.member_move:                   None,
            AuditLogAction.member_disconnect:             None,
            AuditLogAction.bot_add:                       None,
            AuditLogAction.role_create:                   AuditLogActionCategory.create,
            AuditLogAction.role_update:                   AuditLogActionCategory.update,
            AuditLogAction.role_delete:                   AuditLogActionCategory.delete,
            AuditLogAction.invite_create:                 AuditLogActionCategory.create,
            AuditLogAction.invite_update:                 AuditLogActionCategory.update,
            AuditLogAction.invite_delete:                 AuditLogActionCategory.delete,
            AuditLogAction.webhook_create:                AuditLogActionCategory.create,
            AuditLogAction.webhook_update:                AuditLogActionCategory.update,
            AuditLogAction.webhook_delete:                AuditLogActionCategory.delete,
            AuditLogAction.emoji_create:                  AuditLogActionCategory.create,
            AuditLogAction.emoji_update:                  AuditLogActionCategory.update,
            AuditLogAction.emoji_delete:                  AuditLogActionCategory.delete,
            AuditLogAction.message_delete:                AuditLogActionCategory.delete,
            AuditLogAction.message_bulk_delete:           AuditLogActionCategory.delete,
            AuditLogAction.message_pin:                   None,
            AuditLogAction.message_unpin:                 None,
            AuditLogAction.integration_create:            AuditLogActionCategory.create,
            AuditLogAction.integration_update:            AuditLogActionCategory.update,
            AuditLogAction.integration_delete:            AuditLogActionCategory.delete,
            AuditLogAction.stage_instance_create:         AuditLogActionCategory.create,
            AuditLogAction.stage_instance_update:         AuditLogActionCategory.update,
            AuditLogAction.stage_instance_delete:         AuditLogActionCategory.delete,
            AuditLogAction.sticker_create:                AuditLogActionCategory.create,
            AuditLogAction.sticker_update:                AuditLogActionCategory.update,
            AuditLogAction.sticker_delete:                AuditLogActionCategory.delete,
            AuditLogAction.scheduled_event_create:        AuditLogActionCategory.create,
            AuditLogAction.scheduled_event_update:        AuditLogActionCategory.update,
            AuditLogAction.scheduled_event_delete:        AuditLogActionCategory.delete,
            AuditLogAction.thread_create:                 AuditLogActionCategory.create,
            AuditLogAction.thread_delete:                 AuditLogActionCategory.delete,
            AuditLogAction.thread_update:                 AuditLogActionCategory.update,
            AuditLogAction.app_command_permission_update: AuditLogActionCategory.update,
            AuditLogAction.automod_rule_create:           AuditLogActionCategory.create,
            AuditLogAction.automod_rule_update:           AuditLogActionCategory.update,
            AuditLogAction.automod_rule_delete:           AuditLogActionCategory.delete,
            AuditLogAction.automod_block_message:         None,
            AuditLogAction.automod_flag_message:          None,
            AuditLogAction.automod_timeout_member:        None,
        }
        # fmt: on
        return lookup[self]

    @property
    def target_type(self) -> Optional[str]:
        v = self.value
        if v == -1:
            return 'all'
        elif v < 10:
            return 'guild'
        elif v < 20:
            return 'channel'
        elif v < 30:
            return 'user'
        elif v < 40:
            return 'role'
        elif v < 50:
            return 'invite'
        elif v < 60:
            return 'webhook'
        elif v < 70:
            return 'emoji'
        elif v == 73:
            return 'channel'
        elif v < 80:
            return 'message'
        elif v < 83:
            return 'integration'
        elif v < 90:
            return 'stage_instance'
        elif v < 93:
            return 'sticker'
        elif v < 103:
            return 'guild_scheduled_event'
        elif v < 113:
            return 'thread'
        elif v < 122:
            return 'integration_or_app_command'
        elif v < 143:
            return 'auto_moderation'
        elif v < 146:
            return 'user'


class UserFlags(Enum):
    staff = 1
    partner = 2
    hypesquad = 4
    bug_hunter = 8
    bug_hunter_level_1 = 8
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
    disable_premium = 2097152
    active_developer = 4194304
    quarantined = 17592186044416


class ActivityType(Enum):
    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5

    def __int__(self) -> int:
        return self.value


class HypeSquadHouse(Enum):
    bravery = 1
    brilliance = 2
    balance = 3


class PremiumType(Enum):
    none = 0
    nitro_classic = 1
    nitro = 2
    nitro_basic = 3

    @classmethod
    def from_sku_id(cls, sku_id: int) -> Optional[PremiumType]:
        if sku_id == 628379670982688768:
            return cls.none
        elif sku_id == 521846918637420545:
            return cls.nitro_classic
        elif sku_id in (521842865731534868, 521847234246082599):
            return cls.nitro
        elif sku_id == 978380684370378762:
            return cls.nitro_basic


class ApplicationMembershipState(Enum, comparable=True):
    invited = 1
    accepted = 2


class PayoutAccountStatus(Enum):
    unsubmitted = 1
    pending = 2
    action_required = 3
    active = 4
    blocked = 5
    suspended = 6


class PayoutStatus(Enum):
    open = 1
    paid = 2
    pending = 3
    manual = 4
    canceled = 5
    cancelled = 5
    deferred = 6
    deferred_internal = 7
    processing = 8
    error = 9
    rejected = 10
    risk_review = 11
    submitted = 12
    pending_funds = 13


class PayoutReportType(Enum):
    by_sku = 'sku'
    by_transaction = 'transaction'

    def __str__(self) -> str:
        return self.value


class WebhookType(Enum):
    incoming = 1
    channel_follower = 2
    application = 3


class ExpireBehaviour(Enum):
    remove_role = 0
    kick = 1

    def __int__(self) -> int:
        return self.value


ExpireBehavior = ExpireBehaviour


class StickerType(Enum):
    standard = 1
    guild = 2


class StickerFormatType(Enum):
    png = 1
    apng = 2
    lottie = 3
    gif = 4

    @property
    def file_extension(self) -> str:
        # fmt: off
        lookup: Dict[StickerFormatType, str] = {
            StickerFormatType.png: 'png',
            StickerFormatType.apng: 'png',
            StickerFormatType.lottie: 'json',
            StickerFormatType.gif: 'gif',
        }
        # fmt: on
        return lookup.get(self, 'png')


class ReportType(Enum):
    illegal_content = 1
    harassment = 2
    phishing = 3
    self_harm = 4
    nsfw_content = 5

    def __int__(self):
        return self.value


class RelationshipAction(Enum):
    send_friend_request = 'request'
    unfriend = 'unfriend'
    accept_request = 'accept'
    deny_request = 'deny'
    block = 'block'
    unblock = 'unblock'
    remove_pending_request = 'remove'


class RequiredActionType(Enum):
    update_agreements = 'AGREEMENTS'
    acknowledge_tos_update = 'TOS_UPDATE_ACKNOWLEDGMENT'
    complete_captcha = 'REQUIRE_CAPTCHA'
    verify_email = 'REQUIRE_VERIFIED_EMAIL'
    reverify_email = 'REQUIRE_REVERIFIED_EMAIL'
    verify_phone = 'REQUIRE_VERIFIED_PHONE'
    reverify_phone = 'REQUIRE_REVERIFIED_PHONE'
    reverify_email_or_verify_phone = 'REQUIRE_REVERIFIED_EMAIL_OR_VERIFIED_PHONE'
    verify_email_or_reverify_phone = 'REQUIRE_VERIFIED_EMAIL_OR_REVERIFIED_PHONE'
    reverify_email_or_reverify_phone = 'REQUIRE_REVERIFIED_EMAIL_OR_REVERIFIED_PHONE'


class InviteTarget(Enum):
    unknown = 0
    stream = 1
    embedded_application = 2
    role_subscriptions = 3
    creator_page = 4


class InviteType(Enum):
    guild = 0
    group_dm = 1
    friend = 2


class InteractionType(Enum):
    ping = 1
    application_command = 2
    component = 3
    autocomplete = 4
    modal_submit = 5

    def __int__(self) -> int:
        return self.value


class VideoQualityMode(Enum):
    auto = 1
    full = 2

    def __int__(self) -> int:
        return self.value


class ComponentType(Enum):
    action_row = 1
    button = 2
    select = 3
    text_input = 4

    def __int__(self) -> int:
        return self.value


class ButtonStyle(Enum):
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

    def __int__(self) -> int:
        return self.value


class TextStyle(Enum):
    short = 1
    paragraph = 2

    # Aliases
    long = 2

    def __int__(self) -> int:
        return self.value


class GiftStyle(Enum):
    snowglobe = 1
    box = 2
    cup = 3

    def __int__(self) -> int:
        return self.value


class PrivacyLevel(Enum):
    public = 1
    closed = 2
    guild_only = 2


class ScheduledEventEntityType(Enum):
    stage_instance = 1
    voice = 2
    external = 3


class ScheduledEventStatus(Enum):
    scheduled = 1
    active = 2
    completed = 3
    canceled = 4


class NSFWLevel(Enum, comparable=True):
    default = 0
    explicit = 1
    safe = 2
    age_restricted = 3


class MFALevel(Enum, comparable=True):
    disabled = 0
    require_2fa = 1


class ApplicationVerificationState(Enum, comparable=True):
    ineligible = 1
    unsubmitted = 2
    submitted = 3
    succeeded = 4


class StoreApplicationState(Enum, comparable=True):
    none = 1
    paid = 2
    submitted = 3
    approved = 4
    rejected = 5
    blocked = 6


class RPCApplicationState(Enum, comparable=True):
    disabled = 0
    none = 0
    unsubmitted = 1
    submitted = 2
    approved = 3
    rejected = 4


class ApplicationDiscoverabilityState(Enum, comparable=True):
    ineligible = 1
    not_discoverable = 2
    discoverable = 3
    featureable = 4
    blocked = 5


class ApplicationBuildStatus(Enum):
    created = 'CREATED'
    uploading = 'UPLOADING'
    uploaded = 'UPLOADED'
    invalid = 'INVALID'
    validating = 'VALIDATING'
    corrupted = 'CORRUPTED'
    ready = 'READY'

    def __str__(self) -> str:
        return self.value


class ApplicationType(Enum):
    game = 1
    music = 2
    ticketed_events = 3
    guild_role_subscriptions = 4

    def __int__(self) -> int:
        return self.value


class EmbeddedActivityPlatform(Enum):
    web = 'web'
    ios = 'ios'
    android = 'android'

    def __str__(self) -> str:
        return self.value


class EmbeddedActivityOrientation(Enum):
    unlocked = 1
    portrait = 2
    landscape = 3

    def __int__(self) -> int:
        return self.value


T = TypeVar('T')


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


E = TypeVar('E', bound='Enum')


class EntityType(Enum):
    stage_instance = 1
    voice = 2
    external = 3


class EventStatus(Enum):
    scheduled = 1
    active = 2
    completed = 3
    canceled = 4

    ended = 3
    cancelled = 4


class AppCommandOptionType(Enum):
    subcommand = 1
    sub_command = 1
    subcommand_group = 2
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


class AppCommandType(Enum):
    chat_input = 1
    user = 2
    message = 3

    def __int__(self) -> int:
        return self.value


class ConnectionType(Enum):
    battle_net = 'battlenet'
    contacts = 'contacts'
    crunchyroll = 'crunchyroll'
    ebay = 'ebay'
    epic_games = 'epicgames'
    facebook = 'facebook'
    github = 'github'
    league_of_legends = 'leagueoflegends'
    paypal = 'paypal'
    playstation = 'playstation'
    reddit = 'reddit'
    riot_games = 'riotgames'
    samsung = 'samsung'
    spotify = 'spotify'
    skype = 'skype'
    steam = 'steam'
    tiktok = 'tiktok'
    twitch = 'twitch'
    twitter = 'twitter'
    youtube = 'youtube'
    xbox = 'xbox'

    def __str__(self) -> str:
        return self.value


class ClientType(Enum):
    web = 'web'
    mobile = 'mobile'
    desktop = 'desktop'
    unknown = 'unknown'

    def __str__(self) -> str:
        return self.value


class PaymentSourceType(Enum):
    unknown = 0
    card = 1
    paypal = 2
    giropay = 3
    sofort = 4
    przzelewy24 = 5
    sepa_debit = 6
    paysafecard = 7
    gcash = 8
    grabpay = 9
    momo_wallet = 10
    venmo = 11
    gopay_wallet = 12
    kakaopay = 13
    bancontact = 14
    eps = 15
    ideal = 16
    payment_request = 99


class PaymentGateway(Enum):
    stripe = 1
    braintree = 2
    apple = 3
    google = 4
    adyen = 5
    apple_pay = 6

    def __int__(self) -> int:
        return self.value


class SubscriptionType(Enum):
    premium = 1
    guild = 2
    application = 3


class SubscriptionStatus(Enum):
    unpaid = 0
    active = 1
    past_due = 2
    canceled = 3
    cancelled = 3
    ended = 4
    inactive = 5
    account_hold = 6

    def __int__(self) -> int:
        return self.value


class SubscriptionInvoiceStatus(Enum, comparable=True):
    open = 1
    paid = 2
    void = 3
    uncollectible = 4


class SubscriptionDiscountType(Enum):
    subscription_plan = 1
    entitlement = 2
    premium_legacy_upgrade_promotion = 3
    premium_trial = 4


class SubscriptionInterval(Enum):
    month = 1
    year = 2
    day = 3


class SubscriptionPlanPurchaseType(Enum):
    default = 0
    gift = 1
    sale = 2
    nitro_classic = 3
    nitro = 4


class PaymentStatus(Enum):
    pending = 0
    completed = 1
    failed = 2
    reversed = 3
    refunded = 4
    canceled = 5
    cancelled = 5


class ApplicationAssetType(Enum):
    one = 1
    two = 2

    def __int__(self) -> int:
        return self.value


class SKUType(Enum):
    durable_primary = 1
    durable = 2
    consumable = 3
    bundle = 4
    subscription = 5
    group = 6

    def __int__(self) -> int:
        return self.value


class SKUAccessLevel(Enum, comparable=True):
    full = 1
    early_access = 2
    vip_access = 3

    def __int__(self) -> int:
        return self.value


class SKUFeature(Enum):
    single_player = 1
    online_multiplayer = 2
    local_multiplayer = 3
    pvp = 4
    local_coop = 5
    cross_platform = 6
    rich_presence = 7
    discord_game_invites = 8
    spectator_mode = 9
    controller_support = 10
    cloud_saves = 11
    online_coop = 12
    secure_networking = 13

    def __int__(self) -> int:
        return self.value


class SKUGenre(Enum):
    action = 1
    action_adventure = 9
    action_rpg = 2
    adventure = 8
    artillery = 50
    baseball = 34
    basketball = 35
    billiards = 36
    bowling = 37
    boxing = 38
    brawler = 3
    card_game = 58
    driving_racing = 16
    dual_joystick_shooter = 27
    dungeon_crawler = 21
    education = 59
    fighting = 56
    fishing = 32
    fitness = 60
    flight_simulator = 29
    football = 39
    four_x = 49
    fps = 26
    gambling = 61
    golf = 40
    hack_and_slash = 4
    hockey = 41
    life_simulator = 31
    light_gun = 24
    massively_multiplayer = 18
    metroidvania = 10
    mmorpg = 19
    moba = 55
    music_rhythm = 62
    open_world = 11
    party_mini_game = 63
    pinball = 64
    platformer = 5
    psychological_horror = 12
    puzzle = 57
    rpg = 22
    role_playing = 20
    rts = 51
    sandbox = 13
    shooter = 23
    shoot_em_up = 25
    simulation = 28
    skateboarding_skating = 42
    snowboarding_skiing = 43
    soccer = 44
    sports = 33
    stealth = 6
    strategy = 48
    surfing_wakeboarding = 46
    survival = 7
    survival_horror = 14
    tower_defense = 52
    track_field = 45
    train_simulator = 30
    trivia_board_game = 65
    turn_based_strategy = 53
    vehicular_combat = 17
    visual_novel = 15
    wargame = 54
    wrestling = 47

    def __int__(self) -> int:
        return self.value


# There are tons of different operating system/client enums in the API,
# so we try to unify them here
# They're normalized as the numbered enum, and converted from the stringified enums
class OperatingSystem(Enum):
    windows = 1
    macos = 2
    linux = 3

    android = -1
    ios = -1
    unknown = -1

    @classmethod
    def from_string(cls, value: str) -> Self:
        lookup = {
            'windows': cls.windows,
            'macos': cls.macos,
            'linux': cls.linux,
            'android': cls.android,
            'ios': cls.ios,
            'unknown': cls.unknown,
        }
        return lookup.get(value, create_unknown_value(cls, value))


class ContentRatingAgency(Enum):
    esrb = 1
    pegi = 2


class ESRBRating(Enum):
    everyone = 1
    everyone_ten_plus = 2
    teen = 3
    mature = 4
    adults_only = 5
    rating_pending = 6

    def __int__(self) -> int:
        return self.value


class PEGIRating(Enum):
    three = 1
    seven = 2
    twelve = 3
    sixteen = 4
    eighteen = 5

    def __int__(self) -> int:
        return self.value


class ESRBContentDescriptor(Enum):
    alcohol_reference = 1
    animated_blood = 2
    blood = 3
    blood_and_gore = 4
    cartoon_violence = 5
    comic_mischief = 6
    crude_humor = 7
    drug_reference = 8
    fantasy_violence = 9
    intense_violence = 10
    language = 11
    lyrics = 12
    mature_humor = 13
    nudity = 14
    partial_nudity = 15
    real_gambling = 16
    sexual_content = 17
    sexual_themes = 18
    sexual_violence = 19
    simulated_gambling = 20
    strong_language = 21
    strong_lyrics = 22
    strong_sexual_content = 23
    suggestive_themes = 24
    tobacco_reference = 25
    use_of_alcohol = 26
    use_of_drugs = 27
    use_of_tobacco = 28
    violence = 29
    violent_references = 30
    in_game_purchases = 31
    users_interact = 32
    shares_location = 33
    unrestricted_internet = 34
    mild_blood = 35
    mild_cartoon_violence = 36
    mild_fantasy_violence = 37
    mild_language = 38
    mild_lyrics = 39
    mild_sexual_themes = 40
    mild_suggestive_themes = 41
    mild_violence = 42
    animated_violence = 43

    def __int__(self) -> int:
        return self.value


class PEGIContentDescriptor(Enum):
    violence = 1
    bad_language = 2
    fear = 3
    gambling = 4
    sex = 5
    drugs = 6
    discrimination = 7

    def __int__(self) -> int:
        return self.value


class Distributor(Enum):
    discord = 'discord'
    steam = 'steam'
    twitch = 'twitch'
    uplay = 'uplay'
    battle_net = 'battlenet'
    origin = 'origin'
    gog = 'gog'
    epic_games = 'epic'
    google_play = 'google_play'


class EntitlementType(Enum):
    purchase = 1
    premium_subscription = 2
    developer_gift = 3
    test_mode_purchase = 4
    free_purchase = 5
    user_gift = 6
    premium_purchase = 7
    application_subscription = 8

    def __int__(self) -> int:
        return self.value


class AutoModRuleTriggerType(Enum):
    keyword = 1
    harmful_link = 2
    spam = 3
    keyword_preset = 4
    mention_spam = 5


class AutoModRuleEventType(Enum):
    message_send = 1


class AutoModRuleActionType(Enum):
    block_message = 1
    send_alert_message = 2
    timeout = 3


class ForumLayoutType(Enum):
    not_set = 0
    list_view = 1
    gallery_view = 2


class ForumOrderType(Enum):
    latest_activity = 0
    creation_date = 1


def create_unknown_value(cls: Type[E], val: Any) -> E:
    value_cls = cls._enum_value_cls_  # type: ignore # This is narrowed below
    name = f'unknown_{val}'
    return value_cls(name=name, value=val)


def try_enum(cls: Type[E], val: Any) -> E:
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns a proxy invalid value instead.
    """

    try:
        return cls._enum_value_map_[val]  # type: ignore # All errors are caught below
    except (KeyError, TypeError, AttributeError):
        return create_unknown_value(cls, val)
