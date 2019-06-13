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

from collections import namedtuple

import discord.abc
from .utils import snowflake_time, _bytes_to_base64_data, parse_time
from .enums import DefaultAvatar, RelationshipType, UserFlags, HypeSquadHouse, PremiumType, try_enum
from .errors import ClientException
from .colour import Colour
from .asset import Asset

class Profile(namedtuple('Profile', 'flags user mutual_guilds connected_accounts premium_since')):
    __slots__ = ()

    @property
    def nitro(self):
        return self.premium_since is not None

    premium = nitro

    def _has_flag(self, o):
        v = o.value
        return (self.flags & v) == v

    @property
    def staff(self):
        return self._has_flag(UserFlags.staff)

    @property
    def partner(self):
        return self._has_flag(UserFlags.partner)

    @property
    def bug_hunter(self):
        return self._has_flag(UserFlags.bug_hunter)

    @property
    def early_supporter(self):
        return self._has_flag(UserFlags.early_supporter)

    @property
    def hypesquad(self):
        return self._has_flag(UserFlags.hypesquad)

    @property
    def hypesquad_houses(self):
        flags = (UserFlags.hypesquad_bravery, UserFlags.hypesquad_brilliance, UserFlags.hypesquad_balance)
        return [house for house, flag in zip(HypeSquadHouse, flags) if self._has_flag(flag)]

_BaseUser = discord.abc.User

