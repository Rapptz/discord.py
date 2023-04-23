"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

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
from __future__ import annotations

import importlib
import inspect
import os
import pathlib
import sys
import types
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import discord.utils

from . import errors
from .commands import (
    ApplicationCommand,
    ApplicationContext,
    SlashCommandGroup,
    _BaseCommand,
)

__all__ = (
    "CogMeta",
    "Cog",
    "CogMixin",
)

CogT = TypeVar("CogT", bound="Cog")
FuncT = TypeVar("FuncT", bound=Callable[..., Any])

MISSING: Any = discord.utils.MISSING


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(f"{parent}.")


class CogMeta(type):
    """A metaclass for defining a cog.

    Note that you should probably not use this directly. It is exposed
    purely for documentation purposes along with making custom metaclasses to intermix
    with other metaclasses such as the :class:`abc.ABCMeta` metaclass.

    For example, to create an abstract cog mixin class, the following would be done.

    .. code-block:: python3

        import abc

        class CogABCMeta(commands.CogMeta, abc.ABCMeta):
            pass

        class SomeMixin(metaclass=abc.ABCMeta):
            pass

        class SomeCogMixin(SomeMixin, commands.Cog, metaclass=CogABCMeta):
            pass

    .. note::

        When passing an attribute of a metaclass that is documented below, note
        that you must pass it as a keyword-only argument to the class creation
        like the following example:

        .. code-block:: python3

            class MyCog(commands.Cog, name='My Cog'):
                pass

    Attributes
    -----------
    name: :class:`str`
        The cog name. By default, it is the name of the class with no modification.
    description: :class:`str`
        The cog description. By default, it is the cleaned docstring of the class.

        .. versionadded:: 1.6

    command_attrs: :class:`dict`
        A list of attributes to apply to every command inside this cog. The dictionary
        is passed into the :class:`Command` options at ``__init__``.
        If you specify attributes inside the command attribute in the class, it will
        override the one specified inside this attribute. For example:

        .. code-block:: python3

            class MyCog(commands.Cog, command_attrs=dict(hidden=True)):
                @commands.command()
                async def foo(self, ctx):
                    pass # hidden -> True

                @commands.command(hidden=False)
                async def bar(self, ctx):
                    pass # hidden -> False

    guild_ids: Optional[List[:class:`int`]]
        A shortcut to command_attrs, what guild_ids should all application commands have
        in the cog. You can override this by setting guild_ids per command.

        .. versionadded:: 2.0
    """

    __cog_name__: str
    __cog_settings__: Dict[str, Any]
    __cog_commands__: List[ApplicationCommand]
    __cog_listeners__: List[Tuple[str, str]]
    __cog_guild_ids__: List[int]

    def __new__(cls: Type[CogMeta], *args: Any, **kwargs: Any) -> CogMeta:
        name, bases, attrs = args
        attrs["__cog_name__"] = kwargs.pop("name", name)
        attrs["__cog_settings__"] = kwargs.pop("command_attrs", {})
        attrs["__cog_guild_ids__"] = kwargs.pop("guild_ids", [])

        description = kwargs.pop("description", None)
        if description is None:
            description = inspect.cleandoc(attrs.get("__doc__", ""))
        attrs["__cog_description__"] = description

        commands = {}
        listeners = {}
        no_bot_cog = "Commands or listeners must not start with cog_ or bot_ (in method {0.__name__}.{1})"

        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        valid_commands = [
            (c for i, c in j.__dict__.items() if isinstance(c, _BaseCommand)) for j in reversed(new_cls.__mro__)
        ]
        if any(isinstance(i, ApplicationCommand) for i in valid_commands) and any(
            not isinstance(i, _BaseCommand) for i in valid_commands
        ):
            _filter = ApplicationCommand
        else:
            _filter = _BaseCommand

        for base in reversed(new_cls.__mro__):
            for elem, value in base.__dict__.items():
                if elem in commands:
                    del commands[elem]
                if elem in listeners:
                    del listeners[elem]

                try:
                    if getattr(value, "parent") is not None and isinstance(value, ApplicationCommand):
                        # Skip commands if they are a part of a group
                        continue
                except AttributeError:
                    pass

                is_static_method = isinstance(value, staticmethod)
                if is_static_method:
                    value = value.__func__
                if isinstance(value, _filter):
                    if is_static_method:
                        raise TypeError(f"Command in method {base}.{elem!r} must not be staticmethod.")
                    if elem.startswith(("cog_", "bot_")):
                        raise TypeError(no_bot_cog.format(base, elem))
                    commands[elem] = value

                try:
                    # a test to see if this value is a BridgeCommand
                    getattr(value, "add_to")

                    if is_static_method:
                        raise TypeError(f"Command in method {base}.{elem!r} must not be staticmethod.")
                    if elem.startswith(("cog_", "bot_")):
                        raise TypeError(no_bot_cog.format(base, elem))

                    commands[f"ext_{elem}"] = value.get_ext_command()
                    commands[f"application_{elem}"] = value.get_application_command()
                except AttributeError:
                    # we are confident that the value is not a Bridge Command
                    pass

                if inspect.iscoroutinefunction(value):
                    try:
                        getattr(value, "__cog_listener__")
                    except AttributeError:
                        continue
                    else:
                        if elem.startswith(("cog_", "bot_")):
                            raise TypeError(no_bot_cog.format(base, elem))
                        listeners[elem] = value

        new_cls.__cog_commands__ = list(commands.values())

        listeners_as_list = []
        for listener in listeners.values():
            for listener_name in listener.__cog_listener_names__:
                # I use __name__ instead of just storing the value so I can inject
                # the self attribute when the time comes to add them to the bot
                listeners_as_list.append((listener_name, listener.__name__))

        new_cls.__cog_listeners__ = listeners_as_list

        cmd_attrs = new_cls.__cog_settings__

        # Either update the command with the cog provided defaults or copy it.
        # r.e type ignore, type-checker complains about overriding a ClassVar
        new_cls.__cog_commands__ = tuple(c._update_copy(cmd_attrs) for c in new_cls.__cog_commands__)  # type: ignore

        lookup = {cmd.qualified_name: cmd for cmd in new_cls.__cog_commands__}

        # Update the Command instances dynamically as well
        for command in new_cls.__cog_commands__:
            if (
                isinstance(command, ApplicationCommand)
                and command.guild_ids is None
                and len(new_cls.__cog_guild_ids__) != 0
            ):
                command.guild_ids = new_cls.__cog_guild_ids__
            if not isinstance(command, SlashCommandGroup):
                setattr(new_cls, command.callback.__name__, command)
                parent = command.parent
                if parent is not None:
                    # Get the latest parent reference
                    parent = lookup[parent.qualified_name]  # type: ignore

                    # Update our parent's reference to our self
                    parent.remove_command(command.name)  # type: ignore
                    parent.add_command(command)  # type: ignore

        return new_cls

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)

    @classmethod
    def qualified_name(cls) -> str:
        return cls.__cog_name__


