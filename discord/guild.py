# -*- coding: utf-8 -*-

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

import copy
from collections import namedtuple

from . import utils
from .role import Role
from .member import Member, VoiceState
from .emoji import Emoji
from .errors import InvalidData
from .permissions import PermissionOverwrite
from .colour import Colour
from .errors import InvalidArgument, ClientException
from .channel import *
from .enums import VoiceRegion, ChannelType, try_enum, VerificationLevel, ContentFilter, NotificationLevel
from .mixins import Hashable
from .user import User
from .invite import Invite
from .iterators import AuditLogIterator, MemberIterator
from .widget import Widget
from .asset import Asset
from .flags import SystemChannelFlags
from .integrations import Integration


BanEntry = namedtuple('BanEntry', 'reason user')
_GuildLimit = namedtuple('_GuildLimit', 'emoji bitrate filesize')


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
        The channel that denotes the AFK channel. ``None`` if it doesn't exist.
    icon: Optional[:class:`str`]
        The guild's icon.
    id: :class:`int`
        The guild's ID.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :meth:`Guild.id` is slim and they might
        all be ``None``. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.

        .. note::

            This attribute is only available via :meth:`.Client.fetch_guild`.
    max_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a video channel.

        .. versionadded:: 1.4
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
        - ``FEATURABLE``: Guild is able to be featured in Server Discovery.
        - ``COMMUNITY``: Guild is a community server.
        - ``COMMERCE``: Guild can sell things using store channels.
        - ``PUBLIC``: Guild is a public guild.
        - ``NEWS``: Guild can create news channels.
        - ``BANNER``: Guild can upload and use a banner (i.e. :meth:`banner_url`).
        - ``ANIMATED_ICON``: Guild can upload an animated icon.
        - ``PUBLIC_DISABLED``: Guild cannot be public.
        - ``WELCOME_SCREEN_ENABLED``: Guild has enabled the welcome screen
        - ``MEMBER_VERIFICATION_GATE_ENABLED``: Guild has Membership Screening enabled.
        - ``PREVIEW_ENABLED``: Guild can be viewed before being accepted via Membership Screening.

    splash: Optional[:class:`str`]
        The guild's invite splash.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    preferred_locale: Optional[:class:`str`]
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.
    discovery_splash: :class:`str`
        The guild's discovery splash.

        .. versionadded:: 1.3
    """

    __slots__ = ('afk_timeout', 'afk_channel', '_members', '_channels', 'icon',
                 'name', 'id', 'unavailable', 'banner', 'region', '_state',
                 '_roles', '_member_count', '_large',
                 'owner_id', 'mfa_level', 'emojis', 'features',
                 'verification_level', 'explicit_content_filter', 'splash',
                 '_voice_states', '_system_channel_id', 'default_notifications',
                 'description', 'max_presences', 'max_members', 'max_video_channel_users',
                 'premium_tier', 'premium_subscription_count', '_system_channel_flags',
                 'preferred_locale', 'discovery_splash', '_rules_channel_id',
                 '_public_updates_channel_id')

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
        return self.name or ''

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
        if member is None:
            try:
                member = Member(data=data['member'], state=self._state, guild=self)
            except KeyError:
                member = None

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
        if member_count is not None:
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
        self.max_video_channel_users = guild.get('max_video_channel_users')
        self.premium_tier = guild.get('premium_tier', 0)
        self.premium_subscription_count = guild.get('premium_subscription_count') or 0
        self._system_channel_flags = guild.get('system_channel_flags', 0)
        self.preferred_locale = guild.get('preferred_locale')
        self.discovery_splash = guild.get('discovery_splash')
        self._rules_channel_id = utils._get_as_snowflake(guild, 'rules_channel_id')
        self._public_updates_channel_id = utils._get_as_snowflake(guild, 'public_updates_channel_id')

        cache_online_members = self._state.member_cache_flags.online
        cache_joined = self._state.member_cache_flags.joined
        self_id = self._state.self_id
        for mdata in guild.get('members', []):
            member = Member(data=mdata, guild=self, state=state)
            if cache_joined or (cache_online_members and member.raw_status != 'offline') or member.id == self_id:
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
                factory, ch_type = _channel_factory(c['type'])
                if factory:
                    self._add_channel(factory(guild=self, data=c, state=self._state))

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
    def stage_channels(self):
        """List[:class:`StageChannel`]: A list of voice channels that belongs to this guild.

        .. versionadded:: 1.7

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def me(self):
        """:class:`Member`: Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id
        return self.get_member(self_id)

    @property
    def voice_client(self):
        """Optional[:class:`VoiceProtocol`]: Returns the :class:`VoiceProtocol` associated with this guild, if any."""
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
        grouped = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue

            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]

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
        """Returns a channel with the given ID.

        Parameters
        -----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`.abc.GuildChannel`]
            The returned channel or ``None`` if not found.
        """
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
    def rules_channel(self):
        """Optional[:class:`TextChannel`]: Return's the guild's channel used for the rules.
        The guild must be a Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.3
        """
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)

    @property
    def public_updates_channel(self):
        """Optional[:class:`TextChannel`]: Return's the guild's channel where admins and
        moderators of the guilds receive notices from Discord. The guild must be a
        Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.4
        """
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)

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
        """Returns a member with the given ID.

        Parameters
        -----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`Member`]
            The member or ``None`` if not found.
        """
        return self._members.get(user_id)

    @property
    def premium_subscribers(self):
        """List[:class:`Member`]: A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self):
        """List[:class:`Role`]: Returns a :class:`list` of the guild's roles in hierarchy order.

        The first element of this list will be the lowest role in the
        hierarchy.
        """
        return sorted(self._roles.values())

    def get_role(self, role_id):
        """Returns a role with the given ID.

        Parameters
        -----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        --------
        Optional[:class:`Role`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

    @property
    def default_role(self):
        """:class:`Role`: Gets the @everyone role that all members have by default."""
        return self.get_role(self.id)

    @property
    def premium_subscriber_role(self):
        """Optional[:class:`Role`]: Gets the premium subscriber role, AKA "boost" role, in this guild.

        .. versionadded:: 1.6
        """
        for role in self._roles.values():
            if role.is_premium_subscriber():
                return role
        return None

    @property
    def self_role(self):
        """Optional[:class:`Role`]: Gets the role associated with this client's user, if any.

        .. versionadded:: 1.6
        """
        self_id = self._state.self_id
        for role in self._roles.values():
            tags = role.tags
            if tags and tags.bot_id == self_id:
                return role
        return None

    @property
    def owner(self):
        """Optional[:class:`Member`]: The member that owns the guild."""
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
    def discovery_splash_url(self):
        """:class:`Asset`: Returns the guild's discovery splash asset.

        .. versionadded:: 1.3
        """
        return self.discovery_splash_url_as()

    def discovery_splash_url_as(self, *, format='webp', size=2048):
        """Returns an :class:`Asset` for the guild's discovery splash.

        The format must be one of 'webp', 'jpeg', 'jpg', or 'png'. The
        size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.3

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
        return Asset._from_guild_image(self._state, self.id, self.discovery_splash, 'discovery-splashes', format=format, size=size)

    @property
    def member_count(self):
        """:class:`int`: Returns the true member count regardless of it being loaded fully or not.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        """
        return self._member_count

    @property
    def chunked(self):
        """:class:`bool`: Returns a boolean indicating if the guild is "chunked".

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
        Optional[:class:`Member`]
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

        try:
            rtc_region = options.pop('rtc_region')
        except KeyError:
            pass
        else:
            options['rtc_region'] = None if rtc_region is None else str(rtc_region)

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
        rtc_region: Optional[:class:`VoiceRegion`]
            The region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.

            .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.voice, category, reason=reason, **options)
        channel = VoiceChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_stage_channel(self, name, *, topic=None, category=None, overwrites=None, reason=None, position=None):
        """|coro|

        This is similar to :meth:`create_text_channel` except makes a :class:`StageChannel` instead.

        .. note::

            The ``slowmode_delay`` and ``nsfw`` parameters are not supported in this function.

        .. versionadded:: 1.7

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.stage_voice, category, reason=reason, position=position, topic=topic)
        channel = StageChannel(state=self._state, guild=self, data=data)

        # temporarily add to the cache
        self._channels[channel.id] = channel
        return channel

    async def create_category(self, name, *, overwrites=None, reason=None, position=None):
        """|coro|

        Same as :meth:`create_text_channel` except makes a :class:`CategoryChannel` instead.

        .. note::

            The ``category`` parameter is not supported in this function since categories
            cannot have categories.

        Raises
        ------
        Forbidden
            You do not have the proper permissions to create this channel.
        HTTPException
            Creating the channel failed.
        InvalidArgument
            The permission overwrite information is not in proper form.

        Returns
        -------
        :class:`CategoryChannel`
            The channel that was just created.
        """
        data = await self._create_channel(name, overwrites, ChannelType.category, reason=reason, position=position)
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

        .. versionchanged:: 1.4
            The `rules_channel` and `public_updates_channel` keyword-only parameters were added.

        Parameters
        ----------
        name: :class:`str`
            The new name of the guild.
        description: :class:`str`
            The new description of the guild. This is only available to guilds that
            contain ``PUBLIC`` in :attr:`Guild.features`.
        icon: :class:`bytes`
            A :term:`py:bytes-like object` representing the icon. Only PNG/JPEG supported
            and GIF This is only available to guilds that contain ``ANIMATED_ICON`` in :attr:`Guild.features`.
            Could be ``None`` to denote removal of the icon.
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the banner.
            Could be ``None`` to denote removal of the banner.
        splash: :class:`bytes`
            A :term:`py:bytes-like object` representing the invite splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. This is only available to guilds that contain ``INVITE_SPLASH``
            in :attr:`Guild.features`.
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
        preferred_locale: :class:`str`
            The new preferred locale for the guild. Used as the primary language in the guild.
            If set, this must be an ISO 639 code, e.g. ``en-US`` or ``ja`` or ``zh-CN``.
        rules_channel: Optional[:class:`TextChannel`]
            The new channel that is used for rules. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no rules
            channel.
        public_updates_channel: Optional[:class:`TextChannel`]
            The new channel that is used for public updates from Discord. This is only available to
            guilds that contain ``PUBLIC`` in :attr:`Guild.features`. Could be ``None`` for no
            public updates channel.
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

        default_message_notifications = fields.get('default_notifications', self.default_notifications)
        if not isinstance(default_message_notifications, NotificationLevel):
            raise InvalidArgument('default_notifications field must be of type NotificationLevel')
        fields['default_message_notifications'] = default_message_notifications.value

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
            if self.owner_id != self._state.self_id:
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

        try:
            rules_channel = fields.pop('rules_channel')
        except KeyError:
            pass
        else:
            if rules_channel is None:
                fields['rules_channel_id'] = rules_channel
            else:
                fields['rules_channel_id'] = rules_channel.id

        try:
            public_updates_channel = fields.pop('public_updates_channel')
        except KeyError:
            pass
        else:
            if public_updates_channel is None:
                fields['public_updates_channel_id'] = public_updates_channel
            else:
                fields['public_updates_channel_id'] = public_updates_channel.id
        await http.edit_guild(self.id, reason=reason, **fields)

    async def fetch_channels(self):
        """|coro|

        Retrieves all :class:`abc.GuildChannel` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`channels` instead.

        .. versionadded:: 1.2

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

    def fetch_members(self, *, limit=1000, after=None):
        """Retrieves an :class:`.AsyncIterator` that enables receiving the guild's members. In order to use this,
        :meth:`Intents.members` must be enabled.

        .. note::

            This method is an API call. For general usage, consider :attr:`members` instead.

        .. versionadded:: 1.3

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of members to retrieve. Defaults to 1000.
            Pass ``None`` to fetch all members. Note that this is potentially slow.
        after: Optional[Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve members after this date or object.
            If a date is provided it must be a timezone-naive datetime representing UTC time.

        Raises
        ------
        ClientException
            The members intent is not enabled.
        HTTPException
            Getting the members failed.

        Yields
        ------
        :class:`.Member`
            The member with the member data parsed.

        Examples
        --------

        Usage ::

            async for member in guild.fetch_members(limit=150):
                print(member.name)

        Flattening into a list ::

            members = await guild.fetch_members(limit=150).flatten()
            # members is now a list of Member...
        """

        if not self._state._intents.members:
            raise ClientException('Intents.members must be enabled to use this.')

        return MemberIterator(self, limit=limit, after=after)

    async def fetch_member(self, member_id):
        """|coro|

        Retrieves a :class:`Member` from a guild ID, and a member ID.

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
            Fetching the member failed.

        Returns
        --------
        :class:`Member`
            The member from the member ID.
        """
        data = await self._state.http.get_member(self.id, member_id)
        return Member(data=data, state=self._state, guild=self)

    async def fetch_ban(self, user):
        """|coro|

        Retrieves the :class:`BanEntry` for a user.

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
        :class:`BanEntry`
            The :class:`BanEntry` object for the specified user.
        """
        data = await self._state.http.get_ban(user.id, self.id)
        return BanEntry(
            user=User(state=self._state, data=data['user']),
            reason=data['reason']
        )

    async def bans(self):
        """|coro|

        Retrieves all the users that are banned from the guild as a :class:`list` of :class:`BanEntry`.

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
        List[:class:`BanEntry`]
            A list of :class:`BanEntry` objects.
        """

        data = await self._state.http.get_bans(self.id)
        return [BanEntry(user=User(state=self._state, data=e['user']),
                         reason=e['reason'])
                for e in data]

    async def prune_members(self, *, days, compute_prune_count=True, roles=None, reason=None):
        r"""|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and they have no roles.

        You must have the :attr:`~Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        To prune members that have specific roles see the ``roles`` parameter.

        .. versionchanged:: 1.4
            The ``roles`` keyword-only parameter was added.

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
        roles: Optional[List[:class:`abc.Snowflake`]]
            A list of :class:`abc.Snowflake` that represent roles to include in the pruning process. If a member
            has a role that is not specified, they'll be excluded.

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

        if roles:
            roles = [str(role.id) for role in roles]

        data = await self._state.http.prune_members(self.id, days, compute_prune_count=compute_prune_count, roles=roles, reason=reason)
        return data['pruned']

    async def templates(self):
        """|coro|

        Gets the list of templates from this guild.

        Requires :attr:`~.Permissions.manage_guild` permissions.

        .. versionadded:: 1.7

        Raises
        -------
        Forbidden
            You don't have permissions to get the templates.

        Returns
        --------
        List[:class:`Template`]
            The templates for this guild.
        """
        from .template import Template
        data = await self._state.http.guild_templates(self.id)
        return [Template(data=d, state=self._state) for d in data]

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

        from .webhook import Webhook
        data = await self._state.http.guild_webhooks(self.id)
        return [Webhook.from_state(d, state=self._state) for d in data]

    async def estimate_pruned_members(self, *, days, roles=None):
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        -----------
        days: :class:`int`
            The number of days before counting as inactive.
        roles: Optional[List[:class:`abc.Snowflake`]]
            A list of :class:`abc.Snowflake` that represent roles to include in the estimate. If a member
            has a role that is not specified, they'll be excluded.

            .. versionadded:: 1.7

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

        if roles:
            roles = [str(role.id) for role in roles]

        data = await self._state.http.estimate_pruned_members(self.id, days, roles)
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

    async def create_template(self, *, name, description=None):
        """|coro|

        Creates a template for the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.7

        Parameters
        -----------
        name: :class:`str`
            The name of the template.
        description: Optional[:class:`str`]
            The description of the template.
        """
        from .template import Template

        payload = {
            'name': name
        }

        if description:
            payload['description'] = description

        data = await self._state.http.create_template(self.id, payload)

        return Template(state=self._state, data=data)

    async def create_integration(self, *, type, id):
        """|coro|

        Attaches an integration to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Parameters
        -----------
        type: :class:`str`
            The integration type (e.g. Twitch).
        id: :class:`int`
            The integration ID.

        Raises
        -------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            The account could not be found.
        """
        await self._state.http.create_integration(self.id, type, id)

    async def integrations(self):
        """|coro|

        Returns a list of all integrations attached to the guild.

        You must have the :attr:`~Permissions.manage_guild` permission to
        do this.

        .. versionadded:: 1.4

        Raises
        -------
        Forbidden
            You do not have permission to create the integration.
        HTTPException
            Fetching the integrations failed.

        Returns
        --------
        List[:class:`Integration`]
            The list of integrations that are attached to the guild.
        """
        data = await self._state.http.get_all_integrations(self.id)
        return [Integration(guild=self, data=d) for d in data]

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

    async def fetch_roles(self):
        """|coro|

        Retrieves all :class:`Role` that the guild has.

        .. note::

            This method is an API call. For general usage, consider :attr:`roles` instead.

        .. versionadded:: 1.3

        Raises
        -------
        HTTPException
            Retrieving the roles failed.

        Returns
        -------
        List[:class:`Role`]
            All roles in the guild.
        """
        data = await self._state.http.get_roles(self.id)
        return [Role(guild=self, state=self._state, data=d) for d in data]

    async def create_role(self, *, reason=None, **fields):
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionchanged:: 1.6
            Can now pass ``int`` to ``colour`` keyword-only parameter.

        Parameters
        -----------
        name: :class:`str`
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        colour: Union[:class:`Colour`, :class:`int`]
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
            if isinstance(colour, int):
                colour = Colour(value=colour)
            fields['color'] = colour.value

        valid_keys = ('name', 'permissions', 'color', 'hoist', 'mentionable')
        for key in fields:
            if key not in valid_keys:
                raise InvalidArgument('%r is not a valid field.' % key)

        data = await self._state.http.create_role(self.id, reason=reason, **fields)
        role = Role(guild=self, data=data, state=self._state)

        # TODO: add to cache
        return role

    async def edit_role_positions(self, positions, *, reason=None):
        """|coro|

        Bulk edits a list of :class:`Role` in the guild.

        You must have the :attr:`~Permissions.manage_roles` permission to
        do this.

        .. versionadded:: 1.4

        Example:

        .. code-block:: python3

            positions = {
                bots_role: 1, # penultimate role
                tester_role: 2,
                admin_role: 6
            }

            await guild.edit_role_positions(positions=positions)

        Parameters
        -----------
        positions
            A :class:`dict` of :class:`Role` to :class:`int` to change the positions
            of each given role.
        reason: Optional[:class:`str`]
            The reason for editing the role positions. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to move the roles.
        HTTPException
            Moving the roles failed.
        InvalidArgument
            An invalid keyword argument was given.

        Returns
        --------
        List[:class:`Role`]
            A list of all the roles in the guild.
        """
        if not isinstance(positions, dict):
            raise InvalidArgument('positions parameter expects a dict.')

        role_positions = []
        for role, position in positions.items():

            payload = {
                'id': role.id,
                'position': position
            }

            role_positions.append(payload)

        data = await self._state.http.move_role_position(self.id, role_positions, reason=reason)
        roles = []
        for d in data:
            role = Role(guild=self, data=d, state=self._state)
            roles.append(role)
            self._roles[role.id] = role

        return roles

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

        The guild must have ``VANITY_URL`` in :attr:`~Guild.features`.

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

    @utils.deprecated()
    def ack(self):
        """|coro|

        Marks every message in this guild as read.

        The user must not be a bot user.

        .. deprecated:: 1.7

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
            If set to ``True``, return entries in oldest->newest order. Defaults to ``True`` if
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

    async def chunk(self, *, cache=True):
        """|coro|

        Requests all members that belong to this guild. In order to use this,
        :meth:`Intents.members` must be enabled.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.5

        Parameters
        -----------
        cache: :class:`bool`
            Whether to cache the members as well.

        Raises
        -------
        ClientException
            The members intent is not enabled.
        """

        if not self._state._intents.members:
            raise ClientException('Intents.members must be enabled to use this.')

        return await self._state.chunk_guild(self, cache=cache)

    async def query_members(self, query=None, *, limit=5, user_ids=None, presences=False, cache=True):
        """|coro|

        Request members that belong to this guild whose username starts with
        the query given.

        This is a websocket operation and can be slow.

        .. versionadded:: 1.3

        Parameters
        -----------
        query: Optional[:class:`str`]
            The string that the username's start with.
        limit: :class:`int`
            The maximum number of members to send back. This must be
            a number between 5 and 100.
        presences: :class:`bool`
            Whether to request for presences to be provided. This defaults
            to ``False``.

            .. versionadded:: 1.6

        cache: :class:`bool`
            Whether to cache the members internally. This makes operations
            such as :meth:`get_member` work for those that matched.
        user_ids: Optional[List[:class:`int`]]
            List of user IDs to search for. If the user ID is not in the guild then it won't be returned.

            .. versionadded:: 1.4


        Raises
        -------
        asyncio.TimeoutError
            The query timed out waiting for the members.
        ValueError
            Invalid parameters were passed to the function
        ClientException
            The presences intent is not enabled.

        Returns
        --------
        List[:class:`Member`]
            The list of members that have matched the query.
        """

        if presences and not self._state._intents.presences:
            raise ClientException('Intents.presences must be enabled to use this.')

        if query is None:
            if query == '':
                raise ValueError('Cannot pass empty query string.')

            if user_ids is None:
                raise ValueError('Must pass either query or user_ids')

        if user_ids is not None and query is not None:
            raise ValueError('Cannot pass both query and user_ids')

        if user_ids is not None and not user_ids:
            raise ValueError('user_ids must contain at least 1 value')

        limit = min(100, limit or 5)
        return await self._state.query_members(self, query=query, limit=limit, user_ids=user_ids, presences=presences, cache=cache)

    async def change_voice_state(self, *, channel, self_mute=False, self_deaf=False):
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        -----------
        channel: Optional[:class:`VoiceChannel`]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        """
        ws = self._state._get_websocket(self.id)
        channel_id = channel.id if channel else None
        await ws.voice_state(self.id, channel_id, self_mute, self_deaf)
