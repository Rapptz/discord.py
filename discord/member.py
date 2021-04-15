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

import datetime
import inspect
import itertools
import sys
from operator import attrgetter

import discord.abc

from . import utils
from .errors import ClientException
from .user import BaseUser, User
from .activity import create_activity
from .permissions import Permissions
from .enums import Status, try_enum
from .colour import Colour
from .object import Object

class VoiceState:
    """Represents a Discord user's voice state.

    Attributes
    ------------
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the guild.
    mute: :class:`bool`
        Indicates if the user is currently muted by the guild.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    self_stream: :class:`bool`
        Indicates if the user is currently streaming via 'Go Live' feature.

        .. versionadded:: 1.3

    self_video: :class:`bool`
        Indicates if the user is currently broadcasting video.
    suppress: :class:`bool`
        Indicates if the user is suppressed from speaking.

        Only applies to stage channels.

        .. versionadded:: 1.7

    requested_to_speak_at: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC that the member
        requested to speak. It will be ``None`` if they are not requesting to speak
        anymore or have been accepted to speak.

        Only applicable to stage channels.

        .. versionadded:: 1.7

    afk: :class:`bool`
        Indicates if the user is currently in the AFK channel in the guild.
    channel: Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]
        The voice channel that the user is currently connected to. ``None`` if the user
        is not currently in a voice channel.
    """

    __slots__ = ('session_id', 'deaf', 'mute', 'self_mute',
                 'self_stream', 'self_video', 'self_deaf', 'afk', 'channel',
                 'requested_to_speak_at', 'suppress')

    def __init__(self, *, data, channel=None):
        self.session_id = data.get('session_id')
        self._update(data, channel)

    def _update(self, data, channel):
        self.self_mute = data.get('self_mute', False)
        self.self_deaf = data.get('self_deaf', False)
        self.self_stream = data.get('self_stream', False)
        self.self_video = data.get('self_video', False)
        self.afk = data.get('suppress', False)
        self.mute = data.get('mute', False)
        self.deaf = data.get('deaf', False)
        self.suppress = data.get('suppress', False)
        self.requested_to_speak_at = utils.parse_time(data.get('request_to_speak_timestamp'))
        self.channel = channel

    def __repr__(self):
        attrs = [
            ('self_mute', self.self_mute),
            ('self_deaf', self.self_deaf),
            ('self_stream', self.self_stream),
            ('suppress', self.suppress),
            ('requested_to_speak_at', self.requested_to_speak_at),
            ('channel', self.channel)
        ]
        return '<%s %s>' % (self.__class__.__name__, ' '.join('%s=%r' % t for t in attrs))

def flatten_user(cls):
    for attr, value in itertools.chain(BaseUser.__dict__.items(), User.__dict__.items()):
        # ignore private/special methods
        if attr.startswith('_'):
            continue

        # don't override what we already have
        if attr in cls.__dict__:
            continue

        # if it's a slotted attribute or a property, redirect it
        # slotted members are implemented as member_descriptors in Type.__dict__
        if not hasattr(value, '__annotations__'):
            getter = attrgetter('_user.' + attr)
            setattr(cls, attr, property(getter, doc='Equivalent to :attr:`User.%s`' % attr))
        else:
            # Technically, this can also use attrgetter
            # However I'm not sure how I feel about "functions" returning properties
            # It probably breaks something in Sphinx.
            # probably a member function by now
            def generate_function(x):
                # We want sphinx to properly show coroutine functions as coroutines
                if inspect.iscoroutinefunction(value):
                    async def general(self, *args, **kwargs):
                        return await getattr(self._user, x)(*args, **kwargs)
                else:
                    def general(self, *args, **kwargs):
                        return getattr(self._user, x)(*args, **kwargs)

                general.__name__ = x
                return general

            func = generate_function(attr)
            func = utils.copy_doc(value)(func)
            setattr(cls, attr, func)

    return cls

_BaseUser = discord.abc.User

