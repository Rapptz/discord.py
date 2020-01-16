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

__all__ = (
    'SystemChannelFlags',
    'MessageFlags',
)

class flag_value:
    def __init__(self, func):
        self.flag = func(None)
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        return instance._has_flag(self.flag)

    def __set__(self, instance, value):
        instance._set_flag(self.flag, value)

def fill_with_flags(*, inverted=False):
    def decorator(cls):
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2 ** max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls
    return decorator

# n.b. flags must inherit from this and use the decorator above
class BaseFlags:
    __slots__ = ('value',)

    def __init__(self, **kwargs):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError('%r is not a valid flag name.' % key)
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<%s value=%s>' % (self.__class__.__name__, self.value)

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o):
        return (self.value & o) == o

    def _set_flag(self, o, toggle):
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError('Value to set for %s must be a bool.' % self.__class__.__name__)

@fill_with_flags()
class Intents(BaseFlags):
    r"""Wraps up the intents for the gateway.

    Each flag represents the events that you will receive when the 
    client connects to the gateway.

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

    def _set_guild_subscriptions(self):
        self.guild_members = True
        # self.guild_presences = True
        self.guild_message_typing = True

    @flag_value
    def guilds(self):
        """:class:`bool`: This enables:

        - :func:`on_guild_join`
        - :func:`on_guild_remove`
        - :func:`on_guild_role_create`
        - :func:`on_guild_role_create`
        - :func:`on_guild_role_delete`
        - :func:`on_guild_role_update`
        - :func:`on_guild_channel_create`
        - :func:`on_guild_channel_delete`
        - :func:`on_guild_channel_update`
        - :func:`on_guild_channel_pins_update`
        """
        return 1

    @flag_value
    def guild_members(self):
        """:class:`bool`: This enables:
        
        - :func:`on_member_join`
        - :func:`on_member_remove`
        - :func:`on_member_update`
        """
        return 2

    @flag_value
    def guild_bans(self):
        """:class:`bool`: This enables:
        
        - :func:`on_member_ban`
        - :func:`on_member_unban`
        """
        return 4

    @flag_value
    def guild_emojis(self):
        """:class:`bool`: This enables:
        
        - :func:`on_guild_emojis_update`
        """
        return 8

    @flag_value
    def guild_integrations(self):
        """:class:`bool`: This enables:

        - :func:`on_guild_integrations_update`
        """
        return 16

    @flag_value
    def guild_webhooks(self):
        """:class:`bool`: This enables:

        - :func:`on_webhooks_update`
        """
        return 32

    @flag_value
    def guild_invites(self):
        """:class:`bool`: This enables:
        
        - :func:`on_invite_create`
        - :func:`on_invite_delete`
        """
        return 64

    @flag_value
    def guild_voice_states(self):
        """:class:`bool`: This enables:
        
        - :func:`on_voice_state_update`
        """
        return 128

    @flag_value
    def guild_presences(self):
        """:class:`bool`: This enables:
        
        - :func:`on_member_update`
        """
        return 256

    @flag_value
    def guild_messages(self):
        """:class:`bool`: This enables:

        - :func:`on_message`
        - :func:`on_message_edit`
        - :func:`on_message_delete`

        for guilds.
        """
        return 512

    @flag_value
    def guild_message_reactions(self):
        """:class:`bool`: This enables:

        - :func:`on_reaction_add`
        - :func:`on_reaction_remove`
        - :func:`on_reaction_clear`

        for guilds.
        """
        return 1024

    @flag_value
    def guild_message_typing(self):
        """:class:`bool`: This enables:

        - :func:`on_typing`

        for guilds.
        """
        return 2048

    @flag_value
    def direct_messages(self):
        """:class:`bool`: This enables:

        - :func:`on_message`
        - :func:`on_message_edit`
        - :func:`on_message_delete`

        for DM channels.
        """
        return 4096

    @flag_value
    def direct_message_reactions(self):
        """:class:`bool`: This enables:

        - :func:`on_reaction_add`
        - :func:`on_reaction_remove`
        - :func:`on_reaction_clear`

        for DM channels.
        """
        return 8192

    @flag_value
    def direct_message_typing(self):
        """:class:`bool`: This enables:

        - :func:`on_typing`

        for DM channels.
        """
        return 16384

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
    # ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o):
        return (self.value & o) != o

    def _set_flag(self, o, toggle):
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool.')

    @flag_value
    def join_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @flag_value
    def premium_subscriptions(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for Nitro boosting notifications."""
        return 2


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
        """:class:`bool`: Returns ``True`` if the source message is an urgent message.

        An urgent message is one sent by Discord Trust and Safety.
        """
        return 16
