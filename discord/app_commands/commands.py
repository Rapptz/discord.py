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

from __future__ import annotations
import inspect

from typing import (
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from textwrap import TextWrapper

import re

from ..enums import AppCommandOptionType, AppCommandType
from .models import Choice
from .transformers import annotation_to_parameter, CommandParameter, NoneType
from .errors import AppCommandError, CommandInvokeError, CommandSignatureMismatch, CommandAlreadyRegistered
from ..message import Message
from ..user import User
from ..member import Member
from ..utils import resolve_annotation, MISSING, is_inside_class

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Concatenate
    from ..interactions import Interaction
    from ..abc import Snowflake
    from .namespace import Namespace
    from .models import ChoiceT

    # Generally, these two libraries are supposed to be separate from each other.
    # However, for type hinting purposes it's unfortunately necessary for one to
    # reference the other to prevent type checking errors in callbacks
    from discord.ext.commands import Cog

__all__ = (
    'Command',
    'ContextMenu',
    'Group',
    'context_menu',
    'command',
    'describe',
    'choices',
    'autocomplete',
    'guilds',
)

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')

T = TypeVar('T')
GroupT = TypeVar('GroupT', bound='Union[Group, Cog]')
Coro = Coroutine[Any, Any, T]
Error = Union[
    Callable[[GroupT, 'Interaction', AppCommandError], Coro[Any]],
    Callable[['Interaction', AppCommandError], Coro[Any]],
]


if TYPE_CHECKING:
    CommandCallback = Union[
        Callable[Concatenate[GroupT, 'Interaction', P], Coro[T]],
        Callable[Concatenate['Interaction', P], Coro[T]],
    ]

    ContextMenuCallback = Union[
        # If groups end up support context menus these would be uncommented
        # Callable[[GroupT, 'Interaction', Member], Coro[Any]],
        # Callable[[GroupT, 'Interaction', User], Coro[Any]],
        # Callable[[GroupT, 'Interaction', Message], Coro[Any]],
        # Callable[[GroupT, 'Interaction', Union[Member, User]], Coro[Any]],
        Callable[['Interaction', Member], Coro[Any]],
        Callable[['Interaction', User], Coro[Any]],
        Callable[['Interaction', Message], Coro[Any]],
        Callable[['Interaction', Union[Member, User]], Coro[Any]],
    ]

    AutocompleteCallback = Union[
        Callable[[GroupT, 'Interaction', ChoiceT], Coro[List[Choice[ChoiceT]]]],
        Callable[['Interaction', ChoiceT], Coro[List[Choice[ChoiceT]]]],
    ]
else:
    CommandCallback = Callable[..., Coro[T]]
    ContextMenuCallback = Callable[..., Coro[T]]
    AutocompleteCallback = Callable[..., Coro[T]]


VALID_SLASH_COMMAND_NAME = re.compile(r'^[\w-]{1,32}$')
VALID_CONTEXT_MENU_NAME = re.compile(r'^[\w\s-]{1,32}$')
CAMEL_CASE_REGEX = re.compile(r'(?<!^)(?=[A-Z])')


def _shorten(
    input: str,
    *,
    _wrapper: TextWrapper = TextWrapper(width=100, max_lines=1, replace_whitespace=True, placeholder='…'),
) -> str:
    return _wrapper.fill(' '.join(input.strip().split()))


def _to_kebab_case(text: str) -> str:
    return CAMEL_CASE_REGEX.sub('-', text).lower()


def validate_name(name: str) -> str:
    match = VALID_SLASH_COMMAND_NAME.match(name)
    if match is None:
        raise ValueError('names must be between 1-32 characters')

    # Ideally, name.islower() would work instead but since certain characters
    # are Lo (e.g. CJK) those don't pass the test. I'd use `casefold` instead as
    # well, but chances are the server-side check is probably something similar to
    # this code anyway.
    if name.lower() != name:
        raise ValueError('names must be all lower case')
    return name


def validate_context_menu_name(name: str) -> str:
    if VALID_CONTEXT_MENU_NAME.match(name) is None:
        raise ValueError('context menu names must be between 1-32 characters')
    return name


def _validate_auto_complete_callback(
    callback: AutocompleteCallback[GroupT, ChoiceT]
) -> AutocompleteCallback[GroupT, ChoiceT]:

    requires_binding = is_inside_class(callback)
    required_parameters = 2 + requires_binding
    callback.requires_binding = requires_binding
    params = inspect.signature(callback).parameters
    if len(params) != required_parameters:
        raise TypeError('autocomplete callback requires either 2 or 3 parameters to be passed')

    return callback


def _context_menu_annotation(annotation: Any, *, _none: type = NoneType) -> AppCommandType:
    if annotation is Message:
        return AppCommandType.message

    supported_types: Set[Any] = {Member, User}
    if annotation in supported_types:
        return AppCommandType.user

    # Check if there's an origin
    origin = getattr(annotation, '__origin__', None)
    if origin is not Union:
        # Only Union is supported so bail early
        msg = (
            f'unsupported type annotation {annotation!r}, must be either discord.Member, '
            'discord.User, discord.Message, or a typing.Union of discord.Member and discord.User'
        )
        raise TypeError(msg)

    # Only Union[Member, User] is supported
    if not all(arg in supported_types for arg in annotation.__args__):
        raise TypeError(f'unsupported types given inside {annotation!r}')

    return AppCommandType.user


def _populate_descriptions(params: Dict[str, CommandParameter], descriptions: Dict[str, Any]) -> None:
    for name, param in params.items():
        description = descriptions.pop(name, MISSING)
        if description is MISSING:
            param.description = '…'
            continue

        if not isinstance(description, str):
            raise TypeError('description must be a string')

        param.description = description

    if descriptions:
        first = next(iter(descriptions))
        raise TypeError(f'unknown parameter given: {first}')


def _populate_choices(params: Dict[str, CommandParameter], all_choices: Dict[str, List[Choice]]) -> None:
    for name, param in params.items():
        choices = all_choices.pop(name, MISSING)
        if choices is MISSING:
            continue

        if not isinstance(choices, list):
            raise TypeError('choices must be a list of Choice')

        if not all(isinstance(choice, Choice) for choice in choices):
            raise TypeError('choices must be a list of Choice')

        if param.type not in (AppCommandOptionType.string, AppCommandOptionType.number, AppCommandOptionType.integer):
            raise TypeError('choices are only supported for integer, string, or number option types')

        if not all(param.type == choice._option_type for choice in choices):
            raise TypeError('choices must all have the same inner option type as the parameter choice type')

        param.choices = choices

    if all_choices:
        first = next(iter(all_choices))
        raise TypeError(f'unknown parameter given: {first}')


def _populate_autocomplete(params: Dict[str, CommandParameter], autocomplete: Dict[str, Any]) -> None:
    for name, param in params.items():
        callback = autocomplete.pop(name, MISSING)
        if callback is MISSING:
            continue

        if not inspect.iscoroutinefunction(callback):
            raise TypeError('autocomplete callback must be a coroutine function')

        if param.type not in (AppCommandOptionType.string, AppCommandOptionType.number, AppCommandOptionType.integer):
            raise TypeError('autocomplete is only supported for integer, string, or number option types')

        if param.is_choice_annotation():
            raise TypeError(
                'Choice annotation unsupported for autocomplete parameters, consider using a regular annotation instead'
            )

        param.autocomplete = _validate_auto_complete_callback(callback)

    if autocomplete:
        first = next(iter(autocomplete))
        raise TypeError(f'unknown parameter given: {first}')


def _extract_parameters_from_callback(func: Callable[..., Any], globalns: Dict[str, Any]) -> Dict[str, CommandParameter]:
    params = inspect.signature(func).parameters
    cache = {}
    required_params = is_inside_class(func) + 1
    if len(params) < required_params:
        raise TypeError(f'callback must have more than {required_params - 1} parameter(s)')

    iterator = iter(params.values())
    for _ in range(0, required_params):
        next(iterator)

    parameters: List[CommandParameter] = []
    for parameter in iterator:
        if parameter.annotation is parameter.empty:
            raise TypeError(f'annotation for {parameter.name} must be given')

        resolved = resolve_annotation(parameter.annotation, globalns, globalns, cache)
        param = annotation_to_parameter(resolved, parameter)
        parameters.append(param)

    values = sorted(parameters, key=lambda a: a.required, reverse=True)
    result = {v.name: v for v in values}

    try:
        descriptions = func.__discord_app_commands_param_description__
    except AttributeError:
        for param in values:
            if param.description is MISSING:
                param.description = '…'
    else:
        _populate_descriptions(result, descriptions)

    try:
        choices = func.__discord_app_commands_param_choices__
    except AttributeError:
        pass
    else:
        _populate_choices(result, choices)

    try:
        autocomplete = func.__discord_app_commands_param_autocomplete__
    except AttributeError:
        pass
    else:
        _populate_autocomplete(result, autocomplete)

    return result


def _get_context_menu_parameter(func: ContextMenuCallback) -> Tuple[str, Any, AppCommandType]:
    params = inspect.signature(func).parameters
    if len(params) != 2:
        msg = (
            'context menu callbacks require 2 parameters, the first one being the annotation and the '
            'other one explicitly annotated with either discord.Message, discord.User, discord.Member, '
            'or a typing.Union of discord.Member and discord.User'
        )
        raise TypeError(msg)

    iterator = iter(params.values())
    next(iterator)  # skip interaction
    parameter = next(iterator)
    if parameter.annotation is parameter.empty:
        msg = (
            'second parameter of context menu callback must be explicitly annotated with either discord.Message, '
            'discord.User, discord.Member, or a typing.Union of discord.Member and discord.User'
        )
        raise TypeError(msg)

    resolved = resolve_annotation(parameter.annotation, func.__globals__, func.__globals__, {})
    type = _context_menu_annotation(resolved)
    return (parameter.name, resolved, type)


class Command(Generic[GroupT, P, T]):
    """A class that implements an application command.

    These are usually not created manually, instead they are created using
    one of the following decorators:

    - :func:`~discord.app_commands.command`
    - :meth:`Group.command <discord.app_commands.Group.command>`
    - :meth:`CommandTree.command <discord.app_commands.CommandTree.command>`

    .. versionadded:: 2.0

    Attributes
    ------------
    name: :class:`str`
        The name of the application command.
    description: :class:`str`
        The description of the application command. This shows up in the UI to describe
        the application command.
    parent: Optional[:class:`Group`]
        The parent application command. ``None`` if there isn't one.
    """

    def __init__(
        self,
        *,
        name: str,
        description: str,
        callback: CommandCallback[GroupT, P, T],
        parent: Optional[Group] = None,
        guild_ids: Optional[List[int]] = None,
    ):
        self.name: str = validate_name(name)
        self.description: str = description
        self._attr: Optional[str] = None
        self._callback: CommandCallback[GroupT, P, T] = callback
        self.parent: Optional[Group] = parent
        self.binding: Optional[GroupT] = None
        self.on_error: Optional[Error[GroupT]] = None
        self.module: Optional[str] = callback.__module__

        # Unwrap __self__ for bound methods
        try:
            self.binding = callback.__self__
            self._callback = callback = callback.__func__
        except AttributeError:
            pass

        self._params: Dict[str, CommandParameter] = _extract_parameters_from_callback(callback, callback.__globals__)
        self._guild_ids: Optional[List[int]] = guild_ids or getattr(
            callback, '__discord_app_commands_default_guilds__', None
        )

        if self._guild_ids is not None and self.parent is not None:
            raise ValueError('child commands cannot have default guilds set, consider setting them in the parent instead')

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self._attr = name

    @property
    def callback(self) -> CommandCallback[GroupT, P, T]:
        """:ref:`coroutine <coroutine>`: The coroutine that is executed when the command is called."""
        return self._callback

    def _copy_with_binding(self, binding: GroupT) -> Command:
        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy._guild_ids = self._guild_ids
        copy.description = self.description
        copy._attr = self._attr
        copy._callback = self._callback
        copy.parent = self.parent
        copy.on_error = self.on_error
        copy._params = self._params.copy()
        copy.module = self.module
        copy.binding = binding
        return copy

    def to_dict(self) -> Dict[str, Any]:
        # If we have a parent then our type is a subcommand
        # Otherwise, the type falls back to the specific command type (e.g. slash command or context menu)
        option_type = AppCommandType.chat_input.value if self.parent is None else AppCommandOptionType.subcommand.value
        return {
            'name': self.name,
            'description': self.description,
            'type': option_type,
            'options': [param.to_dict() for param in self._params.values()],
        }

    async def _invoke_error_handler(self, interaction: Interaction, error: AppCommandError) -> None:
        # These type ignores are because the type checker can't narrow this type properly.
        if self.on_error is not None:
            if self.binding is not None:
                await self.on_error(self.binding, interaction, error)  # type: ignore
            else:
                await self.on_error(interaction, error)  # type: ignore

        parent = self.parent
        if parent is not None:
            await parent.on_error(interaction, self, error)

            if parent.parent is not None:
                await parent.parent.on_error(interaction, self, error)

    async def _invoke_with_namespace(self, interaction: Interaction, namespace: Namespace) -> T:
        values = namespace.__dict__
        for name, param in self._params.items():
            try:
                value = values[name]
            except KeyError:
                if not param.required:
                    values[name] = param.default
                else:
                    raise CommandSignatureMismatch(self) from None
            else:
                values[name] = await param.transform(interaction, value)

        # These type ignores are because the type checker doesn't quite understand the narrowing here
        # Likewise, it thinks we're missing positional arguments when there aren't any.
        try:
            if self.binding is not None:
                return await self._callback(self.binding, interaction, **values)  # type: ignore
            return await self._callback(interaction, **values)  # type: ignore
        except TypeError as e:
            # In order to detect mismatch from the provided signature and the Discord data,
            # there are many ways it can go wrong yet all of them eventually lead to a TypeError
            # from the Python compiler showcasing that the signature is incorrect. This lovely
            # piece of code essentially checks the last frame of the caller and checks if the
            # locals contains our `self` reference.
            #
            # This is because there is a possibility that a TypeError is raised within the body
            # of the function, and in that case the locals wouldn't contain a reference to
            # the command object under the name `self`.
            frame = inspect.trace()[-1].frame
            if frame.f_locals.get('self') is self:
                raise CommandSignatureMismatch(self) from None
            raise CommandInvokeError(self, e) from e
        except AppCommandError:
            raise
        except Exception as e:
            raise CommandInvokeError(self, e) from e

    async def _invoke_autocomplete(self, interaction: Interaction, name: str, namespace: Namespace):
        value = namespace.__dict__[name]

        try:
            param = self._params[name]
        except KeyError:
            raise CommandSignatureMismatch(self) from None

        if param.autocomplete is None:
            raise CommandSignatureMismatch(self)

        if param.autocomplete.requires_binding:
            if self.binding is not None:
                choices = await param.autocomplete(self.binding, interaction, value)
            else:
                raise TypeError('autocomplete parameter expected a bound self parameter but one was not provided')
        else:
            choices = await param.autocomplete(interaction, value)

        if interaction.response.is_done():
            return

        await interaction.response.autocomplete(choices)

    def _get_internal_command(self, name: str) -> Optional[Union[Command, Group]]:
        return None

    @property
    def root_parent(self) -> Optional[Group]:
        """Optional[:class:`Group`]: The root parent of this command."""
        if self.parent is None:
            return None
        parent = self.parent
        return parent.parent or parent

    def error(self, coro: Error[GroupT]) -> Error[GroupT]:
        """A decorator that registers a coroutine as a local error handler.

        The local error handler is called whenever an exception is raised in the body
        of the command or during handling of the command. The error handler must take
        2 parameters, the interaction and the error.

        The error passed will be derived from :exc:`AppCommandError`.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not inspect.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        self.on_error = coro
        return coro

    def autocomplete(
        self, name: str
    ) -> Callable[[AutocompleteCallback[GroupT, ChoiceT]], AutocompleteCallback[GroupT, ChoiceT]]:
        """A decorator that registers a coroutine as an autocomplete prompt for a parameter.

        The coroutine callback must have 2 parameters, the :class:`~discord.Interaction`,
        and the current value by the user (usually either a :class:`str`, :class:`int`, or :class:`float`,
        depending on the type of the parameter being marked as autocomplete).

        To get the values from other parameters that may be filled in, accessing
        :attr:`.Interaction.namespace` will give a :class:`Namespace` object with those
        values.

        The coroutine decorator **must** return a list of :class:`~discord.app_commands.Choice` objects.
        Only up to 25 objects are supported.

        Example:

        .. code-block:: python3

            @app_commands.command()
            async def fruits(interaction: discord.Interaction, fruits: str):
                await interaction.response.send_message(f'Your favourite fruit seems to be {fruits}')

            @fruits.autocomplete('fruits')
            async def fruits_autocomplete(
                interaction: discord.Interaction,
                current: str,
            ) -> List[app_commands.Choice[str]]:
                fruits = ['Banana', 'Pineapple', 'Apple', 'Watermelon', 'Melon', 'Cherry']
                return [
                    app_commands.Choice(name=fruit, value=fruit)
                    for fruit in fruits if current.lower() in fruit.lower()
                ]


        Parameters
        -----------
        name: :class:`str`
            The parameter name to register as autocomplete.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine or
            the parameter is not found or of an invalid type.
        """

        def decorator(coro: AutocompleteCallback[GroupT, ChoiceT]) -> AutocompleteCallback[GroupT, ChoiceT]:
            if not inspect.iscoroutinefunction(coro):
                raise TypeError('The error handler must be a coroutine.')

            try:
                param = self._params[name]
            except KeyError:
                raise TypeError(f'unknown parameter: {name!r}') from None

            if param.type not in (AppCommandOptionType.string, AppCommandOptionType.number, AppCommandOptionType.integer):
                raise TypeError('autocomplete is only supported for integer, string, or number option types')

            if param.is_choice_annotation():
                raise TypeError(
                    'Choice annotation unsupported for autocomplete parameters, consider using a regular annotation instead'
                )

            param.autocomplete = _validate_auto_complete_callback(coro)
            return coro

        return decorator


class ContextMenu:
    """A class that implements a context menu application command.

    These are usually not created manually, instead they are created using
    one of the following decorators:

    - :func:`~discord.app_commands.context_menu`
    - :meth:`CommandTree.command <discord.app_commands.CommandTree.context_menu>`

    .. versionadded:: 2.0

    Attributes
    ------------
    name: :class:`str`
        The name of the context menu.
    type: :class:`.AppCommandType`
        The type of context menu application command.
    """

    def __init__(
        self,
        *,
        name: str,
        callback: ContextMenuCallback,
        type: AppCommandType,
        guild_ids: Optional[List[int]] = None,
    ):
        self.name: str = validate_context_menu_name(name)
        self._callback: ContextMenuCallback = callback
        self.type: AppCommandType = type
        (param, annotation, actual_type) = _get_context_menu_parameter(callback)
        if actual_type != type:
            raise ValueError(f'context menu callback implies a type of {actual_type} but {type} was passed.')
        self._param_name = param
        self._annotation = annotation
        self.module: Optional[str] = callback.__module__
        self._guild_ids = guild_ids

    @property
    def callback(self) -> ContextMenuCallback:
        """:ref:`coroutine <coroutine>`: The coroutine that is executed when the context menu is called."""
        return self._callback

    @classmethod
    def _from_decorator(cls, callback: ContextMenuCallback, *, name: str = MISSING) -> ContextMenu:
        (param, annotation, type) = _get_context_menu_parameter(callback)

        self = cls.__new__(cls)
        self.name = callback.__name__.title() if name is MISSING else name
        self._callback = callback
        self.type = type
        self._param_name = param
        self._annotation = annotation
        self.module = callback.__module__
        self._guild_ids = None
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type.value,
        }

    async def _invoke(self, interaction: Interaction, arg: Any):
        try:
            await self._callback(interaction, arg)
        except AppCommandError:
            raise
        except Exception as e:
            raise CommandInvokeError(self, e) from e


class Group:
    """A class that implements an application command group.

    These are usually inherited rather than created manually.

    .. versionadded:: 2.0

    Attributes
    ------------
    name: :class:`str`
        The name of the group. If not given, it defaults to a lower-case
        kebab-case version of the class name.
    description: :class:`str`
        The description of the group. This shows up in the UI to describe
        the group. If not given, it defaults to the docstring of the
        class shortened to 100 characters.
    parent: Optional[:class:`Group`]
        The parent group. ``None`` if there isn't one.
    """

    __discord_app_commands_group_children__: ClassVar[List[Union[Command[Any, ..., Any], Group]]] = []
    __discord_app_commands_skip_init_binding__: bool = False
    __discord_app_commands_group_name__: str = MISSING
    __discord_app_commands_group_description__: str = MISSING
    __discord_app_commands_has_module__: bool = False

    def __init_subclass__(cls, *, name: str = MISSING, description: str = MISSING) -> None:
        if not cls.__discord_app_commands_group_children__:
            children: List[Union[Command[Any, ..., Any], Group]] = [
                member for member in cls.__dict__.values() if isinstance(member, (Group, Command)) and member.parent is None
            ]

            cls.__discord_app_commands_group_children__ = children

            found = set()
            for child in children:
                if child.name in found:
                    raise TypeError(f'Command {child.name!r} is a duplicate')
                found.add(child.name)

            if len(children) > 25:
                raise TypeError('groups cannot have more than 25 commands')

        if name is MISSING:
            cls.__discord_app_commands_group_name__ = validate_name(_to_kebab_case(cls.__name__))
        else:
            cls.__discord_app_commands_group_name__ = validate_name(name)

        if description is MISSING:
            if cls.__doc__ is None:
                cls.__discord_app_commands_group_description__ = '…'
            else:
                cls.__discord_app_commands_group_description__ = _shorten(cls.__doc__)
        else:
            cls.__discord_app_commands_group_description__ = description

        if cls.__module__ != __name__:
            cls.__discord_app_commands_has_module__ = True

    def __init__(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        parent: Optional[Group] = None,
        guild_ids: Optional[List[int]] = None,
    ):
        cls = self.__class__
        self.name: str = validate_name(name) if name is not MISSING else cls.__discord_app_commands_group_name__
        self.description: str = description or cls.__discord_app_commands_group_description__
        self._attr: Optional[str] = None
        self._guild_ids: Optional[List[int]] = guild_ids

        if not self.description:
            raise TypeError('groups must have a description')

        self.parent: Optional[Group] = parent
        self.module: Optional[str]
        if cls.__discord_app_commands_has_module__:
            self.module = cls.__module__
        else:
            try:
                # This is pretty hacky
                # It allows the module to be fetched if someone just constructs a bare Group object though.
                self.module = inspect.currentframe().f_back.f_globals['__name__']  # type: ignore
            except (AttributeError, IndexError):
                self.module = None

        self._children: Dict[str, Union[Command, Group]] = {}

        for child in self.__discord_app_commands_group_children__:
            child.parent = self
            child = child._copy_with_binding(self) if not cls.__discord_app_commands_skip_init_binding__ else child
            self._children[child.name] = child
            if child._attr and not cls.__discord_app_commands_skip_init_binding__:
                setattr(self, child._attr, child)

        if parent is not None and parent.parent is not None:
            raise ValueError('groups can only be nested at most one level')

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self._attr = name
        self.module = owner.__module__

    def _copy_with_binding(self, binding: Union[Group, Cog]) -> Group:
        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy._guild_ids = self._guild_ids
        copy.description = self.description
        copy.parent = self.parent
        copy.module = self.module
        copy._attr = self._attr
        copy._children = {child.name: child._copy_with_binding(binding) for child in self._children.values()}
        return copy

    def to_dict(self) -> Dict[str, Any]:
        # If this has a parent command then it's part of a subcommand group
        # Otherwise, it's just a regular command
        option_type = 1 if self.parent is None else AppCommandOptionType.subcommand_group.value
        return {
            'name': self.name,
            'description': self.description,
            'type': option_type,
            'options': [child.to_dict() for child in self._children.values()],
        }

    @property
    def root_parent(self) -> Optional[Group]:
        """Optional[:class:`Group`]: The parent of this group."""
        return self.parent

    def _get_internal_command(self, name: str) -> Optional[Union[Command[Any, ..., Any], Group]]:
        return self._children.get(name)

    @property
    def commands(self) -> List[Union[Command[Any, ..., Any], Group]]:
        """List[Union[:class:`Command`, :class:`Group`]]: The commands that this group contains."""
        return list(self._children.values())

    def walk_commands(self) -> Generator[Union[Command[Any, ..., Any], Group], None, None]:
        """An iterator that recursively walks through all commands that this group contains.

        Yields
        ---------
        Union[:class:`Command`, :class:`Group`]
            The commands in this group.
        """

        for command in self._children.values():
            yield command
            if isinstance(command, Group):
                yield from command.walk_commands()

    async def on_error(self, interaction: Interaction, command: Command[Any, ..., Any], error: AppCommandError) -> None:
        """|coro|

        A callback that is called when a child's command raises an :exc:`AppCommandError`.

        The default implementation does nothing.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that is being handled.
        command: :class:`~discord.app_commands.Command`
            The command that failed.
        error: :exc:`AppCommandError`
            The exception that was raised.
        """

        pass

    def add_command(self, command: Union[Command[Any, ..., Any], Group], /, *, override: bool = False) -> None:
        """Adds a command or group to this group's internal list of commands.

        Parameters
        -----------
        command: Union[:class:`Command`, :class:`Group`]
            The command or group to add.
        override: :class:`bool`
            Whether to override a pre-existing command or group with the same name.
            If ``False`` then an exception is raised.

        Raises
        -------
        CommandAlreadyRegistered
            The command or group is already registered. Note that the :attr:`CommandAlreadyRegistered.guild_id`
            attribute will always be ``None`` in this case.
        ValueError
            There are too many commands already registered or the group is too
            deeply nested.
        TypeError
            The wrong command type was passed.
        """

        if not isinstance(command, (Command, Group)):
            raise TypeError(f'expected Command or Group not {command.__class__!r}')

        if isinstance(command, Group) and self.parent is not None:
            # In a tree like so:
            # <group>
            #   <self>
            #     <group>
            # this needs to be forbidden
            raise ValueError('groups can only be nested at most one level')

        if not override and command.name in self._children:
            raise CommandAlreadyRegistered(command.name, guild_id=None)

        self._children[command.name] = command
        command.parent = self
        if len(self._children) > 25:
            raise ValueError('maximum number of child commands exceeded')

    def remove_command(self, name: str, /) -> Optional[Union[Command[Any, ..., Any], Group]]:
        """Removes a command or group from the internal list of commands.

        Parameters
        -----------
        name: :class:`str`
            The name of the command or group to remove.

        Returns
        --------
        Optional[Union[:class:`~discord.app_commands.Command`, :class:`~discord.app_commands.Group`]]
            The command that was removed. If nothing was removed
            then ``None`` is returned instead.
        """

        self._children.pop(name, None)

    def get_command(self, name: str, /) -> Optional[Union[Command[Any, ..., Any], Group]]:
        """Retrieves a command or group from its name.

        Parameters
        -----------
        name: :class:`str`
            The name of the command or group to retrieve.

        Returns
        --------
        Optional[Union[:class:`~discord.app_commands.Command`, :class:`~discord.app_commands.Group`]]
            The command or group that was retrieved. If nothing was found
            then ``None`` is returned instead.
        """
        return self._children.get(name)

    def command(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
    ) -> Callable[[CommandCallback[GroupT, P, T]], Command[GroupT, P, T]]:
        """Creates an application command under this group.

        Parameters
        ------------
        name: :class:`str`
            The name of the application command. If not given, it defaults to a lower-case
            version of the callback name.
        description: :class:`str`
            The description of the application command. This shows up in the UI to describe
            the application command. If not given, it defaults to the first line of the docstring
            of the callback shortened to 100 characters.
        """

        def decorator(func: CommandCallback[GroupT, P, T]) -> Command[GroupT, P, T]:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('command function must be a coroutine function')

            if description is MISSING:
                if func.__doc__ is None:
                    desc = '…'
                else:
                    desc = _shorten(func.__doc__)
            else:
                desc = description

            command = Command(
                name=name if name is not MISSING else func.__name__,
                description=desc,
                callback=func,
                parent=self,
            )
            self.add_command(command)
            return command

        return decorator


def command(
    *,
    name: str = MISSING,
    description: str = MISSING,
) -> Callable[[CommandCallback[GroupT, P, T]], Command[GroupT, P, T]]:
    """Creates an application command from a regular function.

    Parameters
    ------------
    name: :class:`str`
        The name of the application command. If not given, it defaults to a lower-case
        version of the callback name.
    description: :class:`str`
        The description of the application command. This shows up in the UI to describe
        the application command. If not given, it defaults to the first line of the docstring
        of the callback shortened to 100 characters.
    """

    def decorator(func: CommandCallback[GroupT, P, T]) -> Command[GroupT, P, T]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError('command function must be a coroutine function')

        if description is MISSING:
            if func.__doc__ is None:
                desc = '…'
            else:
                desc = _shorten(func.__doc__)
        else:
            desc = description

        return Command(
            name=name if name is not MISSING else func.__name__,
            description=desc,
            callback=func,
            parent=None,
        )

    return decorator


def context_menu(*, name: str = MISSING) -> Callable[[ContextMenuCallback], ContextMenu]:
    """Creates a application command context menu from a regular function.

    This function must have a signature of :class:`~discord.Interaction` as its first parameter
    and taking either a :class:`~discord.Member`, :class:`~discord.User`, or :class:`~discord.Message`,
    or a :obj:`typing.Union` of ``Member`` and ``User`` as its second parameter.

    Examples
    ---------

    .. code-block:: python3

        @app_commands.context_menu()
        async def react(interaction: discord.Interaction, message: discord.Message):
            await interaction.response.send_message('Very cool message!', ephemeral=True)

        @app_commands.context_menu()
        async def ban(interaction: discord.Interaction, user: discord.Member):
            await interaction.response.send_message(f'Should I actually ban {user}...', ephemeral=True)

    Parameters
    ------------
    name: :class:`str`
        The name of the context menu command. If not given, it defaults to a title-case
        version of the callback name. Note that unlike regular slash commands this can
        have spaces and upper case characters in the name.
    """

    def decorator(func: ContextMenuCallback) -> ContextMenu:
        if not inspect.iscoroutinefunction(func):
            raise TypeError('context menu function must be a coroutine function')

        return ContextMenu._from_decorator(func, name=name)

    return decorator


def describe(**parameters: str) -> Callable[[T], T]:
    r"""Describes the given parameters by their name using the key of the keyword argument
    as the name.

    Example:

    .. code-block:: python3

        @app_commands.command()
        @app_commands.describe(member='the member to ban')
        async def ban(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.send_message(f'Banned {member}')

    Parameters
    -----------
    \*\*parameters
        The description of the parameters.

    Raises
    --------
    TypeError
        The parameter name is not found.
    """

    def decorator(inner: T) -> T:
        if isinstance(inner, Command):
            _populate_descriptions(inner._params, parameters)
        else:
            try:
                inner.__discord_app_commands_param_description__.update(parameters)  # type: ignore - Runtime attribute access
            except AttributeError:
                inner.__discord_app_commands_param_description__ = parameters  # type: ignore - Runtime attribute assignment

        return inner

    return decorator


def choices(**parameters: List[Choice[ChoiceT]]) -> Callable[[T], T]:
    r"""Instructs the given parameters by their name to use the given choices for their choices.

    Example:

    .. code-block:: python3

        @app_commands.command()
        @app_commands.describe(fruits='fruits to choose from')
        @app_commands.choices(fruits=[
            Choice(name='apple', value=1),
            Choice(name='banana', value=2),
            Choice(name='cherry', value=3),
        ])
        async def fruit(interaction: discord.Interaction, fruits: Choice[int]):
            await interaction.response.send_message(f'Your favourite fruit is {fruits.name}.')

    .. note::

        This is not the only way to provide choices to a command. There are two more ergonomic ways
        of doing this. The first one is to use a :obj:`typing.Literal` annotation:

        .. code-block:: python3

            @app_commands.command()
            @app_commands.describe(fruits='fruits to choose from')
            async def fruit(interaction: discord.Interaction, fruits: Literal['apple', 'banana', 'cherry']):
                await interaction.response.send_message(f'Your favourite fruit is {fruits}.')

        The second way is to use an :class:`enum.Enum`:

        .. code-block:: python3

            class Fruits(enum.Enum):
                apple = 1
                banana = 2
                cherry = 3

            @app_commands.command()
            @app_commands.describe(fruits='fruits to choose from')
            async def fruit(interaction: discord.Interaction, fruits: Fruits):
                await interaction.response.send_message(f'Your favourite fruit is {fruits}.')


    Parameters
    -----------
    \*\*parameters
        The choices of the parameters.

    Raises
    --------
    TypeError
        The parameter name is not found or the parameter type was incorrect.
    """

    def decorator(inner: T) -> T:
        if isinstance(inner, Command):
            _populate_choices(inner._params, parameters)
        else:
            try:
                inner.__discord_app_commands_param_choices__.update(parameters)  # type: ignore - Runtime attribute access
            except AttributeError:
                inner.__discord_app_commands_param_choices__ = parameters  # type: ignore - Runtime attribute assignment

        return inner

    return decorator


def autocomplete(**parameters: AutocompleteCallback[GroupT, ChoiceT]) -> Callable[[T], T]:
    r"""Associates the given parameters with the given autocomplete callback.

    Autocomplete is only supported on types that have :class:`str`, :class:`int`, or :class:`float`
    values.

    For more information, see the :meth:`Command.autocomplete` documentation.

    Example:

    .. code-block:: python3

            @app_commands.command()
            @app_commands.autocomplete(fruits=fruits_autocomplete)
            async def fruits(interaction: discord.Interaction, fruits: str):
                await interaction.response.send_message(f'Your favourite fruit seems to be {fruits}')

            async def fruits_autocomplete(
                interaction: discord.Interaction,
                current: str,
            ) -> List[app_commands.Choice[str]]:
                fruits = ['Banana', 'Pineapple', 'Apple', 'Watermelon', 'Melon', 'Cherry']
                return [
                    app_commands.Choice(name=fruit, value=fruit)
                    for fruit in fruits if current.lower() in fruit.lower()
                ]

    Parameters
    -----------
    \*\*parameters
        The parameters to mark as autocomplete.

    Raises
    --------
    TypeError
        The parameter name is not found or the parameter type was incorrect.
    """

    def decorator(inner: T) -> T:
        if isinstance(inner, Command):
            _populate_autocomplete(inner._params, parameters)
        else:
            try:
                inner.__discord_app_commands_param_autocomplete__.update(parameters)  # type: ignore - Runtime attribute access
            except AttributeError:
                inner.__discord_app_commands_param_autocomplete__ = parameters  # type: ignore - Runtime attribute assignment

        return inner

    return decorator


def guilds(*guild_ids: Union[Snowflake, int]) -> Callable[[T], T]:
    r"""Associates the given guilds with the command.

    When the command instance is added to a :class:`CommandTree`, the guilds that are
    specified by this decorator become the default guilds that it's added to rather
    than being a global command.

    .. note::

        Due to an implementation quirk and Python limitation, if this is used in conjunction
        with the :meth:`CommandTree.command` or :meth:`CommandTree.context_menu` decorator
        then this must go below that decorator.

    Example:

    .. code-block:: python3

            MY_GUILD_ID = discord.Object(...)  # Guild ID here

            @app_commands.command()
            @app_commands.guilds(MY_GUILD_ID)
            async def bonk(interaction: discord.Interaction):
                await interaction.response.send_message('Bonk', ephemeral=True)

    Parameters
    -----------
    \*guild_ids: Union[:class:`int`, :class:`~discord.abc.Snowflake`]
        The guilds to associate this command with. The command tree will
        use this as the default when added rather than adding it as a global
        command.
    """

    defaults: List[int] = [g if isinstance(g, int) else g.id for g in guild_ids]

    def decorator(inner: T) -> T:
        if isinstance(inner, (Group, ContextMenu)):
            inner._guild_ids = defaults
        elif isinstance(inner, Command):
            if inner.parent is not None:
                raise ValueError('child commands of a group cannot have default guilds set')

            inner._guild_ids = defaults
        else:
            # Runtime attribute assignment
            inner.__discord_app_commands_default_guilds__ = defaults  # type: ignore

        return inner

    return decorator
