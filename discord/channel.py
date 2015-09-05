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

class Channel(object):
    """Represents a Discord server channel.

    Instance attributes:

    .. attribute:: name

        The channel name.
    .. attribute:: server

        The :class:`Server` the channel belongs to.
    .. attribute:: id

        The channel ID.
    .. attribute:: is_private

        ``True`` if the channel is a private channel (i.e. PM). ``False`` in this case.
    .. attribute:: position

        The position in the channel list.
    .. attribute:: type

        The channel type. Usually ``'voice'`` or ``'text'``.
    .. attribute:: changed_roles

        An array of :class:`Roles` that have been overridden from their default
        values in the :attr:`Server.roles` attribute.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.server = kwargs.get('server')
        self.id = kwargs.get('id')
        self.is_private = False
        self.position = kwargs.get('position')
        self.type = kwargs.get('type')
        self.changed_roles = kwargs.get('permission_overwrites', [])

class PrivateChannel(object):
    """Represents a Discord private channel.

    Instance attributes:

    .. attribute:: user

        The :class:`User` in the private channel.
    .. attribute:: id

        The private channel ID.
    .. attribute:: is_private

        ``True`` if the channel is a private channel (i.e. PM). ``True`` in this case.
    """

    def __init__(self, user, id, **kwargs):
        self.user = user
        self.id = id
        self.is_private = True

