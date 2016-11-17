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

import abc
import io
import os
import asyncio

from .message import Message
from .iterators import LogsFromIterator
from .context_managers import Typing
from .errors import ClientException, NoMoreMessages

class Snowflake(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def created_at(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Snowflake:
            mro = C.__mro__
            for attr in ('created_at', 'id'):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

class User(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def display_name(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def mention(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is User:
            if Snowflake.__subclasshook__(C) is NotImplemented:
                return NotImplemented

            mro = C.__mro__
            for attr in ('display_name', 'mention', 'name', 'avatar', 'discriminator', 'bot'):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

class GuildChannel(metaclass=abc.ABCMeta):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def mention(self):
        raise NotImplementedError

    @abc.abstractmethod
    def overwrites_for(self, obj):
        raise NotImplementedError

    @abc.abstractmethod
    def permissions_for(self, user):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is GuildChannel:
            if Snowflake.__subclasshook__(C) is NotImplemented:
                return NotImplemented

            mro = C.__mro__
            for attr in ('name', 'guild', 'overwrites_for', 'permissions_for', 'mention'):
                for base in mro:
                    if attr in base.__dict__:
                        break
                else:
                    return NotImplemented
            return True
        return NotImplemented

class PrivateChannel(metaclass=abc.ABCMeta):
    __slots__ = ()

    @classmethod
    def __subclasshook__(cls, C):
        if cls is PrivateChannel:
            if Snowflake.__subclasshook__(C) is NotImplemented:
                return NotImplemented

            mro = C.__mro__
            for base in mro:
                if 'me' in base.__dict__:
                    return True
            return NotImplemented
        return NotImplemented

class MessageChannel(metaclass=abc.ABCMeta):
    __slots__ = ()

    @abc.abstractmethod
    def _get_destination(self):
        raise NotImplementedError

    @asyncio.coroutine
    def send_message(self, content=None, *, tts=False, embed=None):
        """|coro|

        Sends a message to the channel with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        If the ``embed`` parameter is provided, it must be of type :class:`Embed` and
        it must be a rich embed type.

        Parameters
        ------------
        content
            The content of the message to send.
        tts: bool
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`Embed`
            The rich embed for the content.

        Raises
        --------
        HTTPException
            Sending the message failed.
        Forbidden
            You do not have the proper permissions to send the message.

        Returns
        ---------
        :class:`Message`
            The message that was sent.
        """

        channel_id, guild_id = self._get_destination()
        content = str(content) if content else None
        if embed is not None:
            embed = embed.to_dict()

        data = yield from self._state.http.send_message(channel_id, content, guild_id=guild_id, tts=tts, embed=embed)
        return Message(channel=self, state=self._state, data=data)

    @asyncio.coroutine
    def send_typing(self):
        """|coro|

        Send a *typing* status to the channel.

        *Typing* status will go away after 10 seconds, or after a message is sent.
        """

        channel_id, _ = self._get_destination()
        yield from self._state.http.send_typing(channel_id)

    def typing(self):
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        Example Usage: ::

            with channel.typing():
                # do expensive stuff here
                await channel.send_message('done!')

        """
        return Typing(self)

    @asyncio.coroutine
    def upload(self, fp, *, filename=None, content=None, tts=False):
        """|coro|

        Sends a message to the channel with the file given.

        The ``fp`` parameter should be either a string denoting the location for a
        file or a *file-like object*. The *file-like object* passed is **not closed**
        at the end of execution. You are responsible for closing it yourself.

        .. note::

            If the file-like object passed is opened via ``open`` then the modes
            'rb' should be used.

        The ``filename`` parameter is the filename of the file.
        If this is not given then it defaults to ``fp.name`` or if ``fp`` is a string
        then the ``filename`` will default to the string given. You can overwrite
        this value by passing this in.

        Parameters
        ------------
        fp
            The *file-like object* or file path to send.
        filename: str
            The filename of the file. Defaults to ``fp.name`` if it's available.
        content: str
            The content of the message to send along with the file. This is
            forced into a string by a ``str(content)`` call.
        tts: bool
            If the content of the message should be sent with TTS enabled.

        Raises
        -------
        HTTPException
            Sending the file failed.

        Returns
        --------
        :class:`Message`
            The message sent.
        """

        channel_id, guild_id = self._get_destination()

        try:
            with open(fp, 'rb') as f:
                buffer = io.BytesIO(f.read())
                if filename is None:
                    _, filename = os.path.split(fp)
        except TypeError:
            buffer = fp

        state = self._state
        data = yield from state.http.send_file(channel_id, buffer, guild_id=guild_id,
                                                     filename=filename, content=content, tts=tts)

        return Message(channel=self, state=state, data=data)

    @asyncio.coroutine
    def get_message(self, id):
        """|coro|

        Retrieves a single :class:`Message` from a channel.

        This can only be used by bot accounts.

        Parameters
        ------------
        id: int
            The message ID to look for.

        Returns
        --------
        :class:`Message`
            The message asked for.

        Raises
        --------
        NotFound
            The specified message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.
        """

        data = yield from self._state.http.get_message(self.id, id)
        return Message(channel=self, state=self._state, data=data)

    @asyncio.coroutine
    def delete_messages(self, messages):
        """|coro|

        Deletes a list of messages. This is similar to :meth:`Message.delete`
        except it bulk deletes multiple messages.

        Usable only by bot accounts.

        Parameters
        -----------
        messages : iterable of :class:`Message`
            An iterable of messages denoting which ones to bulk delete.

        Raises
        ------
        ClientException
            The number of messages to delete is less than 2 or more than 100.
        Forbidden
            You do not have proper permissions to delete the messages or
            you're not using a bot account.
        HTTPException
            Deleting the messages failed.
        """

        messages = list(messages)
        if len(messages) > 100 or len(messages) < 2:
            raise ClientException('Can only delete messages in the range of [2, 100]')

        message_ids = [m.id for m in messages]
        channel_id, guild_id = self._get_destination()

        yield from self._state.http.delete_messages(channel_id, message_ids, guild_id)

    @asyncio.coroutine
    def pins(self):
        """|coro|

        Returns a list of :class:`Message` that are currently pinned.

        Raises
        -------
        HTTPException
            Retrieving the pinned messages failed.
        """

        state = self._state
        data = yield from state.http.pins_from(self.id)
        return [Message(channel=self, state=state, data=m) for m in data]

    def history(self, *, limit=100, before=None, after=None, around=None, reverse=None):
        """Return an async iterator that enables receiving the channel's message history.

        You must have Read Message History permissions to use this.

        All parameters are optional.

        Parameters
        -----------
        limit: int
            The number of messages to retrieve.
        before: :class:`Message` or `datetime`
            Retrieve messages before this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        after: :class:`Message` or `datetime`
            Retrieve messages after this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
        around: :class:`Message` or `datetime`
            Retrieve messages around this date or message.
            If a date is provided it must be a timezone-naive datetime representing UTC time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number then this will return at most limit + 1 messages.
        reverse: bool
            If set to true, return messages in oldest->newest order. If unspecified,
            this defaults to ``False`` for most cases. However if passing in a
            ``after`` parameter then this is set to ``True``. This avoids getting messages
            out of order in the ``after`` case.

        Raises
        ------
        Forbidden
            You do not have permissions to get channel message history.
        HTTPException
            The request to get message history failed.

        Yields
        -------
        :class:`Message`
            The message with the message data parsed.

        Examples
        ---------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Python 3.4 Usage ::

            count = 0
            iterator = channel.history(limit=200)
            while True:
                try:
                    message = yield from iterator.get()
                except discord.NoMoreMessages:
                    break
                else:
                    if message.author == client.user:
                        counter += 1
        """
        return LogsFromIterator(self, limit=limit, before=before, after=after, around=around, reverse=reverse)

    @asyncio.coroutine
    def purge(self, *, limit=100, check=None, before=None, after=None, around=None):
        """|coro|

        Purges a list of messages that meet the criteria given by the predicate
        ``check``. If a ``check`` is not provided then all messages are deleted
        without discrimination.

        You must have :attr:`Permissions.manage_messages` permission to
        delete messages even if they are your own. The
        :attr:`Permissions.read_message_history` permission is also needed to
        retrieve message history.

        Usable only by bot accounts.

        Parameters
        -----------
        limit: int
            The number of messages to search through. This is not the number
            of messages that will be deleted, though it can be.
        check: predicate
            The function used to check if a message should be deleted.
            It must take a :class:`Message` as its sole parameter.
        before
            Same as ``before`` in :meth:`history`.
        after
            Same as ``after`` in :meth:`history`.
        around
            Same as ``around`` in :meth:`history`.

        Raises
        -------
        Forbidden
            You do not have proper permissions to do the actions required or
            you're not using a bot account.
        HTTPException
            Purging the messages failed.

        Examples
        ---------

        Deleting bot's messages ::

            def is_me(m):
                return m.author == client.user

            deleted = await channel.purge(limit=100, check=is_me)
            await channel.send_message('Deleted {} message(s)'.format(len(deleted)))

        Returns
        --------
        list
            The list of messages that were deleted.
        """

        if check is None:
            check = lambda m: True

        iterator = self.history(limit=limit, before=before, after=after, around=around)
        ret = []
        count = 0

        while True:
            try:
                msg = yield from iterator.get()
            except NoMoreMessages:
                # no more messages to poll
                if count >= 2:
                    # more than 2 messages -> bulk delete
                    to_delete = ret[-count:]
                    yield from self.delete_messages(to_delete)
                elif count == 1:
                    # delete a single message
                    yield from ret[-1].delete()

                return ret
            else:
                if count == 100:
                    # we've reached a full 'queue'
                    to_delete = ret[-100:]
                    yield from self.delete_messages(to_delete)
                    count = 0
                    yield from asyncio.sleep(1)

                if check(msg):
                    count += 1
                    ret.append(msg)