class BaseUser(_BaseUser):
    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', '_state')

    def __init__(self, *, state, data):
        self._state = state
        self._update(data)

    def __str__(self):
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22

    def _update(self, data):
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self.avatar = data['avatar']
        self.bot = data.get('bot', False)

    @classmethod
    def _copy(cls, user):
        self = cls.__new__(cls) # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.avatar = user.avatar
        self.bot = user.bot
        self._state = user._state

        return self

    @property
    def avatar_url(self):
        """Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, an asset for
        the default avatar is returned instead.

        This is equivalent to calling :meth:`avatar_url_as` with
        the default parameters (i.e. webp/gif detection and a size of 1024).
        """
        return self.avatar_url_as(format=None, size=1024)

    def is_avatar_animated(self):
        """Indicates if the user has an animated avatar."""
        return bool(self.avatar and self.avatar.startswith('a_'))

    def avatar_url_as(self, *, format=None, static_format='webp', size=1024):
        """Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, an asset for
        the default avatar is returned instead.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated avatars. The size must be a power of 2
        between 16 and 4096.

        Parameters
        -----------
        format: Optional[:class:`str`]
            The format to attempt to convert the avatar to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            avatar being animated or not.
        static_format: Optional[:class:`str`]
            Format to attempt to convert only non-animated avatars to.
            Defaults to 'webp'
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or ``static_format``, or
            invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_avatar(self._state, self, format=format, static_format=static_format, size=size)

    @property
    def default_avatar(self):
        """class:`DefaultAvatar`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return try_enum(DefaultAvatar, int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """:class:`Asset`: Returns a URL for a user's default avatar."""
        return Asset(self._state, 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(self.default_avatar.value))

    @property
    def colour(self):
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :meth:`color`.
        """
        return Colour.default()

    @property
    def color(self):
        """:class:`Colour`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :meth:`colour`.
        """
        return self.colour

    @property
    def mention(self):
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

    def permissions_in(self, channel):
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel: :class:`abc.GuildChannel`
            The channel to check your permissions for.
        """
        return channel.permissions_for(self)

    @property
    def created_at(self):
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's discord account was created."""
        return snowflake_time(self.id)

    @property
    def display_name(self):
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.name

    def mentioned_in(self, message):
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`Message`
            The message to check if you're mentioned in.
        """

        if message.mention_everyone:
            return True

        for user in message.mentions:
            if user.id == self.id:
                return True

        return False

class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    avatar: Optional[:class:`str`]
        The avatar hash the user has. Could be None.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    verified: :class:`bool`
        Specifies if the user is a verified account.
    email: Optional[:class:`str`]
        The email the user used when registering.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    premium: :class:`bool`
        Specifies if the user is a premium user (e.g. has Discord Nitro).
    premium_type: :class:`PremiumType`
        Specifies the type of premium a user has (e.g. Nitro or Nitro Classic). Could be None if the user is not premium.
    """
    __slots__ = ('email', 'locale', '_flags', 'verified', 'mfa_enabled',
                 'premium', 'premium_type', '_relationships', '__weakref__')

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        self._relationships = {}

    def __repr__(self):
        return '<ClientUser id={0.id} name={0.name!r} discriminator={0.discriminator!r}' \
               ' bot={0.bot} verified={0.verified} mfa_enabled={0.mfa_enabled}>'.format(self)

    def _update(self, data):
        super()._update(data)
        # There's actually an Optional[str] phone field as well but I won't use it
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.locale = data.get('locale')
        self._flags = data.get('flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium = data.get('premium', False)
        self.premium_type = try_enum(PremiumType, data.get('premium_type', None))

    def get_relationship(self, user_id):
        """Retrieves the :class:`Relationship` if applicable.

        .. note::

            This only applies to non-bot accounts.

        Parameters
        -----------
        user_id: :class:`int`
            The user ID to check if we have a relationship with them.

        Returns
        --------
        Optional[:class:`Relationship`]
            The relationship if available or ``None``.
        """
        return self._relationships.get(user_id)

    @property
    def relationships(self):
        """List[:class:`User`]: Returns all the relationships that the user has.

        .. note::

            This only applies to non-bot accounts.
        """
        return list(self._relationships.values())

    @property
    def friends(self):
        r"""List[:class:`User`]: Returns all the users that the user is friends with.

        .. note::

            This only applies to non-bot accounts.
        """
        return [r.user for r in self._relationships.values() if r.type is RelationshipType.friend]

    @property
    def blocked(self):
        r"""List[:class:`User`]: Returns all the users that the user has blocked.

        .. note::

            This only applies to non-bot accounts.
        """
        return [r.user for r in self._relationships.values() if r.type is RelationshipType.blocked]

    async def edit(self, **fields):
        """|coro|

        Edits the current profile of the client.

        If a bot account is used then a password field is optional,
        otherwise it is required.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading is JPEG and PNG.

        Parameters
        -----------
        password: :class:`str`
            The current password for the client's account.
            Only applicable to user accounts.
        new_password: :class:`str`
            The new password you wish to change to.
            Only applicable to user accounts.
        email: :class:`str`
            The new email you wish to change to.
            Only applicable to user accounts.
        house: Optional[:class:`HypeSquadHouse`]
            The hypesquad house you wish to change to.
            Could be ``None`` to leave the current house.
            Only applicable to user accounts.
        username: :class:`str`
            The new username you wish to change to.
        avatar: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar``.
        ClientException
            Password is required for non-bot accounts.
            House field was not a HypeSquadHouse.
        """

        try:
            avatar_bytes = fields['avatar']
        except KeyError:
            avatar = self.avatar
        else:
            if avatar_bytes is not None:
                avatar = _bytes_to_base64_data(avatar_bytes)
            else:
                avatar = None

        not_bot_account = not self.bot
        password = fields.get('password')
        if not_bot_account and password is None:
            raise ClientException('Password is required for non-bot accounts.')

        args = {
            'password': password,
            'username': fields.get('username', self.name),
            'avatar': avatar
        }

        if not_bot_account:
            args['email'] = fields.get('email', self.email)

            if 'new_password' in fields:
                args['new_password'] = fields['new_password']

        http = self._state.http

        if 'house' in fields:
            house = fields['house']
            if house is None:
                await http.leave_hypesquad_house()
            elif not isinstance(house, HypeSquadHouse):
                raise ClientException('`house` parameter was not a HypeSquadHouse')
            else:
                value = house.value

            await http.change_hypesquad_house(value)

        data = await http.edit_profile(**args)
        if not_bot_account:
            self.email = data['email']
            try:
                http._token(data['token'], bot=False)
            except KeyError:
                pass

        self._update(data)

    async def create_group(self, *recipients):
        r"""|coro|

        Creates a group direct message with the recipients
        provided. These recipients must be have a relationship
        of type :attr:`RelationshipType.friend`.

        .. note::

            This only applies to non-bot accounts.

        Parameters
        -----------
        \*recipients: :class:`User`
            An argument :class:`list` of :class:`User` to have in
            your group.

        Raises
        -------
        HTTPException
            Failed to create the group direct message.
        ClientException
            Attempted to create a group with only one recipient.
            This does not include yourself.

        Returns
        -------
        :class:`GroupChannel`
            The new group channel.
        """

        from .channel import GroupChannel

        if len(recipients) < 2:
            raise ClientException('You must have two or more recipients to create a group.')

        users = [str(u.id) for u in recipients]
        data = await self._state.http.start_group(self.id, users)
        return GroupChannel(me=self, data=data, state=self._state)

    async def edit_settings(self, **kwargs):
        """|coro|

        Edits the client user's settings.

        .. note::

            This only applies to non-bot accounts.

        Parameters
        -------
        afk_timeout: :class:`int`
            How long (in seconds) the user needs to be AFK until Discord
            sends push notifications to your mobile device.
        animate_emojis: :class:`bool`
            Whether or not to animate emojis in the chat.
        convert_emoticons: :class:`bool`
            Whether or not to automatically convert emoticons into emojis.
            e.g. :-) -> 😃
        default_guilds_restricted: :class:`bool`
            Whether or not to automatically disable DMs between you and
            members of new guilds you join.
        detect_platform_accounts: :class:`bool`
            Whether or not to automatically detect accounts from services
            like Steam and Blizzard when you open the Discord client.
        developer_mode: :class:`bool`
            Whether or not to enable developer mode.
        disable_games_tab: :class:`bool`
            Whether or not to disable the showing of the Games tab.
        enable_tts_command: :class:`bool`
            Whether or not to allow tts messages to be played/sent.
        explicit_content_filter: :class:`UserContentFilter`
            The filter for explicit content in all messages.
        friend_source_flags: :class:`FriendFlags`
            Who can add you as a friend.
        gif_auto_play: :class:`bool`
            Whether or not to automatically play gifs that are in the chat.
        guild_positions: List[:class:`abc.Snowflake`]
            A list of guilds in order of the guild/guild icons that are on
            the left hand side of the UI.
        inline_attachment_media: :class:`bool`
            Whether or not to display attachments when they are uploaded in chat.
        inline_embed_media: :class:`bool`
            Whether or not to display videos and images from links posted in chat.
        locale: :class:`str`
            The :rfc:`3066` language identifier of the locale to use for the language
            of the Discord client.
        message_display_compact: :class:`bool`
            Whether or not to use the compact Discord display mode.
        render_embeds: :class:`bool`
            Whether or not to render embeds that are sent in the chat.
        render_reactions: :class:`bool`
            Whether or not to render reactions that are added to messages.
        restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that you will not receive DMs from.
        show_current_game: :class:`bool`
            Whether or not to display the game that you are currently playing.
        status: :class:`Status`
            The clients status that is shown to others.
        theme: :class:`Theme`
            The theme of the Discord UI.
        timezone_offset: :class:`int`
            The timezone offset to use.

        Raises
        -------
        HTTPException
            Editing the settings failed.
        Forbidden
            The client is a bot user and not a user account.

        Returns
        -------
        :class:`dict`
            The client user's updated settings.
        """
        payload = {}

        content_filter = kwargs.pop('explicit_content_filter', None)
        if content_filter:
            payload.update({'explicit_content_filter': content_filter.value})

        friend_flags = kwargs.pop('friend_source_flags', None)
        if friend_flags:
            dicts = [{}, {'mutual_guilds': True}, {'mutual_friends': True},
            {'mutual_guilds': True, 'mutual_friends': True}, {'all': True}]
            payload.update({'friend_source_flags': dicts[friend_flags.value]})

        guild_positions = kwargs.pop('guild_positions', None)
        if guild_positions:
            guild_positions = [str(x.id) for x in guild_positions]
            payload.update({'guild_positions': guild_positions})

        restricted_guilds = kwargs.pop('restricted_guilds', None)
        if restricted_guilds:
            restricted_guilds = [str(x.id) for x in restricted_guilds]
            payload.update({'restricted_guilds': restricted_guilds})

        status = kwargs.pop('status', None)
        if status:
            payload.update({'status': status.value})

        theme = kwargs.pop('theme', None)
        if theme:
            payload.update({'theme': theme.value})

        payload.update(kwargs)

        data = await self._state.http.edit_settings(**payload)
        return data

class User(BaseUser, discord.abc.Messageable):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator.

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.
    avatar: Optional[:class:`str`]
        The avatar hash the user has. Could be None.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    """

    __slots__ = ('__weakref__',)

    def __repr__(self):
        return '<User id={0.id} name={0.name!r} discriminator={0.discriminator!r} bot={0.bot}>'.format(self)

    async def _get_channel(self):
        ch = await self.create_dm()
        return ch

    @property
    def dm_channel(self):
        """Optional[:class:`DMChannel`]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    async def create_dm(self):
        """Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)

    @property
    def relationship(self):
        """Returns the :class:`Relationship` with this user if applicable, ``None`` otherwise.

        .. note::

            This only applies to non-bot accounts.
        """
        return self._state.user.get_relationship(self.id)

    async def mutual_friends(self):
        """|coro|

        Gets all mutual friends of this user.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to get mutual friends of this user.
        HTTPException
            Getting mutual friends failed.

        Returns
        -------
        List[:class:`User`]
            The users that are mutual friends.
        """
        state = self._state
        mutuals = await state.http.get_mutual_friends(self.id)
        return [User(state=state, data=friend) for friend in mutuals]

    def is_friend(self):
        """Checks if the user is your friend.

        .. note::

            This only applies to non-bot accounts.
        """
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend

    def is_blocked(self):
        """Checks if the user is blocked.

        .. note::

            This only applies to non-bot accounts.
        """
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.blocked

    async def block(self):
        """|coro|

        Blocks the user.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to block this user.
        HTTPException
            Blocking the user failed.
        """

        await self._state.http.add_relationship(self.id, type=RelationshipType.blocked.value)

    async def unblock(self):
        """|coro|

        Unblocks the user.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to unblock this user.
        HTTPException
            Unblocking the user failed.
        """
        await self._state.http.remove_relationship(self.id)

    async def remove_friend(self):
        """|coro|

        Removes the user as a friend.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to remove this user as a friend.
        HTTPException
            Removing the user as a friend failed.
        """
        await self._state.http.remove_relationship(self.id)

    async def send_friend_request(self):
        """|coro|

        Sends the user a friend request.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to send a friend request to the user.
        HTTPException
            Sending the friend request failed.
        """
        await self._state.http.send_friend_request(username=self.name, discriminator=self.discriminator)

    async def profile(self):
        """|coro|

        Gets the user's profile.

        .. note::

            This only applies to non-bot accounts.

        Raises
        -------
        Forbidden
            Not allowed to fetch profiles.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`Profile`
            The profile of the user.
        """

        state = self._state
        data = await state.http.get_user_profile(self.id)

        def transform(d):
            return state._get_guild(int(d['id']))

        since = data.get('premium_since')
        mutual_guilds = list(filter(None, map(transform, data.get('mutual_guilds', []))))
        return Profile(flags=data['user'].get('flags', 0),
                       premium_since=parse_time(since),
                       mutual_guilds=mutual_guilds,
                       user=self,
                       connected_accounts=data['connected_accounts'])
