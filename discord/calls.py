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

from . import utils

class CallMessage:
    """Represents a group call from Discord.

    This is only received in cases where the message type is equivalent to
    :attr:`MessageType.call`.

    Attributes
    -----------
    ended_timestamp: Optional[datetime.datetime]
        A naive UTC datetime object that represents the time that the call has ended.
    participants: List[:class:`User`]
        The list of users that are participating in this call.
    channel: :class:`PrivateChannel`
        The private channel associated with this call.
    """

    def __init__(self, channel, **kwargs):
        self.channel = channel
        self.ended_timestamp = utils.parse_time(kwargs.get('ended_timestamp'))
        self.participants = kwargs.get('participants')
