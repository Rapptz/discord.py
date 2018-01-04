# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import discord.abc
import discord.utils

class Context(discord.abc.Messageable):
    """Represents the context in which a command is being invoked under.

    This class contains a lot of meta data to help you understand more about
    the invocation context. This class is not created manually and is instead
    passed around to commands as the first parameter.

    This class implements the :class:`abc.Messageable` ABC.

    Attributes
    -----------
    message: :class:`discord.Message`
        The message that triggered the command being executed.
    bot: :class:`.Bot`
        The bot that contains the command being executed.
    args: :class:`list`
        The list of transformed arguments that were passed into the command.
        If this is accessed during the :func:`on_command_error` event
        then this list could be incomplete.
    kwargs: :class:`dict`
        A dictionary of transformed arguments that were passed into the command.
        Similar to :attr:`args`\, if this is accessed in the
        :func:`on_command_error` event then this dict could be incomplete.
    prefix: :class:`str`
        The prefix that was used to invoke the command.
    command
        The command (i.e. :class:`.Command` or its superclasses) that is being
        invoked currently.
    invoked_with: :class:`str`
        The command name that triggered this invocation. Useful for finding out
        which alias called the command.
    invoked_subcommand
        The subcommand (i.e. :class:`.Command` or its superclasses) that was
        invoked. If no valid subcommand was invoked then this is equal to
        `None`.
    subcommand_passed: Optional[:class:`str`]
        The string that was attempted to call a subcommand. This does not have
        to point to a valid registered subcommand and could just point to a
        nonsense string. If nothing was passed to attempt a call to a
        subcommand then this is set to `None`.
    command_failed: :class:`bool`
        A boolean that indicates if the command failed to be parsed, checked,
        or invoked.
    """

    def __init__(self, **attrs):
        self.message = attrs.pop('message', None)
        self.bot = attrs.pop('bot', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.prefix = attrs.pop('prefix')
        self.command = attrs.pop('command', None)
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)
        self.command_failed = attrs.pop('command_failed', False)
        self._state = self.message._state

    @asyncio.coroutine
    def invoke(self, *args, **kwargs):
        """|coro|

        Calls a command with the arguments given.

        This is useful if you want to just call the callback that a
        :class:`.Command` holds internally.

        Note
        ------
        You do not pass in the context as it is done for you.

        Warning
        ---------
        The first parameter passed **must** be the command being invoked.

        Parameters
        -----------
        command: :class:`.Command`
            A command or superclass of a command that is going to be called.
        \*args
            The arguments to to use.
        \*\*kwargs
            The keyword arguments to use.
        """

        try:
            command = args[0]
        except IndexError:
            raise TypeError('Missing command to invoke.') from None

        arguments = []
        if command.instance is not None:
            arguments.append(command.instance)

        arguments.append(self)
        arguments.extend(args[1:])

        ret = yield from command.callback(*arguments, **kwargs)
        return ret

    @asyncio.coroutine
    def reinvoke(self, *, call_hooks=False, restart=True):
        """|coro|

        Calls the command again.

        This is similar to :meth:`~.Context.invoke` except that it bypasses
        checks, cooldowns, and error handlers.

        .. note::

            If you want to bypass :exc:`.UserInputError` derived exceptions,
            it is recommended to use the regular :meth:`~.Context.invoke`
            as it will work more naturally. After all, this will end up
            using the old arguments the user has used and will thus just
            fail again.

        Parameters
        ------------
        call_hooks: bool
            Whether to call the before and after invoke hooks.
        restart: bool
            Whether to start the call chain from the very beginning
            or where we left off (i.e. the command that caused the error).
            The default is to start where we left off.
        """
        cmd = self.command
        view = self.view
        if cmd is None:
            raise ValueError('This context is not valid.')

        # some state to revert to when we're done
        index, previous = view.index, view.previous
        invoked_with = self.invoked_with
        invoked_subcommand = self.invoked_subcommand
        subcommand_passed = self.subcommand_passed

        if restart:
            to_call = cmd.root_parent or cmd
            view.index = len(self.prefix)
            view.previous = 0
            view.get_word() # advance to get the root command
        else:
            to_call = cmd

        try:
            yield from to_call.reinvoke(self, call_hooks=call_hooks)
        finally:
            self.command = cmd
            view.index = index
            view.previous = previous
            self.invoked_with = invoked_with
            self.invoked_subcommand = invoked_subcommand
            self.subcommand_passed = subcommand_passed

    @property
    def valid(self):
        """Checks if the invocation context is valid to be invoked with."""
        return self.prefix is not None and self.command is not None

    @asyncio.coroutine
    def _get_channel(self):
        return self.channel

    @property
    def cog(self):
        """Returns the cog associated with this context's command. None if it does not exist."""

        if self.command is None:
            return None
        return self.command.instance

    @discord.utils.cached_property
    def guild(self):
        """Returns the guild associated with this context's command. None if not available."""
        return self.message.guild

    @discord.utils.cached_property
    def channel(self):
        """Returns the channel associated with this context's command. Shorthand for :attr:`Message.channel`."""
        return self.message.channel

    @discord.utils.cached_property
    def author(self):
        """Returns the author associated with this context's command. Shorthand for :attr:`Message.author`"""
        return self.message.author

    @discord.utils.cached_property
    def me(self):
        """Similar to :attr:`Guild.me` except it may return the :class:`ClientUser` in private message contexts."""
        return self.guild.me if self.guild is not None else self.bot.user

    @property
    def voice_client(self):
        """Optional[:class:`VoiceClient`]: A shortcut to :attr:`Guild.voice_client`\, if applicable."""
        g = self.guild
        return g.voice_client if g else None
