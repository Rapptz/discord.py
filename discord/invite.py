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

from .user import User
from .utils import parse_time
from .mixins import Hashable

class Invite(Hashable):
    """Represents a Discord :class:`Server` or :class:`Channel` invite.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    Supported Operations:

    +-----------+--------------------------------------+
    | Operation |             Description              |
    +===========+======================================+
    | x == y    | Checks if two invites are equal.     |
    +-----------+--------------------------------------+
    | x != y    | Checks if two invites are not equal. |
    +-----------+--------------------------------------+
    | hash(x)   | Return the invite's hash.            |
    +-----------+--------------------------------------+
    | str(x)    | Returns the invite's URL.            |
    +-----------+--------------------------------------+

    Attributes
    -----------
    max_age : int
        How long the before the invite expires in seconds. A value of 0 indicates that it doesn't expire.
    code : str
        The URL fragment used for the invite. :attr:`xkcd` is also a possible fragment.
    server : :class:`Server`
        The server the invite is for.
    revoked : bool
        Indicates if the invite has been revoked.
    created_at : `datetime.datetime`
        A datetime object denoting the time the invite was created.
    temporary : bool
        Indicates that the invite grants temporary membership.
        If True, members who joined via this invite will be kicked upon disconnect.
    uses : int
        How many times the invite has been used.
    max_uses : int
        How many times the invite can be used.
    xkcd : str
        The URL fragment used for the invite if it is human readable.
    inviter : :class:`User`
        The user who created the invite.
    channel : :class:`Channel`
        The channel the invite is for.
    """


    __slots__ = [ 'max_age', 'code', 'server', 'revoked', 'created_at', 'uses',
                  'temporary', 'max_uses', 'xkcd', 'inviter', 'channel' ]

    def __init__(self, **kwargs):
        self.max_age = kwargs.get('max_age')
        self.code = kwargs.get('code')
        self.server = kwargs.get('server')
        self.revoked = kwargs.get('revoked')
        self.created_at = parse_time(kwargs.get('created_at'))
        self.temporary = kwargs.get('temporary')
        self.uses = kwargs.get('uses')
        self.max_uses = kwargs.get('max_uses')
        self.xkcd = kwargs.get('xkcdpass')

        inviter_data = kwargs.get('inviter')
        self.inviter = None if inviter_data is None else User(**inviter_data)
        self.channel = kwargs.get('channel')

    def __str__(self):
        return self.url

    @property
    def id(self):
        """Returns the proper code portion of the invite."""
        return self.xkcd if self.xkcd else self.code

    @property
    def url(self):
        """A property that retrieves the invite URL."""
        return 'http://discord.gg/{}'.format(self.id)

