# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

import itertools
import copy
import functools
import inspect
import re
import discord.utils

from .core import Group, Command
from .errors import CommandError

__all__ = (
    'Paginator',
    'HelpCommand',
    'DefaultHelpCommand',
    'MinimalHelpCommand',
)

# help -> shows info of bot on top/bottom and lists subcommands
# help command -> shows detailed info of command
# help command <subcommand chain> -> same as above

# <description>

# <command signature with aliases>

# <long doc>

# Cog:
#   <command> <shortdoc>
#   <command> <shortdoc>
# Other Cog:
#   <command> <shortdoc>
# No Category:
#   <command> <shortdoc>

# Type <prefix>help command for more info on a command.
# You can also type <prefix>help category for more info on a category.

class Paginator:
    """A class that aids in paginating code blocks for Discord messages.

    .. container:: operations

        .. describe:: len(x)

            Returns the total number of characters in the paginator.

    Attributes
    -----------
    prefix: :class:`str`
        The prefix inserted to every page. e.g. three backticks.
    suffix: :class:`str`
        The suffix appended at the end of every page. e.g. three backticks.
    max_size: :class:`int`
        The maximum amount of codepoints allowed in a page.
    linesep: :class:`str`
        The character string inserted between lines. e.g. a newline character.
            .. versionadded:: 1.7
    """
    def __init__(self, prefix='```', suffix='```', max_size=2000, linesep='\n'):
        self.prefix = prefix
        self.suffix = suffix
        self.max_size = max_size
        self.linesep = linesep
        self.clear()

    def clear(self):
        """Clears the paginator to have no pages."""
        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len # prefix + newline
        else:
            self._current_page = []
            self._count = 0
        self._pages = []

    @property
    def _prefix_len(self):
        return len(self.prefix) if self.prefix else 0

    @property
    def _suffix_len(self):
        return len(self.suffix) if self.suffix else 0

    @property
    def _linesep_len(self):
        return len(self.linesep)

    def add_line(self, line='', *, empty=False):
        """Adds a line to the current page.

        If the line exceeds the :attr:`max_size` then an exception
        is raised.

        Parameters
        -----------
        line: :class:`str`
            The line to add.
        empty: :class:`bool`
            Indicates if another empty line should be added.

        Raises
        ------
        RuntimeError
            The line was too big for the current :attr:`max_size`.
        """
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            raise RuntimeError('Line exceeds maximum page size %s' % (max_page_size))

        if self._count + len(line) + self._linesep_len > self.max_size - self._suffix_len:
            self.close_page()

        self._count += len(line) + self._linesep_len
        self._current_page.append(line)

        if empty:
            self._current_page.append('')
            self._count += self._linesep_len

    def close_page(self):
        """Prematurely terminate a page."""
        if self.suffix is not None:
            self._current_page.append(self.suffix)
        self._pages.append(self.linesep.join(self._current_page))

        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len # prefix + linesep
        else:
            self._current_page = []
            self._count = 0

    def __len__(self):
        total = sum(len(p) for p in self._pages)
        return total + self._count

    @property
    def pages(self):
        """List[:class:`str`]: Returns the rendered list of pages."""
        # we have more than just the prefix in our current page
        if len(self._current_page) > (0 if self.prefix is None else 1):
            self.close_page()
        return self._pages

    def __repr__(self):
        fmt = '<Paginator prefix: {0.prefix!r} suffix: {0.suffix!r} linesep: {0.linesep!r} max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)

def _not_overriden(f):
    f.__help_command_not_overriden__ = True
    return f

