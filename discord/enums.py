# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from enum import Enum

__all__ = (
    'ChannelType',
    'MessageType',
    'VoiceRegion',
    'SpeakingState',
    'VerificationLevel',
    'ContentFilter',
    'Status',
    'DefaultAvatar',
    'RelationshipType',
    'AuditLogAction',
    'AuditLogActionCategory',
    'UserFlags',
    'ActivityType',
    'HypeSquadHouse',
    'NotificationLevel',
    'PremiumType',
    'UserContentFilter',
    'FriendFlags',
    'Theme',
)

def fast_lookup(cls):
    # NOTE: implies hashable
    try:
        lookup = cls._value2member_map_
    except AttributeError:
        lookup = {
            member.value: member
            for member in cls.__members__
        }
    finally:
        cls.__fast_value_lookup__ = lookup
        return cls

@fast_lookup
class ChannelType(Enum):
    text     = 0
    private  = 1
    voice    = 2
    group    = 3
    category = 4
    news     = 5
    store    = 6

    def __str__(self):
        return self.name

@fast_lookup
class MessageType(Enum):
    default             = 0
    recipient_add       = 1
    recipient_remove    = 2
    call                = 3
    channel_name_change = 4
    channel_icon_change = 5
    pins_add            = 6
    new_member          = 7

@fast_lookup
class VoiceRegion(Enum):
    us_west       = 'us-west'
    us_east       = 'us-east'
    us_south      = 'us-south'
    us_central    = 'us-central'
    eu_west       = 'eu-west'
    eu_central    = 'eu-central'
    singapore     = 'singapore'
    london        = 'london'
    sydney        = 'sydney'
    amsterdam     = 'amsterdam'
    frankfurt     = 'frankfurt'
    brazil        = 'brazil'
    hongkong      = 'hongkong'
    russia        = 'russia'
    japan         = 'japan'
    southafrica   = 'southafrica'
    vip_us_east   = 'vip-us-east'
    vip_us_west   = 'vip-us-west'
    vip_amsterdam = 'vip-amsterdam'

    def __str__(self):
        return self.value

@fast_lookup
class SpeakingState(Enum):
    none       = 0
    voice      = 1
    soundshare = 2
    priority   = 4

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value

@fast_lookup
class VerificationLevel(Enum):
    none              = 0
    low               = 1
    medium            = 2
    high              = 3
    table_flip        = 3
    extreme           = 4
    double_table_flip = 4

    def __str__(self):
        return self.name

@fast_lookup
class ContentFilter(Enum):
    disabled    = 0
    no_role     = 1
    all_members = 2

    def __str__(self):
        return self.name

@fast_lookup
class UserContentFilter(Enum):
    disabled    = 0
    friends     = 1
    all_messages = 2

@fast_lookup
class FriendFlags(Enum):
    noone = 0
    mutual_guilds = 1
    mutual_friends = 2
    guild_and_friends = 3
    everyone = 4

@fast_lookup
class Theme(Enum):
    light = 'light'
    dark = 'dark'

@fast_lookup
class Status(Enum):
    online = 'online'
    offline = 'offline'
    idle = 'idle'
    dnd = 'dnd'
    do_not_disturb = 'dnd'
    invisible = 'invisible'

    def __str__(self):
        return self.value

@fast_lookup
class DefaultAvatar(Enum):
    blurple = 0
    grey    = 1
    gray    = 1
    green   = 2
    orange  = 3
    red     = 4

    def __str__(self):
        return self.name

@fast_lookup
class RelationshipType(Enum):
    friend           = 1
    blocked          = 2
    incoming_request = 3
    outgoing_request = 4

@fast_lookup
class NotificationLevel(Enum):
    all_messages  = 0
    only_mentions = 1

@fast_lookup
class AuditLogActionCategory(Enum):
    create = 1
    delete = 2
    update = 3

