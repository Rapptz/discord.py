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

import discord.abc
from .flags import PublicUserFlags
from .utils import snowflake_time, _bytes_to_base64_data
from .enums import DefaultAvatar, try_enum
from .colour import Colour
from .asset import Asset

__all__ = (
    'User',
    'ClientUser',
)

_BaseUser = discord.abc.User


class BaseUser(_BaseUser):
    __slots__ = ('name', 'id', 'discriminator', 'avatar', 'bot', 'system', '_public_flags', '_state')

    def __init__(self, *, state, data):
        self._state = state
        self._update(data)

    def __str__(self):
        return f'{self.name}#{self.discriminator}'

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
        self._public_flags = data.get('public_flags', 0)
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)

    @classmethod
    def _copy(cls, user):
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.avatar = user.avatar
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags

        return self

    def _to_minimal_user_json(self):
        return {
            'username': self.name,
            'id': self.id,
            'avatar': self.avatar,
            'discriminator': self.discriminator,
            'bot': self.bot,
        }

    @property
    def public_flags(self):
        """:class:`PublicUserFlags`: The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def avatar_url(self):
        """:class:`Asset`: Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, an asset for
        the default avatar is returned instead.

        This is equivalent to calling :meth:`avatar_url_as` with
        the default parameters (i.e. webp/gif detection and a size of 1024).
        """
        return self.avatar_url_as(format=None, size=1024)

    def is_avatar_animated(self):
        """:class:`bool`: Indicates if the user has an animated avatar."""
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
        """:class:`DefaultAvatar`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return try_enum(DefaultAvatar, int(self.discriminator) % len(DefaultAvatar))

    @property
    def default_avatar_url(self):
        """:class:`Asset`: Returns a URL for a user's default avatar."""
        return Asset(self._state, f'/embed/avatars/{self.default_avatar.value}.png')

    @property
    def colour(self):
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`color`.
        """
        return Colour.default()

    @property
    def color(self):
        """:class:`Colour`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def mention(self):
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return f'<@{self.id}>'

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

        This is when the user's Discord account was created.
        """
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

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)


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
        The avatar hash the user has. Could be ``None``.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3

    verified: :class:`bool`
        Specifies if the user is a verified account.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    """

    __slots__ = BaseUser.__slots__ + ('locale', '_flags', 'verified', 'mfa_enabled', '__weakref__')

    def __init__(self, *, state, data):
        super().__init__(state=state, data=data)

    def __repr__(self):
        return (
            f'<ClientUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}'
            f' bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>'
        )

    def _update(self, data):
        super()._update(data)
        # There's actually an Optional[str] phone field as well but I won't use it
        self.verified = data.get('verified', False)
        self.locale = data.get('locale')
        self._flags = data.get('flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)

    async def edit(self, *, username=None, avatar=None):
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading is JPEG and PNG.

        Parameters
        -----------
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
        """

        if avatar is not None:
            avatar = _bytes_to_base64_data(avatar)

        data = await self._state.http.edit_profile(username=username, avatar=avatar)
        self._update(data)


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
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = BaseUser.__slots__ + ('__weakref__',)

    def __repr__(self):
        return f'<User id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot}>'

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

    @property
    def mutual_guilds(self):
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [guild for guild in self._state._guilds.values() if guild.get_member(self.id)]

    async def create_dm(self):
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)
