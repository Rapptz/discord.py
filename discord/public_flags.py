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

from .enums import UserFlags


class PublicUserFlags:
    """Wraps up the Discord public flags.

    .. container:: operations
        .. describe:: x == y

            Checks if two PublicUserFlags are equal.
        .. describe:: x != y

            Checks if two PublicUserFlags are not equal.

    .. versionadded :: 1.4

    Attributes
    -----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """
    __slots__ = ('value',)

    def __repr__(self):
        return '<PublicUserFlags all={0}>'.format(self.all)

    def __eq__(self, other):
        return isinstance(other, PublicUserFlags) and self.all == other.all

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def _from_value(cls, value):
        self = cls.__new__(cls)
        self.value = value
        return self

    def has_flag(self, flag: UserFlags):
        v = flag.value
        return (self.value & v) == v

    @property
    def staff(self):
        """Indicates whether the user is a Discord Employee."""
        return self.has_flag(UserFlags.staff)

    @property
    def partner(self):
        """Indicates whether the user is a Discord Partner."""
        return self.has_flag(UserFlags.partner)

    @property
    def hypesquad(self):
        """Indicates whether the user is a HypeSquad Events member."""
        return self.has_flag(UserFlags.hypesquad)

    @property
    def bug_hunter(self):
        """Indicates whether the user is a Bug Hunter"""
        return self.has_flag(UserFlags.bug_hunter)

    @property
    def hypesquad_bravery(self):
        """Indicates whether the user is a HypeSquad Bravery member."""
        return self.has_flag(UserFlags.hypesquad_bravery)

    @property
    def hypesquad_brilliance(self):
        """Indicates whether the user is a HypeSquad Brilliance member."""
        return self.has_flag(UserFlags.hypesquad_brilliance)

    @property
    def hypesquad_balance(self):
        """Indicates whether the user is a HypeSquad Balance member."""
        return self.has_flag(UserFlags.hypesquad_balance)

    @property
    def early_supporter(self):
        """Indicates whether the user is an Early Supporter."""
        return self.has_flag(UserFlags.early_supporter)

    @property
    def team_user(self):
        """Indicates whether the user is a Team User."""
        return self.has_flag(UserFlags.team_user)

    @property
    def system(self):
        """Indicates whether the user is a system user (i.e. represents Discord officially)."""
        return self.has_flag(UserFlags.system)

    @property
    def bug_hunter_level_2(self):
        """Indicates whether the user is a Bug Hunter Level 2"""
        return self.has_flag(UserFlags.bug_hunter_level_2)

    @property
    def verified_bot(self):
        """Indicates whether the user is a Verified Bot."""
        return self.has_flag(UserFlags.verified_bot)

    @property
    def verified_bot_developer(self):
        """Indicates whether the user is a Verified Bot Developer."""
        return self.has_flag(UserFlags.verified_bot_developer)

    @property
    def all(self):
        """List[:class:`UserFlags`]: Returns all public flags the user has."""
        return [public_flag for public_flag in UserFlags if self.has_flag(public_flag)]
