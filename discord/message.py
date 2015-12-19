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
from .member import Member
from .object import Object
import re

class Message:
    """Represents a message from Discord.

    There should be no need to create one of these manually.

    Attributes
    -----------
    edited_timestamp : Optional[datetime.datetime]
        A naive UTC datetime object containing the edited time of the message.
    timestamp : datetime.datetime
        A naive UTC datetime object containing the time the message was created.
    tts : bool
        Specifies if the message was done with text-to-speech.
    author
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel, then it is a :class:`User` instead.
    content : str
        The actual contents of the message.
    embeds : list
        A list of embedded objects. The elements are objects that meet oEmbed's specification_.

        .. _specification: http://oembed.com/
    channel
        The :class:`Channel` that the message was sent from.
        Could be a :class:`PrivateChannel` if it's a private message.
        In :issue:`very rare cases <21>` this could be a :class:`Object` instead.

        For the sake of convenience, this :class:`Object` instance has an attribute ``is_private`` set to ``True``.
    server : Optional[:class:`Server`]
        The server that the message belongs to. If not applicable (i.e. a PM) then it's None instead.
    mention_everyone : bool
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` text is in the message itself.
            Rather this boolean indicates if the ``@everyone`` text is in the message
            **and** it did end up mentioning everyone.

    mentions : list
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list is always empty.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a discord limitation, not one with the library.

    channel_mentions : list
        A list of :class:`Channel` that were mentioned. If the message is in a private message
        then the list is always empty.
    id : str
        The message ID.
    attachments : list
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
        self.attachments = kwargs.get('attachments')
        self._handle_upgrades(kwargs.get('channel_id'))
        self._handle_mentions(kwargs.get('mentions', []))

    def _handle_mentions(self, mentions):
        self.mentions = []
        self.channel_mentions = []
        if getattr(self.channel, 'is_private', True):
            return

        if self.channel is not None:
            for mention in mentions:
                id_search = mention.get('id')
                member = utils.find(lambda m: m.id == id_search, self.server.members)
                if member is not None:
                    self.mentions.append(member)

        if self.server is not None:
            for mention in self.raw_channel_mentions:
                channel = utils.find(lambda m: m.id == mention, self.server.channels)
                if channel is not None:
                    self.channel_mentions.append(channel)

    @utils.cached_property
    def raw_mentions(self):
        """A property that returns an array of user IDs matched with
        the syntax of <@user_id> in the message content.

        This allows you receive the user IDs of mentioned users
        even in a private message context.
        """
        return re.findall(r'<@([0-9]+)>', self.content)

    @utils.cached_property
    def raw_channel_mentions(self):
        """A property that returns an array of channel IDs matched with
        the syntax of <#channel_id> in the message content.

        This allows you receive the channel IDs of mentioned users
        even in a private message context.
        """
        return re.findall(r'<#([0-9]+)>', self.content)

    @utils.cached_property
    def clean_content(self):
        """A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.
        """

        transformations = {
            re.escape('<#{0.id}>'.format(channel)): '#' + channel.name
            for channel in self.channel_mentions
        }

        mention_transforms = {
            re.escape('<@{0.id}>'.format(member)): '@' + member.name
            for member in self.mentions
        }

        transformations.update(mention_transforms)

        def repl(obj):
            return transformations.get(re.escape(obj.group(0)), '')

        pattern = re.compile('|'.join(transformations.keys()))
        return pattern.sub(repl, self.content)

    def _handle_upgrades(self, channel_id):
        self.server = None
        if self.channel is None:
            if channel_id is not None:
                self.channel = Object(id=channel_id)
                self.channel.is_private = True
            return

        if not self.channel.is_private:
            self.server = self.channel.server
            found = utils.find(lambda m: m.id == self.author.id, self.server.members)
            if found is not None:
                self.author = found
