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

from copy import deepcopy
from . import utils

class Channel(object):
    """Represents a Discord server channel.

    Instance attributes:

    .. attribute:: name

        The channel name.
    .. attribute:: server

        The :class:`Server` the channel belongs to.
    .. attribute:: id

        The channel ID.
    .. attribute:: topic

        The channel's topic. None if it doesn't exist.
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
        self.update(**kwargs)

    def update(self, **kwargs):
        self.name = kwargs.get('name')
        self.server = kwargs.get('server')
        self.id = kwargs.get('id')
        self.topic = kwargs.get('topic')
        self.is_private = False
        self.position = kwargs.get('position')
        self.type = kwargs.get('type')
        self.changed_roles = []
        for overridden in kwargs.get('permission_overwrites', []):
            # this is pretty inefficient due to the deep nested loops unfortunately
            role = utils.find(lambda r: r.id == overridden['id'], self.server.roles)
            if role is None:
                continue

            denied = overridden.get('deny', 0)
            allowed = overridden.get('allow', 0)
            override = deepcopy(role)

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
            # The OP is (base ^ denied) & ~denied.
            # The OP2 is base | allowed.
            override.permissions.value = ((override.permissions.value ^ denied) & ~denied) | allowed
            self.changed_roles.append(override)

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