def _cog_special_method(func: FuncT) -> FuncT:
    func.__cog_special_method__ = None
    return func


class Cog(metaclass=CogMeta):
    """The base class that all cogs must inherit from.

    A cog is a collection of commands, listeners, and optional state to
    help group commands together. More information on them can be found on
    the :ref:`ext_commands_cogs` page.

    When inheriting from this class, the options shown in :class:`CogMeta`
    are equally valid here.
    """

    __cog_name__: ClassVar[str]
    __cog_settings__: ClassVar[Dict[str, Any]]
    __cog_commands__: ClassVar[List[ApplicationCommand]]
    __cog_listeners__: ClassVar[List[Tuple[str, str]]]
    __cog_guild_ids__: ClassVar[List[int]]

    def __new__(cls: Type[CogT], *args: Any, **kwargs: Any) -> CogT:
        # For issue 426, we need to store a copy of the command objects
        # since we modify them to inject `self` to them.
        # To do this, we need to interfere with the Cog creation process.
        return super().__new__(cls)

    def get_commands(self) -> List[ApplicationCommand]:
        r"""
        Returns
        --------
        List[:class:`.ApplicationCommand`]
            A :class:`list` of :class:`.ApplicationCommand`\s that are
            defined inside this cog.

            .. note::

                This does not include subcommands.
        """
        return [c for c in self.__cog_commands__ if isinstance(c, ApplicationCommand) and c.parent is None]

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the cog's specified name, not the class name."""
        return self.__cog_name__

    @property
    def description(self) -> str:
        """:class:`str`: Returns the cog's description, typically the cleaned docstring."""
        return self.__cog_description__

    @description.setter
    def description(self, description: str) -> None:
        self.__cog_description__ = description

    def walk_commands(self) -> Generator[ApplicationCommand, None, None]:
        """An iterator that recursively walks through this cog's commands and subcommands.

        Yields
        ------
        Union[:class:`.Command`, :class:`.Group`]
            A command or group from the cog.
        """
        for command in self.__cog_commands__:
            if isinstance(command, SlashCommandGroup):
                yield from command.walk_commands()

    def get_listeners(self) -> List[Tuple[str, Callable[..., Any]]]:
        """Returns a :class:`list` of (name, function) listener pairs that are defined in this cog.

        Returns
        --------
        List[Tuple[:class:`str`, :ref:`coroutine <coroutine>`]]
            The listeners defined in this cog.
        """
        return [(name, getattr(self, method_name)) for name, method_name in self.__cog_listeners__]

    @classmethod
    def _get_overridden_method(cls, method: FuncT) -> Optional[FuncT]:
        """Return None if the method is not overridden. Otherwise returns the overridden method."""
        return getattr(getattr(method, "__func__", method), "__cog_special_method__", method)

    @classmethod
    def listener(cls, name: str = MISSING) -> Callable[[FuncT], FuncT]:
        """A decorator that marks a function as a listener.

        This is the cog equivalent of :meth:`.Bot.listen`.

        Parameters
        ------------
        name: :class:`str`
            The name of the event being listened to. If not provided, it
            defaults to the function's name.

        Raises
        --------
        TypeError
            The function is not a coroutine function or a string was not passed as
            the name.
        """

        if name is not MISSING and not isinstance(name, str):
            raise TypeError(f"Cog.listener expected str but received {name.__class__.__name__!r} instead.")

        def decorator(func: FuncT) -> FuncT:
            actual = func
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Listener function must be a coroutine function.")
            actual.__cog_listener__ = True
            to_assign = name or actual.__name__
            try:
                actual.__cog_listener_names__.append(to_assign)
            except AttributeError:
                actual.__cog_listener_names__ = [to_assign]
            # we have to return `func` instead of `actual` because
            # we need the type to be `staticmethod` for the metaclass
            # to pick it up but the metaclass unfurls the function and
            # thus the assignments need to be on the actual function
            return func

        return decorator

    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the cog has an error handler.

        .. versionadded:: 1.7
        """
        return not hasattr(self.cog_command_error.__func__, "__cog_special_method__")

    @_cog_special_method
    def cog_unload(self) -> None:
        """A special method that is called when the cog gets removed.

        This function **cannot** be a coroutine. It must be a regular
        function.

        Subclasses must replace this if they want special unloading behaviour.
        """
        pass

    @_cog_special_method
    def bot_check_once(self, ctx: ApplicationContext) -> bool:
        """A special method that registers as a :meth:`.Bot.check_once`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def bot_check(self, ctx: ApplicationContext) -> bool:
        """A special method that registers as a :meth:`.Bot.check`
        check.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    def cog_check(self, ctx: ApplicationContext) -> bool:
        """A special method that registers as a :func:`~discord.ext.commands.check`
        for every command and subcommand in this cog.

        This function **can** be a coroutine and must take a sole parameter,
        ``ctx``, to represent the :class:`.Context`.
        """
        return True

    @_cog_special_method
    async def cog_command_error(self, ctx: ApplicationContext, error: Exception) -> None:
        """A special method that is called whenever an error
        is dispatched inside this cog.

        This is similar to :func:`.on_command_error` except only applying
        to the commands inside this cog.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context where the error happened.
        error: :class:`ApplicationCommandError`
            The error that happened.
        """
        pass

    @_cog_special_method
    async def cog_before_invoke(self, ctx: ApplicationContext) -> None:
        """A special method that acts as a cog local pre-invoke hook.

        This is similar to :meth:`.Command.before_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    @_cog_special_method
    async def cog_after_invoke(self, ctx: ApplicationContext) -> None:
        """A special method that acts as a cog local post-invoke hook.

        This is similar to :meth:`.Command.after_invoke`.

        This **must** be a coroutine.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context.
        """
        pass

    def _inject(self: CogT, bot) -> CogT:
        cls = self.__class__

        # realistically, the only thing that can cause loading errors
        # is essentially just the command loading, which raises if there are
        # duplicates. When this condition is met, we want to undo all what
        # we've added so far for some form of atomic loading.

        for index, command in enumerate(self.__cog_commands__):
            command._set_cog(self)

            if isinstance(command, ApplicationCommand):
                bot.add_application_command(command)

            elif command.parent is None:
                try:
                    bot.add_command(command)
                except Exception as e:
                    # undo our additions
                    for to_undo in self.__cog_commands__[:index]:
                        if to_undo.parent is None:
                            bot.remove_command(to_undo.name)
                    raise e
        # check if we're overriding the default
        if cls.bot_check is not Cog.bot_check:
            bot.add_check(self.bot_check)

        if cls.bot_check_once is not Cog.bot_check_once:
            bot.add_check(self.bot_check_once, call_once=True)

        # while Bot.add_listener can raise if it's not a coroutine,
        # this precondition is already met by the listener decorator
        # already, thus this should never raise.
        # Outside of, memory errors and the like...
        for name, method_name in self.__cog_listeners__:
            bot.add_listener(getattr(self, method_name), name)

        return self

    def _eject(self, bot) -> None:
        cls = self.__class__

        try:
            for command in self.__cog_commands__:
                if isinstance(command, ApplicationCommand):
                    bot.remove_application_command(command)
                elif command.parent is None:
                    bot.remove_command(command.name)

            for _, method_name in self.__cog_listeners__:
                bot.remove_listener(getattr(self, method_name))

            if cls.bot_check is not Cog.bot_check:
                bot.remove_check(self.bot_check)

            if cls.bot_check_once is not Cog.bot_check_once:
                bot.remove_check(self.bot_check_once, call_once=True)
        finally:
            try:
                self.cog_unload()
            except Exception:
                pass


class CogMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__cogs: Dict[str, Cog] = {}
        self.__extensions: Dict[str, types.ModuleType] = {}

    def add_cog(self, cog: Cog, *, override: bool = False) -> None:
        """Adds a "cog" to the bot.

        A cog is a class that has its own event listeners and commands.

        .. versionchanged:: 2.0

            :exc:`.ClientException` is raised when a cog with the same name
            is already loaded.

        Parameters
        -----------
        cog: :class:`.Cog`
            The cog to register to the bot.
        override: :class:`bool`
            If a previously loaded cog with the same name should be ejected
            instead of raising an error.

            .. versionadded:: 2.0

        Raises
        -------
        TypeError
            The cog does not inherit from :class:`.Cog`.
        ApplicationCommandError
            An error happened during loading.
        ClientException
            A cog with the same name is already loaded.
        """

        if not isinstance(cog, Cog):
            raise TypeError("cogs must derive from Cog")

        cog_name = cog.__cog_name__
        existing = self.__cogs.get(cog_name)

        if existing is not None:
            if not override:
                raise discord.ClientException(f"Cog named {cog_name!r} already loaded")
            self.remove_cog(cog_name)

        cog = cog._inject(self)
        self.__cogs[cog_name] = cog

    def get_cog(self, name: str) -> Optional[Cog]:
        """Gets the cog instance requested.

        If the cog is not found, ``None`` is returned instead.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog you are requesting.
            This is equivalent to the name passed via keyword
            argument in class creation or the class name if unspecified.

        Returns
        --------
        Optional[:class:`Cog`]
            The cog that was requested. If not found, returns ``None``.
        """
        return self.__cogs.get(name)

    def remove_cog(self, name: str) -> Optional[Cog]:
        """Removes a cog from the bot and returns it.

        All registered commands and event listeners that the
        cog has registered will be removed as well.

        If no cog is found then this method has no effect.

        Parameters
        -----------
        name: :class:`str`
            The name of the cog to remove.

        Returns
        -------
        Optional[:class:`.Cog`]
             The cog that was removed. ``None`` if not found.
        """

        cog = self.__cogs.pop(name, None)
        if cog is None:
            return

        if hasattr(self, "_help_command"):
            help_command = self._help_command
            if help_command and help_command.cog is cog:
                help_command.cog = None

        cog._eject(self)

        return cog

    @property
    def cogs(self) -> Mapping[str, Cog]:
        """Mapping[:class:`str`, :class:`Cog`]: A read-only mapping of cog name to cog."""
        return types.MappingProxyType(self.__cogs)

    # extensions

    def _remove_module_references(self, name: str) -> None:
        # find all references to the module
        # remove the cogs registered from the module
        for cogname, cog in self.__cogs.copy().items():
            if _is_submodule(name, cog.__module__):
                self.remove_cog(cogname)

        # remove all the commands from the module
        if self._supports_prefixed_commands:
            for cmd in self.prefixed_commands.copy().values():
                if cmd.module is not None and _is_submodule(name, cmd.module):
                    # if isinstance(cmd, GroupMixin):
                    #     cmd.recursively_remove_all_commands()
                    self.remove_command(cmd.name)
        for cmd in self._application_commands.copy().values():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                # if isinstance(cmd, GroupMixin):
                #     cmd.recursively_remove_all_commands()
                self.remove_application_command(cmd)

        # remove all the listeners from the module
        for event_list in self.extra_events.copy().values():
            remove = [
                index
                for index, event in enumerate(event_list)
                if event.__module__ is not None and _is_submodule(name, event.__module__)
            ]

            for index in reversed(remove):
                del event_list[index]

    def _call_module_finalizers(self, lib: types.ModuleType, key: str) -> None:
        try:
            func = getattr(lib, "teardown")
        except AttributeError:
            pass
        else:
            try:
                func(self)
            except Exception:
                pass
        finally:
            self.__extensions.pop(key, None)
            sys.modules.pop(key, None)
            name = lib.__name__
            for module in list(sys.modules.keys()):
                if _is_submodule(name, module):
                    del sys.modules[module]

    def _load_from_module_spec(self, spec: importlib.machinery.ModuleSpec, key: str) -> None:
        # precondition: key not in self.__extensions
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise errors.ExtensionFailed(key, e) from e

        try:
            setup = getattr(lib, "setup")
        except AttributeError:
            del sys.modules[key]
            raise errors.NoEntryPointError(key)

        try:
            setup(self)
        except Exception as e:
            del sys.modules[key]
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, key)
            raise errors.ExtensionFailed(key, e) from e
        else:
            self.__extensions[key] = lib

    def _resolve_name(self, name: str, package: Optional[str]) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError:
            raise errors.ExtensionNotFound(name)

    def load_extension(
        self,
        name: str,
        *,
        package: Optional[str] = None,
        recursive: bool = False,
        store: bool = True,
    ) -> Optional[Union[Dict[str, Union[Exception, bool]], List[str]]]:
        """Loads an extension.

        An extension is a python module that contains commands, cogs, or
        listeners.

        An extension must have a global function, ``setup`` defined as
        the entry point on what to do when the extension is loaded. This entry
        point must have a single argument, the ``bot``.

        The extension passed can either be the direct name of a file within
        the current working directory or a folder that contains multiple extensions.

        Parameters
        -----------
        name: :class:`str`
            The extension or folder name to load. It must be dot separated
            like regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative
            path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7
        recursive: Optional[:class:`bool`]
            If subdirectories under the given head directory should be
            recursively loaded.
            Defaults to ``False``.

            .. versionadded:: 2.0
        store: Optional[:class:`bool`]
            If exceptions should be stored or raised. If set to ``True``,
            all exceptions encountered will be stored in a returned dictionary
            as a load status. If set to ``False``, if any exceptions are
            encountered they will be raised and the bot will be closed.
            If no exceptions are encountered, a list of loaded
            extension names will be returned.
            Defaults to ``True``.

            .. versionadded:: 2.0

        Raises
        -------
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionAlreadyLoaded
            The extension is already loaded.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension or its setup function had an execution error.

        Returns
        --------
        Optional[Union[Dict[:class:`str`, Union[:exc:`errors.ExtensionError`, :class:`bool`]], List[:class:`str`]]]
            If the store parameter is set to ``True``, a dictionary will be returned that
            contains keys to represent the loaded extension names. The values bound to
            each key can either be an exception that occurred when loading that extension
            or a ``True`` boolean representing a successful load. If the store parameter
            is set to ``False``, either a list containing a list of loaded extensions or
            nothing due to an encountered exception.
        """

        name = self._resolve_name(name, package)

        if name in self.__extensions:
            exc = errors.ExtensionAlreadyLoaded(name)
            final_out = {name: exc} if store else exc
        # This indicates that there is neither an extension nor folder here
        elif (spec := importlib.util.find_spec(name)) is None:
            exc = errors.ExtensionNotFound(name)
            final_out = {name: exc} if store else exc
        # This indicates we've found an extension file to load, and we need to store any exceptions
        elif spec.has_location and store:
            try:
                self._load_from_module_spec(spec, name)
            except Exception as exc:
                final_out = {name: exc}
            else:
                final_out = {name: True}
        # This indicates we've found an extension file to load, and any encountered exceptions can be raised
        elif spec.has_location:
            self._load_from_module_spec(spec, name)
            final_out = [name]
        # This indicates we've been given a folder because the ModuleSpec exists but is not a file
        else:
            # Split the directory path and join it to get an os-native Path object
            path = pathlib.Path(os.path.join(*name.split(".")))
            glob = path.rglob if recursive else path.glob
            final_out = {} if store else []

            # Glob all files with a pattern to gather all .py files that don't start with _
            for ext_file in glob("[!_]*.py"):
                # Gets all parts leading to the directory minus the file name
                parts = list(ext_file.parts[:-1])
                # Gets the file name without the extension
                parts.append(ext_file.stem)
                loaded = self.load_extension(".".join(parts))
                final_out.update(loaded) if store else final_out.extend(loaded)

        if isinstance(final_out, Exception):
            raise final_out
        else:
            return final_out

    def load_extensions(
        self,
        *names: str,
        package: Optional[str] = None,
        recursive: bool = False,
        store: bool = True,
    ) -> Optional[Union[Dict[str, Union[Exception, bool]], List[str]]]:
        """Loads multiple extensions at once.

        This method simplifies the process of loading multiple
        extensions by handling the looping of ``load_extension``.

        Parameters
        -----------
        names: :class:`str`
           The extension or folder names to load. It must be dot separated
           like regular Python imports if accessing a sub-module. e.g.
           ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative
            path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7
        recursive: Optional[:class:`bool`]
            If subdirectories under the given head directory should be
            recursively loaded.
            Defaults to ``False``.

            .. versionadded:: 2.0
        store: Optional[:class:`bool`]
            If exceptions should be stored or raised. If set to ``True``,
            all exceptions encountered will be stored in a returned dictionary
            as a load status. If set to ``False``, if any exceptions are
            encountered they will be raised and the bot will be closed.
            If no exceptions are encountered, a list of loaded
            extension names will be returned.
            Defaults to ``True``.

            .. versionadded:: 2.0

        Raises
        --------
        ExtensionNotFound
            A given extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionAlreadyLoaded
            A given extension is already loaded.
        NoEntryPointError
            A given extension does not have a setup function.
        ExtensionFailed
            A given extension or its setup function had an execution error.

        Returns
        --------
        Optional[Union[Dict[:class:`str`, Union[:exc:`errors.ExtensionError`, :class:`bool`]], List[:class:`str`]]]
            If the store parameter is set to ``True``, a dictionary will be returned that
            contains keys to represent the loaded extension names. The values bound to
            each key can either be an exception that occurred when loading that extension
            or a ``True`` boolean representing a successful load. If the store parameter
            is set to ``False``, either a list containing names of loaded extensions or
            nothing due to an encountered exception.
        """

        loaded_extensions = {} if store else []

        for ext_path in names:
            loaded = self.load_extension(ext_path, package=package, recursive=recursive, store=store)
            loaded_extensions.update(loaded) if store else loaded_extensions.extend(loaded)

        return loaded_extensions

    def unload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Unloads an extension.

        When the extension is unloaded, all commands, listeners, and cogs are
        removed from the bot and the module is un-imported.

        The extension can provide an optional global function, ``teardown``,
        to do miscellaneous clean-up if necessary. This function takes a single
        parameter, the ``bot``, similar to ``setup`` from
        :meth:`~.Bot.load_extension`.

        Parameters
        ------------
        name: :class:`str`
            The extension name to unload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7

        Raises
        -------
        ExtensionNotFound
            The name of the extension could not
            be resolved using the provided ``package`` parameter.
        ExtensionNotLoaded
            The extension was not loaded.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        self._remove_module_references(lib.__name__)
        self._call_module_finalizers(lib, name)

    def reload_extension(self, name: str, *, package: Optional[str] = None) -> None:
        """Atomically reloads an extension.

        This replaces the extension with the same extension, only refreshed. This is
        equivalent to a :meth:`unload_extension` followed by a :meth:`load_extension`
        except done in an atomic way. That is, if an operation fails mid-reload then
        the bot will roll-back to the prior working state.

        Parameters
        ------------
        name: :class:`str`
            The extension name to reload. It must be dot separated like
            regular Python imports if accessing a sub-module. e.g.
            ``foo.test`` if you want to import ``foo/test.py``.
        package: Optional[:class:`str`]
            The package name to resolve relative imports with.
            This is required when reloading an extension using a relative path, e.g ``.foo.test``.
            Defaults to ``None``.

            .. versionadded:: 1.7

        Raises
        -------
        ExtensionNotLoaded
            The extension was not loaded.
        ExtensionNotFound
            The extension could not be imported.
            This is also raised if the name of the extension could not
            be resolved using the provided ``package`` parameter.
        NoEntryPointError
            The extension does not have a setup function.
        ExtensionFailed
            The extension setup function had an execution error.
        """

        name = self._resolve_name(name, package)
        lib = self.__extensions.get(name)
        if lib is None:
            raise errors.ExtensionNotLoaded(name)

        # get the previous module states from sys modules
        modules = {name: module for name, module in sys.modules.items() if _is_submodule(lib.__name__, name)}

        try:
            # Unload and then load the module...
            self._remove_module_references(lib.__name__)
            self._call_module_finalizers(lib, name)
            self.load_extension(name)
        except Exception:
            # if the load failed, the remnants should have been
            # cleaned from the load_extension function call
            # so let's load it from our old compiled library.
            lib.setup(self)  # type: ignore
            self.__extensions[name] = lib

            # revert sys.modules back to normal and raise back to caller
            sys.modules.update(modules)
            raise

    @property
    def extensions(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__extensions)
