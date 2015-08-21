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

from user import User

class Server(object):
    """Represents a Discord server.

    Instance attributes:

    .. attribute:: name

        The server name.
    .. attribute:: roles

        An array of role names.
    .. attribute:: region

        The region the server belongs on.
    .. attribute:: afk_timeout

        The timeout to get sent to the AFK channel.
    .. attribute:: afk_channel_id

        The channel ID for the AFK channel. None if it doesn't exist.
    .. attribute:: members

        An array of :class:`User` that are currently on the server.
    .. attribute:: channels

        An array of :class:`Channel` that are currently on the server.
    .. attribute:: icon

        The server's icon.
    .. attribute:: id

        The server's ID.
    .. attribute:: owner_id

        The ID of the server's owner.
    """

    def __init__(self, name, roles, region, afk_timeout, afk_channel_id, members, icon, id, owner_id, **kwargs):
        self.name = name
        self.roles = roles
        self.region = region
        self.afk_timeout = afk_timeout
        self.afk_channel_id = afk_channel_id
        self.members = members
        self.icon = icon
        self.id = id
        self.owner_id = owner_id
