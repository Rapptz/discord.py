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

from copy import copy
from typing import Any, Dict, List, Optional, Type, TypeVar, TYPE_CHECKING, Union

import discord.abc
from .asset import Asset
from .colour import Colour
from .enums import DefaultAvatar, HypeSquadHouse, PremiumType, RelationshipAction, RelationshipType, try_enum, UserFlags
from .errors import ClientException, NotFound
from .flags import PublicUserFlags
from .object import Object
from .relationship import Relationship
from .settings import UserSettings
from .utils import _bytes_to_base64_data, _get_as_snowflake, cached_slot_property, parse_time, snowflake_time, MISSING

if TYPE_CHECKING:
    from datetime import datetime

    from .calls import PrivateCall
    from .channel import DMChannel
    from .guild import Guild
    from .member import VoiceState
    from .message import Message
    from .state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.snowflake import Snowflake
    from .types.user import User as UserPayload


__all__ = (
    'User',
    'ClientUser',
)

BU = TypeVar('BU', bound='BaseUser')


class Note:
    """Represents a Discord note."""
    __slots__ = ('_state', '_note', '_user_id', '_user')

    def __init__(
        self, state: ConnectionState, user_id: int, *, user: BaseUser = MISSING, note: Optional[str] = MISSING
    ) -> None:
        self._state = state
        self._user_id = user_id
        self._note = note
        if user is not MISSING:
            self._user: Union[User, Object] = user

    @property
    def note(self) -> Optional[str]:
        """Returns the note.

        Raises
        -------
        ClientException
            Attempted to access note without fetching it.
        """
        if self._note is MISSING:
            raise ClientException('Note is not fetched')
        return self._note

    @cached_slot_property('_user')
    def user(self) -> Union[User, Object]:
        """Returns the :class:`User` the note belongs to.

        If the user isn't in the cache, it returns a
        :class:`Object` instead.
        """
        user_id = self._user_id

        user = self._state.get_user(user_id)
        if user is None:
            user = Object(user_id)
        return user

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
            data = await self._state.http.get_note(self.user.id)
            self._note = data['note']
            return data['note']
        except NotFound:  # 404 = no note :(
            self._note = None
            return None

    async def edit(self, note: Optional[str]) -> None:
        """|coro|

        Changes the note.

        Raises
        -------
        HTTPException
            Changing the note failed.
        """
        await self._state.http.set_note(self._user_id, note=note)
        self._note = note

    async def delete(self) -> None:
        """|coro|

        A shortcut to :meth:`.edit` that deletes the note.

        Raises
        -------
        HTTPException
            Deleting the note failed.
        """
        await self.edit(None)

    def __str__(self) -> str:
        note = self._note
        if note is MISSING:
            raise ClientException('Note is not fetched')
        elif note is None:
            return ''
        else:
            return note

    def __repr__(self) -> str:
        base = f'<Note user={self.user!r}'
        note = self._note
        if note is not MISSING:
            base += f' note={note or ""}>'
        else:
            base += '>'
        return base

    def __len__(self) -> int:
        try:
            return len(self._note)
        except TypeError:
            return 0

    def __eq__(self, other) -> bool:
        try:
            return isinstance(other, Note) and self._note == other._note
        except TypeError:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __bool__(self) -> bool:
        try:
            return bool(self._note)
        except TypeError:
            return False


