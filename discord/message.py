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

from .utils import parse_time
from .user import User

class Message(object):
    """Represents a message from Discord.

    There should be no need to create one of these manually.

    Instance attributes:

    .. attribute:: edited_timestamp

        A naive UTC datetime object containing the edited time of the message. Could be None.
    .. attribute:: timestamp

        A naive UTC datetime object containing the time the message was created.
    .. attribute:: tts

        Checks the message has text-to-speech support.
    .. attribute:: author

        A :class:`User` that sent the message.
    .. attribute:: content

        The actual contents of the message.
    .. attribute:: embeds

        An array of embedded objects.
    .. attribute:: channel

        The :class:`Channel` that the message was sent from. Could be a :class:`PrivateChannel` if it's a private message.
    .. attribute:: mention_everyone

        A boolean specifying if the message mentions everyone.
    .. attribute:: mentions

        An array of :class:`User` that were mentioned.
    .. attribute:: id

        The message ID.
    .. attribute:: attachments

        An array of attachments given to a message.
    """

    def __init__(self, **kwargs):
        # at the moment, the timestamps seem to be naive so they have no time zone and operate on UTC time.
        # we can use this to our advantage to use strptime instead of a complicated parsing routine.
        # example timestamp: 2015-08-21T12:03:45.782000+00:00
        # sometimes the .%f modifier is missing
        self.edited_timestamp = parse_time(kwargs.get('edited_timestamp'))
        self.timestamp = parse_time(kwargs.get('timestamp'))
        self.tts = kwargs.get('tts')
        self.content = kwargs.get('content')
        self.mention_everyone = kwargs.get('mention_everyone')
        self.embeds = kwargs.get('embeds')
        self.id = kwargs.get('id')
        self.channel = kwargs.get('channel')
        self.author = User(**kwargs.get('author', {}))
        self.mentions = [User(**mention) for mention in kwargs.get('mentions', {})]
        self.attachments = kwargs.get('attachments')