class _HelpCommandImpl(Command):
    def __init__(self, inject, *args, **kwargs):
        super().__init__(inject.command_callback, *args, **kwargs)
        self._original = inject
        self._injected = inject

    async def prepare(self, ctx):
        self._injected = injected = self._original.copy()
        injected.context = ctx
        self.callback = injected.command_callback

        on_error = injected.on_help_command_error
        if not hasattr(on_error, '__help_command_not_overriden__'):
            if self.cog is not None:
                self.on_error = self._on_error_cog_implementation
            else:
                self.on_error = on_error

        await super().prepare(ctx)

    async def _parse_arguments(self, ctx):
        # Make the parser think we don't have a cog so it doesn't
        # inject the parameter into `ctx.args`.
        original_cog = self.cog
        self.cog = None
        try:
            await super()._parse_arguments(ctx)
        finally:
            self.cog = original_cog

    async def _on_error_cog_implementation(self, dummy, ctx, error):
        await self._injected.on_help_command_error(ctx, error)

    @property
    def clean_params(self):
        result = self.params.copy()
        try:
            result.popitem(last=False)
        except Exception:
            raise ValueError('Missing context parameter') from None
        else:
            return result

    def _inject_into_cog(self, cog):
        # Warning: hacky

        # Make the cog think that get_commands returns this command
        # as well if we inject it without modifying __cog_commands__
        # since that's used for the injection and ejection of cogs.
        def wrapped_get_commands(*, _original=cog.get_commands):
            ret = _original()
            ret.append(self)
            return ret

        # Ditto here
        def wrapped_walk_commands(*, _original=cog.walk_commands):
            yield from _original()
            yield self

        functools.update_wrapper(wrapped_get_commands, cog.get_commands)
        functools.update_wrapper(wrapped_walk_commands, cog.walk_commands)
        cog.get_commands = wrapped_get_commands
        cog.walk_commands = wrapped_walk_commands
        self.cog = cog

    def _eject_cog(self):
        if self.cog is None:
            return

        # revert back into their original methods
        cog = self.cog
        cog.get_commands = cog.get_commands.__wrapped__
        cog.walk_commands = cog.walk_commands.__wrapped__
        self.cog = None

