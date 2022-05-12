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

from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from .errors import AppCommandError, TransformerError
from .models import AppCommandChannel, AppCommandThread, Choice
from ..channel import StageChannel, VoiceChannel, TextChannel, CategoryChannel
from ..threads import Thread
from ..enums import Enum as InternalEnum, AppCommandOptionType, ChannelType
from ..utils import MISSING, maybe_coroutine
from ..user import User
from ..role import Role
from ..member import Member
from ..message import Attachment

__all__ = (
    'Transformer',
    'Transform',
    'Range',
)

T = TypeVar('T')
FuncT = TypeVar('FuncT', bound=Callable[..., Any])
ChoiceT = TypeVar('ChoiceT', str, int, float, Union[str, int, float])
NoneType = type(None)

if TYPE_CHECKING:
    from ..interactions import Interaction


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
    type: :class:`~discord.AppCommandOptionType`
        The underlying type of this parameter.
    channel_types: List[:class:`~discord.ChannelType`]
        The channel types that are allowed for this parameter.
    min_value: Optional[Union[:class:`int`, :class:`float`]]
        The minimum supported value for this parameter.
    max_value: Optional[Union[:class:`int`, :class:`float`]]
        The maximum supported value for this parameter.
    """

    name: str = MISSING
    description: str = MISSING
    required: bool = MISSING
    default: Any = MISSING
    choices: List[Choice[Union[str, int, float]]] = MISSING
    type: AppCommandOptionType = MISSING
    channel_types: List[ChannelType] = MISSING
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    autocomplete: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    _rename: str = MISSING
    _annotation: Any = MISSING

    def to_dict(self) -> Dict[str, Any]:
        base = {
            'type': self.type.value,
            'name': self.display_name,
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

    def is_choice_annotation(self) -> bool:
        return getattr(self._annotation, '__discord_app_commands_is_choice__', False)

    async def transform(self, interaction: Interaction, value: Any) -> Any:
        if hasattr(self._annotation, '__discord_app_commands_transformer__'):
            # This one needs special handling for type safety reasons
            if self._annotation.__discord_app_commands_is_choice__:
                choice = next((c for c in self.choices if c.value == value), None)
                if choice is None:
                    raise TransformerError(value, self.type, self._annotation)
                return choice

            try:
                # ParamSpec doesn't understand that transform is a callable since it's unbound
                return await maybe_coroutine(self._annotation.transform, interaction, value)  # type: ignore
            except AppCommandError:
                raise
            except Exception as e:
                raise TransformerError(value, self.type, self._annotation) from e

        return value

    @property
    def display_name(self) -> str:
        """:class:`str`: The name of the parameter as it should be displayed to the user."""
        return self.name if self._rename is MISSING else self._rename


class Transformer:
    """The base class that allows a type annotation in an application command parameter
    to map into a :class:`~discord.AppCommandOptionType` and transform the raw value into one
    from this type.

    This class is customisable through the overriding of :func:`classmethod` in the class
    and by using it as the second type parameter of the :class:`~discord.app_commands.Transform`
    class. For example, to convert a string into a custom pair type:

    .. code-block:: python3

        class Point(typing.NamedTuple):
            x: int
            y: int

        class PointTransformer(app_commands.Transformer):
            @classmethod
            async def transform(cls, interaction: discord.Interaction, value: str) -> Point:
                (x, _, y) = value.partition(',')
                return Point(x=int(x.strip()), y=int(y.strip()))

        @app_commands.command()
        async def graph(
            interaction: discord.Interaction,
            point: app_commands.Transform[Point, PointTransformer],
        ):
            await interaction.response.send_message(str(point))

    .. versionadded:: 2.0
    """

    __discord_app_commands_transformer__: ClassVar[bool] = True
    __discord_app_commands_is_choice__: ClassVar[bool] = False

    @classmethod
    def type(cls) -> AppCommandOptionType:
        """:class:`~discord.AppCommandOptionType`: The option type associated with this transformer.

        This must be a :obj:`classmethod`.

        Defaults to :attr:`~discord.AppCommandOptionType.string`.
        """
        return AppCommandOptionType.string

    @classmethod
    def channel_types(cls) -> List[ChannelType]:
        """List[:class:`~discord.ChannelType`]: A list of channel types that are allowed to this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.channel`.

        Defaults to an empty list.
        """
        return []

    @classmethod
    def min_value(cls) -> Optional[Union[int, float]]:
        """Optional[:class:`int`]: The minimum supported value for this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.number` or
        :attr:`~discord.AppCommandOptionType.integer`.

        Defaults to ``None``.
        """
        return None

    @classmethod
    def max_value(cls) -> Optional[Union[int, float]]:
        """Optional[:class:`int`]: The maximum supported value for this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.number` or
        :attr:`~discord.AppCommandOptionType.integer`.

        Defaults to ``None``.
        """
        return None

    @classmethod
    async def transform(cls, interaction: Interaction, value: Any) -> Any:
        """|maybecoro|

        Transforms the converted option value into another value.

        The value passed into this transform function is the same as the
        one in the :class:`conversion table <discord.app_commands.Namespace>`.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction being handled.
        value: Any
            The value of the given argument after being resolved.
            See the :class:`conversion table <discord.app_commands.Namespace>`
            for how certain option types correspond to certain values.
        """
        raise NotImplementedError('Derived classes need to implement this.')

    @classmethod
    async def autocomplete(
        cls, interaction: Interaction, value: Union[int, float, str]
    ) -> List[Choice[Union[int, float, str]]]:
        """|coro|

        An autocomplete prompt handler to be automatically used by options using this transformer.

        .. note::

            Autocomplete is only supported for options with a :meth:`~discord.app_commands.Transformer.type`
            of :attr:`~discord.AppCommandOptionType.string`, :attr:`~discord.AppCommandOptionType.integer`,
            or :attr:`~discord.AppCommandOptionType.number`.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The autocomplete interaction being handled.
        value: Union[:class:`str`, :class:`int`, :class:`float`]
            The current value entered by the user.

        Returns
        --------
        List[:class:`~discord.app_commands.Choice`]
            A list of choices to be displayed to the user, a maximum of 25.

        """
        raise NotImplementedError('Derived classes can implement this.')


class _TransformMetadata:
    __discord_app_commands_transform__: ClassVar[bool] = True
    __slots__ = ('metadata',)

    def __init__(self, metadata: Type[Transformer]):
        self.metadata: Type[Transformer] = metadata

    # This is needed to pass typing's type checks.
    # e.g. Optional[Transform[discord.Member, MyTransformer]]
    def __call__(self) -> None:
        pass


async def _identity_transform(cls, interaction: Interaction, value: Any) -> Any:
    return value


def _make_range_transformer(
    opt_type: AppCommandOptionType,
    *,
    min: Optional[Union[int, float]] = None,
    max: Optional[Union[int, float]] = None,
) -> Type[Transformer]:
    ns = {
        'type': classmethod(lambda _: opt_type),
        'min_value': classmethod(lambda _: min),
        'max_value': classmethod(lambda _: max),
        'transform': classmethod(_identity_transform),
    }
    return type('RangeTransformer', (Transformer,), ns)


def _make_literal_transformer(values: Tuple[Any, ...]) -> Type[Transformer]:
    first = type(values[0])
    if first is int:
        opt_type = AppCommandOptionType.integer
    elif first is float:
        opt_type = AppCommandOptionType.number
    elif first is str:
        opt_type = AppCommandOptionType.string
    else:
        raise TypeError(f'expected int, str, or float values not {first!r}')

    ns = {
        'type': classmethod(lambda _: opt_type),
        'transform': classmethod(_identity_transform),
        '__discord_app_commands_transformer_choices__': [Choice(name=str(v), value=v) for v in values],
    }
    return type('LiteralTransformer', (Transformer,), ns)


def _make_choice_transformer(inner_type: Any) -> Type[Transformer]:
    if inner_type is int:
        opt_type = AppCommandOptionType.integer
    elif inner_type is float:
        opt_type = AppCommandOptionType.number
    elif inner_type is str:
        opt_type = AppCommandOptionType.string
    else:
        raise TypeError(f'expected int, str, or float values not {inner_type!r}')

    ns = {
        'type': classmethod(lambda _: opt_type),
        'transform': classmethod(_identity_transform),
        '__discord_app_commands_is_choice__': True,
    }
    return type('ChoiceTransformer', (Transformer,), ns)


def _make_enum_transformer(enum) -> Type[Transformer]:
    values = list(enum)
    if len(values) < 2:
        raise TypeError(f'enum.Enum requires at least two values.')

    first = type(values[0].value)
    if first is int:
        opt_type = AppCommandOptionType.integer
    elif first is float:
        opt_type = AppCommandOptionType.number
    elif first is str:
        opt_type = AppCommandOptionType.string
    else:
        raise TypeError(f'expected int, str, or float values not {first!r}')

    async def transform(cls, interaction: Interaction, value: Any) -> Any:
        return enum(value)

    ns = {
        'type': classmethod(lambda _: opt_type),
        'transform': classmethod(transform),
        '__discord_app_commands_transformer_enum__': enum,
        '__discord_app_commands_transformer_choices__': [Choice(name=v.name, value=v.value) for v in values],
    }

    return type(f'{enum.__name__}EnumTransformer', (Transformer,), ns)


def _make_complex_enum_transformer(enum) -> Type[Transformer]:
    values = list(enum)
    if len(values) < 2:
        raise TypeError(f'enum.Enum requires at least two values.')

    async def transform(cls, interaction: Interaction, value: Any) -> Any:
        return enum[value]

    ns = {
        'type': classmethod(lambda _: AppCommandOptionType.string),
        'transform': classmethod(transform),
        '__discord_app_commands_transformer_enum__': enum,
        '__discord_app_commands_transformer_choices__': [Choice(name=v.name, value=v.name) for v in values],
    }

    return type(f'{enum.__name__}ComplexEnumTransformer', (Transformer,), ns)


if TYPE_CHECKING:
    from typing_extensions import Annotated as Transform
    from typing_extensions import Annotated as Range
else:

    class Transform:
        """A type annotation that can be applied to a parameter to customise the behaviour of
        an option type by transforming with the given :class:`Transformer`. This requires
        the usage of two generic parameters, the first one is the type you're converting to and the second
        one is the type of the :class:`Transformer` actually doing the transformation.

        During type checking time this is equivalent to :obj:`typing.Annotated` so type checkers understand
        the intent of the code.

        For example usage, check :class:`Transformer`.

        .. versionadded:: 2.0
        """

        def __class_getitem__(cls, items) -> _TransformMetadata:
            if not isinstance(items, tuple):
                raise TypeError(f'expected tuple for arguments, received {items.__class__!r} instead')

            if len(items) != 2:
                raise TypeError(f'Transform only accepts exactly two arguments')

            _, transformer = items

            is_valid = inspect.isclass(transformer) and issubclass(transformer, Transformer)
            if not is_valid:
                raise TypeError(f'second argument of Transform must be a Transformer class not {transformer!r}')

            return _TransformMetadata(transformer)

    class Range:
        """A type annotation that can be applied to a parameter to require a numeric type
        to fit within the range provided.

        During type checking time this is equivalent to :obj:`typing.Annotated` so type checkers understand
        the intent of the code.

        Some example ranges:

        - ``Range[int, 10]`` means the minimum is 10 with no maximum.
        - ``Range[int, None, 10]`` means the maximum is 10 with no minimum.
        - ``Range[int, 1, 10]`` means the minimum is 1 and the maximum is 10.

        .. versionadded:: 2.0

        Examples
        ----------

        .. code-block:: python3

            @app_commands.command()
            async def range(interaction: discord.Interaction, value: app_commands.Range[int, 10, 12]):
                await interaction.response.send_message(f'Your value is {value}', ephemeral=True)
        """

        def __class_getitem__(cls, obj) -> _TransformMetadata:
            if not isinstance(obj, tuple):
                raise TypeError(f'expected tuple for arguments, received {obj.__class__!r} instead')

            if len(obj) == 2:
                obj = (*obj, None)
            elif len(obj) != 3:
                raise TypeError('Range accepts either two or three arguments with the first being the type of range.')

            obj_type, min, max = obj

            if min is None and max is None:
                raise TypeError('Range must not be empty')

            if min is not None and max is not None:
                # At this point max and min are both not none
                if type(min) != type(max):
                    raise TypeError('Both min and max in Range must be the same type')

            if obj_type is int:
                opt_type = AppCommandOptionType.integer
            elif obj_type is float:
                opt_type = AppCommandOptionType.number
            else:
                raise TypeError(f'expected int or float as range type, received {obj_type!r} instead')

            transformer = _make_range_transformer(
                opt_type,
                min=obj_type(min) if min is not None else None,
                max=obj_type(max) if max is not None else None,
            )
            return _TransformMetadata(transformer)


def passthrough_transformer(opt_type: AppCommandOptionType) -> Type[Transformer]:
    class _Generated(Transformer):
        @classmethod
        def type(cls) -> AppCommandOptionType:
            return opt_type

        @classmethod
        async def transform(cls, interaction: Interaction, value: Any) -> Any:
            return value

    return _Generated


class MemberTransformer(Transformer):
    @classmethod
    def type(cls) -> AppCommandOptionType:
        return AppCommandOptionType.user

    @classmethod
    async def transform(cls, interaction: Interaction, value: Any) -> Member:
        if not isinstance(value, Member):
            raise TransformerError(value, cls.type(), cls)
        return value


def channel_transformer(*channel_types: Type[Any], raw: Optional[bool] = False) -> Type[Transformer]:
    if raw:

        async def transform(cls, interaction: Interaction, value: Any):
            if not isinstance(value, channel_types):
                raise TransformerError(value, AppCommandOptionType.channel, cls)
            return value

    elif raw is False:

        async def transform(cls, interaction: Interaction, value: Any):
            resolved = value.resolve()
            if resolved is None or not isinstance(resolved, channel_types):
                raise TransformerError(value, AppCommandOptionType.channel, cls)
            return resolved

    else:

        async def transform(cls, interaction: Interaction, value: Any):
            if isinstance(value, channel_types):
                return value

            resolved = value.resolve()
            if resolved is None or not isinstance(resolved, channel_types):
                raise TransformerError(value, AppCommandOptionType.channel, cls)
            return resolved

    if len(channel_types) == 1:
        name = channel_types[0].__name__
        types = CHANNEL_TO_TYPES[channel_types[0]]
    else:
        name = 'MultiChannel'
        types = []

        for t in channel_types:
            try:
                types.extend(CHANNEL_TO_TYPES[t])
            except KeyError:
                raise TypeError(f'Union type of channels must be entirely made up of channels') from None

    return type(
        f'{name}Transformer',
        (Transformer,),
        {
            'type': classmethod(lambda cls: AppCommandOptionType.channel),
            'transform': classmethod(transform),
            'channel_types': classmethod(lambda cls: types),
        },
    )


CHANNEL_TO_TYPES: Dict[Any, List[ChannelType]] = {
    AppCommandChannel: [
        ChannelType.stage_voice,
        ChannelType.voice,
        ChannelType.text,
        ChannelType.news,
        ChannelType.category,
    ],
    AppCommandThread: [ChannelType.news_thread, ChannelType.private_thread, ChannelType.public_thread],
    Thread: [ChannelType.news_thread, ChannelType.private_thread, ChannelType.public_thread],
    StageChannel: [ChannelType.stage_voice],
    VoiceChannel: [ChannelType.voice],
    TextChannel: [ChannelType.text, ChannelType.news],
    CategoryChannel: [ChannelType.category],
}

BUILT_IN_TRANSFORMERS: Dict[Any, Type[Transformer]] = {
    str: passthrough_transformer(AppCommandOptionType.string),
    int: passthrough_transformer(AppCommandOptionType.integer),
    float: passthrough_transformer(AppCommandOptionType.number),
    bool: passthrough_transformer(AppCommandOptionType.boolean),
    User: passthrough_transformer(AppCommandOptionType.user),
    Member: MemberTransformer,
    Role: passthrough_transformer(AppCommandOptionType.role),
    AppCommandChannel: channel_transformer(AppCommandChannel, raw=True),
    AppCommandThread: channel_transformer(AppCommandThread, raw=True),
    Thread: channel_transformer(Thread),
    StageChannel: channel_transformer(StageChannel),
    VoiceChannel: channel_transformer(VoiceChannel),
    TextChannel: channel_transformer(TextChannel),
    CategoryChannel: channel_transformer(CategoryChannel),
    Attachment: passthrough_transformer(AppCommandOptionType.attachment),
}

ALLOWED_DEFAULTS: Dict[AppCommandOptionType, Tuple[Type[Any], ...]] = {
    AppCommandOptionType.string: (str, NoneType),
    AppCommandOptionType.integer: (int, NoneType),
    AppCommandOptionType.boolean: (bool, NoneType),
    AppCommandOptionType.number: (float, NoneType),
}


def get_supported_annotation(
    annotation: Any,
    *,
    _none: type = NoneType,
    _mapping: Dict[Any, Type[Transformer]] = BUILT_IN_TRANSFORMERS,
) -> Tuple[Any, Any]:
    """Returns an appropriate, yet supported, annotation along with an optional default value.

    This differs from the built in mapping by supporting a few more things.
    Likewise, this returns a "transformed" annotation that is ready to use with CommandParameter.transform.
    """

    try:
        return (_mapping[annotation], MISSING)
    except KeyError:
        pass

    if hasattr(annotation, '__discord_app_commands_transform__'):
        return (annotation.metadata, MISSING)

    if hasattr(annotation, '__metadata__'):
        return get_supported_annotation(annotation.__metadata__[0])

    if inspect.isclass(annotation):
        if issubclass(annotation, Transformer):
            return (annotation, MISSING)
        if issubclass(annotation, (Enum, InternalEnum)):
            if all(isinstance(v.value, (str, int, float)) for v in annotation):
                return (_make_enum_transformer(annotation), MISSING)
            else:
                return (_make_complex_enum_transformer(annotation), MISSING)
        if annotation is Choice:
            raise TypeError(f'Choice requires a type argument of int, str, or float')

    # Check if there's an origin
    origin = getattr(annotation, '__origin__', None)
    if origin is Literal:
        args = annotation.__args__  # type: ignore
        return (_make_literal_transformer(args), MISSING)

    if origin is Choice:
        arg = annotation.__args__[0]  # type: ignore
        return (_make_choice_transformer(arg), MISSING)

    if origin is not Union:
        # Only Union/Optional is supported right now so bail early
        raise TypeError(f'unsupported type annotation {annotation!r}')

    default = MISSING
    args = annotation.__args__  # type: ignore
    if args[-1] is _none:
        if len(args) == 2:
            underlying = args[0]
            inner, _ = get_supported_annotation(underlying)
            if inner is None:
                raise TypeError(f'unsupported inner optional type {underlying!r}')
            return (inner, None)
        else:
            args = args[:-1]
            default = None

    # Check for channel union types
    if any(arg in CHANNEL_TO_TYPES for arg in args):
        # If any channel type is given, then *all* must be channel types
        return (channel_transformer(*args, raw=None), default)

    # The only valid transformations here are:
    # [Member, User] => user
    # [Member, User, Role] => mentionable
    # [Member | User, Role] => mentionable
    supported_types: Set[Any] = {Role, Member, User}
    if not all(arg in supported_types for arg in args):
        raise TypeError(f'unsupported types given inside {annotation!r}')
    if args == (User, Member) or args == (Member, User):
        return (passthrough_transformer(AppCommandOptionType.user), default)

    return (passthrough_transformer(AppCommandOptionType.mentionable), default)


def annotation_to_parameter(annotation: Any, parameter: inspect.Parameter) -> CommandParameter:
    """Returns the appropriate :class:`CommandParameter` for the given annotation.

    The resulting ``_annotation`` attribute might not match the one given here and might
    be transformed in order to be easier to call from the ``transform`` asynchronous function
    of a command parameter.
    """

    (inner, default) = get_supported_annotation(annotation)
    type = inner.type()

    if default is MISSING or default is None:
        param_default = parameter.default
        if param_default is not parameter.empty:
            default = param_default

    # Verify validity of the default parameter
    if default is not MISSING:
        enum_type = getattr(inner, '__discord_app_commands_transformer_enum__', None)
        if default.__class__ is not enum_type:
            valid_types: Tuple[Any, ...] = ALLOWED_DEFAULTS.get(type, (NoneType,))
            if not isinstance(default, valid_types):
                raise TypeError(f'invalid default parameter type given ({default.__class__}), expected {valid_types}')

    result = CommandParameter(
        type=type,
        _annotation=inner,
        default=default,
        required=default is MISSING,
        name=parameter.name,
    )

    try:
        choices = inner.__discord_app_commands_transformer_choices__
    except AttributeError:
        pass
    else:
        result.choices = choices

    # These methods should be duck typed
    if type in (AppCommandOptionType.number, AppCommandOptionType.integer):
        result.min_value = inner.min_value()
        result.max_value = inner.max_value()

    if type is AppCommandOptionType.channel:
        result.channel_types = inner.channel_types()

    if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL):
        raise TypeError(f'unsupported parameter kind in callback: {parameter.kind!s}')

    autocomplete_func = getattr(inner.autocomplete, '__func__', inner.autocomplete)
    if autocomplete_func is not Transformer.autocomplete.__func__:
        from .commands import _validate_auto_complete_callback

        result.autocomplete = _validate_auto_complete_callback(inner.autocomplete, skip_binding=True)

    return result
