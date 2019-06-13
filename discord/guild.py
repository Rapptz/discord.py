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

import copy
from collections import namedtuple, defaultdict

from . import utils
from .role import Role
from .member import Member, VoiceState
from .activity import create_activity
from .emoji import Emoji
from .errors import InvalidData
from .permissions import PermissionOverwrite
from .colour import Colour
from .errors import InvalidArgument, ClientException
from .channel import *
from .enums import VoiceRegion, Status, ChannelType, try_enum, VerificationLevel, ContentFilter, NotificationLevel
from .mixins import Hashable
from .user import User
from .invite import Invite
from .iterators import AuditLogIterator
from .webhook import Webhook
from .widget import Widget
from .asset import Asset

BanEntry = namedtuple('BanEntry', 'reason user')
_GuildLimit = namedtuple('_GuildLimit', 'emoji bitrate filesize')

class _flag_descriptor:
    def __init__(self, func):
        self.flag = func(None)
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        return instance._has_flag(self.flag)

    def __set__(self, instance, value):
        instance._set_flag(self.flag, value)

def fill_with_flags(cls):
    cls.VALID_FLAGS = {
        name: value.flag
        for name, value in cls.__dict__.items()
        if isinstance(value, _flag_descriptor)
    }

    max_bits = max(cls.VALID_FLAGS.values()).bit_length()
    cls.ALL_OFF_VALUE = -1 + (2 ** max_bits)
    return cls

@fill_with_flags
class SystemChannelFlags:
    r"""Wraps up a Discord system channel flag value.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit the system flags easily.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.
        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """
    __slots__ = ('value',)

    def __init__(self, **kwargs):
        self.value = self.ALL_OFF_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid flag name.' % key)
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other):
        return isinstance(other, SystemChannelFlags) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<SystemChannelFlags value=%s>' % self.value

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, _flag_descriptor):
                yield (name, self._has_flag(value.flag))

    # For some reason the flags in the Discord API are "inverted"
    # ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o):
        return (self.value & o) != o

    def _set_flag(self, o, toggle):
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool.')

    @_flag_descriptor
    def join_notifications(self):
        """:class:`bool`: Returns True if the system channel is used for member join notifications."""
        return 1

    @_flag_descriptor
    def premium_subscriptions(self):
        """:class:`bool`: Returns True if the system channel is used for Nitro boosting notifications."""
        return 2


