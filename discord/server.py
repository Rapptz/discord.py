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

from . import utils

class Server(object):
    """Represents a Discord server.

    Instance attributes:

    .. attribute:: name

        The server name.
    .. attribute:: roles

        An array of :class:`Role` that the server has available.
    .. attribute:: region

        The region the server belongs on.
    .. attribute:: afk_timeout

        The timeout to get sent to the AFK channel.
    .. attribute:: afk_channel_id

        The channel ID for the AFK channel. None if it doesn't exist.
    .. attribute:: members

        An array of :class:`Member` that are currently on the server.
    .. attribute:: channels

        An array of :class:`Channel` that are currently on the server.
    .. attribute:: icon

        The server's icon.
    .. attribute:: id

        The server's ID.
    .. attribute:: owner

        The :class:`Member` who owns the server.
    .. attribute:: unavailable

        A boolean indicating if the server is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :meth:`Server.id` is slim and they might
        all be None. It is best to not do anything with the server if it is unavailable.

        Check the :func:`on_server_unavailable` and :func:`on_server_available` events.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.roles = kwargs.get('roles')
        self.region = kwargs.get('region')
        self.afk_timeout = kwargs.get('afk_timeout')
        self.afk_channel_id = kwargs.get('afk_channel_id')
        self.members = kwargs.get('members')
        self.icon = kwargs.get('icon')
        self.id = kwargs.get('id')
        self.owner = kwargs.get('owner')
        self.unavailable = kwargs.get('unavailable', False)

    def get_default_role(self):
        """Gets the @everyone role that all members have by default."""
        return utils.find(lambda r: r.is_everyone(), self.roles)
    
    def get_default_channel(self):
        """Gets the default :class:`Channel` for the server."""
        return utils.find(lambda c: c.is_default_channel(), self.channels)
    
    def icon_url(self):
        """Returns the URL version of the server's icon. Returns None if it has no icon."""
        if self.icon is None:
            return ''
        return 'https://cdn.discordapp.com/icons/{0.id}/{0.icon}.jpg'.format(self)
    
