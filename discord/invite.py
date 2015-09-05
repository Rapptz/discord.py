# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

class Invite(object):
    """Represents a Discord :class:`Server` or :class:`Channel` invite.

    Instance attributes:

    .. attribute:: max_age

        How long the before the invite expires in seconds. A value of 0 indicates that it doesn't expire.
    .. attribute:: code

        The URL fragment used for the invite. :attr:`xkcd` is also a possible fragment.
    .. attribute:: server

        The :class:`Server` the invite is for.
    .. attribute:: revoked

        A boolean indicating if the invite has been revoked.
    .. attribute:: created_at

        A datetime object denoting the time the invite was created.
    .. attribute:: temporary

        A boolean indicating that the invite grants temporary membership. If True, members who joined via this invite will be kicked upon disconnect.
    .. attribute:: uses

        How many times the invite has been used.
    .. attribute:: max_uses

        How many times the invite can be used.
    .. attribute:: xkcd

        The URL fragment used for the invite if it is human readable.
    .. attribute:: inviter

        The :class:`User` who created the invite.
    .. attribute:: channel

        The :class:`Channel` the invite is for.
    """

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
        self.inviter = User(**kwargs.get('inviter', {}))
        self.channel = kwargs.get('channel')

    @property
    def id(self):
        """Returns the proper code portion of the invite."""
        return self.xkcd if self.xkcd else self.code

    @property
    def url(self):
        """A property that retrieves the invite URL."""
        return 'http://discord.gg/{}'.format(self.id)