@fast_lookup
class AuditLogAction(Enum):
    guild_update             = 1
    channel_create           = 10
    channel_update           = 11
    channel_delete           = 12
    overwrite_create         = 13
    overwrite_update         = 14
    overwrite_delete         = 15
    kick                     = 20
    member_prune             = 21
    ban                      = 22
    unban                    = 23
    member_update            = 24
    member_role_update       = 25
    role_create              = 30
    role_update              = 31
    role_delete              = 32
    invite_create            = 40
    invite_update            = 41
    invite_delete            = 42
    webhook_create           = 50
    webhook_update           = 51
    webhook_delete           = 52
    emoji_create             = 60
    emoji_update             = 61
    emoji_delete             = 62
    message_delete           = 72

    @property
    def category(self):
        lookup = {
            AuditLogAction.guild_update:       AuditLogActionCategory.update,
            AuditLogAction.channel_create:     AuditLogActionCategory.create,
            AuditLogAction.channel_update:     AuditLogActionCategory.update,
            AuditLogAction.channel_delete:     AuditLogActionCategory.delete,
            AuditLogAction.overwrite_create:   AuditLogActionCategory.create,
            AuditLogAction.overwrite_update:   AuditLogActionCategory.update,
            AuditLogAction.overwrite_delete:   AuditLogActionCategory.delete,
            AuditLogAction.kick:               None,
            AuditLogAction.member_prune:       None,
            AuditLogAction.ban:                None,
            AuditLogAction.unban:              None,
            AuditLogAction.member_update:      AuditLogActionCategory.update,
            AuditLogAction.member_role_update: AuditLogActionCategory.update,
            AuditLogAction.role_create:        AuditLogActionCategory.create,
            AuditLogAction.role_update:        AuditLogActionCategory.update,
            AuditLogAction.role_delete:        AuditLogActionCategory.delete,
            AuditLogAction.invite_create:      AuditLogActionCategory.create,
            AuditLogAction.invite_update:      AuditLogActionCategory.update,
            AuditLogAction.invite_delete:      AuditLogActionCategory.delete,
            AuditLogAction.webhook_create:     AuditLogActionCategory.create,
            AuditLogAction.webhook_update:     AuditLogActionCategory.update,
            AuditLogAction.webhook_delete:     AuditLogActionCategory.delete,
            AuditLogAction.emoji_create:       AuditLogActionCategory.create,
            AuditLogAction.emoji_update:       AuditLogActionCategory.update,
            AuditLogAction.emoji_delete:       AuditLogActionCategory.delete,
            AuditLogAction.message_delete:     AuditLogActionCategory.delete,
        }
        return lookup[self]

    @property
    def target_type(self):
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
        elif v < 80:
            return 'message'

@fast_lookup
class UserFlags(Enum):
    staff = 1
    partner = 2
    hypesquad = 4
    bug_hunter = 8
    hypesquad_bravery = 64
    hypesquad_brilliance = 128
    hypesquad_balance = 256
    early_supporter = 512

@fast_lookup
class ActivityType(Enum):
    unknown = -1
    playing = 0
    streaming = 1
    listening = 2
    watching = 3

@fast_lookup
class HypeSquadHouse(Enum):
    bravery = 1
    brilliance = 2
    balance = 3

@fast_lookup
class PremiumType(Enum):
    nitro_classic = 1
    nitro = 2

def try_enum(cls, val):
    """A function that tries to turn the value into enum ``cls``.

    If it fails it returns the value instead.
    """

    # For some ungodly reason, `cls(x)` is *really* slow
    # For most use cases it's about 750ns per call
    # Internally this is dispatched like follows:
    # cls(x)
    # cls.__new__(cls, x)
    # cls._value2member_map[x]
    # if above fails ^
    # find it in cls._member_map.items()

    # Accessing the _value2member_map directly gives the biggest
    # boost to performance, from 750ns to 130ns

    # Now, the weird thing is that regular dict access is approx 31ns
    # So there's a slowdown in the attribute access somewhere in the
    # __getattr__ chain that I can't do much about

    # Since this relies on internals the enums have an internal shim
    # decorator that defines an alias for my own purposes or creates
    # it for me under __fast_value_lookup__

    try:
        return cls.__fast_value_lookup__[val]
    except (KeyError, AttributeError):
        return val
