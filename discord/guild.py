# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import asyncio

from collections import namedtuple

from . import utils
from .role import Role
from .member import Member, VoiceState
from .game import Game
from .permissions import PermissionOverwrite
from .colour import Colour
from .errors import InvalidArgument, ClientException
from .channel import *
from .enums import GuildRegion, Status, ChannelType, try_enum, VerificationLevel, ContentFilter
from .mixins import Hashable
from .user import User
from .invite import Invite

BanEntry = namedtuple('BanEntry', 'reason user')

class Guild(Hashable):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    Supported Operations:

    +-----------+-------------------------------------+
    | Operation |             Description             |
    +===========+=====================================+
    | x == y    | Checks if two guilds are equal.     |
    +-----------+-------------------------------------+
    | x != y    | Checks if two guilds are not equal. |
    +-----------+-------------------------------------+
    | hash(x)   | Returns the guild's hash.           |
    +-----------+-------------------------------------+
    | str(x)    | Returns the guild's name.           |
    +-----------+-------------------------------------+

    Attributes
    ----------
    name: str
        The guild name.
    roles
        A list of :class:`Role` that the guild has available.
    emojis
        A tuple of :class:`Emoji` that the guild owns.
    region: :class:`GuildRegion`
        The region the guild belongs on. There is a chance that the region
        will be a ``str`` if the value is not recognised by the enumerator.
    afk_timeout: int
        The timeout to get sent to the AFK channel.
    afk_channel: Optional[:class:`VoiceChannel`]
        The channel that denotes the AFK channel. None if it doesn't exist.
    icon: str
        The guild's icon.
    id: int
        The guild's ID.
    owner_id: int
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: bool
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :meth:`Guild.id` is slim and they might
        all be None. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    mfa_level: int
        Indicates the guild's two factor authorisation level. If this value is 0 then
        the guild does not require 2FA for their administrative members. If the value is
        1 then they do.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    features: List[str]
        A list of features that the guild has. They are currently as follows:

        - ``VIP_REGIONS``: Guild has VIP voice regions
        - ``VANITY_URL``: Guild has a vanity invite URL (e.g. discord.gg/discord-api)
        - ``INVITE_SPLASH``: Guild's invite page has a special splash.

    splash: str
        The guild's invite splash.
    """

    __slots__ = ('afk_timeout', 'afk_channel', '_members', '_channels', 'icon',
                 'name', 'id', 'unavailable', 'name', 'region', '_state',
                 '_default_role', 'roles', '_member_count', '_large',
                 'owner_id', 'mfa_level', 'emojis', 'features',
                 'verification_level', 'explicit_content_filter', 'splash',
                 '_voice_states' )

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
        return '<Guild id={0.id} name={0.name!r} chunked={0.chunked}>'.format(self)

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
        for r in self.roles:
            r.position += bool(r.position)

        self.roles.append(role)

    def _remove_role(self, role):
        # this raises ValueError if it fails..
        self.roles.remove(role)

        # since it didn't, we can change the positions now
        # basically the same as above except we only decrement
        # the position if we're above the role we deleted.
        for r in self.roles:
            r.position -= r.position > role.position

    def _from_data(self, guild):
        # according to Stan, this is always available even if the guild is unavailable
        # I don't have this guarantee when someone updates the guild.
        member_count = guild.get('member_count', None)
        if member_count:
            self._member_count = member_count

        self.name = guild.get('name')
        self.region = try_enum(GuildRegion, guild.get('region'))
        self.verification_level = try_enum(VerificationLevel, guild.get('verification_level'))
        self.explicit_content_filter = try_enum(ContentFilter, guild.get('explicit_content_filter', 0))
        self.afk_timeout = guild.get('afk_timeout')
        self.icon = guild.get('icon')
        self.unavailable = guild.get('unavailable', False)
        self.id = int(guild['id'])
        self.roles = [Role(guild=self, data=r, state=self._state) for r in guild.get('roles', [])]
        self.mfa_level = guild.get('mfa_level')
        self.emojis = tuple(map(lambda d: self._state.store_emoji(self, d), guild.get('emojis', [])))
        self.features = guild.get('features', [])
        self.splash = guild.get('splash')

        for mdata in guild.get('members', []):
            member = Member(data=mdata, guild=self, state=self._state)
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

        for presence in data.get('presences', []):
            user_id = int(presence['user']['id'])
            member = self.get_member(user_id)
            if member is not None:
                member.status = try_enum(Status, presence['status'])
                game = presence.get('game', {})
                member.game = Game(**game) if game else None

        if 'channels' in data:
            channels = data['channels']
            for c in channels:
                if c['type'] == ChannelType.text.value:
                    channel = TextChannel(guild=self, data=c, state=self._state)
                else:
                    channel = VoiceChannel(guild=self, data=c, state=self._state)

                self._add_channel(channel)

    @property
    def channels(self):
        """List[:class:`abc.GuildChannel`]: A list of channels that belongs to this guild."""
        return list(self._channels.values())

    @property
    def large(self):
        """bool: Indicates if the guild is a 'large' guild.

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
        r.sort(key=lambda c: c.position)
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
        r.sort(key=lambda c: c.position)
        return r

    def get_channel(self, channel_id):
        """Returns a :class:`abc.GuildChannel` with the given ID. If not found, returns None."""
        return self._channels.get(channel_id)

    @property
    def members(self):
        """List[:class:`Member`]: A list of members that belongs to this guild."""
        return list(self._members.values())

    def get_member(self, user_id):
        """Returns a :class:`Member` with the given ID. If not found, returns None."""
        return self._members.get(user_id)

    @utils.cached_slot_property('_default_role')
    def default_role(self):
        """Gets the @everyone role that all members have by default."""
        return utils.find(lambda r: r.is_default(), self.roles)

    @property
    def default_channel(self):
        """Gets the default :class:`TextChannel` for the guild."""
        return self.get_channel(self.id)

    @property
    def owner(self):
        """:class:`Member`: The member that owns the guild."""
        return self.get_member(self.owner_id)

    @property
    def icon_url(self):
        """Returns the URL version of the guild's icon. Returns an empty string if it has no icon."""
        if self.icon is None:
            return ''
        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)

    @property
    def splash_url(self):
        """Returns the URL version of the guild's invite splash. Returns an empty string if it has no splash."""
        if self.splash is None:
            return ''
        return 'https://cdn.discordapp.com/splashes/{0.id}/{0.splash}.jpg?size=2048'.format(self)

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
        """Returns the shard ID for this guild if applicable."""
        count = self._state.shard_count
        if count is None:
            return None
        return (self.id >> 22) % count

    @property
    def created_at(self):
        """Returns the guild's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def role_hierarchy(self):
        """Returns the guild's roles in the order of the hierarchy.

        The first element of this list will be the highest role in the
        hierarchy.
        """
        return sorted(self.roles, reverse=True)

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
        name: str
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

    def _create_channel(self, name, overwrites, type):
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

        return self._state.http.create_channel(self.id, name, str(type), permission_overwrites=perms)

    @asyncio.coroutine
    def create_text_channel(self, name, *, overwrites=None):
        """|coro|

        Creates a :class:`TextChannel` for the guild.

        Note that you need the proper permissions to create the channel.

        The ``overwrites`` parameter can be used to create a 'secret'
        channel upon creation. This parameter expects a `dict` of
        overwrites with the target (either a :class:`Member` or a :class:`Role`)
        as the key and a :class:`PermissionOverwrite` as the value.

        Examples
        ----------

        Creating a basic channel:

        .. code-block:: python

            channel = await guild.create_text_channel('cool-channel')

        Creating a "secret" channel:

        .. code-block:: python

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }

            channel = await guild.create_text_channel('secret', overwrites=overwrites)

        Parameters
        -----------
        name: str
            The channel's name.
        overwrites
            A `dict` of target (either a role or a member) to
            :class:`PermissionOverwrite` to apply upon creation of a channel.
            Useful for creating secret channels.

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
        data = yield from self._create_channel(name, overwrites, ChannelType.text)
        return TextChannel(state=self._state, guild=self, data=data)

    @asyncio.coroutine
    def create_voice_channel(self, name, *, overwrites=None):
        """|coro|

        Same as :meth:`create_text_channel` except makes a
        :class:`VoiceChannel` instead.
        """
        data = yield from self._create_channel(name, overwrites, ChannelType.voice)
        return VoiceChannel(state=self._state, guild=self, data=data)

    @asyncio.coroutine
    def leave(self):
        """|coro|

        Leaves the guild.

        Note
        --------
        You cannot leave the guild that you own, you must delete it instead
        via :meth:`delete`.

        Raises
        --------
        HTTPException
            Leaving the guild failed.
        """
        yield from self._state.http.leave_guild(self.id)

    @asyncio.coroutine
    def delete(self):
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

        yield from self._state.http.delete_guild(self.id)

    @asyncio.coroutine
    def edit(self, **fields):
        """|coro|

        Edits the guild.

        You must have the :attr:`Permissions.manage_guild` permission
        to edit the guild.

        Parameters
        ----------
        name: str
            The new name of the guild.
        icon: bytes
            A *bytes-like* object representing the icon. Only PNG/JPEG supported.
            Could be ``None`` to denote removal of the icon.
        splash: bytes
            A *bytes-like* object representing the invite splash.
            Only PNG/JPEG supported. Could be ``None`` to denote removing the
            splash. Only available for partnered guilds with ``INVITE_SPLASH``
            feature.
        region: :class:`GuildRegion`
            The new region for the guild's voice communication.
        afk_channel: :class:`VoiceChannel`
            The new channel that is the AFK channel. Could be ``None`` for no AFK channel.
        afk_timeout: int
            The number of seconds until someone is moved to the AFK channel.
        owner: :class:`Member`
            The new owner of the guild to transfer ownership to. Note that you must
            be owner of the guild to do this.
        verification_level: :class:`VerificationLevel`
            The new verification level for the guild.

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
            splash_bytes = fields['splash']
        except KeyError:
            splash = self.splash
        else:
            if splash_bytes is not None:
                splash = utils._bytes_to_base64_data(splash_bytes)
            else:
                splash = None

        fields['icon'] = icon
        fields['splash'] = splash
        if 'afk_channel' in fields:
            fields['afk_channel_id'] = fields['afk_channel'].id

        if 'owner' in fields:
            if self.owner != self.me:
                raise InvalidArgument('To transfer ownership you must be the owner of the guild.')

            fields['owner_id'] = fields['owner'].id

        if 'region' in fields:
            fields['region'] = str(fields['region'])

        level = fields.get('verification_level', self.verification_level)
        if not isinstance(level, VerificationLevel):
            raise InvalidArgument('verification_level field must of type VerificationLevel')

        fields['verification_level'] = level.value
        yield from self._state.http.edit_guild(self.id, **fields)


    @asyncio.coroutine
    def bans(self):
        """|coro|

        Retrieves all the users that are banned from the guild.

        This coroutine returns a list of BanEntry objects. Which is a
        namedtuple with a ``user`` field to denote the :class:`User`
        that got banned along with a ``reason`` field specifying
        why the user was banned that could be set to ``None``.

        You must have :attr:`Permissions.ban_members` permission
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

        data = yield from self._state.http.get_bans(self.id)
        return [BanEntry(user=User(state=self._state, data=e['user']),
                         reason=e['reason'])
                for e in data]

    @asyncio.coroutine
    def prune_members(self, *, days):
        """|coro|

        Prunes the guild from its inactive members.

        The inactive members are denoted if they have not logged on in
        ``days`` number of days and they have no roles.

        You must have the :attr:`Permissions.kick_members` permission
        to use this.

        To check how many members you would prune without actually pruning,
        see the :meth:`estimate_pruned_members` function.

        Parameters
        -----------
        days: int
            The number of days before counting as inactive.

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
        int
            The number of members pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = yield from self._state.http.prune_members(self.id, days)
        return data['pruned']

    @asyncio.coroutine
    def estimate_pruned_members(self, *, days):
        """|coro|

        Similar to :meth:`prune_members` except instead of actually
        pruning members, it returns how many members it would prune
        from the guild had it been called.

        Parameters
        -----------
        days: int
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
        int
            The number of members estimated to be pruned.
        """

        if not isinstance(days, int):
            raise InvalidArgument('Expected int for ``days``, received {0.__class__.__name__} instead.'.format(days))

        data = yield from self._state.http.estimate_pruned_members(self.id, days)
        return data['pruned']

    @asyncio.coroutine
    def invites(self):
        """|coro|

        Returns a list of all active instant invites from the guild.

        You must have :attr:`Permissions.manage_guild` to get this information.

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

        data = yield from self._state.http.invites_from(self.id)
        result = []
        for invite in data:
            channel = self.get_channel(int(invite['channel']['id']))
            invite['channel'] = channel
            invite['guild'] = self
            result.append(Invite(state=self._state, data=invite))

        return result

    @asyncio.coroutine
    def create_invite(self, **fields):
        """|coro|

        Creates an instant invite.

        Parameters
        ------------
        max_age : int
            How long the invite should last. If it's 0 then the invite
            doesn't expire. Defaults to 0.
        max_uses : int
            How many uses the invite could be used for. If it's 0 then there
            are unlimited uses. Defaults to 0.
        temporary : bool
            Denotes that the invite grants temporary membership
            (i.e. they get kicked after they disconnect). Defaults to False.
        unique: bool
            Indicates if a unique invite URL should be created. Defaults to True.
            If this is set to False then it will return a previously created
            invite.

        Raises
        -------
        HTTPException
            Invite creation failed.

        Returns
        --------
        :class:`Invite`
            The invite that was created.
        """

        data = yield from self._state.http.create_invite(self.id, **fields)
        return Invite.from_incomplete(data=data, state=self._state)

    @asyncio.coroutine
    def create_custom_emoji(self, *, name, image):
        """|coro|

        Creates a custom :class:`Emoji` for the guild.

        This endpoint is only allowed for user bots or white listed
        bots. If this is done by a user bot then this is a local
        emoji that can only be used inside the guild. If done by
        a whitelisted bot, then this emoji is "global".

        There is currently a limit of 50 local emotes per guild.

        Parameters
        -----------
        name: str
            The emoji name. Must be at least 2 characters.
        image: bytes
            The *bytes-like* object representing the image data to use.
            Only JPG and PNG images are supported.

        Returns
        --------
        :class:`Emoji`
            The created emoji.

        Raises
        -------
        Forbidden
            You are not allowed to create emojis.
        HTTPException
            An error occurred creating an emoji.
        """

        img = utils._bytes_to_base64_data(image)
        data = yield from self._state.http.create_custom_emoji(self.id, name, img)
        return self._state.store_emoji(self, data)

    @asyncio.coroutine
    def create_role(self, **fields):
        """|coro|

        Creates a :class:`Role` for the guild.

        All fields are optional.

        Parameters
        -----------
        name: str
            The role name. Defaults to 'new role'.
        permissions: :class:`Permissions`
            The permissions to have. Defaults to no permissions.
        colour: :class:`Colour`
            The colour for the role. Defaults to :meth:`Colour.default`.
            This is aliased to ``color`` as well.
        hoist: bool
            Indicates if the role should be shown separately in the member list.
            Defaults to False.
        mentionable: bool
            Indicates if the role should be mentionable by others.
            Defaults to False.

        Returns
        --------
        :class:`Role`
            The newly created role.

        Raises
        -------
        Forbidden
            You do not have permissions to change the role.
        HTTPException
            Editing the role failed.
        InvalidArgument
            An invalid keyword argument was given.
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

        data = yield from self._state.http.create_role(self.id, **fields)
        role = Role(guild=self, data=data, state=self._state)

        # TODO: add to cache
        return role

    @asyncio.coroutine
    def kick(self, user):
        """|coro|

        Kicks a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have :attr:`Permissions.kick_members` permissions to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to kick from their guild.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to kick.
        HTTPException
            Kicking failed.
        """
        yield from self._state.http.kick(user.id, self.id)

    @asyncio.coroutine
    def ban(self, user, *, delete_message_days=1):
        """|coro|

        Bans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have :attr:`Permissions.ban_members` permissions to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to ban from their guild.
        delete_message_days: int
            The number of days worth of messages to delete from the user
            in the guild. The minimum is 0 and the maximum is 7.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to ban.
        HTTPException
            Banning failed.
        """
        yield from self._state.http.ban(user.id, self.id, delete_message_days)

    @asyncio.coroutine
    def unban(self, user):
        """|coro|

        Unbans a user from the guild.

        The user must meet the :class:`abc.Snowflake` abc.

        You must have :attr:`Permissions.ban_members` permissions to
        do this.

        Parameters
        -----------
        user: :class:`abc.Snowflake`
            The user to unban.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to unban.
        HTTPException
            Unbanning failed.
        """
        yield from self._state.http.unban(user.id, self.id)

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
