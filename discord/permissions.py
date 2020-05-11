# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2020 Rapptz

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

from .flags import BaseFlags, flag_value, fill_with_flags

__all__ = (
    'Permissions',
    'PermissionOverwrite',
)

# A permission alias works like a regular flag but is marked
# So the PermissionOverwrite knows to work with it
class permission_alias(flag_value):
    pass

def make_permission_alias(alias):
    def decorator(func):
        ret = permission_alias(func)
        ret.alias = alias
        return ret
    return decorator

@fill_with_flags()
class Permissions(BaseFlags):
    """Wraps up the Discord permission value.

    The properties provided are two way. You can set and retrieve individual
    bits using the properties as if they were regular bools. This allows
    you to edit permissions.

    .. versionchanged:: 1.3
        You can now use keyword arguments to initialize :class:`Permissions`
        similar to :meth:`update`.

    .. container:: operations

        .. describe:: x == y

            Checks if two permissions are equal.
        .. describe:: x != y

            Checks if two permissions are not equal.
        .. describe:: x <= y

            Checks if a permission is a subset of another permission.
        .. describe:: x >= y

            Checks if a permission is a superset of another permission.
        .. describe:: x < y

             Checks if a permission is a strict subset of another permission.
        .. describe:: x > y

             Checks if a permission is a strict superset of another permission.
        .. describe:: hash(x)

               Return the permission's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(perm, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.
               Note that aliases are not shown.

    Attributes
    -----------
    value
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available permissions. You should query
        permissions via the properties rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, permissions=0, **kwargs):
        if not isinstance(permissions, int):
            raise TypeError('Expected int parameter, received %s instead.' % permissions.__class__.__name__)

        self.value = permissions
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid permission name.' % key)
            setattr(self, key, value)

    def is_subset(self, other):
        """Returns ``True`` if self has the same or fewer permissions as other."""
        if isinstance(other, Permissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError("cannot compare {} with {}".format(self.__class__.__name__, other.__class__.__name__))

    def is_superset(self, other):
        """Returns ``True`` if self has the same or more permissions as other."""
        if isinstance(other, Permissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError("cannot compare {} with {}".format(self.__class__.__name__, other.__class__.__name__))

    def is_strict_subset(self, other):
        """Returns ``True`` if the permissions on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    def is_strict_superset(self, other):
        """Returns ``True`` if the permissions on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, permission_alias):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to ``False``."""
        return cls(0)

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to True."""
        return cls(0b01111111111111111111111111111111)

    @classmethod
    def all_channel(cls):
        """A :class:`Permissions` with all channel-specific permissions set to
        ``True`` and the guild-specific ones set to ``False``. The guild-specific
        permissions are currently:

        - manage_guild
        - kick_members
        - ban_members
        - administrator
        - change_nickname
        - manage_nicknames
        """
        return cls(0b00110011111101111111110001010001)

    @classmethod
    def general(cls):
        """A factory method that creates a :class:`Permissions` with all
        "General" permissions from the official Discord UI set to ``True``."""
        return cls(0b01111100000010000000000010111111)

    @classmethod
    def text(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Text" permissions from the official Discord UI set to ``True``."""
        return cls(0b00000000000001111111110001000000)

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions from the official Discord UI set to ``True``."""
        return cls(0b00000011111100000000001100000000)


    def update(self, **kwargs):
        r"""Bulk updates this permission object.

        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.

        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update permissions with.
        """
        for key, value in kwargs.items():
            if key in self.VALID_FLAGS:
                setattr(self, key, value)

    def handle_overwrite(self, allow, deny):
        # Basically this is what's happening here.
        # We have an original bit array, e.g. 1010
        # Then we have another bit array that is 'denied', e.g. 1111
        # And then we have the last one which is 'allowed', e.g. 0101
        # We want original OP denied to end up resulting in
        # whatever is in denied to be set to 0.
        # So 1010 OP 1111 -> 0000
        # Then we take this value and look at the allowed values.
        # And whatever is allowed is set to 1.
        # So 0000 OP2 0101 -> 0101
        # The OP is base  & ~denied.
        # The OP2 is base | allowed.
        self.value = (self.value & ~deny) | allow

    @flag_value
    def create_instant_invite(self):
        """:class:`bool`: Returns ``True`` if the user can create instant invites."""
        return 1 << 0

    @flag_value
    def kick_members(self):
        """:class:`bool`: Returns ``True`` if the user can kick users from the guild."""
        return 1 << 1

    @flag_value
    def ban_members(self):
        """:class:`bool`: Returns ``True`` if a user can ban users from the guild."""
        return 1 << 2

    @flag_value
    def administrator(self):
        """:class:`bool`: Returns ``True`` if a user is an administrator. This role overrides all other permissions.

        This also bypasses all channel-specific overrides.
        """
        return 1 << 3

    @flag_value
    def manage_channels(self):
        """:class:`bool`: Returns ``True`` if a user can edit, delete, or create channels in the guild.

        This also corresponds to the "Manage Channel" channel-specific override."""
        return 1 << 4

    @flag_value
    def manage_guild(self):
        """:class:`bool`: Returns ``True`` if a user can edit guild properties."""
        return 1 << 5

    @flag_value
    def add_reactions(self):
        """:class:`bool`: Returns ``True`` if a user can add reactions to messages."""
        return 1 << 6

    @flag_value
    def view_audit_log(self):
        """:class:`bool`: Returns ``True`` if a user can view the guild's audit log."""
        return 1 << 7

    @flag_value
    def priority_speaker(self):
        """:class:`bool`: Returns ``True`` if a user can be more easily heard while talking."""
        return 1 << 8

    @flag_value
    def stream(self):
        """:class:`bool`: Returns ``True`` if a user can stream in a voice channel."""
        return 1 << 9

    @flag_value
    def read_messages(self):
        """:class:`bool`: Returns ``True`` if a user can read messages from all or specific text channels."""
        return 1 << 10

    @make_permission_alias('read_messages')
    def view_channel(self):
        """:class:`bool`: An alias for :attr:`read_messages`.

        .. versionadded:: 1.3
        """
        return 1 << 10

    @flag_value
    def send_messages(self):
        """:class:`bool`: Returns ``True`` if a user can send messages from all or specific text channels."""
        return 1 << 11

    @flag_value
    def send_tts_messages(self):
        """:class:`bool`: Returns ``True`` if a user can send TTS messages from all or specific text channels."""
        return 1 << 12

    @flag_value
    def manage_messages(self):
        """:class:`bool`: Returns ``True`` if a user can delete or pin messages in a text channel.

        .. note::

            Note that there are currently no ways to edit other people's messages.
        """
        return 1 << 13

    @flag_value
    def embed_links(self):
        """:class:`bool`: Returns ``True`` if a user's messages will automatically be embedded by Discord."""
        return 1 << 14

    @flag_value
    def attach_files(self):
        """:class:`bool`: Returns ``True`` if a user can send files in their messages."""
        return 1 << 15

    @flag_value
    def read_message_history(self):
        """:class:`bool`: Returns ``True`` if a user can read a text channel's previous messages."""
        return 1 << 16

    @flag_value
    def mention_everyone(self):
        """:class:`bool`: Returns ``True`` if a user's @everyone or @here will mention everyone in the text channel."""
        return 1 << 17

    @flag_value
    def external_emojis(self):
        """:class:`bool`: Returns ``True`` if a user can use emojis from other guilds."""
        return 1 << 18

    @make_permission_alias('external_emojis')
    def use_external_emojis(self):
        """:class:`bool`: An alias for :attr:`external_emojis`.

        .. versionadded:: 1.3
        """
        return 1 << 18

    @flag_value
    def view_guild_insights(self):
        """:class:`bool`: Returns ``True`` if a user can view the guild's insights.

        .. versionadded:: 1.3
        """
        return 1 << 19

    @flag_value
    def connect(self):
        """:class:`bool`: Returns ``True`` if a user can connect to a voice channel."""
        return 1 << 20

    @flag_value
    def speak(self):
        """:class:`bool`: Returns ``True`` if a user can speak in a voice channel."""
        return 1 << 21

    @flag_value
    def mute_members(self):
        """:class:`bool`: Returns ``True`` if a user can mute other users."""
        return 1 << 22

    @flag_value
    def deafen_members(self):
        """:class:`bool`: Returns ``True`` if a user can deafen other users."""
        return 1 << 23

    @flag_value
    def move_members(self):
        """:class:`bool`: Returns ``True`` if a user can move users between other voice channels."""
        return 1 << 24

    @flag_value
    def use_voice_activation(self):
        """:class:`bool`: Returns ``True`` if a user can use voice activation in voice channels."""
        return 1 << 25

    @flag_value
    def change_nickname(self):
        """:class:`bool`: Returns ``True`` if a user can change their nickname in the guild."""
        return 1 << 26

    @flag_value
    def manage_nicknames(self):
        """:class:`bool`: Returns ``True`` if a user can change other user's nickname in the guild."""
        return 1 << 27

    @flag_value
    def manage_roles(self):
        """:class:`bool`: Returns ``True`` if a user can create or edit roles less than their role's position.

        This also corresponds to the "Manage Permissions" channel-specific override.
        """
        return 1 << 28

    @make_permission_alias('manage_roles')
    def manage_permissions(self):
        """:class:`bool`: An alias for :attr:`manage_roles`.

        .. versionadded:: 1.3
        """
        return 1 << 28

    @flag_value
    def manage_webhooks(self):
        """:class:`bool`: Returns ``True`` if a user can create, edit, or delete webhooks."""
        return 1 << 29

    @flag_value
    def manage_emojis(self):
        """:class:`bool`: Returns ``True`` if a user can create, edit, or delete emojis."""
        return 1 << 30

    # 1 unused

    # after these 32 bits, there's 21 more unused ones technically

