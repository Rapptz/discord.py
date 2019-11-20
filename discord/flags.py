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

class _flag_descriptor:
    def __init__(self, func):
        self.flag = func(None)
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        return instance._has_flag(self.flag)

    def __set__(self, instance, value):
        instance._set_flag(self.flag, value)

def fill_with_flags(cls):
    cls.VALID_FLAGS = {
        name: value.flag
        for name, value in cls.__dict__.items()
        if isinstance(value, _flag_descriptor)
    }

    max_bits = max(cls.VALID_FLAGS.values()).bit_length()
    cls.ALL_OFF_VALUE = -1 + (2 ** max_bits)
    return cls

@fill_with_flags
class SystemChannelFlags:
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
    __slots__ = ('value',)

    def __init__(self, **kwargs):
        self.value = self.ALL_OFF_VALUE
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
        return isinstance(other, SystemChannelFlags) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<SystemChannelFlags value=%s>' % self.value

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, _flag_descriptor):
                yield (name, self._has_flag(value.flag))

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

    @_flag_descriptor
    def join_notifications(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @_flag_descriptor
    def premium_subscriptions(self):
        """:class:`bool`: Returns ``True`` if the system channel is used for Nitro boosting notifications."""
        return 2


@fill_with_flags
class MessageFlags:
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
    __slots__ = ('value',)

    def __init__(self, **kwargs):
        self.value = 0
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
        return isinstance(other, MessageFlags) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return '<MessageFlags value=%s>' % self.value

    def __iter__(self):
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, _flag_descriptor):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o):
        return (self.value & o) == o

    def _set_flag(self, o, toggle):
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= o
        else:
            raise TypeError('Value to set for MessageFlags must be a bool.')

    @_flag_descriptor
    def crossposted(self):
        """:class:`bool`: Returns ``True`` if the message is the original crossposted message."""
        return 1

    @_flag_descriptor
    def is_crossposted(self):
        """:class:`bool`: Returns ``True`` if the message was crossposted from another channel."""
        return 2

    @_flag_descriptor
    def suppress_embeds(self):
        """:class:`bool`: Returns ``True`` if the message's embeds have been suppressed."""
        return 4
    
    @_flag_descriptor
    def source_message_deleted(self):
        """:class:`bool`: Returns ``True`` if the source message for this crosspost has been deleted."""
        return 8