class HelpCommand:
    r"""The base implementation for help command formatting.

    .. note::

        Internally instances of this class are deep copied every time
        the command itself is invoked to prevent a race condition
        mentioned in :issue:`2123`.

        This means that relying on the state of this class to be
        the same between command invocations would not work as expected.

    Attributes
    ------------
    context: Optional[:class:`Context`]
        The context that invoked this help formatter. This is generally set after
        the help command assigned, :func:`command_callback`\, has been called.
    show_hidden: :class:`bool`
        Specifies if hidden commands should be shown in the output.
        Defaults to ``False``.
    verify_checks: Optional[:class:`bool`]
        Specifies if commands should have their :attr:`.Command.checks` called
        and verified. If ``True``, always calls :attr:`.Commands.checks`.
        If ``None``, only calls :attr:`.Commands.checks` in a guild setting.
        If ``False``, never calls :attr:`.Commands.checks`. Defaults to ``True``.

        .. versionchanged:: 1.7
    command_attrs: :class:`dict`
        A dictionary of options to pass in for the construction of the help command.
        This allows you to change the command behaviour without actually changing
        the implementation of the command. The attributes will be the same as the
        ones passed in the :class:`.Command` constructor.
    """

    MENTION_TRANSFORMS = {
        '@everyone': '@\u200beveryone',
        '@here': '@\u200bhere',
        r'<@!?[0-9]{17,22}>': '@deleted-user',
        r'<@&[0-9]{17,22}>': '@deleted-role'
    }

    MENTION_PATTERN = re.compile('|'.join(MENTION_TRANSFORMS.keys()))

    def __new__(cls, *args, **kwargs):
        # To prevent race conditions of a single instance while also allowing
        # for settings to be passed the original arguments passed must be assigned
        # to allow for easier copies (which will be made when the help command is actually called)
        # see issue 2123
        self = super().__new__(cls)

        # Shallow copies cannot be used in this case since it is not unusual to pass
        # instances that need state, e.g. Paginator or what have you into the function
        # The keys can be safely copied as-is since they're 99.99% certain of being
        # string keys
        deepcopy = copy.deepcopy
        self.__original_kwargs__ = {
            k: deepcopy(v)
            for k, v in kwargs.items()
        }
        self.__original_args__ = deepcopy(args)
        return self

    def __init__(self, **options):
        self.show_hidden = options.pop('show_hidden', False)
        self.verify_checks = options.pop('verify_checks', True)
        self.command_attrs = attrs = options.pop('command_attrs', {})
        attrs.setdefault('name', 'help')
        attrs.setdefault('help', 'Shows this message')
        self.context = None
        self._command_impl = _HelpCommandImpl(self, **self.command_attrs)

    def copy(self):
        obj = self.__class__(*self.__original_args__, **self.__original_kwargs__)
        obj._command_impl = self._command_impl
        return obj

    def _add_to_bot(self, bot):
        command = _HelpCommandImpl(self, **self.command_attrs)
        bot.add_command(command)
        self._command_impl = command

    def _remove_from_bot(self, bot):
        bot.remove_command(self._command_impl.name)
        self._command_impl._eject_cog()

    def add_check(self, func):
        """
        Adds a check to the help command.

        .. versionadded:: 1.4

        Parameters
        ----------
        func
            The function that will be used as a check.
        """

        self._command_impl.add_check(func)

    def remove_check(self, func):
        """
        Removes a check from the help command.

        This function is idempotent and will not raise an exception if
        the function is not in the command's checks.

        .. versionadded:: 1.4

        Parameters
        ----------
        func
            The function to remove from the checks.
        """

        self._command_impl.remove_check(func)

    def get_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        bot = self.context.bot
        mapping = {
            cog: cog.get_commands()
            for cog in bot.cogs.values()
        }
        mapping[None] = [c for c in bot.commands if c.cog is None]
        return mapping

    @property
    def clean_prefix(self):
        """:class:`str`: The cleaned up invoke prefix. i.e. mentions are ``@name`` instead of ``<@id>``."""
        user = self.context.guild.me if self.context.guild else self.context.bot.user
        # this breaks if the prefix mention is not the bot itself but I
        # consider this to be an *incredibly* strange use case. I'd rather go
        # for this common use case rather than waste performance for the
        # odd one.
        pattern = re.compile(r"<@!?%s>" % user.id)
        return pattern.sub("@%s" % user.display_name.replace('\\', r'\\'), self.context.prefix)

    @property
    def invoked_with(self):
        """Similar to :attr:`Context.invoked_with` except properly handles
        the case where :meth:`Context.send_help` is used.

        If the help command was used regularly then this returns
        the :attr:`Context.invoked_with` attribute. Otherwise, if
        it the help command was called using :meth:`Context.send_help`
        then it returns the internal command name of the help command.

        Returns
        ---------
        :class:`str`
            The command name that triggered this invocation.
        """
        command_name = self._command_impl.name
        ctx = self.context
        if ctx is None or ctx.command is None or ctx.command.qualified_name != command_name:
            return command_name
        return ctx.invoked_with

    def get_command_signature(self, command):
        """Retrieves the signature portion of the help page.

        Parameters
        ------------
        command: :class:`Command`
            The command to get the signature of.

        Returns
        --------
        :class:`str`
            The signature for the command.
        """

        parent = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + ' ' + parent.signature)
            parent = parent.parent
        parent_sig = ' '.join(reversed(entries))

        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = '[%s|%s]' % (command.name, aliases)
            if parent_sig:
                fmt = parent_sig + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent_sig else parent_sig + ' ' + command.name

        return '%s%s %s' % (self.clean_prefix, alias, command.signature)

    def remove_mentions(self, string):
        """Removes mentions from the string to prevent abuse.

        This includes ``@everyone``, ``@here``, member mentions and role mentions.

        Returns
        -------
        :class:`str`
            The string with mentions removed.
        """

        def replace(obj, *, transforms=self.MENTION_TRANSFORMS):
            return transforms.get(obj.group(0), '@invalid')

        return self.MENTION_PATTERN.sub(replace, string)

    @property
    def cog(self):
        """A property for retrieving or setting the cog for the help command.

        When a cog is set for the help command, it is as-if the help command
        belongs to that cog. All cog special methods will apply to the help
        command and it will be automatically unset on unload.

        To unbind the cog from the help command, you can set it to ``None``.

        Returns
        --------
        Optional[:class:`Cog`]
            The cog that is currently set for the help command.
        """
        return self._command_impl.cog

    @cog.setter
    def cog(self, cog):
        # Remove whatever cog is currently valid, if any
        self._command_impl._eject_cog()

        # If a new cog is set then inject it.
        if cog is not None:
            self._command_impl._inject_into_cog(cog)

    def command_not_found(self, string):
        """|maybecoro|

        A method called when a command is not found in the help command.
        This is useful to override for i18n.

        Defaults to ``No command called {0} found.``

        Parameters
        ------------
        string: :class:`str`
            The string that contains the invalid command. Note that this has
            had mentions removed to prevent abuse.

        Returns
        ---------
        :class:`str`
            The string to use when a command has not been found.
        """
        return 'No command called "{}" found.'.format(string)

    def subcommand_not_found(self, command, string):
        """|maybecoro|

        A method called when a command did not have a subcommand requested in the help command.
        This is useful to override for i18n.

        Defaults to either:

        - ``'Command "{command.qualified_name}" has no subcommands.'``
            - If there is no subcommand in the ``command`` parameter.
        - ``'Command "{command.qualified_name}" has no subcommand named {string}'``
            - If the ``command`` parameter has subcommands but not one named ``string``.

        Parameters
        ------------
        command: :class:`Command`
            The command that did not have the subcommand requested.
        string: :class:`str`
            The string that contains the invalid subcommand. Note that this has
            had mentions removed to prevent abuse.

        Returns
        ---------
        :class:`str`
            The string to use when the command did not have the subcommand requested.
        """
        if isinstance(command, Group) and len(command.all_commands) > 0:
            return 'Command "{0.qualified_name}" has no subcommand named {1}'.format(command, string)
        return 'Command "{0.qualified_name}" has no subcommands.'.format(command)

    async def filter_commands(self, commands, *, sort=False, key=None):
        """|coro|

        Returns a filtered list of commands and optionally sorts them.

        This takes into account the :attr:`verify_checks` and :attr:`show_hidden`
        attributes.

        Parameters
        ------------
        commands: Iterable[:class:`Command`]
            An iterable of commands that are getting filtered.
        sort: :class:`bool`
            Whether to sort the result.
        key: Optional[Callable[:class:`Command`, Any]]
            An optional key function to pass to :func:`py:sorted` that
            takes a :class:`Command` as its sole parameter. If ``sort`` is
            passed as ``True`` then this will default as the command name.

        Returns
        ---------
        List[:class:`Command`]
            A list of commands that passed the filter.
        """

        if sort and key is None:
            key = lambda c: c.name

        iterator = commands if self.show_hidden else filter(lambda c: not c.hidden, commands)

        if self.verify_checks is False:
            # if we do not need to verify the checks then we can just
            # run it straight through normally without using await.
            return sorted(iterator, key=key) if sort else list(iterator)

        if self.verify_checks is None and not self.context.guild:
            # if verify_checks is None and we're in a DM, don't verify
            return sorted(iterator, key=key) if sort else list(iterator)

        # if we're here then we need to check every command if it can run
        async def predicate(cmd):
            try:
                return await cmd.can_run(self.context)
            except CommandError:
                return False

        ret = []
        for cmd in iterator:
            valid = await predicate(cmd)
            if valid:
                ret.append(cmd)

        if sort:
            ret.sort(key=key)
        return ret

    def get_max_size(self, commands):
        """Returns the largest name length of the specified command list.

        Parameters
        ------------
        commands: Sequence[:class:`Command`]
            A sequence of commands to check for the largest size.

        Returns
        --------
        :class:`int`
            The maximum width of the commands.
        """

        as_lengths = (
            discord.utils._string_width(c.name)
            for c in commands
        )
        return max(as_lengths, default=0)

    def get_destination(self):
        """Returns the :class:`~discord.abc.Messageable` where the help command will be output.

        You can override this method to customise the behaviour.

        By default this returns the context's channel.

        Returns
        -------
        :class:`.abc.Messageable`
            The destination where the help command will be output.
        """
        return self.context.channel

    async def send_error_message(self, error):
        """|coro|

        Handles the implementation when an error happens in the help command.
        For example, the result of :meth:`command_not_found` or
        :meth:`command_has_no_subcommand_found` will be passed here.

        You can override this method to customise the behaviour.

        By default, this sends the error message to the destination
        specified by :meth:`get_destination`.

        .. note::

            You can access the invocation context with :attr:`HelpCommand.context`.

        Parameters
        ------------
        error: :class:`str`
            The error message to display to the user. Note that this has
            had mentions removed to prevent abuse.
        """
        destination = self.get_destination()
        await destination.send(error)

    @_not_overriden
    async def on_help_command_error(self, ctx, error):
        """|coro|

        The help command's error handler, as specified by :ref:`ext_commands_error_handler`.

        Useful to override if you need some specific behaviour when the error handler
        is called.

        By default this method does nothing and just propagates to the default
        error handlers.

        Parameters
        ------------
        ctx: :class:`Context`
            The invocation context.
        error: :class:`CommandError`
            The error that was raised.
        """
        pass

    async def send_bot_help(self, mapping):
        """|coro|

        Handles the implementation of the bot command page in the help command.
        This function is called when the help command is called with no arguments.

        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.

        You can override this method to customise the behaviour.

        .. note::

            You can access the invocation context with :attr:`HelpCommand.context`.

            Also, the commands in the mapping are not filtered. To do the filtering
            you will have to call :meth:`filter_commands` yourself.

        Parameters
        ------------
        mapping: Mapping[Optional[:class:`Cog`], List[:class:`Command`]]
            A mapping of cogs to commands that have been requested by the user for help.
            The key of the mapping is the :class:`~.commands.Cog` that the command belongs to, or
            ``None`` if there isn't one, and the value is a list of commands that belongs to that cog.
        """
        return None

    async def send_cog_help(self, cog):
        """|coro|

        Handles the implementation of the cog page in the help command.
        This function is called when the help command is called with a cog as the argument.

        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.

        You can override this method to customise the behaviour.

        .. note::

            You can access the invocation context with :attr:`HelpCommand.context`.

            To get the commands that belong to this cog see :meth:`Cog.get_commands`.
            The commands returned not filtered. To do the filtering you will have to call
            :meth:`filter_commands` yourself.

        Parameters
        -----------
        cog: :class:`Cog`
            The cog that was requested for help.
        """
        return None

    async def send_group_help(self, group):
        """|coro|

        Handles the implementation of the group page in the help command.
        This function is called when the help command is called with a group as the argument.

        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.

        You can override this method to customise the behaviour.

        .. note::

            You can access the invocation context with :attr:`HelpCommand.context`.

            To get the commands that belong to this group without aliases see
            :attr:`Group.commands`. The commands returned not filtered. To do the
            filtering you will have to call :meth:`filter_commands` yourself.

        Parameters
        -----------
        group: :class:`Group`
            The group that was requested for help.
        """
        return None

    async def send_command_help(self, command):
        """|coro|

        Handles the implementation of the single command page in the help command.

        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.

        You can override this method to customise the behaviour.

        .. note::

            You can access the invocation context with :attr:`HelpCommand.context`.

        .. admonition:: Showing Help
            :class: helpful

            There are certain attributes and methods that are helpful for a help command
            to show such as the following:

            - :attr:`Command.help`
            - :attr:`Command.brief`
            - :attr:`Command.short_doc`
            - :attr:`Command.description`
            - :meth:`get_command_signature`

            There are more than just these attributes but feel free to play around with
            these to help you get started to get the output that you want.

        Parameters
        -----------
        command: :class:`Command`
            The command that was requested for help.
        """
        return None

    async def prepare_help_command(self, ctx, command=None):
        """|coro|

        A low level method that can be used to prepare the help command
        before it does anything. For example, if you need to prepare
        some state in your subclass before the command does its processing
        then this would be the place to do it.

        The default implementation does nothing.

        .. note::

            This is called *inside* the help command callback body. So all
            the usual rules that happen inside apply here as well.

        Parameters
        -----------
        ctx: :class:`Context`
            The invocation context.
        command: Optional[:class:`str`]
            The argument passed to the help command.
        """
        pass

    async def command_callback(self, ctx, *, command=None):
        """|coro|

        The actual implementation of the help command.

        It is not recommended to override this method and instead change
        the behaviour through the methods that actually get dispatched.

        - :meth:`send_bot_help`
        - :meth:`send_cog_help`
        - :meth:`send_group_help`
        - :meth:`send_command_help`
        - :meth:`get_destination`
        - :meth:`command_not_found`
        - :meth:`subcommand_not_found`
        - :meth:`send_error_message`
        - :meth:`on_help_command_error`
        - :meth:`prepare_help_command`
        """
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        # Check if it's a cog
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        if isinstance(cmd, Group):
            return await self.send_group_help(cmd)
        else:
            return await self.send_command_help(cmd)

