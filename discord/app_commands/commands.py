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
from dataclasses import dataclass
from textwrap import TextWrapper

import sys
import re

from .enums import AppCommandOptionType, AppCommandType
from ..interactions import Interaction
from ..enums import ChannelType, try_enum
from .models import Choice
from .errors import CommandSignatureMismatch, CommandAlreadyRegistered
from ..utils import resolve_annotation, MISSING, is_inside_class
from ..user import User
from ..member import Member
from ..role import Role
from ..mixins import Hashable
from ..permissions import Permissions

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Concatenate
    from ..interactions import Interaction
    from ..types.interactions import (
        ResolvedData,
        PartialThread,
        PartialChannel,
        ApplicationCommandInteractionDataOption,
    )
    from ..state import ConnectionState
    from .namespace import Namespace

__all__ = (
    'CommandParameter',
    'Command',
    'Group',
    'command',
    'describe',
)

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')

T = TypeVar('T')
GroupT = TypeVar('GroupT', bound='Group')
Coro = Coroutine[Any, Any, T]

if TYPE_CHECKING:
    CommandCallback = Union[
        Callable[Concatenate[GroupT, Interaction, P], Coro[T]],
        Callable[Concatenate[Interaction, P], Coro[T]],
    ]
else:
    CommandCallback = Callable[..., Coro[T]]


VALID_SLASH_COMMAND_NAME = re.compile(r'^[\w-]{1,32}$')
CAMEL_CASE_REGEX = re.compile(r'(?<!^)(?=[A-Z])')


def _shorten(
    input: str,
    *,
    _wrapper: TextWrapper = TextWrapper(width=100, max_lines=1, replace_whitespace=True, placeholder='...'),
) -> str:
    return _wrapper.fill(' '.join(input.strip().split()))


def _to_kebab_case(text: str) -> str:
    return CAMEL_CASE_REGEX.sub('-', text).lower()


@dataclass
class CommandParameter:
    """Represents a application command parameter.

    Attributes
    -----------
    name: :class:`str`
        The name of the parameter.
    description: :class:`str`
        The description of the parameter
    required: :class:`bool`
        Whether the parameter is required
    choices: List[:class:`~discord.app_commands.Choice`]
        A list of choices this parameter takes
    type: :class:`~discord.app_commands.AppCommandOptionType`
        The underlying type of this parameter.
    channel_types: List[:class:`~discord.ChannelType`]
        The channel types that are allowed for this parameter.
    min_value: Optional[:class:`int`]
        The minimum supported value for this parameter.
    max_value: Optional[:class:`int`]
        The maximum supported value for this parameter.
    autocomplete: :class:`bool`
        Whether this parameter enables autocomplete.
    """

    name: str = MISSING
    description: str = MISSING
    required: bool = MISSING
    default: Any = MISSING
    choices: List[Choice] = MISSING
    type: AppCommandOptionType = MISSING
    channel_types: List[ChannelType] = MISSING
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    autocomplete: bool = MISSING
    annotation: Any = MISSING
    # restrictor: Optional[RestrictorType] = None

    def to_dict(self) -> Dict[str, Any]:
        base = {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'required': self.required,
        }

        if self.choices:
            base['choices'] = [choice.to_dict() for choice in self.choices]
        if self.channel_types:
            base['channel_types'] = [t.value for t in self.channel_types]
        if self.autocomplete:
            base['autocomplete'] = True
        if self.min_value is not None:
            base['min_value'] = self.min_value
        if self.max_value is not None:
            base['max_value'] = self.max_value

        return base


annotation_to_option_type: Dict[Any, AppCommandOptionType] = {
    str: AppCommandOptionType.string,
    int: AppCommandOptionType.integer,
    float: AppCommandOptionType.number,
    bool: AppCommandOptionType.boolean,
    User: AppCommandOptionType.user,
    Member: AppCommandOptionType.user,
    Role: AppCommandOptionType.role,
    # StageChannel: AppCommandOptionType.channel,
    # StoreChannel: AppCommandOptionType.channel,
    # VoiceChannel: AppCommandOptionType.channel,
    # TextChannel: AppCommandOptionType.channel,
}

NoneType = type(None)
allowed_default_types: Dict[AppCommandOptionType, Tuple[Type[Any], ...]] = {
    AppCommandOptionType.string: (str, NoneType),
    AppCommandOptionType.integer: (int, NoneType),
    AppCommandOptionType.boolean: (bool, NoneType),
}


# Some sanity checks:
# str => string
# int => int
# User => user
# etc ...
# Optional[str] => string, required: false, default: None
# Optional[int] => integer, required: false, default: None
# Optional[Model] = None => resolved, required: false, default: None
# Optional[Model] can only have (CommandParameter, None) as default
# Optional[int | str | bool] can have (CommandParameter, None, int | str | bool) as a default
# Union[str, Member] => disallowed
# Union[int, str] => disallowed
# Union[Member, User] => user
# Optional[Union[Member, User]] => user, required: false, default: None
# Union[Member, User, Object] => mentionable
# Union[Models] => mentionable
# Optional[Union[Models]] => mentionable, required: false, default: None


