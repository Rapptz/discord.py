# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

class Permissions:
    """Wraps up the Discord permission value.

    The properties provided are two way. You can set and retrieve individual
    bits using the properties as if they were regular bools. This allows
    you to edit permissions.

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

    Attributes
    -----------
    value
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available permissions. You should query
        permissions via the properties rather than using this raw value.
    """

    __slots__ = ('value',)
    def __init__(self, permissions=0):
        if not isinstance(permissions, int):
            raise TypeError('Expected int parameter, received %s instead.' % permissions.__class__.__name__)

        self.value = permissions

    def __eq__(self, other):
        return isinstance(other, Permissions) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<Permissions value=%s>' % self.value

    def _perm_iterator(self):
        for attr in dir(self):
            # check if it's a property, because if so it's a permission
            is_property = isinstance(getattr(self.__class__, attr), property)
            if is_property:
                yield (attr, getattr(self, attr))

    def __iter__(self):
        return self._perm_iterator()

    def is_subset(self, other):
        """Returns True if self has the same or fewer permissions as other."""
        if isinstance(other, Permissions):
            return (self.value & other.value) == self.value
        else:
            raise TypeError("cannot compare {} with {}".format(self.__class__.__name__, other.__class__.__name__))

    def is_superset(self, other):
        """Returns True if self has the same or more permissions as other."""
        if isinstance(other, Permissions):
            return (self.value | other.value) == self.value
        else:
            raise TypeError("cannot compare {} with {}".format(self.__class__.__name__, other.__class__.__name__))

    def is_strict_subset(self, other):
        """Returns True if the permissions on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    def is_strict_superset(self, other):
        """Returns True if the permissions on other are a strict superset of those on self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to False."""
        return cls(0)

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`Permissions` with all
        permissions set to True."""
        return cls(0b01111111111101111111111111111111)

    @classmethod
    def all_channel(cls):
        """A :class:`Permissions` with all channel-specific permissions set to
        True and the guild-specific ones set to False. The guild-specific
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
        "General" permissions from the official Discord UI set to True."""
        return cls(0b01111100000000000000000010111111)

    @classmethod
    def text(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Text" permissions from the official Discord UI set to True."""
        return cls(0b00000000000001111111110001000000)

    @classmethod
    def voice(cls):
        """A factory method that creates a :class:`Permissions` with all
        "Voice" permissions from the official Discord UI set to True."""
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
            try:
                is_property = isinstance(getattr(self.__class__, key), property)
            except AttributeError:
                continue

            if is_property:
                setattr(self, key, value)

    def _bit(self, index):
        return bool((self.value >> index) & 1)

    def _set(self, index, value):
        if value is True:
            self.value |= (1 << index)
        elif value is False:
            self.value &= ~(1 << index)
        else:
            raise TypeError('Value to set for Permissions must be a bool.')

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

    @property
    def create_instant_invite(self):
        """Returns True if the user can create instant invites."""
        return self._bit(0)

    @create_instant_invite.setter
    def create_instant_invite(self, value):
        self._set(0, value)

    @property
    def kick_members(self):
        """Returns True if the user can kick users from the guild."""
        return self._bit(1)

    @kick_members.setter
    def kick_members(self, value):
        self._set(1, value)

    @property
    def ban_members(self):
        """Returns True if a user can ban users from the guild."""
        return self._bit(2)

    @ban_members.setter
    def ban_members(self, value):
        self._set(2, value)

    @property
    def administrator(self):
        """Returns True if a user is an administrator. This role overrides all other permissions.

        This also bypasses all channel-specific overrides.
        """
        return self._bit(3)

    @administrator.setter
    def administrator(self, value):
        self._set(3, value)

    @property
    def manage_channels(self):
        """Returns True if a user can edit, delete, or create channels in the guild.

        This also corresponds to the "Manage Channel" channel-specific override."""
        return self._bit(4)

    @manage_channels.setter
    def manage_channels(self, value):
        self._set(4, value)

    @property
    def manage_guild(self):
        """Returns True if a user can edit guild properties."""
        return self._bit(5)

    @manage_guild.setter
    def manage_guild(self, value):
        self._set(5, value)

    @property
    def add_reactions(self):
        """Returns True if a user can add reactions to messages."""
        return self._bit(6)

    @add_reactions.setter
    def add_reactions(self, value):
        self._set(6, value)

    @property
    def view_audit_log(self):
        """Returns True if a user can view the guild's audit log."""
        return self._bit(7)

    @view_audit_log.setter
    def view_audit_log(self, value):
        self._set(7, value)

    @property
    def priority_speaker(self):
        """Returns True if a user can be more easily heard while talking."""
        return self._bit(8)

    @priority_speaker.setter
    def priority_speaker(self, value):
        self._set(8, value)

    @property
    def stream(self):
        """Returns ``True`` if a user can stream in a voice channel."""
        return self._bit(9)

    @stream.setter
    def stream(self, value):
        self._set(9, value)

    @property
    def read_messages(self):
        """Returns True if a user can read messages from all or specific text channels."""
        return self._bit(10)

    @read_messages.setter
    def read_messages(self, value):
        self._set(10, value)

    @property
    def send_messages(self):
        """Returns True if a user can send messages from all or specific text channels."""
        return self._bit(11)

    @send_messages.setter
    def send_messages(self, value):
        self._set(11, value)

    @property
    def send_tts_messages(self):
        """Returns True if a user can send TTS messages from all or specific text channels."""
        return self._bit(12)

    @send_tts_messages.setter
    def send_tts_messages(self, value):
        self._set(12, value)

    @property
    def manage_messages(self):
        """Returns True if a user can delete or pin messages in a text channel. Note that there are currently no ways to edit other people's messages."""
        return self._bit(13)

    @manage_messages.setter
    def manage_messages(self, value):
        self._set(13, value)

    @property
    def embed_links(self):
        """Returns True if a user's messages will automatically be embedded by Discord."""
        return self._bit(14)

    @embed_links.setter
    def embed_links(self, value):
        self._set(14, value)

    @property
    def attach_files(self):
        """Returns True if a user can send files in their messages."""
        return self._bit(15)

    @attach_files.setter
    def attach_files(self, value):
        self._set(15, value)

    @property
    def read_message_history(self):
        """Returns True if a user can read a text channel's previous messages."""
        return self._bit(16)

    @read_message_history.setter
    def read_message_history(self, value):
        self._set(16, value)

    @property
    def mention_everyone(self):
        """Returns True if a user's @everyone or @here will mention everyone in the text channel."""
        return self._bit(17)

    @mention_everyone.setter
    def mention_everyone(self, value):
        self._set(17, value)

    @property
    def external_emojis(self):
        """Returns True if a user can use emojis from other guilds."""
        return self._bit(18)

    @external_emojis.setter
    def external_emojis(self, value):
        self._set(18, value)

    # 1 unused

    @property
    def connect(self):
        """Returns True if a user can connect to a voice channel."""
        return self._bit(20)

    @connect.setter
    def connect(self, value):
        self._set(20, value)

    @property
    def speak(self):
        """Returns True if a user can speak in a voice channel."""
        return self._bit(21)

    @speak.setter
    def speak(self, value):
        self._set(21, value)

    @property
    def mute_members(self):
        """Returns True if a user can mute other users."""
        return self._bit(22)

    @mute_members.setter
    def mute_members(self, value):
        self._set(22, value)

    @property
    def deafen_members(self):
        """Returns True if a user can deafen other users."""
        return self._bit(23)

    @deafen_members.setter
    def deafen_members(self, value):
        self._set(23, value)

    @property
    def move_members(self):
        """Returns True if a user can move users between other voice channels."""
        return self._bit(24)

    @move_members.setter
    def move_members(self, value):
        self._set(24, value)

    @property
    def use_voice_activation(self):
        """Returns True if a user can use voice activation in voice channels."""
        return self._bit(25)

    @use_voice_activation.setter
    def use_voice_activation(self, value):
        self._set(25, value)

    @property
    def change_nickname(self):
        """Returns True if a user can change their nickname in the guild."""
        return self._bit(26)

    @change_nickname.setter
    def change_nickname(self, value):
        self._set(26, value)

    @property
    def manage_nicknames(self):
        """Returns True if a user can change other user's nickname in the guild."""
        return self._bit(27)

    @manage_nicknames.setter
    def manage_nicknames(self, value):
        self._set(27, value)

    @property
    def manage_roles(self):
        """Returns True if a user can create or edit roles less than their role's position.

        This also corresponds to the "Manage Permissions" channel-specific override.
        """
        return self._bit(28)

    @manage_roles.setter
    def manage_roles(self, value):
        self._set(28, value)

    @property
    def manage_webhooks(self):
        """Returns True if a user can create, edit, or delete webhooks."""
        return self._bit(29)

    @manage_webhooks.setter
    def manage_webhooks(self, value):
        self._set(29, value)

    @property
    def manage_emojis(self):
        """Returns True if a user can create, edit, or delete emojis."""
        return self._bit(30)

    @manage_emojis.setter
    def manage_emojis(self, value):
        self._set(30, value)

    # 1 unused

    # after these 32 bits, there's 21 more unused ones technically

def augment_from_permissions(cls):
    cls.VALID_NAMES = {name for name in dir(Permissions) if isinstance(getattr(Permissions, name), property)}

    # make descriptors for all the valid names
    for name in cls.VALID_NAMES:
        # god bless Python
        def getter(self, x=name):
            return self._values.get(x)
        def setter(self, value, x=name):
            self._set(x, value)

        prop = property(getter, setter)
        setattr(cls, name, prop)

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

    Supported operations:

    +-----------+------------------------------------------+
    | Operation |               Description                |
    +===========+==========================================+
    | x == y    | Checks if two overwrites are equal.      |
    +-----------+------------------------------------------+
    | x != y    | Checks if two overwrites are not equal.  |
    +-----------+------------------------------------------+
    | iter(x)   | Returns an iterator of (perm, value)     |
    |           | pairs. This allows this class to be used |
    |           | as an iterable in e.g. set/list/dict     |
    |           | constructions.                           |
    +-----------+------------------------------------------+

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
        return self._values == other._values

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
        to True or False.
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
        for key in self.VALID_NAMES:
            yield key, self._values.get(key)
