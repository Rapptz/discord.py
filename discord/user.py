# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

from .utils import snowflake_time, _bytes_to_base64_data
from .enums import DefaultAvatar
from .errors import ClientException

import discord.abc
import asyncio

class BaseUser:
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
        return isinstance(other, BaseUser) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.id >> 22

    @property
    def avatar_url(self):
        """Returns a friendly URL version of the avatar the user has.

        If the user does not have a traditional avatar, their default
        avatar URL is returned instead.
        """
        if self.avatar is None:
            return self.default_avatar_url

        url = 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.{1}?size=1024'
        if self.avatar.startswith('a_'):
            return url.format(self, 'gif')
        else:
            return url.format(self, 'webp')

    @property
    def default_avatar(self):
        """Returns the default avatar for a given user. This is calculated by the user's descriminator"""
        return DefaultAvatar(int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """Returns a URL for a user's default avatar."""
        return 'https://cdn.discordapp.com/embed/avatars/{}.png'.format(self.default_avatar.value)

    @property
    def mention(self):
        """Returns a string that allows you to mention the given user."""
        return '<@{0.id}>'.format(self)

    def permissions_in(self, channel):
        """An alias for :meth:`Channel.permissions_for`.

        Basically equivalent to:

        .. code-block:: python

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
        return getattr(self, 'nick', None) or self.name

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

    Supported Operations:

    +-----------+---------------------------------------------+
    | Operation |                 Description                 |
    +===========+=============================================+
    | x == y    | Checks if two users are equal.              |
    +-----------+---------------------------------------------+
    | x != y    | Checks if two users are not equal.          |
    +-----------+---------------------------------------------+
    | hash(x)   | Return the user's hash.                     |
    +-----------+---------------------------------------------+
    | str(x)    | Returns the user's name with discriminator. |
    +-----------+---------------------------------------------+

    Attributes
    -----------
    name: str
        The user's username.
    id: int
        The user's unique ID.
    discriminator: str
        The user's discriminator. This is given when the username has conflicts.
    avatar: str
        The avatar hash the user has. Could be None.
    bot: bool
        Specifies if the user is a bot account.
    verified: bool
        Specifies if the user is a verified account.
    email: Optional[str]
        The email the user used when registering.
    mfa_enabled: bool
        Specifies if the user has MFA turned on and working.
    premium: bool
        Specifies if the user is a premium user (e.g. has Discord Nitro).
    """
    __slots__ = ('email', 'verified', 'mfa_enabled', 'premium')

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium = data.get('premium', False)

    def __repr__(self):
        return '<ClientUser id={0.id} name={0.name!r} discriminator={0.discriminator!r}' \
               ' bot={0.bot} verified={0.verified} mfa_enabled={0.mfa_enabled}>'.format(self)


    @asyncio.coroutine
    def edit(self, **fields):
        """|coro|

        Edits the current profile of the client.

        If a bot account is used then a password field is optional,
        otherwise it is required.

        Note
        -----
        To upload an avatar, a *bytes-like object* must be passed in that
        represents the image being uploaded. If this is done through a file
        then the file must be opened via ``open('some_filename', 'rb')`` and
        the *bytes-like object* is given through the use of ``fp.read()``.

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
        username :str
            The new username you wish to change to.
        avatar: bytes
            A *bytes-like object* representing the image to upload.
            Could be ``None`` to denote no avatar.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar``.
        ClientException
            Password is required for non-bot accounts.
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

        data = yield from http.edit_profile(**args)
        if not_bot_account:
            self.email = data['email']
            try:
                http._token(data['token'], bot=False)
            except KeyError:
                pass

        # manually update data by calling __init__ explicitly.
        self.__init__(state=self._state, data=data)

class User(BaseUser, discord.abc.Messageable):
    """Represents a Discord user.

    Supported Operations:

    +-----------+---------------------------------------------+
    | Operation |                 Description                 |
    +===========+=============================================+
    | x == y    | Checks if two users are equal.              |
    +-----------+---------------------------------------------+
    | x != y    | Checks if two users are not equal.          |
    +-----------+---------------------------------------------+
    | hash(x)   | Return the user's hash.                     |
    +-----------+---------------------------------------------+
    | str(x)    | Returns the user's name with discriminator. |
    +-----------+---------------------------------------------+

    Attributes
    -----------
    name: str
        The user's username.
    id: int
        The user's unique ID.
    discriminator: str
        The user's discriminator. This is given when the username has conflicts.
    avatar: str
        The avatar hash the user has. Could be None.
    bot: bool
        Specifies if the user is a bot account.
    """

    __slots__ = ('__weakref__')

    def __repr__(self):
        return '<User id={0.id} name={0.name!r} discriminator={0.discriminator!r} bot={0.bot}>'.format(self)

    @asyncio.coroutine
    def _get_channel(self):
        ch = yield from self.create_dm()
        return ch

    @property
    def dm_channel(self):
        """Returns the :class:`DMChannel` associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @asyncio.coroutine
    def create_dm(self):
        """Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data = yield from state.http.start_private_message(self.id)
        return state.add_dm_channel(data)