def _annotation_to_type(
    annotation: Any,
    *,
    mapping=annotation_to_option_type,
    _none=NoneType,
) -> Tuple[AppCommandOptionType, Any]:
    # Straight simple case, a regular ol' parameter
    try:
        option_type = mapping[annotation]
    except KeyError:
        pass
    else:
        return (option_type, MISSING)

    # Check if there's an origin
    origin = getattr(annotation, '__origin__', None)
    if origin is not Union:  # TODO: Python 3.10
        # Only Union/Optional is supported so bail early
        raise TypeError(f'unsupported type annotation {annotation!r}')

    default = MISSING
    if annotation.__args__[-1] is _none:
        if len(annotation.__args__) == 2:
            underlying = annotation.__args__[0]
            option_type = mapping.get(underlying)
            if option_type is None:
                raise TypeError(f'unsupported inner optional type {underlying!r}')
            return (option_type, None)
        else:
            args = annotation.__args__[:-1]
            default = None
    else:
        args = annotation.__args__

    # At this point only models are allowed
    # Since Optional[int | bool | str] will be taken care of above
    # The only valid transformations here are:
    # [Member, User] => user
    # [Member, User, Role] => mentionable
    # [Member | User, Role] => mentionable
    supported_types: Set[Any] = {Role, Member, User}
    if not all(arg in supported_types for arg in args):
        raise TypeError(f'unsupported types given inside {annotation!r}')
    if args == (User, Member) or args == (Member, User):
        return (AppCommandOptionType.user, default)

    return (AppCommandOptionType.mentionable, default)


def _populate_descriptions(params: Dict[str, CommandParameter], descriptions: Dict[str, Any]) -> None:
    for name, param in params.items():
        description = descriptions.pop(name, MISSING)
        if description is MISSING:
            param.description = '...'
            continue

        if not isinstance(description, str):
            raise TypeError('description must be a string')

        param.description = description

    if descriptions:
        first = next(iter(descriptions))
        raise TypeError(f'unknown parameter given: {first}')


def _get_parameter(annotation: Any, parameter: inspect.Parameter) -> CommandParameter:
    (type, default) = _annotation_to_type(annotation)
    if default is MISSING:
        default = parameter.default
        if default is parameter.empty:
            default = MISSING

    result = CommandParameter(
        type=type,
        default=default,
        required=default is MISSING,
        name=parameter.name,
    )

    if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL):
        raise TypeError(f'unsupported parameter kind in callback: {parameter.kind!s}')

    # Verify validity of the default parameter
    if result.default is not MISSING:
        valid_types: Tuple[Any, ...] = allowed_default_types.get(result.type, (NoneType,))
        if not isinstance(result.default, valid_types):
            raise TypeError(f'invalid default parameter type given ({result.default.__class__}), expected {valid_types}')

    result.annotation = annotation
    return result


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
        param = _get_parameter(resolved, parameter)
        parameters.append(param)

    values = sorted(parameters, key=lambda a: a.required, reverse=True)
    result = {v.name: v for v in values}

    try:
        descriptions = func.__discord_app_commands_param_description__
    except AttributeError:
        pass
    else:
        _populate_descriptions(result, descriptions)

    return result


