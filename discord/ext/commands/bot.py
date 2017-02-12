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
import discord
import inspect
import importlib
import sys
import traceback
import re

from .core import GroupMixin, Command, command
from .view import StringView
from .context import Context
from .errors import CommandNotFound, CommandError
from .formatter import HelpFormatter

def when_mentioned(bot, msg):
    """A callable that implements a command prefix equivalent
    to being mentioned, e.g. ``@bot ``."""
    guild = msg.guild
    if guild is not None:
        return '{0.me.mention} '.format(guild)
    return '{0.user.mention} '.format(bot)

def when_mentioned_or(*prefixes):
    """A callable that implements when mentioned or other prefixes provided.

    Example
    --------

    .. code-block:: python

        bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

    See Also
    ----------
    :func:`when_mentioned`
    """
    def inner(bot, msg):
        r = list(prefixes)
        r.append(when_mentioned(bot, msg))
        return r

    return inner

_mentions_transforms = {
    '@everyone': '@\u200beveryone',
    '@here': '@\u200bhere'
}

_mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

@asyncio.coroutine
def _default_help_command(ctx, *commands : str):
    """Shows this message."""
    bot = ctx.bot
    destination = ctx.message.author if bot.pm_help else ctx.message.channel

    def repl(obj):
        return _mentions_transforms.get(obj.group(0), '')

    # help by itself just lists our own commands.
    if len(commands) == 0:
        pages = yield from bot.formatter.format_help_for(ctx, bot)
    elif len(commands) == 1:
        # try to see if it is a cog name
        name = _mention_pattern.sub(repl, commands[0])
        command = None
        if name in bot.cogs:
            command = bot.cogs[name]
        else:
            command = bot.commands.get(name)
            if command is None:
                yield from destination.send(bot.command_not_found.format(name))
                return

        pages = yield from bot.formatter.format_help_for(ctx, command)
    else:
        name = _mention_pattern.sub(repl, commands[0])
        command = bot.commands.get(name)
        if command is None:
            yield from destination.send(bot.command_not_found.format(name))
            return

        for key in commands[1:]:
            try:
                key = _mention_pattern.sub(repl, key)
                command = command.commands.get(key)
                if command is None:
                    yield from destination.send(bot.command_not_found.format(key))
                    return
            except AttributeError:
                yield from destination.send(bot.command_has_no_subcommands.format(command, key))
                return

        pages = yield from bot.formatter.format_help_for(ctx, command)

    if bot.pm_help is None:
        characters = sum(map(lambda l: len(l), pages))
        # modify destination based on length of pages.
        if characters > 1000:
            destination = ctx.message.author

    for page in pages:
        yield from destination.send(page)