class Profile:
    """Represents a Discord profile.

    Attributes
    ----------
    flags: :class:`int`
        The user's flags. Will be its own class (like public_flags) in the future.
    bio: Optional[:class:`str`]
        The user's "about me" field. Could be ``None``.
    user: :class:`User`
        The user the profile represents (with banner/accent_colour).
    premium_since: Optional[:class:`datetime.datetime`]
        A datetime object denoting how long a user has been premium (had Nitro).
        Could be ``None``.
    connected_accounts: Optional[List[:class:`dict`]]
        The connected accounts that show up on the profile.
        These are currently just the raw json, but this will change in the future.
    note: :class:`Note`
        Represents the note on the profile.
    """

    __slots__ = (
        '_state',
        'user',
        'flags',
        'bio',
        'premium_since',
        'connected_accounts',
        'note',
        'mutual_guilds',
        'mutual_friends',
    )

    def __init__(self, state: ConnectionState, data) -> None:  # Type data
        self._state = state

        user = data['user']
        self.flags: int = user.pop('flags', 0)  # TODO: figure them all out and parse them
        self.bio: Optional[str] = user.pop('bio') or None
        self.user: User = User(data=user, state=state)

        self.premium_since: datetime = parse_time(data['premium_since'])
        self.connected_accounts: List[dict] = data['connected_accounts']  # TODO: parse these

        self.note: Note = Note(state, self.user.id, user=self.user)

        if 'mutual_guilds' in data:
            self.mutual_guilds: List[Guild] = self._parse_mutual_guilds(data['mutual_guilds'])
        if 'mutual_friends' in data:  # TODO: maybe make Relationships
            self.mutual_friends: List[User] = self._parse_mutual_friends(data['mutual_friends'])

    def __str__(self) -> str:
        return '{0.name}#{0.discriminator}'.format(self.user)

    def __repr__(self) -> str:
        return '<Profile user={0.user!r} bio={0.bio}>'.format(self)

    def _parse_mutual_guilds(self, mutual_guilds) -> List[Guild]:
        state = self._state

        def get_guild(guild) -> Optional[Guild]:
            return state._get_guild(int(guild['id']))

        return list(filter(None, map(get_guild, mutual_guilds)))

    def _parse_mutual_friends(self, mutual_friends) -> List[User]:
        state = self._state
        return [state.store_user(friend) for friend in mutual_friends]

    @property
    def nitro(self) -> bool:
        return self.premium_since is not None

    premium = nitro

    def _has_flag(self, o) -> bool:
        v = o.value
        return (self.flags & v) == v

    @property
    def staff(self) -> bool:
        return self._has_flag(UserFlags.staff)

    @property
    def partner(self) -> bool:
        return self._has_flag(UserFlags.partner)

    @property
    def bug_hunter(self) -> bool:
        return self._has_flag(UserFlags.bug_hunter)

    @property
    def early_supporter(self) -> bool:
        return self._has_flag(UserFlags.early_supporter)

    @property
    def hypesquad(self) -> bool:
        return self._has_flag(UserFlags.hypesquad)

    @property
    def hypesquad_house(self) -> HypeSquadHouse:
        return self.hypesquad_houses[0]

    @property
    def hypesquad_houses(self) -> List[HypeSquadHouse]:
        flags = (UserFlags.hypesquad_bravery, UserFlags.hypesquad_brilliance, UserFlags.hypesquad_balance)
        return [house for house, flag in zip(HypeSquadHouse, flags) if self._has_flag(flag)]

    @property
    def team_user(self) -> bool:
        return self._has_flag(UserFlags.team_user)

    @property
    def system(self) -> bool:
        return self._has_flag(UserFlags.system)


class _UserTag:
    __slots__ = ()
    id: int


