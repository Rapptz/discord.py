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

from .utils import snowflake_time, _bytes_to_base64_data, parse_time, valid_icon_size
from .enums import DefaultAvatar, RelationshipType, UserFlags, HypeSquadHouse
from .errors import ClientException, InvalidArgument
from .colour import Colour

from collections import namedtuple

import discord.abc

VALID_STATIC_FORMATS = {"jpeg", "jpg", "webp", "png"}
VALID_AVATAR_FORMATS = VALID_STATIC_FORMATS | {"gif"}

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
    def hypesquad(self):
        return self._has_flag(UserFlags.hypesquad)

    @property
    def partner(self):
        return self._has_flag(UserFlags.partner)

    @property
    def hypesquad_houses(self):
        flags = (UserFlags.hypesquad_bravery, UserFlags.hypesquad_brilliance, UserFlags.hypesquad_balance)
        return [house for house, flag in zip(HypeSquadHouse, flags) if self._has_flag(flag)]

_BaseUser = discord.abc.User

class BaseUser(_BaseUser):
    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', '_state')

    def __init__(self, *, state, data):
        self._state = state
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self.avatar = data['avatar']
        self.bot = data.get('bot', False)

    def __str__(self):
        return '{0.name}#{0.discriminator}'.format(self)

    def __eq__(self, other):
        return isinstance(other, _BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22

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
        """Returns a friendly URL version of the avatar the user has.

        If the user does not have a traditional avatar, their default
        avatar URL is returned instead.

        This is equivalent to calling :meth:`avatar_url_as` with
        the default parameters (i.e. webp/gif detection and a size of 1024).
        """
        return self.avatar_url_as(format=None, size=1024)

    def is_avatar_animated(self):
        """:class:`bool`: Returns True if the user has an animated avatar."""
        return bool(self.avatar and self.avatar.startswith('a_'))

    def avatar_url_as(self, *, format=None, static_format='webp', size=1024):
        """Returns a friendly URL version of the avatar the user has.

        If the user does not have a traditional avatar, their default
        avatar URL is returned instead.

        The format must be one of 'webp', 'jpeg', 'jpg', 'png' or 'gif', and
        'gif' is only valid for animated avatars. The size must be a power of 2
        between 16 and 1024.

        Parameters
        -----------
        format: Optional[str]
            The format to attempt to convert the avatar to.
            If the format is ``None``, then it is automatically
            detected into either 'gif' or static_format depending on the
            avatar being animated or not.
        static_format: 'str'
            Format to attempt to convert only non-animated avatars to.
            Defaults to 'webp'
        size: int
            The size of the image to display.

        Returns
        --------
        str
            The resulting CDN URL.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or ``static_format``, or
            invalid ``size``.
        """
        if not valid_icon_size(size):
            raise InvalidArgument("size must be a power of 2 between 16 and 1024")
        if format is not None and format not in VALID_AVATAR_FORMATS:
            raise InvalidArgument("format must be None or one of {}".format(VALID_AVATAR_FORMATS))
        if format == "gif" and not self.is_avatar_animated():
            raise InvalidArgument("non animated avatars do not support gif format")
        if static_format not in VALID_STATIC_FORMATS:
            raise InvalidArgument("static_format must be one of {}".format(VALID_STATIC_FORMATS))

        if self.avatar is None:
            return self.default_avatar_url

        if format is None:
            if self.is_avatar_animated():
                format = 'gif'
            else:
                format = static_format

        return 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.{1}?size={2}'.format(self, format, size)

    @property
    def default_avatar(self):
        """Returns the default avatar for a given user. This is calculated by the user's discriminator"""
        return DefaultAvatar(int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """Returns a URL for a user's default avatar."""
        return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(self.default_avatar.value)

    @property
    def colour(self):
        """A property that returns a :class:`Colour` denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this under ``color``.
        """
        return Colour.default()

    color = colour

    @property
    def mention(self):
        """Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

    def permissions_in(self, channel):
        """An alias for :meth:`abc.GuildChannel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python3

            channel.permissions_for(self)

        Parameters
        -----------
        channel
            The channel to check your permissions for.
        """
        return channel.permissions_for(self)

    @property
    def created_at(self):
        """Returns the user's creation time in UTC.

        This is when the user's discord account was created."""
        return snowflake_time(self.id)

    @property
    def display_name(self):
        """Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.name

    def mentioned_in(self, message):
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message : :class:`Message`
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
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    premium: :class:`bool`
        Specifies if the user is a premium user (e.g. has Discord Nitro).
    """
    __slots__ = ('email', 'verified', 'mfa_enabled', 'premium', '_relationships')

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium = data.get('premium', False)
        self._relationships = {}

    def __repr__(self):
        return '<ClientUser id={0.id} name={0.name!r} discriminator={0.discriminator!r}' \
               ' bot={0.bot} verified={0.verified} mfa_enabled={0.mfa_enabled}>'.format(self)


    def get_relationship(self, user_id):
        """Retrieves the :class:`Relationship` if applicable.

        Parameters
        -----------
        user_id: int
            The user ID to check if we have a relationship with them.

        Returns
        --------
        Optional[:class:`Relationship`]
            The relationship if available or ``None``
        """
        return self._relationships.get(user_id)

    @property
    def relationships(self):
        """Returns a :class:`list` of :class:`Relationship` that the user has."""
        return list(self._relationships.values())

    @property
    def friends(self):
        r"""Returns a :class:`list` of :class:`User`\s that the user is friends with."""
        return [r.user for r in self._relationships.values() if r.type is RelationshipType.friend]

    @property
    def blocked(self):
        r"""Returns a :class:`list` of :class:`User`\s that the user has blocked."""
        return [r.user for r in self._relationships.values() if r.type is RelationshipType.blocked]

    async def edit(self, **fields):
        """|coro|

        Edits the current profile of the client.

        If a bot account is used then a password field is optional,
        otherwise it is required.

        Note
        -----
        To upload an avatar, a :term:`py:bytes-like object` must be passed in that
        represents the image being uploaded. If this is done through a file
        then the file must be opened via ``open('some_filename', 'rb')`` and
        the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

        The only image formats supported for uploading is JPEG and PNG.

        Parameters
        -----------
        password : str
            The current password for the client's account.
            Only applicable to user accounts.
        new_password: str
            The new password you wish to change to.
            Only applicable to user accounts.
        email: str
            The new email you wish to change to.
            Only applicable to user accounts.
        house: Optional[:class:`HypeSquadHouse`]
            The hypesquad house you wish to change to.
            Could be ``None`` to leave the current house.
            Only applicable to user accounts.
        username :str
            The new username you wish to change to.
        avatar: bytes
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

        # manually update data by calling __init__ explicitly.
        self.__init__(state=self._state, data=data)

    async def create_group(self, *recipients):
        r"""|coro|

        Creates a group direct message with the recipients
        provided. These recipients must be have a relationship
        of type :attr:`RelationshipType.friend`.

        Bot accounts cannot create a group.

        Parameters
        -----------
        \*recipients
            An argument :class:`list` of :class:`User` to have in
            your group.

        Return
        -------
        :class:`GroupChannel`
            The new group channel.

        Raises
        -------
        HTTPException
            Failed to create the group direct message.
        ClientException
            Attempted to create a group with only one recipient.
            This does not include yourself.
        """

        from .channel import GroupChannel

        if len(recipients) < 2:
            raise ClientException('You must have two or more recipients to create a group.')

        users = [str(u.id) for u in recipients]
        data = await self._state.http.start_group(self.id, users)
        return GroupChannel(me=self, data=data, state=self._state)

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
        """Returns the :class:`DMChannel` associated with this user if it exists.

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
        """Returns the :class:`Relationship` with this user if applicable, ``None`` otherwise."""
        return self._state.user.get_relationship(self.id)

    def is_friend(self):
        """:class:`bool`: Checks if the user is your friend."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend

    def is_blocked(self):
        """:class:`bool`: Checks if the user is blocked."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.blocked

    async def block(self):
        """|coro|

        Blocks the user.

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

        Gets the user's profile. This can only be used by non-bot accounts.

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