class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    name: :class:`str`
        The guild name.
    emojis: Tuple[:class:`Emoji`, ...]
        All emojis that the guild owns.
    region: :class:`VoiceRegion`
        The region the guild belongs on. There is a chance that the region
        will be a :class:`str` if the value is not recognised by the enumerator.
    afk_timeout: :class:`int`
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. None if it doesn't exist.
    icon: Optional[:class:`str`]
        The guild's icon.
    id: :class:`int`
        The guild's ID.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :meth:`Guild.id` is slim and they might
        all be None. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.
    banner: Optional[:class:`str`]
        The guild's banner.
    description: Optional[:class:`str`]
        The guild's description.
    mfa_level: :class:`int`
        Indicates the guild's two factor authorisation level. If this value is 0 then
        the guild does not require 2FA for their administrative members. If the value is
        1 then they do.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    features: List[:class:`str`]
        A list of features that the guild has. They are currently as follows:

        - ``VIP_REGIONS``: Guild has VIP voice regions
        - ``VANITY_URL``: Guild can have a vanity invite URL (e.g. discord.gg/discord-api)
        - ``INVITE_SPLASH``: Guild's invite page can have a special splash.
        - ``VERIFIED``: Guild is a verified server.
        - ``PARTNERED``: Guild is a partnered server.
        - ``MORE_EMOJI``: Guild is allowed to have more than 50 custom emoji.
        - ``DISCOVERABLE``: Guild shows up in Server Discovery.
        - ``COMMERCE``: Guild can sell things using store channels.
        - ``LURKABLE``: Users can lurk in this guild via Server Discovery.
        - ``NEWS``: Guild can create news channels.
        - ``BANNER``: Guild can upload and use a banner (i.e. :meth:`banner_url`).
        - ``ANIMATED_ICON``: Guild can upload an animated icon.

    splash: Optional[:class:`str`]
        The guild's invite splash.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        How many users have currently "boosted" this guild.
    """

    __slots__ = ('afk_timeout', 'afk_channel', '_members', '_channels', 'icon',
                 'name', 'id', 'unavailable', 'banner', 'region', '_state',
                 '_default_role', '_roles', '_member_count', '_large',
                 'owner_id', 'mfa_level', 'emojis', 'features',
                 'verification_level', 'explicit_content_filter', 'splash',
                 '_voice_states', '_system_channel_id', 'default_notifications',
                 'description', 'max_presences', 'max_members', 'premium_tier',
                 'premium_subscription_count', '_system_channel_flags')

    _PREMIUM_GUILD_LIMITS = {
        None: _GuildLimit(emoji=50, bitrate=96e3, filesize=8388608),
        0: _GuildLimit(emoji=50, bitrate=96e3, filesize=8388608),
        1: _GuildLimit(emoji=100, bitrate=128e3, filesize=8388608),
        2: _GuildLimit(emoji=150, bitrate=256e3, filesize=52428800),
        3: _GuildLimit(emoji=250, bitrate=384e3, filesize=104857600),
    }

    def __init__(self, *, data, state):
        self._channels = {}
        self._members = {}
        self._voice_states = {}
        self._state = state
        self._from_data(data)

    def _add_channel(self, channel):
        self._channels[channel.id] = channel

    def _remove_channel(self, channel):
        self._channels.pop(channel.id, None)

    def _voice_state_for(self, user_id):
        return self._voice_states.get(user_id)

    def _add_member(self, member):
        self._members[member.id] = member

    def _remove_member(self, member):
        self._members.pop(member.id, None)

    def __str__(self):
        return self.name

    def __repr__(self):
        attrs = (
            'id', 'name', 'shard_id', 'chunked'
        )
        resolved = ['%s=%r' % (attr, getattr(self, attr)) for attr in attrs]
        resolved.append('member_count=%r' % getattr(self, '_member_count', None))
        return '<Guild %s>' % ' '.join(resolved)

    def _update_voice_state(self, data, channel_id):
        user_id = int(data['user_id'])
        channel = self.get_channel(channel_id)
        try:
            # check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy.copy(after)
            after._update(data, channel)
        except KeyError:
            # if we're here then we're getting added into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        member = self.get_member(user_id)
        return member, before, after

    def _add_role(self, role):
        # roles get added to the bottom (position 1, pos 0 is @everyone)
        # so since self.roles has the @everyone role, we can't increment
        # its position because it's stuck at position 0. Luckily x += False
        # is equivalent to adding 0. So we cast the position to a bool and
        # increment it.
        for r in self._roles.values():
            r.position += (not r.is_default())

        self._roles[role.id] = role

    def _remove_role(self, role_id):
        # this raises KeyError if it fails..
        role = self._roles.pop(role_id)

        # since it didn't, we can change the positions now
        # basically the same as above except we only decrement
        # the position if we're above the role we deleted.
        for r in self._roles.values():
            r.position -= r.position > role.position

        return role

    def _from_data(self, guild):
        # according to Stan, this is always available even if the guild is unavailable
        # I don't have this guarantee when someone updates the guild.
        member_count = guild.get('member_count', None)
        if member_count:
            self._member_count = member_count

        self.name = guild.get('name')
        self.region = try_enum(VoiceRegion, guild.get('region'))
        self.verification_level = try_enum(VerificationLevel, guild.get('verification_level'))
        self.default_notifications = try_enum(NotificationLevel, guild.get('default_message_notifications'))
        self.explicit_content_filter = try_enum(ContentFilter, guild.get('explicit_content_filter', 0))
        self.afk_timeout = guild.get('afk_timeout')
        self.icon = guild.get('icon')
        self.banner = guild.get('banner')
        self.unavailable = guild.get('unavailable', False)
        self.id = int(guild['id'])
        self._roles = {}
        state = self._state # speed up attribute access
        for r in guild.get('roles', []):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role

        self.mfa_level = guild.get('mfa_level')
        self.emojis = tuple(map(lambda d: state.store_emoji(self, d), guild.get('emojis', [])))
        self.features = guild.get('features', [])
        self.splash = guild.get('splash')
        self._system_channel_id = utils._get_as_snowflake(guild, 'system_channel_id')
        self.description = guild.get('description')
        self.max_presences = guild.get('max_presences')
        self.max_members = guild.get('max_members')
        self.premium_tier = guild.get('premium_tier', 0)
        self.premium_subscription_count = guild.get('premium_subscription_count', 0)
        self._system_channel_flags = guild.get('system_channel_flags', 0)

        for mdata in guild.get('members', []):
            member = Member(data=mdata, guild=self, state=state)
            self._add_member(member)

        self._sync(guild)
        self._large = None if member_count is None else self._member_count >= 250

        self.owner_id = utils._get_as_snowflake(guild, 'owner_id')
        self.afk_channel = self.get_channel(utils._get_as_snowflake(guild, 'afk_channel_id'))

        for obj in guild.get('voice_states', []):
            self._update_voice_state(obj, int(obj['channel_id']))

    def _sync(self, data):
        try:
            self._large = data['large']
        except KeyError:
            pass

        empty_tuple = tuple()
        for presence in data.get('presences', []):
            user_id = int(presence['user']['id'])
            member = self.get_member(user_id)
            if member is not None:
                member._presence_update(presence, empty_tuple)

        if 'channels' in data:
            channels = data['channels']
            for c in channels:
                c_type = c['type']
                if c_type in (ChannelType.text.value, ChannelType.news.value):
                    self._add_channel(TextChannel(guild=self, data=c, state=self._state))
                elif c_type == ChannelType.voice.value:
                    self._add_channel(VoiceChannel(guild=self, data=c, state=self._state))
                elif c_type == ChannelType.category.value:
                    self._add_channel(CategoryChannel(guild=self, data=c, state=self._state))
                elif c_type == ChannelType.store.value:
                    self._add_channel(StoreChannel(guild=self, data=c, state=self._state))

    @property
    def channels(self):
        """List[:class:`abc.GuildChannel`]: A list of channels that belongs to this guild."""
        return list(self._channels.values())

    @property
    def large(self):
        """:class:`bool`: Indicates if the guild is a 'large' guild.

        A large guild is defined as having more than ``large_threshold`` count
        members, which for this library is set to the maximum of 250.
        """
        if self._large is None:
            try:
                return self._member_count >= 250
            except AttributeError:
                return len(self._members) >= 250
        return self._large

    @property
    def voice_channels(self):
        """List[:class:`VoiceChannel`]: A list of voice channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def me(self):
        """Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id
        return self.get_member(self_id)

    @property
    def voice_client(self):
        """Returns the :class:`VoiceClient` associated with this guild, if any."""
        return self._state._get_voice_client(self.id)

    @property
    def text_channels(self):
        """List[:class:`TextChannel`]: A list of text channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def categories(self):
        """List[:class:`CategoryChannel`]: A list of categories that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    def by_category(self):
        """Returns every :class:`CategoryChannel` and their associated channels.

        These channels and categories are sorted in the official Discord UI order.

        If the channels do not have a category, then the first element of the tuple is
        ``None``.

        Returns
        --------
        List[Tuple[Optional[:class:`CategoryChannel`], List[:class:`abc.GuildChannel`]]]:
            The categories and their associated channels.
        """
        grouped = defaultdict(list)
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                continue

            grouped[channel.category_id].append(channel)

        def key(t):
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)

        _get = self._channels.get
        as_list = [(_get(k), v) for k, v in grouped.items()]
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position, c.id))
        return as_list

    def get_channel(self, channel_id):
        """Returns a :class:`abc.GuildChannel` with the given ID. If not found, returns None."""
        return self._channels.get(channel_id)

    @property
    def system_channel(self):
        """Optional[:class:`TextChannel`]: Returns the guild's channel used for system messages.

        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def system_channel_flags(self):
        """:class:`SystemChannelFlags`: Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    @property
    def emoji_limit(self):
        """:class:`int`: The maximum number of emoji slots this guild has."""
        more_emoji = 200 if 'MORE_EMOJI' in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)

    @property
    def bitrate_limit(self):
        """:class:`float`: The maximum bitrate for voice channels this guild can have."""
        vip_guild = self._PREMIUM_GUILD_LIMITS[1].bitrate if 'VIP_REGIONS' in self.features else 96e3
        return max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)

    @property
    def filesize_limit(self):
        """:class:`int`: The maximum number of bytes files can have when uploaded to this guild."""
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize

    @property
    def members(self):
        """List[:class:`Member`]: A list of members that belong to this guild."""
        return list(self._members.values())

    def get_member(self, user_id):
        """Returns a :class:`Member` with the given ID. If not found, returns None."""
        return self._members.get(user_id)

    @property
    def premium_subscribers(self):
        """List[:class:`Member`]: A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self):
        """Returns a :class:`list` of the guild's roles in hierarchy order.

        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id):
        """Returns a :class:`Role` with the given ID. If not found, returns None."""
        return self._roles.get(role_id)

    @utils.cached_slot_property('_default_role')
    def default_role(self):
        """Gets the @everyone role that all members have by default."""
        return utils.find(lambda r: r.is_default(), self._roles.values())

    @property
    def owner(self):
        """:class:`Member`: The member that owns the guild."""
        return self.get_member(self.owner_id)

    @property
    def icon_url(self):
        """:class:`Asset`: Returns the guild's icon asset."""
        return self.icon_url_as()

    def is_icon_animated(self):
        """:class:`bool`: Returns True if the guild has an animated icon."""
        return bool(self.icon and self.icon.startswith('a_'))

    def icon_url_as(self, *, format=None, static_format='webp', size=1024):
        """Returns an :class:`Asset` for the guild's icon.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated avatars. The size must be a power of 2
        between 16 and 4096.

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the icon to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            icon being animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated icons to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_icon(self._state, self, format=format, static_format=static_format, size=size)

    @property
    def banner_url(self):
        """:class:`Asset`: Returns the guild's banner asset."""
        return self.banner_url_as()

    def banner_url_as(self, *, format='webp', size=2048):
        """Returns an :class:`Asset` for the guild's banner.

        The format must be one of 'webp', 'jpeg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the banner to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(self._state, self.id, self.banner, 'banners', format=format, size=size)

    @property
    def splash_url(self):
        """:class:`Asset`: Returns the guild's invite splash asset."""
        return self.splash_url_as()

    def splash_url_as(self, *, format='webp', size=2048):
        """Returns an :class:`Asset` for the guild's invite splash.

        The format must be one of 'webp', 'jpeg', 'jpg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the splash to.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_guild_image(self._state, self.id, self.splash, 'splashes', format=format, size=size)

    @property
    def member_count(self):
        """Returns the true member count regardless of it being loaded fully or not."""
        return self._member_count

    @property
    def chunked(self):
        """Returns a boolean indicating if the guild is "chunked".

        A chunked guild means that :attr:`member_count` is equal to the
        number of members stored in the internal :attr:`members` cache.

        If this value returns ``False``, then you should request for
        offline members.
        """
        count = getattr(self, '_member_count', None)
        if count is None:
            return False
        return count == len(self._members)

    @property
    def shard_id(self):
        """:class:`int`: Returns the shard ID for this guild if applicable."""
        count = self._state.shard_count
        if count is None:
            return None
        return (self.id >> 22) % count

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def get_member_named(self, name):
        """Returns the first member found that matches the name provided.

        The name can have an optional discriminator argument, e.g. "Jake#0001"
        or "Jake" will both do the lookup. However the former will give a more
        precise result. Note that the discriminator must have all 4 digits
        for this to work.

        If a nickname is passed, then it is looked up via the nickname. Note
        however, that a nickname + discriminator combo will not lookup the nickname
        but rather the username + discriminator combo due to nickname + discriminator
        not being unique.

        If no member is found, ``None`` is returned.

        Parameters
        -----------
        name: :class:`str`
            The name of the member to lookup with an optional discriminator.

        Returns
        --------
        :class:`Member`
            The member in this guild with the associated name. If not found
            then ``None`` is returned.
        """

        result = None
        members = self.members
        if len(name) > 5 and name[-5] == '#':
            # The 5 length is checking to see if #0000 is in the string,
            # as a#0000 has a length of 6, the minimum for a potential
            # discriminator lookup.
            potential_discriminator = name[-4:]

            # do the actual lookup and return if found
            # if it isn't found then we'll do a full name lookup below.
            result = utils.get(members, name=name[:-5], discriminator=potential_discriminator)
            if result is not None:
                return result

        def pred(m):
            return m.nick == name or m.name == name

        return utils.find(pred, members)

    def _create_channel(self, name, overwrites, channel_type, category=None, **options):
        if overwrites is None:
            overwrites = {}
        elif not isinstance(overwrites, dict):
            raise InvalidArgument('overwrites parameter expects a dict.')

        perms = []
        for target, perm in overwrites.items():
            if not isinstance(perm, PermissionOverwrite):
                raise InvalidArgument('Expected PermissionOverwrite received {0.__name__}'.format(type(perm)))

            allow, deny = perm.pair()
            payload = {
                'allow': allow.value,
                'deny': deny.value,
                'id': target.id
            }

            if isinstance(target, Role):
                payload['type'] = 'role'
            else:
                payload['type'] = 'member'

            perms.append(payload)

        try:
            options['rate_limit_per_user'] = options.pop('slowmode_delay')
        except KeyError:
            pass

        parent_id = category.id if category else None
        return self._state.http.create_channel(self.id, channel_type.value, name=name, parent_id=parent_id,
                                               permission_overwrites=perms, **options)

    async def create_text_channel(self, name, *, overwrites=None, category=None, reason=None, **options):
        """|coro|

        Creates a :class:`TextChannel` for the guild.

        Note that you need the :attr:`~Permissions.manage_channels` permission
        to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a :class:`dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        .. note::

            Creating a channel of a specified position will not update the position of
            other channels to follow suit. A follow-up call to :meth:`~TextChannel.edit`
            will be required to update the position of the channel in the channel list.

        Examples
        ----------

        Creating a basic channel:

        .. code-block:: python3

            channel = await guild.create_text_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python3

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel('secret', overwrites=overwrites)

        Parameters
        -----------
        name: :class:`str`
            The channel's name.
        overwrites
            A :class:`dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.
        category: Optional[:class:`CategoryChannel`]
            The category to place the newly created channel under.
            The permissions will be automatically synced to category if no
            overwrites are provided.
        position: :class:`int`
            The position in the channel list. This is a number that starts
            at 0. e.g. the top channel is position 0.
        topic: Optional[:class:`str`]
            The new channel's topic.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is `21600`.
        nsfw: :class:`bool`
            To mark the channel as NSFW or not.
        reason: Optional[:class:`str`]
            The reason for creating this channel. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.text, category, reason=reason, **options)
        channel = TextChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_voice_channel(self, name, *, overwrites=None, category=None, reason=None, **options):
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`VoiceChannel` instead, in addition
        to having the following new parameters.

        Parameters
        -----------
        bitrate: :class:`int`
            The channel's preferred audio bitrate in bits per second.
        user_limit: :class:`int`
            The channel's limit for number of members that can be in a voice channel.
        """
        data = await self._create_channel(name, overwrites, ChannelType.voice, category, reason=reason, **options)
        channel = VoiceChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_category(self, name, *, overwrites=None, reason=None):
        """|coro|

        Same as :meth:`create_text_channel` except makes a :class:`CategoryChannel` instead.

        .. note::

            The ``category`` parameter is not supported in this function since categories
            cannot have categories.
        """
        data = await self._create_channel(name, overwrites, ChannelType.category, reason=reason)
        channel = CategoryChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    create_category_channel = create_category

    async def leave(self):
        """|coro|

        Leaves the guild.

        .. note::

            You cannot leave the guild that you own, you must delete it instead
            via :meth:`delete`.

        Raises
        --------
        HTTPException
            Leaving the guild failed.
        """
        await self._state.http.leave_guild(self.id)

    async def delete(self):
        """|coro|

        Deletes the guild. You must be the guild owner to delete the
        guild.

        Raises
        --------
        HTTPException
            Deleting the guild failed.
        Forbidden
            You do not have permissions to delete the guild.
        """

        await self._state.http.delete_guild(self.id)

    async def edit(self, *, reason=None, **fields):
        """|coro|

        Edits the guild.

        You must have the :attr:`~Permissions.manage_guild` permission
        to edit the guild.

        Parameters
        ----------
        name: :class:`str`
            The new name of the guild.
        description: :class:`str`
            The new description of the guild. This is only available to guilds that
            contain `VERIFIED` in :attr:`Guild.features`.
        icon: :class:`bytes`
            A :term:`py:bytes-like object` representing the icon. Only PNG/JPEG supported.
            Could be ``None`` to denote removal of the icon.
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the banner.
            Could be ``None`` to denote removal of the banner.
        splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the invite splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. Only available for partnered guilds with ``INVITE_SPLASH``
            feature.
        region: :class:`VoiceRegion`
            The new region for the guild's voice communication.
        afk_channel: Optional[:class:`VoiceChannel`]
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: :class:`int`
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the guild to transfer ownership to. Note that you must
            be owner of the guild to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the guild.
        default_notifications: :class:`NotificationLevel`
            The new default notification level for the guild.
        explicit_content_filter: :class:`ContentFilter`
            The new explicit content filter for the guild.
        vanity_code: :class:`str`
            The new vanity code for the guild.
        system_channel: Optional[:class:`TextChannel`]
            The new channel that is used for the system channel. Could be ``None`` for no system channel.
        system_channel_flags: :class:`SystemChannelFlags`
            The new system channel settings to use with the new system channel.
        reason: Optional[:class:`str`]
            The reason for editing this guild. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to edit the guild.
        HTTPException
            Editing the guild failed.
        InvalidArgument
            The image format passed in to ``icon`` is invalid. It must be
            PNG or JPG. This is also raised if you are not the owner of the
            guild and request an ownership transfer.
        """

        http = self._state.http
        try:
            icon_bytes = fields['icon']
        except KeyError:
            icon = self.icon
        else:
            if icon_bytes is not None:
                icon = utils._bytes_to_base64_data(icon_bytes)
            else:
                icon = None

        try:
            banner_bytes = fields['banner']
        except KeyError:
            banner = self.banner
        else:
            if banner_bytes is not None:
                banner = utils._bytes_to_base64_data(banner_bytes)
            else:
                banner = None

        try:
            vanity_code = fields['vanity_code']
        except KeyError:
            pass
        else:
            await http.change_vanity_code(self.id, vanity_code, reason=reason)

        try:
            splash_bytes = fields['splash']
        except KeyError:
            splash = self.splash
        else:
            if splash_bytes is not None:
                splash = utils._bytes_to_base64_data(splash_bytes)
            else:
                splash = None

        fields['icon'] = icon
        fields['banner'] = banner
        fields['splash'] = splash

        try:
            default_message_notifications = int(fields.pop('default_notifications'))
        except (TypeError, KeyError):
            pass
        else:
            fields['default_message_notifications'] = default_message_notifications

        try:
            afk_channel = fields.pop('afk_channel')
        except KeyError:
            pass
        else:
            if afk_channel is None:
                fields['afk_channel_id'] = afk_channel
            else:
                fields['afk_channel_id'] = afk_channel.id

        try:
            system_channel = fields.pop('system_channel')
        except KeyError:
            pass
        else:
            if system_channel is None:
                fields['system_channel_id'] = system_channel
            else:
                fields['system_channel_id'] = system_channel.id

        if 'owner' in fields:
            if self.owner != self.me:
                raise InvalidArgument('To transfer ownership you must be the owner of the guild.')

            fields['owner_id'] = fields['owner'].id

        if 'region' in fields:
            fields['region'] = str(fields['region'])

        level = fields.get('verification_level', self.verification_level)
        if not isinstance(level, VerificationLevel):
            raise InvalidArgument('verification_level field must be of type VerificationLevel')

        fields['verification_level'] = level.value

        explicit_content_filter = fields.get('explicit_content_filter', self.explicit_content_filter)
        if not isinstance(explicit_content_filter, ContentFilter):
            raise InvalidArgument('explicit_content_filter field must be of type ContentFilter')

        fields['explicit_content_filter'] = explicit_content_filter.value

        system_channel_flags = fields.get('system_channel_flags', self.system_channel_flags)
        if not isinstance(system_channel_flags, SystemChannelFlags):
            raise InvalidArgument('system_channel_flags field must be of type SystemChannelFlags')

        fields['system_channel_flags'] = system_channel_flags.value
        await http.edit_guild(self.id, reason=reason, **fields)

    async def fetch_channels(self):
        """|coro|

        Retrieves all :class:`abc.GuildChannel` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`channels` instead.

        .. versionadded:: 1.2.0

        Raises
        -------
        InvalidData
            An unknown channel type was received from Discord.
        HTTPException
            Retrieving the channels failed.

        Returns
        -------
        List[:class:`abc.GuildChannel`]
            All channels in the guild.
        """
        data = await self._state.http.get_all_guild_channels(self.id)

        def convert(d):
            factory, ch_type = _channel_factory(d['type'])
            if factory is None:
                raise InvalidData('Unknown channel type {type} for channel ID {id}.'.format_map(data))

            channel = factory(guild=self, state=self._state, data=d)
            return channel

        return [convert(d) for d in data]

    async def fetch_member(self, member_id):
        """|coro|

        Retreives a :class:`Member` from a guild ID, and a member ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_member` instead.

        Parameters
        -----------
        member_id: :class:`int`
            The member's ID to fetch from.

        Raises
        -------
        Forbidden
            You do not have access to the guild.
        HTTPException
            Getting the guild failed.

        Returns
        --------
        :class:`Member`
            The member from the member ID.
        """
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def fetch_ban(self, user):
        """|coro|

        Retrieves the :class:`BanEntry` for a user, which is a namedtuple
        with a ``user`` and ``reason`` field. See :meth:`bans` for more
        information.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to get ban information from.

        Raises
        ------
        Forbidden
            You do not have proper permissions to get the information.
        NotFound
            This user is not banned.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        BanEntry
            The BanEntry object for the specified user.
        """
        data = await self._state.http.get_ban(user.id, self.id)
        return BanEntry(
            user=User(state=self._state, data=data['user']),
            reason=data['reason']
        )

    async def bans(self):
        """|coro|

        Retrieves all the users that are banned from the guild.

        This coroutine returns a :class:`list` of BanEntry objects, which is a
        namedtuple with a ``user`` field to denote the :class:`User`
        that got banned along with a ``reason`` field specifying
        why the user was banned that could be set to ``None``.

        You must have the :attr:`~Permissions.ban_members` permission
        to get this information.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        --------
        List[BanEntry]
            A list of BanEntry objects.
        """

        data = await self._state.http.get_bans(self.id)
        return [BanEntry(user=User(state=self._state, data=e['user']),
                         reason=e['reason'])
                for e in data]

    async def prune_members(self, *, days, compute_prune_count=True, reason=None):
        r"""|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and they have no roles.

        You must have the :attr:`~Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        compute_prune_count: :class:`bool`
            Whether to compute the prune count. This defaults to ``True``
            which makes it prone to timeouts in very large guilds. In order
            to prevent timeouts, you must set this to ``False``. If this is
            set to ``False``\, then this function will always return ``None``.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while pruning members.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        Optional[:class:`int`]
            The number of members pruned. If ``compute_prune_count`` is ``False``
            then this returns ``None``.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = await self._state.http.prune_members(self.id, days, compute_prune_count=compute_prune_count, reason=reason)
        return data['pruned']

    async def webhooks(self):
        """|coro|

        Gets the list of webhooks from this guild.

        Requires :attr:`~.Permissions.manage_webhooks` permissions.

        Raises
        -------
        Forbidden
            You don't have permissions to get the webhooks.

        Returns
        --------
        List[:class:`Webhook`]
            The webhooks for this guild.
        """

        data = await self._state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def estimate_pruned_members(self, *, days):
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.

        Raises
        -------
        Forbidden
            You do not have permissions to prune members.
        HTTPException
            An error occurred while fetching the prune members estimate.
        InvalidArgument
            An integer was not passed for ``days``.

        Returns
        ---------
        :class:`int`
            The number of members estimated to be pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = await self._state.http.estimate_pruned_members(self.id, days)
        return data['pruned']

    async def invites(self):
        """|coro|

        Returns a list of all active instant invites from the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to get
        this information.

        Raises
        -------
        Forbidden
            You do not have proper permissions to get the information.
        HTTPException
            An error occurred while fetching the information.

        Returns
        -------
        List[:class:`Invite`]
            The list of invites that are currently active.
        """

        data = await self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite['channel']['id']))
            invite['channel'] = channel
            invite['guild'] = self
            result.append(Invite(state=self._state, data=invite))

        return result

    async def fetch_emojis(self):
        r"""|coro|

        Retrieves all custom :class:`Emoji`\s from the guild.

        .. note::

            This method is an API call. For general usage, consider :attr:`emojis` instead.

        Raises
        ---------
        HTTPException
            An error occurred fetching the emojis.

        Returns
        --------
        List[:class:`Emoji`]
            The retrieved emojis.
        """
        data = await self._state.http.get_all_custom_emojis(self.id)
        return [Emoji(guild=self, state=self._state, data=d) for d in data]

    async def fetch_emoji(self, emoji_id):
        """|coro|

        Retrieves a custom :class:`Emoji` from the guild.

        .. note::

            This method is an API call.
            For general usage, consider iterating over :attr:`emojis` instead.

        Parameters
        -------------
        emoji_id: :class:`int`
            The emoji's ID.

        Raises
        ---------
        NotFound
            The emoji requested could not be found.
        HTTPException
            An error occurred fetching the emoji.

        Returns
        --------
        :class:`Emoji`
            The retrieved emoji.
        """
        data = await self._state.http.get_custom_emoji(self.id, emoji_id)
        return Emoji(guild=self, state=self._state, data=data)

    async def create_custom_emoji(self, *, name, image, roles=None, reason=None):
        r"""|coro|

        Creates a custom :class:`Emoji` for the guild.

        There is currently a limit of 50 static and animated emojis respectively per guild,
        unless the guild has the ``MORE_EMOJI`` feature which extends the limit to 200.

        You must have the :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        -----------
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        image: :class:`bytes`
            The :term:`py:bytes-like object` representing the image data to use.
            Only JPG, PNG and GIF images are supported.
        roles: Optional[List[:class:`Role`]]
            A :class:`list` of :class:`Role`\s that can use this emoji. Leave empty to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for creating this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.

        Returns
        --------
        :class:`Emoji`
            The created emoji.
        """

        img = utils._bytes_to_base64_data(image)
        if roles:
            roles = [role.id for role in roles]
        data = await self._state.http.create_custom_emoji(self.id, name, img, roles=roles, reason=reason)
        return self._state.store_emoji(self, data)

    async def create_role(self, *, reason=None, **fields):
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        Parameters
        -----------
        name: :class:`str`
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        colour: :class:`Colour`
            The colour for the role. Defaults to :meth:`Colour.default`.
            This is aliased to ``color`` as well.
        hoist: :class:`bool`
            Indicates if the role should be shown separately in the member list.
            Defaults to ``False``.
        mentionable: :class:`bool`
            Indicates if the role should be mentionable by others.
            Defaults to ``False``.
        reason: Optional[:class:`str`]
            The reason for creating this role. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to create the role.
        HTTPException
            Creating the role failed.
        InvalidArgument
            An invalid keyword argument was given.

        Returns
        --------
        :class:`Role`
            The newly created role.
        """

        try:
            perms = fields.pop('permissions')
        except KeyError:
            fields['permissions'] = 0
        else:
            fields['permissions'] = perms.value

        try:
            colour = fields.pop('colour')
        except KeyError:
            colour = fields.get('color', Colour.default())
        finally:
            fields['color'] = colour.value

        valid_keys = ('name', 'permissions', 'color', 'hoist', 'mentionable')
        for key in fields:
            if key not in valid_keys:
                raise InvalidArgument('%r is not a valid field.' % key)

        data = await self._state.http.create_role(self.id, reason=reason, **fields)
        role = Role(guild=self, data=data, state=self._state)

        # TODO: add to cache
        return role

    async def kick(self, user, *, reason=None):
        """|coro|

        Kicks a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.kick_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to kick from their guild.
        reason: Optional[:class:`str`]
            The reason the user got kicked.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        await self._state.http.kick(user.id, self.id, reason=reason)

    async def ban(self, user, *, reason=None, delete_message_days=1):
        """|coro|

        Bans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to ban from their guild.
        delete_message_days: :class:`int`
            The number of days worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 7.
        reason: Optional[:class:`str`]
            The reason the user got banned.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """
        await self._state.http.ban(user.id, self.id, delete_message_days, reason=reason)

    async def unban(self, user, *, reason=None):
        """|coro|

        Unbans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have the :attr:`~Permissions.ban_members` permission to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to unban.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        await self._state.http.unban(user.id, self.id, reason=reason)

    async def vanity_invite(self):
        """|coro|

        Returns the guild's special vanity invite.

        The guild must be partnered, i.e. have 'VANITY_URL' in
        :attr:`~Guild.features`.

        You must have the :attr:`~Permissions.manage_guild` permission to use
        this as well.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to get this.
        HTTPException
            Retrieving the vanity invite failed.

        Returns
        --------
        :class:`Invite`
            The special vanity invite.
        """

        # we start with { code: abc }
        payload = await self._state.http.get_vanity_code(self.id)

        # get the vanity URL channel since default channels aren't
        # reliable or a thing anymore
        data = await self._state.http.get_invite(payload['code'])

        payload['guild'] = self
        payload['channel'] = self.get_channel(int(data['channel']['id']))
        payload['revoked'] = False
        payload['temporary'] = False
        payload['max_uses'] = 0
        payload['max_age'] = 0
        return Invite(state=self._state, data=payload)

    def ack(self):
        """|coro|

        Marks every message in this guild as read.

        The user must not be a bot user.

        Raises
        -------
        HTTPException
            Acking failed.
        ClientException
            You must not be a bot user.
        """

        state = self._state
        if state.is_bot:
            raise ClientException('Must not be a bot account to ack messages.')
        return state.http.ack_guild(self.id)

    def audit_logs(self, *, limit=100, before=None, after=None, oldest_first=None, user=None, action=None):
        """Returns an :class:`AsyncIterator` that enables receiving the guild's audit logs.

        You must have the :attr:`~Permissions.view_audit_log` permission to use this.

        Examples
        ----------

        Getting the first 100 entries: ::

            async for entry in guild.audit_logs(limit=100):
                print('{0.user} did {0.action} to {0.target}'.format(entry))

        Getting entries for a specific action: ::

            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban):
                print('{0.user} banned {0.target}'.format(entry))

        Getting entries made by a specific user: ::

            entries = await guild.audit_logs(limit=None, user=guild.me).flatten()
            await channel.send('I made {} moderation actions.'.format(len(entries)))

        Parameters
        -----------
        limit: Optional[:class:`int`]
            The number of entries to retrieve. If ``None`` retrieve all entries.
        before: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries before this date or entry.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: Union[:class:`abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve entries after this date or entry.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        oldest_first: :class:`bool`
            If set to ``True``, return entries in oldest->newest order. Defaults to True if
            ``after`` is specified, otherwise ``False``.
        user: :class:`abc.Snowflake`
            The moderator to filter entries from.
        action: :class:`AuditLogAction`
            The action to filter with.

        Raises
        -------
        Forbidden
            You are not allowed to fetch audit logs
        HTTPException
            An error occurred while fetching the audit logs.

        Yields
        --------
        :class:`AuditLogEntry`
            The audit log entry.
        """
        if user:
            user = user.id

        if action:
            action = action.value

        return AuditLogIterator(self, before=before, after=after, limit=limit,
                                oldest_first=oldest_first, user_id=user, action_type=action)

    async def widget(self):
        """|coro|

        Returns the widget of the guild.

        .. note::

            The guild must have the widget enabled to get this information.

        Raises
        -------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.

        Returns
        --------
        :class:`Widget`
            The guild's widget.
        """
        data = await self._state.http.get_widget(self.id)

        return Widget(state=self._state, data=data)