class BaseUser(_UserTag):
    __slots__ = (
        'name',
        'id',
        'discriminator',
        '_avatar',
        '_banner',
        '_accent_colour',
        'bot',
        'system',
        '_public_flags',
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
        _banner: Optional[str]
        _accent_colour: Optional[str]
        _public_flags: int

    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        self._state = state
        self._update(data)

    def __repr__(self) -> str:
        return (
            f"<BaseUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}"
            f" bot={self.bot} system={self.system}>"
        )

    def __str__(self) -> str:
        return f'{self.name}#{self.discriminator}'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    def _update(self, data: UserPayload) -> None:
        self.name = data['username']
        self.id = int(data['id'])
        self.discriminator = data['discriminator']
        self._avatar = data['avatar']
        self._banner = data.get('banner', None)
        self._accent_colour = data.get('accent_color', None)
        self._public_flags = data.get('public_flags', 0)
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)

    @classmethod
    def _copy(cls: Type[BU], user: BU) -> BU:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self._avatar = user._avatar
        self._banner = user._banner
        self._accent_colour = user._accent_colour
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags

        return self

    def _to_minimal_user_json(self) -> Dict[str, Any]:
        return {
            'username': self.name,
            'id': self.id,
            'avatar': self._avatar,
            'discriminator': self.discriminator,
            'bot': self.bot,
            'system': self.system,
        }

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

        If the user does not have a traditional avatar, ``None`` is returned.
        If you want the avatar that a user has displayed, consider :attr:`display_avatar`.
        """
        if self._avatar is not None:
            return Asset._from_avatar(self._state, self.id, self._avatar)
        return None

    @property
    def default_avatar(self) -> Asset:
        """:class:`Asset`: Returns the default avatar for a given user. This is calculated by the user's discriminator."""
        return Asset._from_default_avatar(self._state, int(self.discriminator) % len(DefaultAvatar))

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        return self.avatar or self.default_avatar

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
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: Returns the user's accent colour, if applicable.

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
    avatar: Optional[:class:`str`]
        The avatar hash the user has. Could be ``None``.
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

    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    premium: :class:`bool`
        Specifies if the user is a premium user (i.e. has Discord Nitro).
    premium_type: Optional[:class:`PremiumType`]
        Specifies the type of premium a user has (i.e. Nitro or Nitro Classic). Could be None if the user is not premium.
    note: :class:`Note`
        The user's note. Not pre-fetched.
    """

    __slots__ = (
        'locale',
        '_flags',
        'verified',
        'mfa_enabled',
        'email',
        'phone',
        'premium_type',
        'note',
        'premium',
        'bio',
    )

    if TYPE_CHECKING:
        verified: bool
        email: Optional[str]
        phone: Optional[int]
        locale: Optional[str]
        _flags: int
        mfa_enabled: bool
        premium: bool
        premium_type: Optional[PremiumType]
        bio: Optional[str]

    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        super().__init__(state=state, data=data)
        self.note: Note = Note(state, self.id)

    def __repr__(self) -> str:
        return (
            f'<ClientUser id={self.id} name={self.name!r} discriminator={self.discriminator!r}'
            f' bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled} premium={self.premium}>'
        )

    def _update(self, data: UserPayload) -> None:
        super()._update(data)
        # There's actually an Optional[str] phone field as well but I won't use it
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.phone = _get_as_snowflake(data, 'phone')
        self.locale = data.get('locale')
        self._flags = data.get('flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium = data.get('premium', False)
        self.premium_type = try_enum(PremiumType, data.get('premium_type', None))
        self.bio = data.get('bio') or None

    @property
    def connected_accounts(self) -> Optional[List[dict]]:
        """Optional[List[:class:`dict`]]: Returns a list of all linked accounts for this user if available."""
        return self._state._connected_accounts

    def get_relationship(self, user_id: int) -> Relationship:
        """Retrieves the :class:`Relationship` if applicable.

        Parameters
        -----------
        user_id: :class:`int`
            The user ID to check if we have a relationship with them.

        Returns
        --------
        Optional[:class:`Relationship`]
            The relationship if available or ``None``.
        """
        return self._state._relationships.get(user_id)

    @property
    def relationships(self) -> List[Relationship]:
        """List[:class:`User`]: Returns all the relationships that the user has."""
        return list(self._state._relationships.values())

    @property
    def friends(self) -> List[Relationship]:
        r"""List[:class:`User`]: Returns all the users that the user is friends with."""
        return [r.user for r in self._state._relationships.values() if r.type is RelationshipType.friend]

    @property
    def blocked(self) -> List[Relationship]:
        r"""List[:class:`User`]: Returns all the users that the user has blocked."""
        return [r.user for r in self._state._relationships.values() if r.type is RelationshipType.blocked]

    @property
    def settings(self) -> Optional[UserSettings]:
        """Optional[:class:`UserSettings`]: Returns the user's settings."""
        return self._state.settings

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: Optional[bytes] = MISSING,
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
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no banner.
        accent_colour/_color: :class:`Colour`
            A :class:`Colour` object of the colour you want to set your profile to.
        bio: :class:`str`
            Your 'about me' section.
            Could be ``None`` to represent no 'about me'.
        date_of_birth: :class:`datetime.datetime`
            Your date of birth. Can only ever be set once.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        ClientException
            Password was not passed when it was required.
            `house` field was not a :class:`HypeSquadHouse`.
            `date_of_birth` field was not a :class:`datetime.datetime`.
            `accent_colo(u)r` parameter was not a :class:`Colour`.

        Returns
        ---------
        :class:`ClientUser`
            The newly edited client user.
        """
        args: Dict[str, any] = {}

        if any(x is not MISSING for x in ('new_password', 'email', 'username', 'discriminator')):
            if password is MISSING:
                raise ClientException('Password is required')
            args['password'] = password

        if avatar is not MISSING:
            if avatar is not None:
                args['avatar'] = _bytes_to_base64_data(avatar)
            else:
                args['avatar'] = None

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
                raise ClientException('`accent_colo(u)r` parameter was not a Colour')
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
                raise ClientException('`date_of_birth` parameter was not a datetime')
            args['date_of_birth'] = date_of_birth.strftime('%F')

        http = self._state.http

        if house is not MISSING:
            if house is None:
                await http.leave_hypesquad_house()
            elif not isinstance(house, HypeSquadHouse):
                raise ClientException('`house` parameter was not a HypeSquadHouse')
            else:
                await http.change_hypesquad_house(house.value)

        data = await http.edit_profile(**args)
        try:
            http._token(data['token'])
        except KeyError:
            pass

        return ClientUser(state=self._state, data=data)

    async def fetch_settings(self) -> UserSettings:
        """|coro|

        Retrieves your settings.

        .. note::

            This method is an API call. For general usage, consider :attr:`settings` instead.

        Raises
        -------
        HTTPException
            Retrieving your settings failed.

        Returns
        --------
        :class:`UserSettings`
            The current settings for your account.
        """
        data = await self._state.http.get_settings()
        return UserSettings(data=data, state=self._state)

    async def edit_settings(self, **kwargs) -> UserSettings:  # TODO: I really wish I didn't have to do this...
        """|coro|

        Edits the client user's settings.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited settings are returned.

        Parameters
        ----------
        afk_timeout: :class:`int`
            How long (in seconds) the user needs to be AFK until Discord
            sends push notifications to your mobile device.
        allow_accessibility_detection: :class:`bool`
            Whether or not to allow Discord to track screen reader usage.
        animate_emojis: :class:`bool`
            Whether or not to animate emojis in the chat.
        animate_stickers: :class:`StickerAnimationOptions`
            Whether or not to animate stickers in the chat.
        contact_sync_enabled: :class:`bool`
            Whether or not to enable the contact sync on Discord mobile.
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
        native_phone_integration_enabled: :class:`bool`
            Whether or not to enable the new Discord mobile phone number friend
            requesting features.
        render_embeds: :class:`bool`
            Whether or not to render embeds that are sent in the chat.
        render_reactions: :class:`bool`
            Whether or not to render reactions that are added to messages.
        restricted_guilds: List[:class:`abc.Snowflake`]
            A list of guilds that you will not receive DMs from.
        show_current_game: :class:`bool`
            Whether or not to display the game that you are currently playing.
        stream_notifications_enabled: :class:`bool`
            Unknown.
        theme: :class:`Theme`
            The theme of the Discord UI.
        timezone_offset: :class:`int`
            The timezone offset to use.
        view_nsfw_guilds: :class:`bool`
            Whether or not to show NSFW guilds on iOS.

        Raises
        -------
        HTTPException
            Editing the settings failed.

        Returns
        -------
        :class:`.UserSettings`
            The client user's updated settings.
        """
        payload = {}

        content_filter = kwargs.pop('explicit_content_filter', None)
        if content_filter:
            payload['explicit_content_filter'] = content_filter.value

        animate_stickers = kwargs.pop('animate_stickers', None)
        if animate_stickers:
            payload['animate_stickers'] = animate_stickers.value

        friend_flags = kwargs.pop('friend_source_flags', None)
        if friend_flags:
            payload['friend_source_flags'] = friend_flags.to_dict()

        guild_positions = kwargs.pop('guild_positions', None)
        if guild_positions:
            guild_positions = [str(x.id) for x in guild_positions]
            payload['guild_positions'] = guild_positions

        restricted_guilds = kwargs.pop('restricted_guilds', None)
        if restricted_guilds:
            restricted_guilds = [str(x.id) for x in restricted_guilds]
            payload['restricted_guilds'] = restricted_guilds

        status = kwargs.pop('status', None)
        if status:
            payload['status'] = status.value

        theme = kwargs.pop('theme', None)
        if theme:
            payload['theme'] = theme.value

        payload.update(kwargs)

        state = self._state
        data = await state.http.edit_settings(**payload)
        return UserSettings(data=data, state=self._state)


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

    __slots__ = ('_stored',)

    def __init__(self, *, state: ConnectionState, data: UserPayload) -> None:
        super().__init__(state=state, data=data)
        self._stored: bool = False

    def __repr__(self) -> str:
        return f'<User id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot}>'

    def __del__(self) -> None:
        try:
            if self._stored:
                self._state.deref_user(self.id)
        except Exception:
            pass

    @classmethod
    def _copy(cls, user: User):
        self = super()._copy(user)
        self._stored = False
        return self

    def _get_voice_client_key(self) -> Union[int, str]:
        return self._state.user.id, 'self_id'

    def _get_voice_state_pair(self) -> Union[int, int]:
        return self._state.user.id, self.dm_channel.id

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
        return getattr(self.dm_channel, 'call', None)

    @property
    def relationship(self):
        """Optional[:class:`Relationship`]: Returns the :class:`Relationship` with this user if applicable, ``None`` otherwise."""
        return self._state.user.get_relationship(self.id)

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [guild for guild in self._state._guilds.values() if guild.get_member(self.id)]

    async def connect(self, *, ring=True, **kwargs):
        channel = await self._get_channel()
        call = self.call
        if call is not None:
            ring = False
        await super().connect(_channel=channel, **kwargs)
        if ring:
            await channel._initial_ring()

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
        await self._state.http.add_relationship(self.id, type=RelationshipType.blocked.value, action=RelationshipAction.block)

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

    async def remove_friend(self) -> bool:
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

    async def send_friend_request(self) -> None:  # TODO: maybe return relationship
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
        self, *, with_mutuals: bool = True, fetch_note: bool = True
    ) -> Profile:
        """|coro|

        Gets the user's profile.

        Parameters
        ------------
        with_mutuals: :class:`bool`
            Whether to fetch mutual guilds and friends.
            This fills in :attr:`mutual_guilds` & :attr:`mutual_friends`.
        fetch_note: :class:`bool`
            Whether to pre-fetch the user's note.

        Raises
        -------
        Forbidden
            Not allowed to fetch this profile.
        HTTPException
            Fetching the profile failed.

        Returns
        --------
        :class:`Profile`
            The profile of the user.
        """
        user_id = self.id
        state = self._state
        data = await state.http.get_user_profile(user_id, with_mutual_guilds=with_mutuals)

        if with_mutuals:
            data['mutual_friends'] = await self.http.get_mutual_friends(user_id)

        profile = Profile(state, data)

        if fetch_note:
            await profile.note.fetch()

        return profile
