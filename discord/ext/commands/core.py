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
from functools import partial

from .errors import *
from .view import quoted_word

__all__ = [ 'Command', 'Group', 'GroupMixin', 'command', 'group',
            'has_role', 'has_permissions', 'has_any_role', 'check' ]

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
        The short help text for the command.
    aliases : list
        The list of aliases the command can be invoked under.
    pass_context : bool
        A boolean that indicates that the current :class:`Context` should
        be passed as the **first parameter**. Defaults to `False`.
    checks
        A list of predicates that verifies if the command could be executed
        with the given :class:`Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one derived from
        :exc:`CommandError` should be used. Note that if the checks fail then
        :exc:`CheckFailure` exception is raised to the :func:`on_command_error`
        event.
    """
    def __init__(self, name, callback, **kwargs):
        self.name = name
        self.callback = callback
        self.help = kwargs.get('help')
        self.brief = kwargs.get('brief')
        self.aliases = kwargs.get('aliases', [])
        self.pass_context = kwargs.get('pass_context', False)
        signature = inspect.signature(callback)
        self.params = signature.parameters.copy()
        self.checks = kwargs.get('checks', [])

    def _receive_item(self, message, argument, regex, receiver, generator):
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
            except:
                raise BadArgument('Invite is invalid')

    def transform(self, ctx, param):
        required = param.default is param.empty
        converter = param.annotation
        view = ctx.view

        if converter is param.empty:
            if not required:
                converter = str if param.default is None else type(param.default)
            else:
                converter = str
        elif not inspect.isclass(type(converter)):
            raise discord.ClientException('Function annotation must be a type')

        view.skip_ws()

        if view.eof:
            if param.kind == param.VAR_POSITIONAL:
                raise StopIteration() # break the loop
            if required:
                raise MissingRequiredArgument('{0.name} is a required argument that is missing.'.format(param))
            return param.default

        argument = quoted_word(view)

        try:
            return self.do_conversion(ctx.bot, ctx.message, converter, argument)
        except CommandError as e:
            raise e
        except Exception:
            raise BadArgument('Converting to "{0.__name__}" failed.'.format(converter))

    def _parse_arguments(self, ctx):
        try:
            ctx.args = []
            ctx.kwargs = {}
            args = ctx.args
            kwargs = ctx.kwargs

            first = True
            view = ctx.view
            for name, param in self.params.items():
                if first and self.pass_context:
                    args.append(ctx)
                    first = False
                    continue

                if param.kind == param.POSITIONAL_OR_KEYWORD:
                    args.append(self.transform(ctx, param))
                elif param.kind == param.KEYWORD_ONLY:
                    # kwarg only param denotes "consume rest" semantics
                    kwargs[name] = view.read_rest()
                    break
                elif param.kind == param.VAR_POSITIONAL:
                    while not view.eof:
                        try:
                            args.append(self.transform(ctx, param))
                        except StopIteration:
                            break
        except CommandError as e:
            ctx.bot.dispatch('command_error', e, ctx)
            return False
        return True

    def _verify_checks(self, ctx):
        predicates = self.checks
        if predicates:
            try:
                check = all(predicate(ctx) for predicate in predicates)
                if not check:
                    raise CheckFailure('The check functions for command {0.name} failed.'.format(self))
            except CommandError as exc:
                ctx.bot.dispatch('command_error', exc, ctx)
                return False

        return True

    @asyncio.coroutine
    def invoke(self, ctx):
        if not self._verify_checks(ctx):
            return

        if self._parse_arguments(ctx):
            yield from self.callback(*ctx.args, **ctx.kwargs)

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
        return self.commands.pop(name, None)

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
    """
    def __init__(self, **attrs):
        super().__init__(**attrs)

    @asyncio.coroutine
    def invoke(self, ctx):
        if not self._verify_checks(ctx):
            return

        if not self._parse_arguments(ctx):
            return

        view = ctx.view

        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            if trigger in self.commands:
                ctx.invoked_subcommand = self.commands[trigger]

        yield from self.callback(*ctx.args, **ctx.kwargs)

        if ctx.invoked_subcommand:
            yield from ctx.invoked_subcommand.invoke(ctx)

# Decorators

def command(name=None, cls=None, **attrs):
    """A decorator that transforms a function into a :class:`Command`.

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
        Keyword arguments to pass into the construction of :class:`Command`.

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

        getter = partial(discord.utils.get, msg.author.roles)
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
