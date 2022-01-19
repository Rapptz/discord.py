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

from typing import Any, Callable, ClassVar, Dict, Iterator, List, Optional, Tuple, Type, TypeVar, overload

from .enums import UserFlags

__all__ = (
    'SystemChannelFlags',
    'MessageFlags',
    'PublicUserFlags',
    'MemberCacheFlags',
    'ApplicationFlags',
    'GuildSubscriptionOptions',
)

FV = TypeVar('FV', bound='flag_value')
BF = TypeVar('BF', bound='BaseFlags')


class flag_value:
    def __init__(self, func: Callable[[Any], int]):
        self.flag = func(None)
        self.__doc__ = func.__doc__

    @overload
    def __get__(self: FV, instance: None, owner: Type[BF]) -> FV:
        ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool:
        ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BF, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self):
        return f'<flag_value flag={self.flag!r}>'


class alias_flag_value(flag_value):
    pass


def fill_with_flags(*, inverted: bool = False):
    def decorator(cls: Type[BF]):
        # fmt: off
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }
        # fmt: on

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2 ** max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls

    return decorator


# Flags must inherit from this and use the decorator above
class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ('value',)

    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(f'Value to set for {self.__class__.__name__} must be a bool.')


@fill_with_flags(inverted=True)
class SystemChannelFlags(BaseFlags):
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

    __slots__ = ()

    # For some reason the flags for system channels are "inverted"
    # Ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) != o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool')

    @flag_value
    def join_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @flag_value
    def premium_subscriptions(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for "Nitro boosting" notifications."""
        return 2

    @flag_value
    def guild_reminder_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for server setup helpful tips notifications.

        .. versionadded:: 2.0
        """
        return 4

    @flag_value
    def join_notification_replies(self):
        """:class:`bool`: Returns ``True`` if members are prompted to reply to join notifications with a sticker.

        .. versionadded:: 2.0
        """
        return 8


@fill_with_flags()
class MessageFlags(BaseFlags):
    r"""Wraps up a Discord Message flag value.

    See :class:`SystemChannelFlags`.

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

    .. versionadded:: 1.3

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def crossposted(self):
        """:class:`bool`: Returns ``True`` if the message is the original crossposted message."""
        return 1

    @flag_value
    def is_crossposted(self):
        """:class:`bool`: Returns ``True`` if the message was crossposted from another channel."""
        return 2

    @flag_value
    def suppress_embeds(self):
        """:class:`bool`: Returns ``True`` if the message's embeds have been suppressed."""
        return 4

    @flag_value
    def source_message_deleted(self):
        """:class:`bool`: Returns ``True`` if the source message for this crosspost has been deleted."""
        return 8

    @flag_value
    def urgent(self):
        """:class:`bool`: Returns ``True`` if the message is an urgent message.

        An urgent message is one sent by Discord Trust and Safety.
        """
        return 16

    @flag_value
    def has_thread(self):
        """:class:`bool`: Returns ``True`` if the message is associated with a thread.

        .. versionadded:: 2.0
        """
        return 32

    @flag_value
    def ephemeral(self):
        """:class:`bool`: Returns ``True`` if the message is ephemeral.

        .. versionadded:: 2.0
        """
        return 64

    @flag_value
    def loading(self):
        """:class:`bool`: Returns ``True`` if the message is a deferred
        interaction response and has a "bot is thinking" response.

        .. versionadded:: 2.0
        """
        return 128

    @flag_value
    def failed_to_mention_some_roles_in_thread(self):
        """:class:`bool`: Returns ``True`` if Discord failed to add some
        mentioned members to the thread.

        There is an alias for this called :attr:`failed_to_mention_roles`.

        .. versionadded:: 2.0
        """
        return 256

    @alias_flag_value
    def failed_to_mention_roles(self):
        """:class:`bool`: Returns ``True`` if the source message failed to
        mention some roles and add their members to the thread.

        This is an alias of :attr:`failed_to_mention_some_roles_in_thread`.

        .. versionadded:: 2.0
        """
        return 256


@fill_with_flags()
class PublicUserFlags(BaseFlags):
    r"""Wraps up the Discord User Public flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two PublicUserFlags are equal.
        .. describe:: x != y

            Checks if two PublicUserFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 1.4

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def staff(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Employee."""
        return UserFlags.staff.value

    @flag_value
    def partner(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Partner."""
        return UserFlags.partner.value

    @flag_value
    def hypesquad(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Events member."""
        return UserFlags.hypesquad.value

    @flag_value
    def bug_hunter(self):
        """:class:`bool`: Returns ``True`` if the user is a level 1 Bug Hunter

        There is an alias for this called :attr:`bug_hunter_level_1`.
        """
        return UserFlags.bug_hunter.value

    @alias_flag_value
    def bug_hunter_level_1(self):
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter

        This is an alias of :attr:`bug_hunter`.
        """
        return UserFlags.bug_hunter_level_1.value

    @flag_value
    def hypesquad_bravery(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Bravery member."""
        return UserFlags.hypesquad_bravery.value

    @flag_value
    def hypesquad_brilliance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Brilliance member."""
        return UserFlags.hypesquad_brilliance.value

    @flag_value
    def hypesquad_balance(self):
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Balance member."""
        return UserFlags.hypesquad_balance.value

    @flag_value
    def early_supporter(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Supporter."""
        return UserFlags.early_supporter.value

    @flag_value
    def team_user(self):
        """:class:`bool`: Returns ``True`` if the user is a Team User."""
        return UserFlags.team_user.value

    @flag_value
    def system(self):
        """:class:`bool`: Returns ``True`` if the user is a system user (i.e. represents Discord officially)."""
        return UserFlags.system.value

    @flag_value
    def bug_hunter_level_2(self):
        """:class:`bool`: Returns ``True`` if the user is a level 2 Bug Hunter"""
        return UserFlags.bug_hunter_level_2.value

    @flag_value
    def verified_bot(self):
        """:class:`bool`: Returns ``True`` if the user is a Verified Bot."""
        return UserFlags.verified_bot.value

    @flag_value
    def verified_bot_developer(self):
        """:class:`bool`: Returns ``True`` if the user is an Early Verified Bot Developer."""
        return UserFlags.verified_bot_developer.value

    @alias_flag_value
    def early_verified_bot_developer(self):
        """:class:`bool`: An alias for :attr:`verified_bot_developer`.

        .. versionadded:: 1.5
        """
        return UserFlags.verified_bot_developer.value

    @flag_value
    def discord_certified_moderator(self):
        """:class:`bool`: Returns ``True`` if the user is a Discord Certified Moderator.

        .. versionadded:: 2.0
        """
        return UserFlags.discord_certified_moderator.value

    @flag_value
    def bot_http_interactions(self):
        """:class:`bool`: Returns ``True`` if the bot doesn't connect to the gateway but should still be shown as online.

        .. versionadded:: 2.0
        """
        return UserFlags.bot_http_interactions.value

    @flag_value
    def spammer(self):
        """:class:`bool`: Returns ``True`` if the user is marked as a spammer.

        .. versionadded:: 2.0
        """
        return UserFlags.spammer.value

    def all(self) -> List[UserFlags]:
        """List[:class:`UserFlags`]: Returns all flags the user has."""
        return [public_flag for public_flag in UserFlags if self._has_flag(public_flag.value)]


@fill_with_flags()
class PrivateUserFlags(PublicUserFlags):
    r"""Wraps up the Discord User flags.

        .. note::
            These are only available on your own user flags.

        .. container:: operations

            .. describe:: x == y

                Checks if two UserFlags are equal.
            .. describe:: x != y

                Checks if two UserFlags are not equal.
            .. describe:: hash(x)

                Return the flag's hash.
            .. describe:: iter(x)

                Returns an iterator of ``(name, value)`` pairs. This allows it
                to be, for example, constructed as a dict or a list of pairs.
                Note that aliases are not shown.

        .. versionadded:: 2.0

        Attributes
        -----------
        value: :class:`int`
            The raw value. This value is a bit array field of a 53-bit integer
            representing the currently available flags. You should query
            flags via the properties rather than using this raw value.
        """

    __slots__ = ()

    @flag_value
    def premium_promo_dismissed(self):
        """:class:`bool`: Returns ``True`` if the user has dismissed the premium promo."""
        return UserFlags.premium_promo_dismissed.value

    @flag_value
    def has_unread_urgent_messages(self):
        """:class:`bool`: Returns ``True`` if the user has unread urgent system messages."""
        return UserFlags.has_unread_urgent_messages.value

    @flag_value
    def mfa_sms(self):
        """:class:`bool`: Returns ``True`` if the user has SMS recovery for MFA enabled."""
        return UserFlags.mfa_sms.value

    @flag_value
    def underage_deleted(self):
        """:class:`bool`: Returns ``True`` if the user has been flagged for deletion for being underage."""
        return UserFlags.underage_deleted.value

    @flag_value
    def partner_or_verification_application(self):
        """:class:`bool`: Returns ``True`` if the user has a partner or a verification application?"""
        return UserFlags.partner_or_verification_application.value


@fill_with_flags()
class MemberCacheFlags(BaseFlags):
    """Controls the library's cache policy when it comes to members.

    This allows for finer grained control over what members are cached.
    Note that the bot's own member is always cached. This class is passed
    to the ``member_cache_flags`` parameter in :class:`Client`.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    The default value is all flags enabled.

    .. versionadded:: 1.5

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
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs: bool):
        bits = max(self.VALID_FLAGS.values()).bit_length()
        self.value = (1 << bits) - 1
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)

    @classmethod
    def all(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @property
    def _empty(self):
        return self.value == self.DEFAULT_VALUE

    @flag_value
    def voice(self):
        """:class:`bool`: Whether to cache members that are in voice.

        Members that leave voice are no longer cached.
        """
        return 1

    @flag_value
    def joined(self):
        """:class:`bool`: Whether to cache members that joined the guild
        or are chunked as part of the initial log in flow.

        Members that leave the guild are no longer cached.
        """
        return 2

    @property
    def _voice_only(self):
        return self.value == 1


@fill_with_flags()
class ApplicationFlags(BaseFlags):
    r"""Wraps up the Discord Application flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two ApplicationFlags are equal.
        .. describe:: x != y

            Checks if two ApplicationFlags are not equal.
        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

    .. versionadded:: 2.0

    Attributes
    -----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def gateway_presence(self):
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive presence information over the gateway.
        """
        return 1 << 12

    @alias_flag_value
    def presence(self):
        """:class:`bool`: Alias for :attr:`gateway_presence`.

        .. versionadded:: 2.0
        """
        return 1 << 12

    @flag_value
    def gateway_presence_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive
        presence information over the gateway but is not whitelisted.
        """
        return 1 << 13

    @alias_flag_value
    def presence_limited(self):
        """:class:`bool`: Alias for :attr:`gateway_presence_limited`.

        .. versionadded:: 2.0
        """
        return 1 << 13

    @flag_value
    def gateway_guild_members(self):
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive full guild member lists.
        """
        return 1 << 14

    @alias_flag_value
    def guild_members(self):
        """:class:`bool`: Alias for :attr:`gateway_guild_members`.

        .. versionadded:: 2.0
        """
        return 1 << 14

    @flag_value
    def gateway_guild_members_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive full
        guild member lists but is not whitelisted.
        """
        return 1 << 15

    @alias_flag_value
    def guild_members_limited(self):
        """:class:`bool`: Alias for :attr:`gateway_guild_members_limited`.

        .. versionadded:: 2.0
        """
        return 1 << 15

    @flag_value
    def gateway_message_content(self):
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive message content.

        .. versionadded:: 2.0
        """
        return 1 << 18

    @alias_flag_value
    def message_content(self):
        """:class:`bool`: Alias for :attr:`gateway_message_content`.

        .. versionadded:: 2.0
        """
        return 1 << 18

    @flag_value
    def gateway_message_content_limited(self):
        """:class:`bool`: Returns ``True`` if the application is allowed to receive
        message content but is not whitelisted.

        .. versionadded:: 2.0
        """
        return 1 << 19

    @alias_flag_value
    def message_content_limited(self):
        """:class:`bool`: Alias for :attr:`gateway_message_content_limited`.

        .. versionadded:: 2.0
        """
        return 1 << 19

    @flag_value
    def verification_pending_guild_limit(self):
        """:class:`bool`: Returns ``True`` if the application is currently pending verification
        and has hit the guild limit.
        """
        return 1 << 16

    @flag_value
    def embedded(self):
        """:class:`bool`: Returns ``True`` if the application is embedded within the Discord client."""
        return 1 << 17

    @flag_value
    def embedded_first_party(self):
        """:class:`bool`: Returns ``True`` if the embedded application is published by Discord.

        .. versionadded:: 2.0
        """
        return 1 << 20

    @flag_value
    def embedded_released(self):
        """:class:`bool`: Returns ``True`` if the embedded application is released to the public.

        .. versionadded:: 2.0
        """
        return 1 << 1


class GuildSubscriptionOptions:
    r"""Controls the library's auto-subscribing feature.

    Subscribing refers to abusing the member sidebar to scrape all* guild
    members. However, you can only request 200 members per OPCode 14.

    Once you send a proper OPCode 14, Discord responds with a
    GUILD_MEMBER_LIST_UPDATE. You then also get subsequent GUILD_MEMBER_LIST_UPDATEs
    that act (kind of) like GUILD_MEMBER_UPDATE/ADD/REMOVEs.

    \*Discord doesn't provide offline members for "large" guilds.
    \*As this is dependent on the member sidebar, guilds that don't have
    a channel (of any type, surprisingly) that @everyone or some other
    role everyone has can't access don't get the full online member list.

    To construct an object you can pass keyword arguments denoting the options
    and their values. If you don't pass a value, the default is used.
    """

    def __init__(
        self, *, auto_subscribe: bool = True, concurrent_guilds: int = 2, max_online: int = 6000
    ) -> None:
        if concurrent_guilds < 1:
            raise TypeError('concurrent_guilds must be positive')
        if max_online < 1:
            raise TypeError('max_online must be positive')

        self.auto_subscribe = auto_subscribe
        self.concurrent_guilds = concurrent_guilds
        self.max_online = max_online

    def __repr__(self) -> str:
        return f'<GuildSubscriptionOptions auto_subscribe={self.auto_subscribe} concurrent_guilds={self.concurrent_guilds} max_online={self.max_online}'

    @classmethod
    def all(cls) -> GuildSubscriptionOptions:
        """A factory method that creates a :class:`GuildSubscriptionOptions` that subscribes every guild. Not recommended in the slightest."""
        return cls(max_online=10000000)

    @classmethod
    def default(cls) -> GuildSubscriptionOptions:
        """A factory method that creates a :class:`GuildSubscriptionOptions` with default values."""
        return cls()

    @classmethod
    def disabled(cls) -> GuildSubscriptionOptions:
        """A factory method that creates a :class:`GuildSubscriptionOptions` with subscribing disabled.

        There is an alias for this called :meth`none`.
        """
        return cls(auto_subscribe=False)

    @classmethod
    def off(cls) -> GuildSubscriptionOptions:
        """A factory method that creates a :class:`GuildSubscriptionOptions` with subscribing disabled.

        This is an alias of :meth:`disabled`.
        """
        return cls(auto_subscribe=False)