class Command(Generic[GroupT, P, T]):
    """A class that implements an application command.

    These are usually not created manually, instead they are created using
    one of the following decorators:

    - :func:`~discord.app_commands.command`
    - :meth:`Group.command <discord.app_commands.Group.command>`

    .. versionadded:: 2.0

    Attributes
    ------------
    name: :class:`str`
        The name of the application command.
    type: :class:`AppCommandType`
        The type of application command.
    callback: :ref:`coroutine <coroutine>`
        The coroutine that is executed when the command is called.
    description: :class:`str`
        The description of the application command. This shows up in the UI to describe
        the application command.
    parent: Optional[:class:`CommandGroup`]
        The parent application command. ``None`` if there isn't one.
    """

    def __init__(
        self,
        *,
        name: str,
        description: str,
        callback: CommandCallback[GroupT, P, T],
        type: AppCommandType = AppCommandType.chat_input,
        parent: Optional[Group] = None,
    ):
        self.name: str = name
        self.description: str = description
        self._callback: CommandCallback[GroupT, P, T] = callback
        self.parent: Optional[Group] = parent
        self.binding: Optional[GroupT] = None
        self.type: AppCommandType = type
        self._params: Dict[str, CommandParameter] = _extract_parameters_from_callback(callback, callback.__globals__)

    def _copy_with_binding(self, binding: GroupT) -> Command:
        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy.description = self.description
        copy._callback = self._callback
        copy.parent = self.parent
        copy.type = self.type
        copy._params = self._params.copy()
        copy.binding = binding
        return copy

    def to_dict(self) -> Dict[str, Any]:
        # If we have a parent then our type is a subcommand
        # Otherwise, the type falls back to the specific command type (e.g. slash command or context menu)
        option_type = self.type.value if self.parent is None else AppCommandOptionType.subcommand.value
        return {
            'name': self.name,
            'description': self.description,
            'type': option_type,
            'options': [param.to_dict() for param in self._params.values()],
        }

    async def _invoke_with_namespace(self, interaction: Interaction, namespace: Namespace) -> T:
        defaults = ((name, param.default) for name, param in self._params.items() if not param.required)
        namespace._update_with_defaults(defaults)
        # These type ignores are because the type checker doesn't quite understand the narrowing here
        # Likewise, it thinks we're missing positional arguments when there aren't any.
        try:
            if self.binding is not None:
                return await self._callback(self.binding, interaction, **namespace.__dict__)  # type: ignore
            return await self._callback(interaction, **namespace.__dict__)  # type: ignore
        except TypeError:
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
            raise

    def get_parameter(self, name: str) -> Optional[CommandParameter]:
        """Returns the :class:`CommandParameter` with the given name.

        Parameters
        -----------
        name: :class:`str`
            The parameter name to get.

        Returns
        --------
        Optional[:class:`CommandParameter`]
            The command parameter, if found.
        """
        return self._params.get(name)

    @property
    def root_parent(self) -> Optional[Group]:
        """Optional[:class:`Group`]: The root parent of this command."""
        if self.parent is None:
            return None
        parent = self.parent
        return parent.parent or parent

    def _get_internal_command(self, name: str) -> Optional[Union[Command, Group]]:
        return None


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
    parent: Optional[:class:`CommandGroup`]
        The parent group. ``None`` if there isn't one.
    """

    __discord_app_commands_group_children__: ClassVar[List[Union[Command, Group]]] = []
    __discord_app_commands_group_name__: str = MISSING
    __discord_app_commands_group_description__: str = MISSING

    def __init_subclass__(cls, *, name: str = MISSING, description: str = MISSING) -> None:
        cls.__discord_app_commands_group_children__ = children = [
            member for member in cls.__dict__.values() if isinstance(member, (Group, Command)) and member.parent is None
        ]

        found = set()
        for child in children:
            if child.name in found:
                raise TypeError(f'Command {child.name} is a duplicate')
            found.add(child.name)

        if name is MISSING:
            cls.__discord_app_commands_group_name__ = _to_kebab_case(cls.__name__)
        else:
            cls.__discord_app_commands_group_name__ = name

        if description is MISSING:
            if cls.__doc__ is None:
                cls.__discord_app_commands_group_description__ = '...'
            else:
                cls.__discord_app_commands_group_description__ = _shorten(cls.__doc__)
        else:
            cls.__discord_app_commands_group_description__ = description

        if len(children) > 25:
            raise TypeError('groups cannot have more than 25 commands')

    def __init__(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        parent: Optional[Group] = None,
    ):
        cls = self.__class__
        self.name: str = name if name is not MISSING else cls.__discord_app_commands_group_name__
        self.description: str = description or cls.__discord_app_commands_group_description__

        if not self.description:
            raise TypeError('groups must have a description')

        self.parent: Optional[Group] = parent

        self._children: Dict[str, Union[Command, Group]] = {
            child.name: child._copy_with_binding(self) for child in self.__discord_app_commands_group_children__
        }

        for child in self._children.values():
            child.parent = self

        if parent is not None and parent.parent is not None:
            raise ValueError('groups can only be nested at most one level')

    def _copy_with_binding(self, binding: Group) -> Group:
        cls = self.__class__
        copy = cls.__new__(cls)
        copy.name = self.name
        copy.description = self.description
        copy.parent = self.parent
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

    def _get_internal_command(self, name: str) -> Optional[Union[Command, Group]]:
        return self._children.get(name)

    def add_command(self, command: Union[Command, Group], /, *, override: bool = False):
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
            There are too many commands already registered.
        """

        if not override and command.name in self._children:
            raise CommandAlreadyRegistered(command.name, guild_id=None)

        self._children[command.name] = command
        if len(self._children) > 25:
            raise ValueError('maximum number of child commands exceeded')

    def remove_command(self, name: str, /) -> Optional[Union[Command, Group]]:
        """Remove a command or group from the internal list of commands.

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

    def get_command(self, name: str, /) -> Optional[Union[Command, Group]]:
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
                    desc = '...'
                else:
                    desc = _shorten(func.__doc__)
            else:
                desc = description

            command = Command(
                name=name if name is not MISSING else func.__name__,
                description=desc,
                callback=func,
                type=AppCommandType.chat_input,
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
                desc = '...'
            else:
                desc = _shorten(func.__doc__)
        else:
            desc = description

        return Command(
            name=name if name is not MISSING else func.__name__,
            description=desc,
            callback=func,
            type=AppCommandType.chat_input,
            parent=None,
        )

    return decorator


def describe(**parameters: str) -> Callable[[T], T]:
    r"""Describes the given parameters by their name using the key of the keyword argument
    as the name.

    Example:

    .. code-block:: python3

        @app_commands.command()
        @app_commads.describe(member='the member to ban')
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
            inner.__discord_app_commands_param_description__ = parameters  # type: ignore - Runtime attribute assignment

        return inner

    return decorator