class BotBase(GroupMixin):
    def __init__(self, command_prefix, formatter=None, description=None, pm_help=False, **options):
        super().__init__(**options)
        self.command_prefix = command_prefix
        self.extra_events = {}
        self.cogs = {}
        self.extensions = {}
        self._checks = []
        self._before_invoke = None
        self._after_invoke = None
        self.description = inspect.cleandoc(description) if description else ''
        self.pm_help = pm_help
        self.command_not_found = options.pop('command_not_found', 'No command called "{}" found.')
        self.command_has_no_subcommands = options.pop('command_has_no_subcommands', 'Command {0.name} has no subcommands.')

        if options.pop('self_bot', False):
            self._skip_check = lambda x, y: x != y
        else:
            self._skip_check = lambda x, y: x == y

        self.help_attrs = options.pop('help_attrs', {})
        self.help_attrs['pass_context'] = True

        if 'name' not in self.help_attrs:
            self.help_attrs['name'] = 'help'

        if formatter is not None:
            if not isinstance(formatter, HelpFormatter):
                raise discord.ClientException('Formatter must be a subclass of HelpFormatter')
            self.formatter = formatter
        else:
            self.formatter = HelpFormatter()

        # pay no mind to this ugliness.
        self.command(**self.help_attrs)(_default_help_command)

    # internal helpers

    def dispatch(self, event_name, *args, **kwargs):
        super().dispatch(event_name, *args, **kwargs)
        ev = 'on_' + event_name
        for event in self.extra_events.get(ev, []):
            coro = self._run_event(event, event_name, *args, **kwargs)
            discord.compat.create_task(coro, loop=self.loop)

    @asyncio.coroutine
    def close(self):
        for extension in tuple(self.extensions):
            try:
                self.unload_extension(extension)
            except:
                pass

        for cog in tuple(self.cogs):
            try:
                self.remove_cog(cog)
            except:
                pass

        yield from super().close()

    @asyncio.coroutine
    def on_command_error(self, exception, context):
        """|coro|

        The default command error handler provided by the bot.

        By default this prints to ``sys.stderr`` however it could be
        overridden to have a different implementation.

        This only fires if you do not specify any listeners for command error.
        """
        if self.extra_events.get('on_command_error', None):
            return

        if hasattr(context.command, "on_error"):
            return

        print('Ignoring exception in command {}'.format(context.command), file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    # global check registration

    def check(self, func):
        """A decorator that adds a global check to the bot.

        A global check is similar to a :func:`check` that is applied
        on a per command basis except it is run before any command checks
        have been verified and applies to every command the bot has.

        .. info::

            This function can either be a regular function or a coroutine.

        Similar to a command :func:`check`\, this takes a single parameter
        of type :class:`Context` and can only raise exceptions derived from
        :exc:`CommandError`.

        Example
        ---------

        .. code-block:: python

            @bot.check
            def whitelist(ctx):
                return ctx.message.author.id in my_whitelist

        """
        self.add_check(func)
        return func

    def add_check(self, func):
        """Adds a global check to the bot.

        This is the non-decorator interface to :meth:`check`.

        Parameters
        -----------
        func
            The function that was used as a global check.
        """
        self._checks.append(func)

    def remove_check(self, func):
        """Removes a global check from the bot.

        This function is idempotent and will not raise an exception
        if the function is not in the global checks.

        Parameters
        -----------
        func
            The function to remove from the global checks.
        """

        try:
            self._checks.remove(func)
        except ValueError:
            pass

    @asyncio.coroutine
    def can_run(self, ctx):
        if len(self._checks) == 0:
            return True

        return (yield from discord.utils.async_all(f(ctx) for f in self._checks))

    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke hook.

        A pre-invoke hook is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This pre-invoke hook takes a sole parameter, a :class:`Context`.

        .. note::

            The :meth:`before_invoke` and :meth:`after_invoke` hooks are
            only called if all checks and argument parsing procedures pass
            without error. If any check or argument parsing procedures fail
            then the hooks are not called.

        Parameters
        -----------
        coro
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        discord.ClientException
            The coroutine is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise discord.ClientException('The error handler must be a coroutine.')

        self._before_invoke = coro
        return coro

    def after_invoke(self, coro):
        """A decorator that registers a coroutine as a post-invoke hook.

        A post-invoke hook is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke hook takes a sole parameter, a :class:`Context`.

        .. note::

            Similar to :meth:`before_invoke`\, this is not called unless
            checks and argument parsing procedures succeed. This hook is,
            however, **always** called regardless of the internal command
            callback raising an error (i.e. :exc:`CommandInvokeError`\).
            This makes it ideal for clean-up scenarios.

        Parameters
        -----------
        coro
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        discord.ClientException
            The coroutine is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise discord.ClientException('The error handler must be a coroutine.')

        self._after_invoke = coro
        return coro

    # listener registration

    def add_listener(self, func, name=None):
        """The non decorator alternative to :meth:`listen`.

        Parameters
        -----------
        func : coroutine
            The extra event to listen to.
        name : Optional[str]
            The name of the command to use. Defaults to ``func.__name__``.

        Example
        --------

        .. code-block:: python

            async def on_ready(): pass
            async def my_message(message): pass

            bot.add_listener(on_ready)
            bot.add_listener(my_message, 'on_message')

        """
        name = func.__name__ if name is None else name

        if not asyncio.iscoroutinefunction(func):
            raise discord.ClientException('Listeners must be coroutines')

        if name in self.extra_events:
            self.extra_events[name].append(func)
        else:
            self.extra_events[name] = [func]

    def remove_listener(self, func, name=None):
        """Removes a listener from the pool of listeners.

        Parameters
        -----------
        func
            The function that was used as a listener to remove.
        name
            The name of the event we want to remove. Defaults to
            ``func.__name__``.
        """

        name = func.__name__ if name is None else name

        if name in self.extra_events:
            try:
                self.extra_events[name].remove(func)
            except ValueError:
                pass

    def listen(self, name=None):
        """A decorator that registers another function as an external
        event listener. Basically this allows you to listen to multiple
        events from different places e.g. such as :func:`discord.on_ready`

        The functions being listened to must be a coroutine.

        Example
        --------

        .. code-block:: python

            @bot.listen()
            async def on_message(message):
                print('one')

            # in some other file...

            @bot.listen('on_message')
            async def my_message(message):
                print('two')

        Would print one and two in an unspecified order.

        Raises
        -------
        discord.ClientException
            The function being listened to is not a coroutine.
        """

        def decorator(func):
            self.add_listener(func, name)
            return func

        return decorator

    # cogs

    def add_cog(self, cog):
        """Adds a "cog" to the bot.

        A cog is a class that has its own event listeners and commands.

        They are meant as a way to organize multiple relevant commands
        into a singular class that shares some state or no state at all.

        The cog can also have a ``__global_check`` member function that allows
        you to define a global check. See :meth:`check` for more info.

        More information will be documented soon.

        Parameters
        -----------
        cog
            The cog to register to the bot.
        """

        self.cogs[type(cog).__name__] = cog

        try:
            check = getattr(cog, '_{.__class__.__name__}__global_check'.format(cog))
        except AttributeError:
            pass
        else:
            self.add_check(check)

        members = inspect.getmembers(cog)
        for name, member in members:
            # register commands the cog has
            if isinstance(member, Command):
                if member.parent is None:
                    self.add_command(member)
                continue

            # register event listeners the cog has
            if name.startswith('on_'):
                self.add_listener(member)

    def get_cog(self, name):
        """Gets the cog instance requested.

        If the cog is not found, ``None`` is returned instead.

        Parameters
        -----------
        name : str
            The name of the cog you are requesting.
        """
        return self.cogs.get(name)

    def remove_cog(self, name):
        """Removes a cog from the bot.

        All registered commands and event listeners that the
        cog has registered will be removed as well.

        If no cog is found then ``None`` is returned, otherwise
        the cog instance that is being removed is returned.

        If the cog defines a special member function named ``__unload``
        then it is called when removal has completed. This function
        **cannot** be a coroutine. It must be a regular function.

        Parameters
        -----------
        name : str
            The name of the cog to remove.
        """

        cog = self.cogs.pop(name, None)
        if cog is None:
            return cog

        members = inspect.getmembers(cog)
        for name, member in members:
            # remove commands the cog has
            if isinstance(member, Command):
                if member.parent is None:
                    self.remove_command(member.name)
                continue

            # remove event listeners the cog has
            if name.startswith('on_'):
                self.remove_listener(member)

        try:
            check = getattr(cog, '_{0.__class__.__name__}__global_check'.format(cog))
        except AttributeError:
            pass
        else:
            self.remove_check(check)

        unloader_name = '_{0.__class__.__name__}__unload'.format(cog)
        try:
            unloader = getattr(cog, unloader_name)
        except AttributeError:
            pass
        else:
            unloader()

        del cog

    # extensions

    def load_extension(self, name):
        if name in self.extensions:
            return

        lib = importlib.import_module(name)
        if not hasattr(lib, 'setup'):
            del lib
            del sys.modules[name]
            raise discord.ClientException('extension does not have a setup function')

        lib.setup(self)
        self.extensions[name] = lib

    def unload_extension(self, name):
        lib = self.extensions.get(name)
        if lib is None:
            return

        # find all references to the module

        # remove the cogs registered from the module
        for cogname, cog in self.cogs.copy().items():
            if inspect.getmodule(cog) is lib:
                self.remove_cog(cogname)

        # first remove all the commands from the module
        for command in self.commands.copy().values():
            if command.module is lib:
                command.module = None
                if isinstance(command, GroupMixin):
                    command.recursively_remove_all_commands()
                self.remove_command(command.name)

        # then remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = []
            for index, event in enumerate(event_list):
                if inspect.getmodule(event) is lib:
                    remove.append(index)

            for index in reversed(remove):
                del event_list[index]

        try:
            func = getattr(lib, 'teardown')
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except:
                pass
        finally:
            # finally remove the import..
            del lib
            del self.extensions[name]
            del sys.modules[name]

    # command processing

    @asyncio.coroutine
    def get_prefix(self, message):
        """|coro|

        Retrieves the prefix the bot is listening to
        with the message as a context.

        Parameters
        -----------
        message: :class:`discord.Message`
            The message context to get the prefix of.

        Returns
        --------
        Union[List[str], str]
            A list of prefixes or a single prefix that the bot is
            listening for.
        """
        prefix = self.command_prefix
        if callable(prefix):
            ret = prefix(self, message)
            if asyncio.iscoroutine(ret):
                ret = yield from ret
            return ret
        else:
            return prefix

    @asyncio.coroutine
    def get_context(self, message, *, cls=Context):
        """|coro|

        Returns the invocation context from the message.

        This is a more low-level counter-part for :meth:`process_message`
        to allow users more fine grained control over the processing.

        The returned context is not guaranteed to be a valid invocation
        context, :attr:`Context.valid` must be checked to make sure it is.
        If the context is not valid then it is not a valid candidate to be
        invoked under :meth:`invoke`.

        Parameters
        -----------
        message: :class:`discord.Message`
            The message to get the invocation context from.
        cls: type
            The factory class that will be used to create the context.
            By default, this is :class:`Context`. Should a custom
            class be provided, it must be similar enough to :class:`Context`\'s
            interface.

        Returns
        --------
        :class:`Context`
            The invocation context. The type of this can change via the
            ``cls`` parameter.
        """

        view = StringView(message.content)
        ctx = cls(prefix=None, view=view, bot=self, message=message)

        if self._skip_check(message.author.id, self.user.id):
            return ctx

        prefix = yield from self.get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return ctx
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return ctx

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = self.commands.get(invoker)
        return ctx

    @asyncio.coroutine
    def invoke(self, ctx):
        """|coro|

        Invokes the command given under the invocation context and
        handles all the internal event dispatch mechanisms.

        Parameters
        -----------
        ctx: :class:`Context`
            The invocation context to invoke.
        """
        if ctx.command is not None:
            self.dispatch('command', ctx)
            try:
                yield from ctx.command.invoke(ctx)
            except CommandError as e:
                yield from ctx.command.dispatch_error(e, ctx)
            else:
                ctx.command_failed = False
                self.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc = CommandNotFound('Command "{}" is not found'.format(ctx.invoked_with))
            self.dispatch('command_error', exc, ctx)

    @asyncio.coroutine
    def process_commands(self, message):
        """|coro|

        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.

        By default, this coroutine is called inside the :func:`on_message`
        event. If you choose to override the :func:`on_message` event, then
        you should invoke this coroutine as well.

        This is built using other low level tools, and is equivalent to a
        call to :meth:`get_context` followed by a call to :meth:`invoke`.

        Parameters
        -----------
        message : discord.Message
            The message to process commands for.
        """
        ctx = yield from self.get_context(message)
        yield from self.invoke(ctx)

    @asyncio.coroutine
    def on_message(self, message):
        yield from self.process_commands(message)

class Bot(BotBase, discord.Client):
    """Represents a discord bot.

    This class is a subclass of :class:`discord.Client` and as a result
    anything that you can do with a :class:`discord.Client` you can do with
    this bot.

    This class also subclasses :class:`GroupMixin` to provide the functionality
    to manage commands.

    Attributes
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in the bot
        as its first parameter and :class:`discord.Message` as its second
        parameter and returns the prefix. This is to facilitate "dynamic"
        command prefixes. This callable can be either a regular function or
        a coroutine.

        The command prefix could also be a list or a tuple indicating that
        multiple checks for the prefix should be used and the first one to
        match will be the invocation prefix. You can get this prefix via
        :attr:`Context.prefix`.
    description : str
        The content prefixed into the default help message.
    self_bot : bool
        If ``True``, the bot will only listen to commands invoked by itself rather
        than ignoring itself. If ``False`` (the default) then the bot will ignore
        itself. This cannot be changed once initialised.
    formatter : :class:`HelpFormatter`
        The formatter used to format the help message. By default, it uses a
        the :class:`HelpFormatter`. Check it for more info on how to override it.
        If you want to change the help command completely (add aliases, etc) then
        a call to :meth:`remove_command` with 'help' as the argument would do the
        trick.
    pm_help : Optional[bool]
        A tribool that indicates if the help command should PM the user instead of
        sending it to the channel it received it from. If the boolean is set to
        ``True``, then all help output is PM'd. If ``False``, none of the help
        output is PM'd. If ``None``, then the bot will only PM when the help
        message becomes too long (dictated by more than 1000 characters).
        Defaults to ``False``.
    help_attrs : dict
        A dictionary of options to pass in for the construction of the help command.
        This allows you to change the command behaviour without actually changing
        the implementation of the command. The attributes will be the same as the
        ones passed in the :class:`Command` constructor. Note that ``pass_context``
        will always be set to ``True`` regardless of what you pass in.
    command_not_found : str
        The format string used when the help command is invoked with a command that
        is not found. Useful for i18n. Defaults to ``"No command called {} found."``.
        The only format argument is the name of the command passed.
    command_has_no_subcommands : str
        The format string used when the help command is invoked with requests for a
        subcommand but the command does not have any subcommands. Defaults to
        ``"Command {0.name} has no subcommands."``. The first format argument is the
        :class:`Command` attempted to get a subcommand and the second is the name.
    """
    pass

class AutoShardedBot(BotBase, discord.AutoShardedClient):
    """This is similar to :class:`Bot` except that it is derived from
    :class:`discord.AutoShardedClient` instead.
    """
    pass
