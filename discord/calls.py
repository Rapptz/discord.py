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

import datetime

from . import utils
from .enums import VoiceRegion, try_enum
from .member import VoiceState

class CallMessage:
    """Represents a group call message from Discord.

    This is only received in cases where the message type is equivalent to
    :attr:`MessageType.call`.

    Attributes
    -----------
    ended_timestamp: Optional[:class:`datetime.datetime`]
        A naive UTC datetime object that represents the time that the call has ended.
    participants: List[:class:`User`]
        The list of users that are participating in this call.
    message: :class:`Message`
        The message associated with this call message.
    """

    def __init__(self, message, **kwargs):
        self.message = message
        self.ended_timestamp = utils.parse_time(kwargs.get('ended_timestamp'))
        self.participants = kwargs.get('participants')

    @property
    def call_ended(self):
        """:class:`bool`: Indicates if the call has ended."""
        return self.ended_timestamp is not None

    @property
    def channel(self):
        r""":class:`GroupChannel`\: The private channel associated with this message."""
        return self.message.channel

    @property
    def duration(self):
        """Queries the duration of the call.

        If the call has not ended then the current duration will
        be returned.

        Returns
        ---------
        :class:`datetime.timedelta`
            The timedelta object representing the duration.
        """
        if self.ended_timestamp is None:
            return datetime.datetime.utcnow() - self.message.created_at
        else:
            return self.ended_timestamp - self.message.created_at

class GroupCall:
    """Represents the actual group call from Discord.

    This is accompanied with a :class:`CallMessage` denoting the information.

    Attributes
    -----------
    call: :class:`CallMessage`
        The call message associated with this group call.
    unavailable: :class:`bool`
        Denotes if this group call is unavailable.
    ringing: List[:class:`User`]
        A list of users that are currently being rung to join the call.
    region: :class:`VoiceRegion`
        The guild region the group call is being hosted on.
    """

    def __init__(self, **kwargs):
        self.call = kwargs.get('call')
        self.unavailable = kwargs.get('unavailable')
        self._voice_states = {}

        for state in kwargs.get('voice_states', []):
            self._update_voice_state(state)

        self._update(**kwargs)

    def _update(self, **kwargs):
        self.region = try_enum(VoiceRegion, kwargs.get('region'))
        lookup = {u.id: u for u in self.call.channel.recipients}
        me = self.call.channel.me
        lookup[me.id] = me
        self.ringing = list(filter(None, map(lookup.get, kwargs.get('ringing', []))))

    def _update_voice_state(self, data):
        user_id = int(data['user_id'])
        # left the voice channel?
        if data['channel_id'] is None:
            self._voice_states.pop(user_id, None)
        else:
            self._voice_states[user_id] = VoiceState(data=data, channel=self.channel)

    @property
    def connected(self):
        """List[:class:`User`]: A property that returns all users that are currently in this call."""
        ret = [u for u in self.channel.recipients if self.voice_state_for(u) is not None]
        me = self.channel.me
        if self.voice_state_for(me) is not None:
            ret.append(me)

        return ret

    @property
    def channel(self):
        r""":class:`GroupChannel`\: Returns the channel the group call is in."""
        return self.call.channel

    def voice_state_for(self, user):
        """Retrieves the :class:`VoiceState` for a specified :class:`User`.

        If the :class:`User` has no voice state then this function returns
        ``None``.

        Parameters
        ------------
        user: :class:`User`
            The user to retrieve the voice state for.

        Returns
        --------
        Optional[:class:`VoiceState`]
            The voice state associated with this user.
        """

        return self._voice_states.get(user.id)