def augment_from_permissions(cls):
    cls.VALID_NAMES = set(Permissions.VALID_FLAGS)
    aliases = set()

    # make descriptors for all the valid names and aliases
    for name, value in Permissions.__dict__.items():
        if isinstance(value, permission_alias):
            key = value.alias
            aliases.add(name)
        elif isinstance(value, flag_value):
            key = name
        else:
            continue

        # god bless Python
        def getter(self, x=key):
            return self._values.get(x)
        def setter(self, value, x=key):
            self._set(x, value)

        prop = property(getter, setter)
        setattr(cls, name, prop)

    cls.PURE_FLAGS = cls.VALID_NAMES - aliases
    return cls

@augment_from_permissions
class PermissionOverwrite:
    r"""A type that is used to represent a channel specific permission.

    Unlike a regular :class:`Permissions`\, the default value of a
    permission is equivalent to ``None`` and not ``False``. Setting
    a value to ``False`` is **explicitly** denying that permission,
    while setting a value to ``True`` is **explicitly** allowing
    that permission.

    The values supported by this are the same as :class:`Permissions`
    with the added possibility of it being set to ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two overwrites are equal.
        .. describe:: x != y

            Checks if two overwrites are not equal.
        .. describe:: iter(x)

           Returns an iterator of ``(perm, value)`` pairs. This allows it
           to be, for example, constructed as a dict or a list of pairs.
           Note that aliases are not shown.

    Parameters
    -----------
    \*\*kwargs
        Set the value of permissions by their name.
    """

    __slots__ = ('_values',)

    def __init__(self, **kwargs):
        self._values = {}

        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                raise ValueError('no permission called {0}.'.format(key))

            setattr(self, key, value)

    def __eq__(self, other):
        return isinstance(other, PermissionOverwrite) and self._values == other._values

    def _set(self, key, value):
        if value not in (True, None, False):
            raise TypeError('Expected bool or NoneType, received {0.__class__.__name__}'.format(value))

        self._values[key] = value

    def pair(self):
        """Returns the (allow, deny) pair from this overwrite.

        The value of these pairs is :class:`Permissions`.
        """

        allow = Permissions.none()
        deny = Permissions.none()

        for key, value in self._values.items():
            if value is True:
                setattr(allow, key, True)
            elif value is False:
                setattr(deny, key, True)

        return allow, deny

    @classmethod
    def from_pair(cls, allow, deny):
        """Creates an overwrite from an allow/deny pair of :class:`Permissions`."""
        ret = cls()
        for key, value in allow:
            if value is True:
                setattr(ret, key, True)

        for key, value in deny:
            if value is True:
                setattr(ret, key, False)

        return ret

    def is_empty(self):
        """Checks if the permission overwrite is currently empty.

        An empty permission overwrite is one that has no overwrites set
        to ``True`` or ``False``.
        """
        return all(x is None for x in self._values.values())

    def update(self, **kwargs):
        r"""Bulk updates this permission overwrite object.

        Allows you to set multiple attributes by using keyword
        arguments. The names must be equivalent to the properties
        listed. Extraneous key/value pairs will be silently ignored.

        Parameters
        ------------
        \*\*kwargs
            A list of key/value pairs to bulk update with.
        """
        for key, value in kwargs.items():
            if key not in self.VALID_NAMES:
                continue

            setattr(self, key, value)

    def __iter__(self):
        for key in self.PURE_FLAGS:
            yield key, self._values.get(key)
