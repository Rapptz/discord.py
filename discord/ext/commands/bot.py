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

import asyncio
import discord
import inspect

from .core import GroupMixin
from .view import StringView
from .context import Context
from .errors import CommandNotFound

class Bot(GroupMixin, discord.Client):
    """Represents a discord bot.

    This class is a subclass of :class:`discord.Client` and as a result
    anything that you can do with a :class:`discord.Client` you can do with
    this bot.

    This class also subclasses :class:`GroupMixin` to provide the functionality
    to manage commands.

    Parameters
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in a
        :class:`discord.Message` as its first parameter and returns the prefix.
        This is to facilitate "dynamic" command prefixes.
    """
    def __init__(self, command_prefix, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix

    def _get_variable(self, name):
        stack = inspect.stack()
        for frames in stack:
            current_locals = frames[0].f_locals
            if name in current_locals:
                return current_locals[name]

    def _get_prefix(self, message):
        prefix = self.command_prefix
        if callable(prefix):
            return prefix(message)
        else:
            return prefix

    @asyncio.coroutine
    def say(self, content):
        """|coro|

        A helper function that is equivalent to doing

        .. code-block:: python

            self.send_message(message.channel, content)

        Parameters
        ----------
        content : str
            The content to pass to :class:`Client.send_message`
        """
        destination = self._get_variable('_internal_channel')
        result = yield from self.send_message(destination, content)
        return result

    @asyncio.coroutine
    def whisper(self, content):
        """|coro|

        A helper function that is equivalent to doing

        .. code-block:: python

            self.send_message(message.author, content)

        Parameters
        ----------
        content : str
            The content to pass to :class:`Client.send_message`
        """
        destination = self._get_variable('_internal_author')
        result = yield from self.send_message(destination, content)
        return result

    @asyncio.coroutine
    def reply(self, content):
        """|coro|

        A helper function that is equivalent to doing

        .. code-block:: python

            msg = '{0.mention}, {1}'.format(message.author, content)
            self.send_message(message.channel, msg)

        Parameters
        ----------
        content : str
            The content to pass to :class:`Client.send_message`
        """
        author = self._get_variable('_internal_author')
        destination = self._get_variable('_internal_channel')
        fmt = '{0.mention}, {1}'.format(author, str(content))
        result = yield from self.send_message(destination, fmt)
        return result

    @asyncio.coroutine
    def upload(self, fp, name=None):
        """|coro|

        A helper function that is equivalent to doing

        .. code-block:: python

            self.send_file(message.channel, fp, name)

        Parameters
        ----------
        fp
            The first parameter to pass to :meth:`Client.send_file`
        name
            The second parameter to pass to :meth:`Client.send_file`
        """
        destination = self._get_variable('_internal_channel')
        result = yield from self.send_file(destination, fp, name)
        return result

    @asyncio.coroutine
    def type(self):
        """|coro|

        A helper function that is equivalent to doing

        .. code-block:: python

            self.send_typing(message.channel)

        See Also
        ---------
        The :meth:`Client.send_typing` function.
        """
        destination = self._get_variable('_internal_channel')
        yield from self.send_typing(destination)

    @asyncio.coroutine
    def process_commands(self, message):
        """|coro|

        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.

        By default, this coroutine is called inside the :func:`on_message`
        event. If you choose to override the :func:`on_message` event, then
        you should invoke this coroutine as well.

        Warning
        --------
        This function is necessary for :meth:`say`, :meth:`whisper`,
        :meth:`type`, :meth:`reply`, and :meth:`upload` to work due to the
        way they are written.

        Parameters
        -----------
        message : discord.Message
            The message to process commands for.
        """
        _internal_channel = message.channel
        _internal_author = message.author

        view = StringView(message.content)
        if message.author == self.user:
            return

        prefix = self._get_prefix(message)
        if not view.skip_string(prefix):
            return

        view.skip_ws()
        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
        }
        ctx = Context(**tmp)
        del tmp
        if invoker in self.commands:
            command = self.commands[invoker]
            ctx.command = command
            yield from command.invoke(ctx)
        else:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)

    @asyncio.coroutine
    def on_message(self, message):
        yield from self.process_commands(message)
