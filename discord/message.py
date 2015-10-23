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

        A boolean specifying if the message was done with text-to-speech.
    .. attribute:: author

        A :class:`Member` that sent the message. If :attr:`channel` is a private channel,
        then it is a :class:`User` instead.
    .. attribute:: content

        The actual contents of the message.
    .. attribute:: embeds

        A list of embedded objects. The elements are objects that meet oEmbed's specification_.

        .. _specification: http://oembed.com/
    .. attribute:: channel

        The :class:`Channel` that the message was sent from. Could be a :class:`PrivateChannel` if it's a private message.
    .. attribute:: server

        The :class:`Server` that the message belongs to. If not applicable (i.e. a PM) then it's None instead.
    .. attribute:: mention_everyone

        A boolean specifying if the message mentions everyone.
    .. attribute:: mentions

        A list of :class:`User` that were mentioned.
    .. attribute:: id

        The message ID.
    .. attribute:: attachments

        A list of attachments given to a message.
    """

    def __init__(self, **kwargs):
        # at the moment, the timestamps seem to be naive so they have no time zone and operate on UTC time.
        # we can use this to our advantage to use strptime instead of a complicated parsing routine.
        # example timestamp: 2015-08-21T12:03:45.782000+00:00
        # sometimes the .%f modifier is missing
        self.edited_timestamp = utils.parse_time(kwargs.get('edited_timestamp'))
        self.timestamp = utils.parse_time(kwargs.get('timestamp'))
        self.tts = kwargs.get('tts')
        self.content = kwargs.get('content')
        self.mention_everyone = kwargs.get('mention_everyone')
        self.embeds = kwargs.get('embeds')
        self.id = kwargs.get('id')
        self.channel = kwargs.get('channel')
        self.author = User(**kwargs.get('author', {}))
        self.mentions = [User(**mention) for mention in kwargs.get('mentions', {})]
        self.attachments = kwargs.get('attachments')
        self.server = self.channel.server if not self.channel.is_private else None
        self._upgrade_to_member()

    def _upgrade_to_member(self):
        assert self.channel is not None

        if not self.channel.is_private:
            found = utils.find(lambda m: m.id == self.author.id, self.channel.server.members)
            if found is not None:
                self.author = found