class DefaultHelpCommand(HelpCommand):
    """The implementation of the default help command.

    This inherits from :class:`HelpCommand`.

    It extends it with the following attributes.

    Attributes
    ------------
    width: :class:`int`
        The maximum number of characters that fit in a line.
        Defaults to 80.
    sort_commands: :class:`bool`
        Whether to sort the commands in the output alphabetically. Defaults to ``True``.
    dm_help: Optional[:class:`bool`]
        A tribool that indicates if the help command should DM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is DM'd. If ``False``, none of the help
        output is DM'd. If ``None``, then the bot will only DM when the help
        message becomes too long (dictated by more than :attr:`dm_help_threshold` characters).
        Defaults to ``False``.
    dm_help_threshold: Optional[:class:`int`]
        The number of characters the paginator must accumulate before getting DM'd to the
        user if :attr:`dm_help` is set to ``None``. Defaults to 1000.
    indent: :class:`int`
        How much to indent the commands from a heading. Defaults to ``2``.
    commands_heading: :class:`str`
        The command list's heading string used when the help command is invoked with a category name.
        Useful for i18n. Defaults to ``"Commands:"``
    no_category: :class:`str`
        The string used when there is a command which does not belong to any category(cog).
        Useful for i18n. Defaults to ``"No Category"``
    paginator: :class:`Paginator`
        The paginator used to paginate the help command output.
    """

    def __init__(self, **options):
        self.width = options.pop('width', 80)
        self.indent = options.pop('indent', 2)
        self.sort_commands = options.pop('sort_commands', True)
        self.dm_help = options.pop('dm_help', False)
        self.dm_help_threshold = options.pop('dm_help_threshold', 1000)
        self.commands_heading = options.pop('commands_heading', "Commands:")
        self.no_category = options.pop('no_category', 'No Category')
        self.paginator = options.pop('paginator', None)

        if self.paginator is None:
            self.paginator = Paginator()

        super().__init__(**options)

    def shorten_text(self, text):
        """:class:`str`: Shortens text to fit into the :attr:`width`."""
        if len(text) > self.width:
            return text[:self.width - 3] + '...'
        return text

    def get_ending_note(self):
        """:class:`str`: Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Type {0}{1} command for more info on a command.\n" \
               "You can also type {0}{1} category for more info on a category.".format(self.clean_prefix, command_name)

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Indents a list of commands after the specified heading.

        The formatting is added to the :attr:`paginator`.

        The default implementation is the command name indented by
        :attr:`indent` spaces, padded to ``max_size`` followed by
        the command's :attr:`Command.short_doc` and then shortened
        to fit into the :attr:`width`.

        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands to indent for output.
        heading: :class:`str`
            The heading to add to the output. This is only added
            if the list of commands is greater than 0.
        max_size: Optional[:class:`int`]
            The max size to use for the gap between indents.
            If unspecified, calls :meth:`get_max_size` on the
            commands parameter.
        """

        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1:<{width}} {2}'.format(self.indent * ' ', name, command.short_doc, width=width)
            self.paginator.add_line(self.shorten_text(entry))

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)

    def add_command_formatting(self, command):
        """A utility function to format the non-indented block of commands and groups.

        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """

        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def get_destination(self):
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx.channel

    async def prepare_help_command(self, ctx, command):
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category}:'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        self.add_indented_commands(filtered, heading=self.commands_heading)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

