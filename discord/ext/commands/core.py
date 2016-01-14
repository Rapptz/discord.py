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
import inspect
import re
import discord
import functools

from .errors import *
from .view import quoted_word

__all__ = [ 'Command', 'Group', 'GroupMixin', 'command', 'group',
            'has_role', 'has_permissions', 'has_any_role', 'check' ]

def inject_context(ctx, coro):
    @functools.wraps(coro)
    @asyncio.coroutine
    def wrapped(*args, **kwargs):
        _internal_channel = ctx.message.channel
        _internal_author = ctx.message.author

        ret = yield from coro(*args, **kwargs)
        return ret
    return wrapped

def _convert_to_bool(argument):
    lowered = argument.lower()
    if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
        return True
    elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
        return False
    else:
        raise BadArgument(lowered + ' is not a recognised boolean option')

class Command:
    """A class that implements the protocol for a bot text command.

    These are not created manually, instead they are created via the
    decorator or functional interface.

    Attributes
    -----------
    name : str
        The name of the command.
    callback : coroutine
        The coroutine that is executed when the command is called.
    help : str
        The long help text for the command.
    brief : str
        The short help text for the command. If this is not specified
        then the first line of the long help text is used instead.
    aliases : list
        The list of aliases the command can be invoked under.
    pass_context : bool
        A boolean that indicates that the current :class:`Context` should
        be passed as the **first parameter**. Defaults to `False`.
    enabled : bool
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`DisabledCommand` is raised to the :func:`on_command_error`
        event. Defaults to ``True``.
    parent : Optional[command]
        The parent command that this command belongs to. ``None`` is there
        isn't one.
    checks
        A list of predicates that verifies if the command could be executed
        with the given :class:`Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one derived from
        :exc:`CommandError` should be used. Note that if the checks fail then
        :exc:`CheckFailure` exception is raised to the :func:`on_command_error`
        event.
    description : str
        The message prefixed into the default help command.
    hidden : bool
        If ``True``, the default help command does not show this in the
        help output.
    rest_is_raw : bool
        If ``False`` and a keyword-only argument is provided then the keyword
        only argument is stripped and handled as if it was a regular argument
        that handles :exc:`MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If ``True``
        then the keyword-only argument will pass in the rest of the arguments
        in a completely raw matter. Defaults to ``False``.
    """
    def __init__(self, name, callback, **kwargs):
        self.name = name
        self.callback = callback
        self.enabled = kwargs.get('enabled', True)
        self.help = kwargs.get('help')
        self.brief = kwargs.get('brief')
        self.rest_is_raw = kwargs.get('rest_is_raw', False)
        self.aliases = kwargs.get('aliases', [])
        self.pass_context = kwargs.get('pass_context', False)
        self.description = inspect.cleandoc(kwargs.get('description', ''))
        self.hidden = kwargs.get('hidden', False)
        signature = inspect.signature(callback)
        self.params = signature.parameters.copy()
        self.checks = kwargs.get('checks', [])
        self.module = inspect.getmodule(callback)
        self.instance = None
        self.parent = None

    def handle_local_error(self, error, ctx):
        try:
            coro = self.on_error
        except AttributeError:
            return

        injected = inject_context(ctx, coro)
        if self.instance is not None:
            discord.utils.create_task(injected(self.instance, error, ctx), loop=ctx.bot.loop)
        else:
            discord.utils.create_task(injected(error, ctx), loop=ctx.bot.loop)

    def _receive_item(self, message, argument, regex, receiver, generator):
        argument = argument.strip()
        match = re.match(regex, argument)
        result = None
        private = message.channel.is_private
        receiver = getattr(message.server, receiver, ())
        if match is None:
            if not private:
                result = discord.utils.get(receiver, name=argument)
        else:
            iterable = receiver if not private else generator
            result = discord.utils.get(iterable, id=match.group(1))
        return result

    def do_conversion(self, bot, message, converter, argument):
        if converter is bool:
            return _convert_to_bool(argument)

        if converter.__module__.split('.')[0] != 'discord':
            return converter(argument)

        # special handling for discord.py related classes
        if converter is discord.User or converter is discord.Member:
            member = self._receive_item(message, argument, r'<@([0-9]+)>', 'members', bot.get_all_members())
            if member is None:
                raise BadArgument('User/Member not found.')
            return member
        elif converter is discord.Channel:
            channel = self._receive_item(message, argument, r'<#([0-9]+)>', 'channels', bot.get_all_channels())
            if channel is None:
                raise BadArgument('Channel not found.')
            return channel
        elif converter is discord.Colour:
            arg = argument.replace('0x', '').lower()
            try:
                value = int(arg, base=16)
                return discord.Colour(value=value)
            except ValueError:
                method = getattr(discord.Colour, arg, None)
                if method is None or not inspect.ismethod(method):
                    raise BadArgument('Colour passed is invalid.')
                return method()
        elif converter is discord.Role:
            if message.channel.is_private:
                raise NoPrivateMessage()

            role = discord.utils.get(message.server.roles, name=argument)
            if role is None:
                raise BadArgument('Role not found')
            return role
        elif converter is discord.Game:
            return discord.Game(name=argument)
        elif converter is discord.Invite:
            try:
                return bot.get_invite(argument)
            except Exception as e:
                raise BadArgument('Invite is invalid') from e

    def _get_converter(self, param):
        converter = param.annotation
        if converter is param.empty:
            if param.default is not param.empty:
                converter = str if param.default is None else type(param.default)
            else:
                converter = str
        elif not inspect.isclass(type(converter)):
            raise discord.ClientException('Function annotation must be a type')

        return converter

    def transform(self, ctx, param):
        required = param.default is param.empty
        converter = self._get_converter(param)
        consume_rest_is_special = param.kind == param.KEYWORD_ONLY and not self.rest_is_raw
        view = ctx.view
        view.skip_ws()

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise StopIteration() # break the loop
            if required:
                raise MissingRequiredArgument('{0.name} is a required argument that is missing.'.format(param))
            return param.default

        if consume_rest_is_special:
            argument = view.read_rest().strip()
        else:
            argument = quoted_word(view)

        try:
            return self.do_conversion(ctx.bot, ctx.message, converter, argument)
        except CommandError as e:
            raise e
        except Exception as e:
            raise BadArgument('Converting to "{0.__name__}" failed.'.format(converter)) from e

    @property
    def clean_params(self):
        """Retrieves the parameter OrderedDict without the context or self parameters.

        Useful for inspecting signature.
        """
        result = self.params.copy()
        if self.instance is not None:
            # first parameter is self
            result.popitem(last=False)

        if self.pass_context:
            # first/second parameter is context
            result.popitem(last=False)

        return result


    def _parse_arguments(self, ctx):
        try:
            ctx.args = [] if self.instance is None else [self.instance]
            ctx.kwargs = {}
            args = ctx.args
            kwargs = ctx.kwargs

            first = True
            view = ctx.view
            iterator = iter(self.params.items())

            if self.instance is not None:
                # we have 'self' as the first parameter so just advance
                # the iterator and resume parsing
                try:
                    next(iterator)
                except StopIteration:
                    fmt = 'Callback for {0.name} command is missing "self" parameter.'
                    raise discord.ClientException(fmt.format(self))

            for name, param in iterator:
                if first and self.pass_context:
                    args.append(ctx)
                    first = False
                    continue

                if param.kind == param.POSITIONAL_OR_KEYWORD:
                    args.append(self.transform(ctx, param))
                elif param.kind == param.KEYWORD_ONLY:
                    # kwarg only param denotes "consume rest" semantics
                    if self.rest_is_raw:
                        converter = self._get_converter(param)
                        argument = view.read_rest()
                        kwargs[name] = self.do_conversion(ctx.bot, ctx.message, converter, argument)
                    else:
                        kwargs[name] = self.transform(ctx, param)
                    break
                elif param.kind == param.VAR_POSITIONAL:
                    while not view.eof:
                        try:
                            args.append(self.transform(ctx, param))
                        except StopIteration:
                            break
        except CommandError as e:
            self.handle_local_error(e, ctx)
            ctx.bot.dispatch('command_error', e, ctx)
            return False
        return True

    def _verify_checks(self, ctx):
        try:
            if not self.enabled:
                raise DisabledCommand('{0.name} command is disabled'.format(self))
            if not self.can_run(ctx):
                raise CheckFailure('The check functions for command {0.name} failed.'.format(self))
        except CommandError as exc:
            self.handle_local_error(exc, ctx)
            ctx.bot.dispatch('command_error', exc, ctx)
            return False

        return True

    @asyncio.coroutine
    def invoke(self, ctx):
        if not self._verify_checks(ctx):
            return

        if self._parse_arguments(ctx):
            injected = inject_context(ctx, self.callback)
            yield from injected(*ctx.args, **ctx.kwargs)

    def error(self, coro):
        """A decorator that registers a coroutine as a local error handler.

        A local error handler is an :func:`on_command_error` event limited to
        a single command. However, the :func:`on_command_error` is still
        invoked afterwards as the catch-all.

        Parameters
        -----------
        coro
            The coroutine to register as the local error handler.

        Raises
        -------
        discord.ClientException
            The coroutine is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise discord.ClientException('The error handler must be a coroutine.')

        self.on_error = coro
        return coro

    @property
    def cog_name(self):
        """The name of the cog this command belongs to. None otherwise."""
        return type(self.instance).__name__ if self.instance is not None else None

    @property
    def short_doc(self):
        """Gets the "short" documentation of a command.

        By default, this is the :attr:`brief` attribute.
        If that lookup leads to an empty string then the first line of the
        :attr:`help` attribute is used instead.
        """
        if self.brief:
            return self.brief
        if self.help:
            return self.help.split('\n', 1)[0]
        return ''

    def can_run(self, context):
        """Checks if the command can be executed by checking all the predicates
        inside the :attr:`checks` attribute.

        Parameters
        -----------
        context : :class:`Context`
            The context of the command currently being invoked.

        Returns
        --------
        bool
            A boolean indicating if the command can be invoked.
        """

        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True
        return all(predicate(context) for predicate in predicates)

class GroupMixin:
    """A mixin that implements common functionality for classes that behave
    similar to :class:`Group` and are allowed to register commands.

    Attributes
    -----------
    commands : dict
        A mapping of command name to :class:`Command` or superclass
        objects.
    """
    def __init__(self, **kwargs):
        self.commands = {}
        super().__init__(**kwargs)

    def recursively_remove_all_commands(self):
        for command in self.commands.copy().values():
            if isinstance(command, GroupMixin):
                command.recursively_remove_all_commands()
            self.remove_command(command.name)

    def add_command(self, command):
        """Adds a :class:`Command` or its superclasses into the internal list
        of commands.

        This is usually not called, instead the :meth:`command` or
        :meth:`group` shortcut decorators are used instead.

        Parameters
        -----------
        command
            The command to add.

        Raises
        -------
        discord.ClientException
            If the command is already registered.
        TypeError
            If the command passed is not a subclass of :class:`Command`.
        """

        if not isinstance(command, Command):
            raise TypeError('The command passed must be a subclass of Command')

        if isinstance(self, Command):
            command.parent = self

        if command.name in self.commands:
            raise discord.ClientException('Command {0.name} is already registered.'.format(command))

        self.commands[command.name] = command
        for alias in command.aliases:
            if alias in self.commands:
                raise discord.ClientException('The alias {} is already an existing command or alias.'.format(alias))
            self.commands[alias] = command

    def remove_command(self, name):
        """Remove a :class:`Command` or subclasses from the internal list
        of commands.

        This could also be used as a way to remove aliases.

        Parameters
        -----------
        name : str
            The name of the command to remove.

        Returns
        --------
        Command or subclass
            The command that was removed. If the name is not valid then
            `None` is returned instead.
        """
        command = self.commands.pop(name, None)
        if name in command.aliases:
            # we're removing an alias so we don't want to remove the rest
            return command

        # we're not removing the alias so let's delete the rest of them.
        for alias in command.aliases:
            self.commands.pop(alias, None)
        return command

    def get_command(self, name):
        """Get a :class:`Command` or subclasses from the internal list
        of commands.

        This could also be used as a way to get aliases.

        Parameters
        -----------
        name : str
            The name of the command to get.

        Returns
        --------
        Command or subclass
            The command that was requested. If not found, returns ``None``.
        """
        return self.commands.get(name, None)

    def command(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`command` and adds it to
        the internal command list via :meth:`add_command`.
        """
        def decorator(func):
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`group` and adds it to
        the internal command list via :meth:`add_command`.
        """
        def decorator(func):
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

class Group(GroupMixin, Command):
    """A class that implements a grouping protocol for commands to be
    executed as subcommands.

    This class is a subclass of :class:`Command` and thus all options
    valid in :class:`Command` are valid in here as well.

    Attributes
    -----------
    invoke_without_command : bool
        Indicates if the group callback should begin parsing and
        invocation only if no subcommand was found. Useful for
        making it an error handling function to tell the user that
        no subcommand was found or to have different functionality
        in case no subcommand was found. If this is ``False``, then
        the group callback will always be invoked first. This means
        that the checks and the parsing dictated by its parameters
        will be executed. Defaults to ``False``.
    """
    def __init__(self, **attrs):
        self.invoke_without_command = attrs.pop('invoke_without_command', False)
        super().__init__(**attrs)

    @asyncio.coroutine
    def invoke(self, ctx):
        early_invoke = not self.invoke_without_command
        if early_invoke:
            valid = self._verify_checks(ctx) and self._parse_arguments(ctx)
            if not valid:
                return

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            if trigger in self.commands:
                ctx.invoked_subcommand = self.commands[trigger]

        if early_invoke:
            injected = inject_context(ctx, self.callback)
            yield from injected(*ctx.args, **ctx.kwargs)

        if ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            yield from ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            valid = self._verify_checks(ctx) and self._parse_arguments(ctx)
            if not valid:
                return
            injected = inject_context(ctx, self.callback)
            yield from injected(*ctx.args, **ctx.kwargs)

# Decorators

def command(name=None, cls=None, **attrs):
    """A decorator that transforms a function into a :class:`Command`
    or if called with :func:`group`, :class:`Group`.

    By default the ``help`` attribute is received automatically from the
    docstring of the function and is cleaned up with the use of
    ``inspect.cleandoc``. If the docstring is ``bytes``, then it is decoded
    into ``str`` using utf-8 encoding.

    All checks added using the :func:`check` & co. decorators are added into
    the function. There is no way to supply your own checks through this
    decorator.

    Parameters
    -----------
    name : str
        The name to create the command with. By default this uses the
        function named unchanged.
    cls
        The class to construct with. By default this is :class:`Command`.
        You usually do not change this.
    attrs
        Keyword arguments to pass into the construction of the class denoted
        by ``cls``.

    Raises
    -------
    TypeError
        If the function is not a coroutine or is already a command.
    """
    if cls is None:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Callback must be a coroutine.')

        try:
            checks = func.__commands_checks__
            checks.reverse()
            del func.__commands_checks__
        except AttributeError:
            checks = []

        help_doc = attrs.get('help')
        if help_doc is not None:
            help_doc = inspect.cleandoc(help_doc)
        else:
            help_doc = inspect.getdoc(func)
            if isinstance(help_doc, bytes):
                help_doc = help_doc.decode('utf-8')

        attrs['help'] = help_doc
        fname = name or func.__name__.lower()
        return cls(name=fname, callback=func, checks=checks, **attrs)

    return decorator

def group(name=None, **attrs):
    """A decorator that transforms a function into a :class:`Group`.

    This is similar to the :func:`command` decorator but creates a
    :class:`Group` instead of a :class:`Command`.
    """
    return command(name=name, cls=Group, **attrs)

def check(predicate):
    """A decorator that adds a check to the :class:`Command` or its
    subclasses. These checks could be accessed via :attr:`Command.checks`.

    These checks should be predicates that take in a single parameter taking
    a :class:`Context`. If the check returns a ``False``\-like value then
    during invocation a :exc:`CheckFailure` exception is raised and sent to
    the :func:`on_command_error` event.

    If an exception should be thrown in the predicate then it should be a
    subclass of :exc:`CommandError`. Any exception not subclassed from it
    will be propagated while those subclassed will be sent to
    :func:`on_command_error`.

    Parameters
    -----------
    predicate
        The predicate to check if the command should be invoked.

    Examples
    ---------

    Creating a basic check to see if the command invoker is you.

    .. code-block:: python

        def check_if_it_is_me(ctx):
            return ctx.message.author.id == 'my-user-id'

        @bot.command()
        @commands.check(check_if_it_is_me)
        async def only_for_me():
            await bot.say('I know you!')

    Transforming common checks into its own decorator:

    .. code-block:: python

        def is_me():
            def predicate(ctx):
                return ctx.message.author.id == 'my-user-id'
            return commands.check(predicate)

        @bot.command()
        @is_me()
        async def only_me():
            await bot.say('Only you!')

    """

    def decorator(func):
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func
    return decorator

def has_role(name):
    """A :func:`check` that is added that checks if the member invoking the
    command has the role specified via the name specified.

    The name is case sensitive and must be exact. No normalisation is done in
    the input.

    If the message is invoked in a private message context then the check will
    return ``False``.

    Parameters
    -----------
    name : str
        The name of the role to check.
    """

    def predicate(ctx):
        msg = ctx.message
        ch = msg.channel
        if ch.is_private:
            return False

        role = discord.utils.get(msg.author.roles, name=name)
        return role is not None

    return check(predicate)

def has_any_role(*names):
    """A :func:`check` that is added that checks if the member invoking the
    command has **any** of the roles specified. This means that if they have
    one out of the three roles specified, then this check will return `True`.

    Similar to :func:`has_role`\, the names passed in must be exact.

    Parameters
    -----------
    names
        An argument list of names to check that the member has roles wise.

    Example
    --------

    .. code-block:: python

        @bot.command()
        @commands.has_any_role('Library Devs', 'Moderators')
        async def cool():
            await bot.say('You are cool indeed')
    """
    def predicate(ctx):
        msg = ctx.message
        ch = msg.channel
        if ch.is_private:
            return False

        getter = functools.partial(discord.utils.get, msg.author.roles)
        return any(getter(name=name) is not None for name in names)
    return check(predicate)

def has_permissions(**perms):
    """A :func:`check` that is added that checks if the member has any of
    the permissions necessary.

    The permissions passed in must be exactly like the properties shown under
    :class:`discord.Permissions`.

    Parameters
    ------------
    perms
        An argument list of permissions to check for.

    Example
    ---------

    .. code-block:: python

        @bot.command()
        @commands.has_permissions(manage_messages=True)
        async def test():
            await bot.say('You can manage messages.')

    """
    def predicate(ctx):
        msg = ctx.message
        ch = msg.channel
        me = msg.server.me if not ch.is_private else ctx.bot.user
        permissions = ch.permissions_for(me)
        return all(getattr(permissions, perm, None) == value for perm, value in perms.items())

    return check(predicate)