@flatten_user
class Member(discord.abc.Messageable, _BaseUser):
    """Represents a Discord member to a :class:`Guild`.

    This implements a lot of the functionality of :class:`User`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's name with the discriminator.

    Attributes
    ----------
    joined_at: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC that the member joined the guild.
        If the member left and rejoined the guild, this will be the latest date. In certain cases, this can be ``None``.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities that the user is currently doing.

        .. note::

            Due to a Discord API limitation, a user's Spotify activity may not appear
            if they are listening to a song with a title longer
            than 128 characters. See :issue:`1738` for more information.

    guild: :class:`Guild`
        The guild that the member belongs to.
    nick: Optional[:class:`str`]
        The guild specific nickname of the user.
    pending: :class:`bool`
        Whether the member is pending member verification.

        .. versionadded:: 1.6
    premium_since: Optional[:class:`datetime.datetime`]
        A datetime object that specifies the date and time in UTC when the member used their
        Nitro boost on the guild, if available. This could be ``None``.
    """

    __slots__ = ('_roles', 'joined_at', 'premium_since', '_client_status',
                 'activities', 'guild', 'pending', 'nick', '_user', '_state')

    def __init__(self, *, data, guild, state):
        self._state = state
        self._user = state.store_user(data['user'])
        self.guild = guild
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)
        self._client_status = {
            None: 'offline'
        }
        self.activities = tuple(map(create_activity, data.get('activities', [])))
        self.nick = data.get('nick', None)
        self.pending = data.get('pending', False)

    def __str__(self):
        return str(self._user)

    def __repr__(self):
        return '<Member id={1.id} name={1.name!r} discriminator={1.discriminator!r}' \
               ' bot={1.bot} nick={0.nick!r} guild={0.guild!r}>'.format(self, self._user)

    def __eq__(self, other):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._user)

    @classmethod
    def _from_message(cls, *, message, data):
        author = message.author
        data['user'] = author._to_minimal_user_json()
        return cls(data=data, guild=message.guild, state=message._state)

    def _update_from_message(self, data):
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)
        self.nick = data.get('nick', None)
        self.pending = data.get('pending', False)

    @classmethod
    def _try_upgrade(cls, *,  data, guild, state):
        # A User object with a 'member' key
        try:
            member_data = data.pop('member')
        except KeyError:
            return state.store_user(data)
        else:
            member_data['user'] = data
            return cls(data=member_data, guild=guild, state=state)

    @classmethod
    def _from_presence_update(cls, *, data, guild, state):
        clone = cls(data=data, guild=guild, state=state)
        to_return = cls(data=data, guild=guild, state=state)
        to_return._client_status = {
            sys.intern(key): sys.intern(value)
            for key, value in data.get('client_status', {}).items()
        }
        to_return._client_status[None] = sys.intern(data['status'])
        return to_return, clone

    @classmethod
    def _copy(cls, member):
        self = cls.__new__(cls) # to bypass __init__

        self._roles = utils.SnowflakeList(member._roles, is_sorted=True)
        self.joined_at = member.joined_at
        self.premium_since = member.premium_since
        self._client_status = member._client_status.copy()
        self.guild = member.guild
        self.nick = member.nick
        self.pending = member.pending
        self.activities = member.activities
        self._state = member._state

        # Reference will not be copied unless necessary by PRESENCE_UPDATE
        # See below
        self._user = member._user
        return self

    async def _get_channel(self):
        ch = await self.create_dm()
        return ch

    def _update_roles(self, data):
        self._roles = utils.SnowflakeList(map(int, data['roles']))

    def _update(self, data):
        # the nickname change is optional,
        # if it isn't in the payload then it didn't change
        try:
            self.nick = data['nick']
        except KeyError:
            pass

        try:
            self.pending = data['pending']
        except KeyError:
            pass

        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._update_roles(data)

    def _presence_update(self, data, user):
        self.activities = tuple(map(create_activity, data.get('activities', [])))
        self._client_status = {
            sys.intern(key): sys.intern(value)
            for key, value in data.get('client_status', {}).items()
        }
        self._client_status[None] = sys.intern(data['status'])

        if len(user) > 1:
            return self._update_inner_user(user)
        return False

    def _update_inner_user(self, user):
        u = self._user
        original = (u.name, u.avatar, u.discriminator, u._public_flags)
        # These keys seem to always be available
        modified = (user['username'], user['avatar'], user['discriminator'], user.get('public_flags', 0))
        if original != modified:
            to_return = User._copy(self._user)
            u.name, u.avatar, u.discriminator, u._public_flags = modified
            # Signal to dispatch on_user_update
            return to_return, u

    @property
    def status(self):
        """:class:`Status`: The member's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return try_enum(Status, self._client_status[None])

    @property
    def raw_status(self):
        """:class:`str`: The member's overall status as a string value.

        .. versionadded:: 1.5
        """
        return self._client_status[None]

    @status.setter
    def status(self, value):
        # internal use only
        self._client_status[None] = str(value)

    @property
    def mobile_status(self):
        """:class:`Status`: The member's status on a mobile device, if applicable."""
        return try_enum(Status, self._client_status.get('mobile', 'offline'))

    @property
    def desktop_status(self):
        """:class:`Status`: The member's status on the desktop client, if applicable."""
        return try_enum(Status, self._client_status.get('desktop', 'offline'))

    @property
    def web_status(self):
        """:class:`Status`: The member's status on the web client, if applicable."""
        return try_enum(Status, self._client_status.get('web', 'offline'))

    def is_on_mobile(self):
        """:class:`bool`: A helper function that determines if a member is active on a mobile device."""
        return 'mobile' in self._client_status

    @property
    def colour(self):
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the member. If the default colour is the one rendered then an instance
        of :meth:`Colour.default` is returned.

        There is an alias for this named :attr:`color`.
        """

        roles = self.roles[1:] # remove @everyone

        # highest order of the colour is the one that gets rendered.
        # if the highest is the default colour then the next one with a colour
        # is chosen instead
        for role in reversed(roles):
            if role.colour.value:
                return role.colour
        return Colour.default()

    @property
    def color(self):
        """:class:`Colour`: A property that returns a color denoting the rendered color for
        the member. If the default color is the one rendered then an instance of :meth:`Colour.default`
        is returned.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def roles(self):
        """List[:class:`Role`]: A :class:`list` of :class:`Role` that the member belongs to. Note
        that the first element of this list is always the default '@everyone'
        role.

        These roles are sorted by their position in the role hierarchy.
        """
        result = []
        g = self.guild
        for role_id in self._roles:
            role = g.get_role(role_id)
            if role:
                result.append(role)
        result.append(g.default_role)
        result.sort()
        return result

    @property
    def mention(self):
        """:class:`str`: Returns a string that allows you to mention the member."""
        if self.nick:
            return '<@!%s>' % self.id
        return '<@%s>' % self.id

    @property
    def display_name(self):
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.nick or self.name

    @property
    def activity(self):
        """Union[:class:`BaseActivity`, :class:`Spotify`]: Returns the primary
        activity the user is currently doing. Could be ``None`` if no activity is being done.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if 
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.

        .. note::

            A user may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if self.activities:
            return self.activities[0]

    def mentioned_in(self, message):
        """Checks if the member is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the member is mentioned in the message.
        """
        if message.guild is None or message.guild.id != self.guild.id:
            return False

        if self._user.mentioned_in(message):
            return True

        return any(self._roles.has(role.id) for role in message.role_mentions)

    def permissions_in(self, channel):
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel: :class:`abc.GuildChannel`
            The channel to check your permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the member.
        """
        return channel.permissions_for(self)

    @property
    def top_role(self):
        """:class:`Role`: Returns the member's highest role.

        This is useful for figuring where a member stands in the role
        hierarchy chain.
        """
        guild = self.guild
        if len(self._roles) == 0:
            return guild.default_role

        return max(guild.get_role(rid) or guild.default_role for rid in self._roles)

    @property
    def guild_permissions(self):
        """:class:`Permissions`: Returns the member's guild permissions.

        This only takes into consideration the guild permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use either :meth:`permissions_in` or
        :meth:`abc.GuildChannel.permissions_for`.

        This does take into consideration guild ownership and the
        administrator implication.
        """

        if self.guild.owner_id == self.id:
            return Permissions.all()

        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value

        if base.administrator:
            return Permissions.all()

        return base

    @property
    def voice(self):
        """Optional[:class:`VoiceState`]: Returns the member's current voice state."""
        return self.guild._voice_state_for(self._user.id)

    async def ban(self, **kwargs):
        """|coro|

        Bans this member. Equivalent to :meth:`Guild.ban`.
        """
        await self.guild.ban(self, **kwargs)

    async def unban(self, *, reason=None):
        """|coro|

        Unbans this member. Equivalent to :meth:`Guild.unban`.
        """
        await self.guild.unban(self, reason=reason)

    async def kick(self, *, reason=None):
        """|coro|

        Kicks this member. Equivalent to :meth:`Guild.kick`.
        """
        await self.guild.kick(self, reason=reason)

    async def edit(self, *, reason=None, **fields):
        """|coro|

        Edits the member's data.

        Depending on the parameter passed, this requires different permissions listed below:

        +---------------+--------------------------------------+
        |   Parameter   |              Permission              |
        +---------------+--------------------------------------+
        | nick          | :attr:`Permissions.manage_nicknames` |
        +---------------+--------------------------------------+
        | mute          | :attr:`Permissions.mute_members`     |
        +---------------+--------------------------------------+
        | deafen        | :attr:`Permissions.deafen_members`   |
        +---------------+--------------------------------------+
        | roles         | :attr:`Permissions.manage_roles`     |
        +---------------+--------------------------------------+
        | voice_channel | :attr:`Permissions.move_members`     |
        +---------------+--------------------------------------+

        All parameters are optional.

        .. versionchanged:: 1.1
            Can now pass ``None`` to ``voice_channel`` to kick a member from voice.

        Parameters
        -----------
        nick: Optional[:class:`str`]
            The member's new nickname. Use ``None`` to remove the nickname.
        mute: :class:`bool`
            Indicates if the member should be guild muted or un-muted.
        deafen: :class:`bool`
            Indicates if the member should be guild deafened or un-deafened.
        suppress: :class:`bool`
            Indicates if the member should be suppressed in stage channels.

            .. versionadded:: 1.7

        roles: Optional[List[:class:`Role`]]
            The member's new list of roles. This *replaces* the roles.
        voice_channel: Optional[:class:`VoiceChannel`]
            The voice channel to move the member to.
            Pass ``None`` to kick them from voice.
        reason: Optional[:class:`str`]
            The reason for editing this member. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to the action requested.
        HTTPException
            The operation failed.
        """
        http = self._state.http
        guild_id = self.guild.id
        me = self._state.self_id == self.id
        payload = {}

        try:
            nick = fields['nick']
        except KeyError:
            # nick not present so...
            pass
        else:
            nick = nick or ''
            if me:
                await http.change_my_nickname(guild_id, nick, reason=reason)
            else:
                payload['nick'] = nick

        deafen = fields.get('deafen')
        if deafen is not None:
            payload['deaf'] = deafen

        mute = fields.get('mute')
        if mute is not None:
            payload['mute'] = mute

        suppress = fields.get('suppress')
        if suppress is not None:
            voice_state_payload = {
                'channel_id': self.voice.channel.id,
                'suppress': suppress,
            }

            if suppress or self.bot:
                voice_state_payload['request_to_speak_timestamp'] = None

            if me:
                await http.edit_my_voice_state(guild_id, voice_state_payload)
            else:
                if not suppress:
                    voice_state_payload['request_to_speak_timestamp'] = datetime.datetime.utcnow().isoformat()
                await http.edit_voice_state(guild_id, self.id, voice_state_payload)

        try:
            vc = fields['voice_channel']
        except KeyError:
            pass
        else:
            payload['channel_id'] = vc and vc.id

        try:
            roles = fields['roles']
        except KeyError:
            pass
        else:
            payload['roles'] = tuple(r.id for r in roles)

        if payload:
            await http.edit_member(guild_id, self.id, reason=reason, **payload)

        # TODO: wait for WS event for modify-in-place behaviour

    async def request_to_speak(self):
        """|coro|

        Request to speak in the connected channel.

        Only applies to stage channels.

        .. note::

            Requesting members that are not the client is equivalent
            to :attr:`.edit` providing ``suppress`` as ``False``.

        .. versionadded:: 1.7

        Raises
        -------
        Forbidden
            You do not have the proper permissions to the action requested.
        HTTPException
            The operation failed.
        """
        payload = {
            'channel_id': self.voice.channel.id,
            'request_to_speak_timestamp': datetime.datetime.utcnow().isoformat(),
        }

        if self._state.self_id != self.id:
            payload['suppress'] = False
            await self._state.http.edit_voice_state(self.guild.id, self.id, payload)
        else:
            await self._state.http.edit_my_voice_state(self.guild.id, payload)

    async def move_to(self, channel, *, reason=None):
        """|coro|

        Moves a member to a new voice channel (they must be connected first).

        You must have the :attr:`~Permissions.move_members` permission to
        use this.

        This raises the same exceptions as :meth:`edit`.

        .. versionchanged:: 1.1
            Can now pass ``None`` to kick a member from voice.

        Parameters
        -----------
        channel: Optional[:class:`VoiceChannel`]
            The new voice channel to move the member to.
            Pass ``None`` to kick them from voice.
        reason: Optional[:class:`str`]
            The reason for doing this action. Shows up on the audit log.
        """
        await self.edit(voice_channel=channel, reason=reason)

    async def add_roles(self, *roles, reason=None, atomic=True):
        r"""|coro|

        Gives the member a number of :class:`Role`\s.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this, and the added :class:`Role`\s must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*roles: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to give to the member.
        reason: Optional[:class:`str`]
            The reason for adding these roles. Shows up on the audit log.
        atomic: :class:`bool`
            Whether to atomically add roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to add these roles.
        HTTPException
            Adding roles failed.
        """

        if not atomic:
            new_roles = utils._unique(Object(id=r.id) for s in (self.roles[1:], roles) for r in s)
            await self.edit(roles=new_roles, reason=reason)
        else:
            req = self._state.http.add_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)

    async def remove_roles(self, *roles, reason=None, atomic=True):
        r"""|coro|

        Removes :class:`Role`\s from this member.

        You must have the :attr:`~Permissions.manage_roles` permission to
        use this, and the removed :class:`Role`\s must appear lower in the list
        of roles than the highest role of the member.

        Parameters
        -----------
        \*roles: :class:`abc.Snowflake`
            An argument list of :class:`abc.Snowflake` representing a :class:`Role`
            to remove from the member.
        reason: Optional[:class:`str`]
            The reason for removing these roles. Shows up on the audit log.
        atomic: :class:`bool`
            Whether to atomically remove roles. This will ensure that multiple
            operations will always be applied regardless of the current
            state of the cache.

        Raises
        -------
        Forbidden
            You do not have permissions to remove these roles.
        HTTPException
            Removing the roles failed.
        """

        if not atomic:
            new_roles = [Object(id=r.id) for r in self.roles[1:]] # remove @everyone
            for role in roles:
                try:
                    new_roles.remove(Object(id=role.id))
                except ValueError:
                    pass

            await self.edit(roles=new_roles, reason=reason)
        else:
            req = self._state.http.remove_role
            guild_id = self.guild.id
            user_id = self.id
            for role in roles:
                await req(guild_id, user_id, role.id, reason=reason)