class MinimalHelpCommand(HelpCommand):
    """An implementation of a help command with minimal output.

    This inherits from :class:`HelpCommand`.

    Attributes
    ------------
    sort_commands: :class:`bool`
        Whether to sort the commands in the output alphabetically. Defaults to ``True``.
    commands_heading: :class:`str`
        The command list's heading string used when the help command is invoked with a category name.
        Useful for i18n. Defaults to ``"Commands"``
    aliases_heading: :class:`str`
        The alias list's heading string used to list the aliases of the command. Useful for i18n.
        Defaults to ``"Aliases:"``.
    dm_help: Optional[:class:`bool`]
        A tribool that indicates if the help command should DM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is DM'd. If ``False``, none of the help
        output is DM'd. If ``None``, then the bot will only DM when the help
        message becomes too long (dictated by more than :attr:`dm_help_threshold` characters).
        Defaults to ``False``.
    dm_help_threshold: Optional[:class:`int`]
        The number of characters the paginator must accumulate before getting DM'd to the
        user if :attr:`dm_help` is set to ``None``. Defaults to 1000.
    no_category: :class:`str`
        The string used when there is a command which does not belong to any category(cog).
        Useful for i18n. Defaults to ``"No Category"``
    paginator: :class:`Paginator`
        The paginator used to paginate the help command output.
    """

    def __init__(self, **options):
        self.sort_commands = options.pop('sort_commands', True)
        self.commands_heading = options.pop('commands_heading', "Commands")
        self.dm_help = options.pop('dm_help', False)
        self.dm_help_threshold = options.pop('dm_help_threshold', 1000)
        self.aliases_heading = options.pop('aliases_heading', "Aliases:")
        self.no_category = options.pop('no_category', 'No Category')
        self.paginator = options.pop('paginator', None)

        if self.paginator is None:
            self.paginator = Paginator(suffix=None, prefix=None)

        super().__init__(**options)

    async def send_pages(self):
        """A helper utility to send the page output from :attr:`paginator` to the destination."""
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(page)

    def get_opening_note(self):
        """Returns help command's opening note. This is mainly useful to override for i18n purposes.

        The default implementation returns ::

            Use `{prefix}{command_name} [command]` for more info on a command.
            You can also use `{prefix}{command_name} [category]` for more info on a category.

        Returns
        -------
        :class:`str`
            The help command opening note.
        """
        command_name = self.invoked_with
        return "Use `{0}{1} [command]` for more info on a command.\n" \
               "You can also use `{0}{1} [category]` for more info on a category.".format(self.clean_prefix, command_name)

    def get_command_signature(self, command):
        return '%s%s %s' % (self.clean_prefix, command.qualified_name, command.signature)

    def get_ending_note(self):
        """Return the help command's ending note. This is mainly useful to override for i18n purposes.

        The default implementation does nothing.

        Returns
        -------
        :class:`str`
            The help command ending note.
        """
        return None

    def add_bot_commands_formatting(self, commands, heading):
        """Adds the minified bot heading with commands to the output.

        The formatting should be added to the :attr:`paginator`.

        The default implementation is a bold underline heading followed
        by commands separated by an EN SPACE (U+2002) in the next line.

        Parameters
        -----------
        commands: Sequence[:class:`Command`]
            A list of commands that belong to the heading.
        heading: :class:`str`
            The heading to add to the line.
        """
        if commands:
            # U+2002 Middle Dot
            joined = '\u2002'.join(c.name for c in commands)
            self.paginator.add_line('__**%s**__' % heading)
            self.paginator.add_line(joined)

    def add_subcommand_formatting(self, command):
        """Adds formatting information on a subcommand.

        The formatting should be added to the :attr:`paginator`.

        The default implementation is the prefix and the :attr:`Command.qualified_name`
        optionally followed by an En dash and the command's :attr:`Command.short_doc`.

        Parameters
        -----------
        command: :class:`Command`
            The command to show information of.
        """
        fmt = '{0}{1} \N{EN DASH} {2}' if command.short_doc else '{0}{1}'
        self.paginator.add_line(fmt.format(self.clean_prefix, command.qualified_name, command.short_doc))

    def add_aliases_formatting(self, aliases):
        """Adds the formatting information on a command's aliases.

        The formatting should be added to the :attr:`paginator`.

        The default implementation is the :attr:`aliases_heading` bolded
        followed by a comma separated list of aliases.

        This is not called if there are no aliases to format.

        Parameters
        -----------
        aliases: Sequence[:class:`str`]
            A list of aliases to format.
        """
        self.paginator.add_line('**%s** %s' % (self.aliases_heading, ', '.join(aliases)), empty=True)

    def add_command_formatting(self, command):
        """A utility function to format commands and groups.

        Parameters
        ------------
        command: :class:`Command`
            The command to format.
        """

        if command.description:
            self.paginator.add_line(command.description, empty=True)

        signature = self.get_command_signature(command)
        if command.aliases:
            self.paginator.add_line(signature)
            self.add_aliases_formatting(command.aliases)
        else:
            self.paginator.add_line(signature, empty=True)

        if command.help:
            try:
                self.paginator.add_line(command.help, empty=True)
            except RuntimeError:
                for line in command.help.splitlines():
                    self.paginator.add_line(line)
                self.paginator.add_line()

    def get_destination(self):
        ctx = self.context
        if self.dm_help is True:
            return ctx.author
        elif self.dm_help is None and len(self.paginator) > self.dm_help_threshold:
            return ctx.author
        else:
            return ctx.channel

    async def prepare_help_command(self, ctx, command):
        self.paginator.clear()
        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        no_category = '\u200b{0.no_category}'.format(self)
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_bot_commands_formatting(commands, category)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands, sort=self.sort_commands)
        if filtered:
            note = self.get_opening_note()
            if note:
                self.paginator.add_line(note, empty=True)

            self.paginator.add_line('**%s**' % self.commands_heading)
            for command in filtered:
                self.add_subcommand_formatting(command)

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        self.add_command_formatting(command)
        self.paginator.close_page()
        await self.send_pages()
