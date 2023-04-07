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

from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING, Union

import discord.abc
from .asset import Asset
from .colour import Colour
from .enums import (
    Locale,
    HypeSquadHouse,
    PremiumType,
    RelationshipAction,
    RelationshipType,
    try_enum,
)
from .errors import ClientException, NotFound
from .flags import PublicUserFlags, PrivateUserFlags, PremiumUsageFlags, PurchasedFlags
from .relationship import Relationship
from .utils import _bytes_to_base64_data, _get_as_snowflake, cached_slot_property, copy_doc, snowflake_time, MISSING
from .voice_client import VoiceClient

if TYPE_CHECKING:
    from typing_extensions import Self

    from datetime import datetime

    from .abc import T as ConnectReturn, VocalChannel
    from .calls import PrivateCall
    from .channel import DMChannel
    from .client import Client
    from .member import VoiceState
    from .message import Message
    from .profile import UserProfile
    from .state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import (
        PartialUser as PartialUserPayload,
        User as UserPayload,
    )
    from .types.snowflake import Snowflake


__all__ = (
    'User',
    'ClientUser',
    'Note',
)


class Note:
    """Represents a Discord note.

    .. container:: operations

        .. describe:: x == y
            Checks if two notes are equal.

        .. describe:: x != y
            Checks if two notes are not equal.

        .. describe:: hash(x)
            Returns the note's hash.

        .. describe:: str(x)
            Returns the note's content.
            Raises :exc:`ClientException` if the note is not fetched.

        .. describe:: bool(x)
            Returns the note's content as a boolean.

        .. describe:: len(x)
            Returns the note's length.

    .. versionadded:: 1.9

    Attributes
    -----------
    user_id: :class:`int`
        The user ID the note is for.
    """

    __slots__ = ('_state', '_value', 'user_id', '_user')

    def __init__(
        self, state: ConnectionState, user_id: int, *, user: Optional[User] = None, note: Optional[str] = MISSING
    ) -> None:
        self._state = state
        self._value: Optional[str] = note
        self.user_id: int = user_id
        self._user: Optional[User] = user

    @property
    def note(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the note.

        There is an alias for this called :attr:`value`.

        Raises
        -------
        ClientException
            Attempted to access note without fetching it.
        """
        if self._value is MISSING:
            raise ClientException('Note is not fetched')
        return self._value

    @property
    def value(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the note.

        This is an alias of :attr:`note`.

        Raises
        -------
        ClientException
            Attempted to access note without fetching it.
        """
        return self.note

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`User`]: Returns the user the note belongs to."""
        return self._state.get_user(self.user_id) or self._user

    async def fetch(self) -> Optional[str]:
        """|coro|

        Retrieves the note.

        Raises
        -------
        HTTPException
            Fetching the note failed.

        Returns
        --------
        Optional[:class:`str`]
            The note or ``None`` if it doesn't exist.
        """
        try:
            data = await self._state.http.get_note(self.user_id)
            self._value = data['note']
            return data['note']
        except NotFound:
            # A 404 means the note doesn't exist
            # However, this is bad UX, so we just return None
            self._value = None
            return None

    async def edit(self, note: Optional[str]) -> None:
        """|coro|

        Modifies the note. Can be at most 256 characters.

        Raises
        -------
        HTTPException
            Changing the note failed.
        """
        await self._state.http.set_note(self.user_id, note=note)
        self._value = note or ''

    async def delete(self) -> None:
        """|coro|

        A shortcut to :meth:`.edit` that deletes the note.

        Raises
        -------
        HTTPException
            Deleting the note failed.
        """
        await self.edit(None)

    def __repr__(self) -> str:
        base = f'<Note user={self.user!r}'
        note = self._value
        if note is not MISSING:
            note = note or ''
            return f'{base} note={note!r}>'
        return f'{base}>'

    def __str__(self) -> str:
        note = self._value
        if note is MISSING:
            raise ClientException('Note is not fetched')
        return note or ''

    def __bool__(self) -> bool:
        return bool(str(self))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Note) and self.user_id == other.user_id

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Note):
            return self._value != other._value or self.user_id != other.user_id
        return True

    def __hash__(self) -> int:
        return hash((self._value, self.user_id))

    def __len__(self) -> int:
        note = str(self)
        return len(note) if note else 0


class _UserTag:
    __slots__ = ()
    id: int


class BaseUser(_UserTag):
    __slots__ = (
        'name',
        'id',
        'discriminator',
        '_avatar',
        '_avatar_decoration',
        '_banner',
        '_accent_colour',
        'bot',
        'system',
        '_public_flags',
        '_cs_note',
        '_state',
    )

    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        bot: bool
        system: bool
        _state: ConnectionState
        _avatar: Optional[str]
        _avatar_decoration: Optional[str]
        _banner: Optional[str]
        _accent_colour: Optional[int]
        _public_flags: int

    def __init__(self, *, state: ConnectionState, data: Union[UserPayload, PartialUserPayload]) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return (
            f"<BaseUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}"
            f" bot={self.bot} system={self.system}>"
        )

    def __str__(self) -> str:
        return f'{self.name}#{self.discriminator}'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    def _update(self, data: Union[UserPayload, PartialUserPayload]) -> None:
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self._avatar = data['avatar']
        self._avatar_decoration = data.get('avatar_decoration')
        self._banner = data.get('banner', None)
        self._accent_colour = data.get('accent_color', None)
        self._public_flags = data.get('public_flags', 0)
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)

    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self._avatar = user._avatar
        self._avatar_decoration = user._avatar_decoration
        self._banner = user._banner
        self._accent_colour = user._accent_colour
        self._public_flags = user._public_flags
        self.bot = user.bot
        self.system = user.system
        self._state = user._state

        return self

    def _to_minimal_user_json(self) -> PartialUserPayload:
        user: PartialUserPayload = {
            'username': self.name,
            'id': self.id,
            'avatar': self._avatar,
            'avatar_decoration': self._avatar_decoration,
            'discriminator': self.discriminator,
            'bot': self.bot,
            'system': self.system,
            'public_flags': self._public_flags,
        }
        return user

    @property
    def voice(self) -> Optional[VoiceState]:
        """Optional[:class:`VoiceState`]: Returns the user's current voice state."""
        return self._state._voice_state_for(self.id)

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar the user has.

        If the user has not uploaded a global avatar, ``None`` is returned.
        If you want the avatar that a user has displayed, consider :attr:`display_avatar`.
        """
        if self._avatar is not None:
            return Asset._from_avatar(self._state, self.id, self._avatar)
        return None

    @property
    def default_avatar(self) -> Asset:
        """:class:`Asset`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return Asset._from_default_avatar(self._state, int(self.discriminator) % 5)

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        return self.avatar or self.default_avatar

    @property
    def avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar decoration the user has.

        If the user does not have a avatar decoration, ``None`` is returned.

        .. versionadded:: 2.0
        """
        if self._avatar_decoration is not None:
            return Asset._from_avatar_decoration(self._state, self.id, self._avatar_decoration)
        return None

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the user's banner asset, if available.

        .. versionadded:: 2.0

        .. note::
            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._banner is None:
            return None
        return Asset._from_user_banner(self._state, self.id, self._banner)

    @property
    def display_banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the user's banner asset, if available.

        This is the same as :attr:`banner` and is here for compatibility.

        .. versionadded:: 2.0
        """
        return self.banner

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: Returns the user's accent colour, if applicable.

        A user's accent colour is only shown if they do not have a banner.
        This will only be available if the user explicitly sets a colour.

        There is an alias for this named :attr:`accent_color`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._accent_colour is None:
            return None
        return Colour(self._accent_colour)

    @property
    def accent_color(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: Returns the user's accent color, if applicable.

        A user's accent color is only shown if they do not have a banner.
        This will only be available if the user explicitly sets a color.

        There is an alias for this named :attr:`accent_colour`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        return self.accent_colour

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`color`.
        """
        return Colour.default()

    @property
    def color(self) -> Colour:
        """:class:`Colour`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return f'<@{self.id}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created.
        """
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their username, but
        if they have a guild specific nickname then that
        is returned instead.
        """
        return self.name

    @cached_slot_property('_cs_note')
    def note(self) -> Note:
        """:class:`Note`: Returns an object representing the user's note.

        .. versionadded:: 2.0

        .. note::

            The underlying note is cached and updated from gateway events.
        """
        return Note(self._state, self.id, user=self)  # type: ignore

    def mentioned_in(self, message: Message) -> bool:
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

    .. versionchanged:: 2.0
        :attr:`Locale` is now a :class:`Locale` instead of a Optional[:class:`str`].

    Attributes
    -----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator.
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3
    verified: :class:`bool`
        Specifies if the user's email is verified.
    email: Optional[:class:`str`]
        The email of the user.
    phone: Optional[:class:`int`]
        The phone number of the user.

        .. versionadded:: 1.9
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    premium_type: Optional[:class:`PremiumType`]
        Specifies the type of premium a user has (i.e. Nitro, Nitro Classic, or Nitro Basic). Could be None if the user is not premium.
    note: :class:`Note`
        The user's note. Not pre-fetched.

        .. versionadded:: 1.9
    nsfw_allowed: Optional[:class:`bool`]
        Specifies if the user should be allowed to access NSFW content.
        If ``None``, then the user's date of birth is not known.

        .. versionadded:: 2.0
    desktop: :class:`bool`
        Specifies whether the user has used a desktop client.

        .. versionadded:: 2.0
    mobile: :class:`bool`
        Specifies whether the user has used a mobile client.

        .. versionadded:: 2.0
    """

    __slots__ = (
        '__weakref__',
        '_locale',
        '_flags',
        'verified',
        'mfa_enabled',
        'email',
        'phone',
        'premium_type',
        'note',
        'bio',
        'nsfw_allowed',
        'desktop',
        'mobile',
        '_purchased_flags',
        '_premium_usage_flags',
    )

    if TYPE_CHECKING:
        verified: bool
        email: Optional[str]
        phone: Optional[int]
        _locale: str
        _flags: int
        mfa_enabled: bool
        premium_type: Optional[PremiumType]
        bio: Optional[str]
        nsfw_allowed: Optional[bool]

    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        self._state = state
        self._full_update(data)
        self.note: Note = Note(state, self.id)

    def __repr__(self) -> str:
        return (
            f'<ClientUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}'
            f' bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled} premium={self.premium}>'
        )

    def _full_update(self, data: UserPayload) -> None:
        self._update(data)
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.phone = _get_as_snowflake(data, 'phone')
        self._locale = data.get('locale', 'en-US')
        self._flags = data.get('flags', 0)
        self._purchased_flags = data.get('purchased_flags', 0)
        self._premium_usage_flags = data.get('premium_usage_flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium_type = try_enum(PremiumType, data.get('premium_type')) if data.get('premium_type') else None
        self.bio = data.get('bio') or None
        self.nsfw_allowed = data.get('nsfw_allowed')
        self.desktop: bool = data.get('desktop', False)
        self.mobile: bool = data.get('mobile', False)

    def _update_self(self, *args: Any) -> None:
        # ClientUser is kept up to date by USER_UPDATEs only
        return

    @property
    def locale(self) -> Locale:
        """:class:`Locale`: The IETF language tag used to identify the language the user is using."""
        return self._state.settings.locale if self._state.settings else try_enum(Locale, self._locale)

    @property
    def premium(self) -> bool:
        """Indicates if the user is a premium user (i.e. has Discord Nitro)."""
        return self.premium_type is not None

    @property
    def flags(self) -> PrivateUserFlags:
        """:class:`PrivateUserFlags`: Returns the user's flags (including private).

        .. versionadded:: 2.0
        """
        return PrivateUserFlags._from_value(self._flags)

    @property
    def premium_usage_flags(self) -> PremiumUsageFlags:
        """:class:`PremiumUsageFlags`: Returns the user's premium usage flags.

        .. versionadded:: 2.0
        """
        return PremiumUsageFlags._from_value(self._premium_usage_flags)

    @property
    def purchased_flags(self) -> PurchasedFlags:
        """:class:`PurchasedFlags`: Returns the user's purchased flags.

        .. versionadded:: 2.0
        """
        return PurchasedFlags._from_value(self._purchased_flags)

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
        avatar_decoration: Optional[bytes] = MISSING,
        password: str = MISSING,
        new_password: str = MISSING,
        email: str = MISSING,
        house: Optional[HypeSquadHouse] = MISSING,
        discriminator: Snowflake = MISSING,
        banner: Optional[bytes] = MISSING,
        accent_colour: Colour = MISSING,
        accent_color: Colour = MISSING,
        bio: Optional[str] = MISSING,
        date_of_birth: datetime = MISSING,
    ) -> ClientUser:
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited client user is returned.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        password: :class:`str`
            The current password for the client's account.
            Required for everything except avatar, banner, accent_colour, date_of_birth, and bio.
        new_password: :class:`str`
            The new password you wish to change to.
        email: :class:`str`
            The new email you wish to change to.
        house: Optional[:class:`HypeSquadHouse`]
            The hypesquad house you wish to change to.
            Could be ``None`` to leave the current house.
        username: :class:`str`
            The new username you wish to change to.
        discriminator: :class:`int`
            The new discriminator you wish to change to.
            Can only be used if you have Nitro.
        avatar: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.
        avatar_decoration: Optional[:class:`bytes`]
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar decoration.

            .. versionadded:: 2.0
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no banner.
        accent_colour: :class:`Colour`
            A :class:`Colour` object of the colour you want to set your profile to.

            .. versionadded:: 2.0
        bio: :class:`str`
            Your "about me" section.
            Could be ``None`` to represent no bio.

            .. versionadded:: 2.0
        date_of_birth: :class:`datetime.datetime`
            Your date of birth. Can only ever be set once.

            .. versionadded:: 2.0

        Raises
        ------
        HTTPException
            Editing your profile failed.
        ValueError
            Password was not passed when it was required.
            `house` field was not a :class:`HypeSquadHouse`.
            `date_of_birth` field was not a :class:`datetime.datetime`.
            `accent_colo(u)r` parameter was not a :class:`Colour`.

        Returns
        ---------
        :class:`ClientUser`
            The newly edited client user.
        """
        args: Dict[str, Any] = {}

        if any(x is not MISSING for x in (new_password, email, username, discriminator)):
            if password is MISSING:
                raise ValueError('Password is required')
            args['password'] = password

        if avatar is not MISSING:
            if avatar is not None:
                args['avatar'] = _bytes_to_base64_data(avatar)
            else:
                args['avatar'] = None

        if avatar_decoration is not MISSING:
            if avatar_decoration is not None:
                args['avatar_decoration'] = _bytes_to_base64_data(avatar_decoration)
            else:
                args['avatar_decoration'] = None

        if banner is not MISSING:
            if banner is not None:
                args['banner'] = _bytes_to_base64_data(banner)
            else:
                args['banner'] = None

        if accent_color is not MISSING or accent_colour is not MISSING:
            colour = accent_colour if accent_colour is not MISSING else accent_color
            if colour is None:
                args['accent_color'] = colour
            elif not isinstance(colour, Colour):
                raise ValueError('`accent_colo(u)r` parameter was not a Colour')
            else:
                args['accent_color'] = accent_color.value

        if email is not MISSING:
            args['email'] = email

        if username is not MISSING:
            args['username'] = username

        if discriminator is not MISSING:
            args['discriminator'] = discriminator

        if new_password is not MISSING:
            args['new_password'] = new_password

        if bio is not MISSING:
            args['bio'] = bio or ''

        if date_of_birth is not MISSING:
            if not isinstance(date_of_birth, datetime):
                raise ValueError('`date_of_birth` parameter was not a datetime')
            args['date_of_birth'] = date_of_birth.strftime('%F')

        http = self._state.http

        if house is not MISSING:
            if house is None:
                await http.leave_hypesquad_house()
            elif not isinstance(house, HypeSquadHouse):
                raise ValueError('`house` parameter was not a HypeSquadHouse')
            else:
                await http.change_hypesquad_house(house.value)

        data = await http.edit_profile(args)
        try:
            http._token(data['token'])
        except KeyError:
            pass

        return ClientUser(state=self._state, data=data)


class User(BaseUser, discord.abc.Connectable, discord.abc.Messageable):
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
        The user's discriminator.
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = ('__weakref__',)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot} system={self.system}>'

    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self._state.self_id, 'self_id'  # type: ignore # self_id is always set at this point

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self._state.self_id, self.dm_channel.id  # type: ignore # self_id is always set at this point

    def _update_self(self, user: Union[PartialUserPayload, Tuple[()]]) -> Optional[Tuple[User, User]]:
        if len(user) == 0 or len(user) <= 1:  # Done because of typing
            return

        original = (self.name, self._avatar, self.discriminator, self._public_flags, self._avatar_decoration)
        # These keys seem to always be available
        modified = (
            user['username'],
            user.get('avatar'),
            user['discriminator'],
            user.get('public_flags', 0),
            user.get('avatar_decoration'),
        )
        if original != modified:
            to_return = User._copy(self)
            self.name, self._avatar, self.discriminator, self._public_flags, self._avatar_decoration = modified
            # Signal to dispatch user_update
            return to_return, self

    async def _get_channel(self) -> DMChannel:
        ch = await self.create_dm()
        return ch

    @property
    def dm_channel(self) -> Optional[DMChannel]:
        """Optional[:class:`DMChannel`]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @property
    def call(self) -> Optional[PrivateCall]:
        """Optional[:class:`PrivateCall`]: Returns the call associated with this user if it exists."""
        return getattr(self.dm_channel, 'call', None)

    @property
    def relationship(self) -> Optional[Relationship]:
        """Optional[:class:`Relationship`]: Returns the :class:`Relationship` with this user if applicable, ``None`` otherwise."""
        return self._state._relationships.get(self.id)

    @copy_doc(discord.abc.Connectable.connect)
    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, VocalChannel], ConnectReturn] = VoiceClient,
        ring: bool = True,
    ) -> ConnectReturn:
        channel = await self._get_channel()
        call = channel.call
        if call is None and ring:
            await channel._initial_ring()
        return await super().connect(timeout=timeout, reconnect=reconnect, cls=cls, _channel=channel)

    async def create_dm(self) -> DMChannel:
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
        data: DMChannelPayload = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)

    def is_friend(self) -> bool:
        """:class:`bool`: Checks if the user is your friend."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend

    def is_blocked(self) -> bool:
        """:class:`bool`: Checks if the user is blocked."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.blocked

    async def block(self) -> None:  # TODO: maybe return relationship
        """|coro|

        Blocks the user.

        Raises
        -------
        Forbidden
            Not allowed to block this user.
        HTTPException
            Blocking the user failed.
        """
        await self._state.http.add_relationship(
            self.id, type=RelationshipType.blocked.value, action=RelationshipAction.block
        )

    async def unblock(self) -> None:
        """|coro|

        Unblocks the user.

        Raises
        -------
        Forbidden
            Not allowed to unblock this user.
        HTTPException
            Unblocking the user failed.
        """
        await self._state.http.remove_relationship(self.id, action=RelationshipAction.unblock)

    async def remove_friend(self) -> None:
        """|coro|

        Removes the user as a friend.

        Raises
        -------
        Forbidden
            Not allowed to remove this user as a friend.
        HTTPException
            Removing the user as a friend failed.
        """
        await self._state.http.remove_relationship(self.id, action=RelationshipAction.unfriend)

    async def send_friend_request(self) -> None:
        """|coro|

        Sends the user a friend request.

        Raises
        -------
        Forbidden
            Not allowed to send a friend request to the user.
        HTTPException
            Sending the friend request failed.
        """
        await self._state.http.send_friend_request(self.name, self.discriminator)

    async def profile(
        self,
        *,
        with_mutual_guilds: bool = True,
        with_mutual_friends_count: bool = False,
        with_mutual_friends: bool = True,
    ) -> UserProfile:
        """|coro|

        A shorthand method to retrieve a :class:`UserProfile` for the user.

        Parameters
        ------------
        with_mutual_guilds: :class:`bool`
            Whether to fetch mutual guilds.
            This fills in :attr:`UserProfile.mutual_guilds`.

            .. versionadded:: 2.0
        with_mutual_friends_count: :class:`bool`
            Whether to fetch the number of mutual friends.
            This fills in :attr:`UserProfile.mutual_friends_count`.

            .. versionadded:: 2.0
        with_mutual_friends: :class:`bool`
            Whether to fetch mutual friends.
            This fills in :attr:`UserProfile.mutual_friends` and :attr:`UserProfile.mutual_friends_count`,
            but requires an extra API call.

            .. versionadded:: 2.0

        Raises
        -------
        Forbidden
            Not allowed to fetch this profile.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`UserProfile`
            The profile of the user.
        """
        return await self._state.client.fetch_user_profile(
            self.id,
            with_mutual_guilds=with_mutual_guilds,
            with_mutual_friends_count=with_mutual_friends_count,
            with_mutual_friends=with_mutual_friends,
        )
