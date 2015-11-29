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
from .permissions import Permissions
from collections import namedtuple

Overwrites = namedtuple('Overwrites', 'id allow deny type')

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

        A list of :class:`Roles` that have been overridden from their default
        values in the :attr:`Server.roles` attribute.
    .. attribute:: voice_members

        A list of :class:`Members` that are currently inside this voice channel.
        If :attr:`type` is not ``'voice'`` then this is always an empty array.
    """

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.voice_members = []

    def update(self, **kwargs):
        self.name = kwargs.get('name')
        self.server = kwargs.get('server')
        self.id = kwargs.get('id')
        self.topic = kwargs.get('topic')
        self.is_private = False
        self.position = kwargs.get('position')
        self.type = kwargs.get('type')
        self.changed_roles = []
        self._permission_overwrites = []
        for overridden in kwargs.get('permission_overwrites', []):
            self._permission_overwrites.append(Overwrites(**overridden))

            if overridden.get('type') == 'member':
                continue

            # this is pretty inefficient due to the deep nested loops unfortunately
            role = utils.find(lambda r: r.id == overridden['id'], self.server.roles)
            if role is None:
                continue

            denied = overridden.get('deny', 0)
            allowed = overridden.get('allow', 0)
            override = deepcopy(role)
            override.permissions.handle_overwrite(allowed, denied)
            self.changed_roles.append(override)

    def is_default_channel(self):
        """Checks if this is the default channel for the :class:`Server` it belongs to."""
        return self.server.id == self.id

    def mention(self):
        """Returns a string that allows you to mention the channel."""
        return '<#{0.id}>'.format(self)

    def permissions_for(self, member):
        """Handles permission resolution for the current :class:`Member`.

        This function takes into consideration the following cases:

        - Server owner
        - Server roles
        - Channel overrides
        - Member overrides
        - Whether the channel is the default channel.

        :param member: The :class:`Member` to resolve permissions for.
        :return: The resolved :class:`Permissions` for the :class:`Member`.
        """

        # The current cases can be explained as:
        # Server owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to
        # True. If the channel is the default channel then everyone gets
        # read permissions regardless.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if member.id == self.server.owner.id:
            return Permissions.all()

        default = member.roles[0]
        base = deepcopy(default.permissions)

        # Apply server roles that the member has.
        for role in member.roles:
            base.value |= role.permissions.value

        # Server-wide Manage Roles -> True for everything
        if base.can_manage_roles:
            base = Permissions.all()

        member_role_ids = set(map(lambda r: r.id, member.roles))

        # Apply channel specific role permission overwrites
        for overwrite in self._permission_overwrites:
            if overwrite.type == 'role':
                if overwrite.id in member_role_ids:
                    base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)

        # Apply member specific permission overwrites
        for overwrite in self._permission_overwrites:
            if overwrite.type == 'member' and overwrite.id == member.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)

        if base.can_manage_roles:
            # This point is essentially Channel-specific Manage Roles.
            tmp = Permissions.all_channel()
            base.value |= tmp.value

        if self.is_default_channel():
            base.can_read_messages = True

        return base

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

    def permissions_for(user):
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with :class:`Channel`.

        Actual private messages do not really have the concept of permissions.

        This returns all the Text related permissions set to true except:

        - can_send_tts_messages: You cannot send TTS messages in a PM.
        - can_manage_messages: You cannot delete others messages in a PM.
        - can_mention_everyone: There is no one to mention in a PM.

        :param user: The :class:`User` to check permissions for.
        :return: A :class:`Permission` with the resolved permission value.
        """

        base = Permissions.TEXT
        base.can_send_tts_messages = False
        base.can_manage_messages = False
        base.can_mention_everyone = False
        return base


