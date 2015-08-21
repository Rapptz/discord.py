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

import datetime
from user import User

class Message(object):
    """Represents a message from Discord.

    There should be no need to create one of these manually.

    Instance attributes:

    .. attribute:: edited_timestamp

        A datetime object containing the edited time of the message. Could be None.
    .. attribute:: timestamp

        A datetime object containing the time the message was created.
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

        An array of :class:`User`s that were mentioned.
    .. attribute:: id

        The message ID.
    """

    def __init__(self, edited_timestamp, timestamp, tts, content, mention_everyone, mentions, embeds, attachments, id, channel, author, **kwargs):
        # at the moment, the timestamps seem to be naive so they have no time zone and operate on UTC time.
        # we can use this to our advantage to use strptime instead of a complicated parsing routine.
        # example timestamp: 2015-08-21T12:03:45.782000+00:00
        time_format = "%Y-%m-%dT%H:%M:%S.%f+00:00"
        self.edited_timestamp = None
        if edited_timestamp is not None:
            self.edited_timestamp = datetime.datetime.strptime(edited_timestamp, time_format)

        self.timestamp = datetime.datetime.strptime(timestamp, time_format)
        self.tts = tts
        self.content = content
        self.mention_everyone = mention_everyone
        self.embeds = embeds
        self.id = id
        self.channel = channel
        self.author = User(**author)
        self.mentions = [User(**mention) for mention in mentions]



