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
    Generic,
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
from .translator import TranslationContextLocation, TranslationContext, Translator, locale_str
from ..channel import StageChannel, VoiceChannel, TextChannel, CategoryChannel, ForumChannel
from ..abc import GuildChannel
from ..threads import Thread
from ..enums import Enum as InternalEnum, AppCommandOptionType, ChannelType, Locale
from ..utils import MISSING, maybe_coroutine, _human_join
from ..user import User
from ..role import Role
from ..member import Member
from ..message import Attachment
from .._types import ClientT

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
    from .commands import Parameter


@dataclass
class CommandParameter:
    # The name of the parameter is *always* the parameter name in the code
    # Therefore, it can't be Union[str, locale_str]
    name: str = MISSING
    description: Union[str, locale_str] = MISSING
    required: bool = MISSING
    default: Any = MISSING
    choices: List[Choice[Union[str, int, float]]] = MISSING
    type: AppCommandOptionType = MISSING
    channel_types: List[ChannelType] = MISSING
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    autocomplete: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    _rename: Union[str, locale_str] = MISSING
    _annotation: Any = MISSING

    async def get_translated_payload(self, translator: Translator, data: Parameter) -> Dict[str, Any]:
        base = self.to_dict()

        rename = self._rename
        description = self.description
        needs_name_translations = isinstance(rename, locale_str)
        needs_description_translations = isinstance(description, locale_str)
        name_localizations: Dict[str, str] = {}
        description_localizations: Dict[str, str] = {}

        # Prevent creating these objects in a heavy loop
        name_context = TranslationContext(location=TranslationContextLocation.parameter_name, data=data)
        description_context = TranslationContext(location=TranslationContextLocation.parameter_description, data=data)
        for locale in Locale:
            if needs_name_translations:
                translation = await translator._checked_translate(rename, locale, name_context)
                if translation is not None:
                    name_localizations[locale.value] = translation

            if needs_description_translations:
                translation = await translator._checked_translate(description, locale, description_context)
                if translation is not None:
                    description_localizations[locale.value] = translation

        if self.choices:
            base['choices'] = [await choice.get_translated_payload(translator) for choice in self.choices]

        if name_localizations:
            base['name_localizations'] = name_localizations

        if description_localizations:
            base['description_localizations'] = description_localizations

        return base

    def to_dict(self) -> Dict[str, Any]:
        base = {
            'type': self.type.value,
            'name': self.display_name,
            'description': str(self.description),
            'required': self.required,
        }

        if self.choices:
            base['choices'] = [choice.to_dict() for choice in self.choices]
        if self.channel_types:
            base['channel_types'] = [t.value for t in self.channel_types]
        if self.autocomplete:
            base['autocomplete'] = True

        min_key, max_key = (
            ('min_value', 'max_value') if self.type is not AppCommandOptionType.string else ('min_length', 'max_length')
        )
        if self.min_value is not None:
            base[min_key] = self.min_value
        if self.max_value is not None:
            base[max_key] = self.max_value

        return base

    def _convert_to_locale_strings(self) -> None:
        if self._rename is MISSING:
            self._rename = locale_str(self.name)
        elif isinstance(self._rename, str):
            self._rename = locale_str(self._rename)

        if isinstance(self.description, str):
            self.description = locale_str(self.description)

        if self.choices:
            for choice in self.choices:
                if choice._locale_name is None:
                    choice._locale_name = locale_str(choice.name)

    def is_choice_annotation(self) -> bool:
        return getattr(self._annotation, '__discord_app_commands_is_choice__', False)

    async def transform(self, interaction: Interaction, value: Any, /) -> Any:
        if hasattr(self._annotation, '__discord_app_commands_transformer__'):
            # This one needs special handling for type safety reasons
            if self._annotation.__discord_app_commands_is_choice__:
                choice = next((c for c in self.choices if c.value == value), None)
                if choice is None:
                    raise TransformerError(value, self.type, self._annotation)
                return choice

            try:
                return await maybe_coroutine(self._annotation.transform, interaction, value)
            except AppCommandError:
                raise
            except Exception as e:
                raise TransformerError(value, self.type, self._annotation) from e

        return value

    @property
    def display_name(self) -> str:
        """:class:`str`: The name of the parameter as it should be displayed to the user."""
        return self.name if self._rename is MISSING else str(self._rename)


class Transformer(Generic[ClientT]):
    """The base class that allows a type annotation in an application command parameter
    to map into a :class:`~discord.AppCommandOptionType` and transform the raw value into one
    from this type.

    This class is customisable through the overriding of methods and properties in the class
    and by using it as the second type parameter of the :class:`~discord.app_commands.Transform`
    class. For example, to convert a string into a custom pair type:

    .. code-block:: python3

        class Point(typing.NamedTuple):
            x: int
            y: int

        class PointTransformer(app_commands.Transformer):
            async def transform(self, interaction: discord.Interaction, value: str) -> Point:
                (x, _, y) = value.partition(',')
                return Point(x=int(x.strip()), y=int(y.strip()))

        @app_commands.command()
        async def graph(
            interaction: discord.Interaction,
            point: app_commands.Transform[Point, PointTransformer],
        ):
            await interaction.response.send_message(str(point))

    If a class is passed instead of an instance to the second type parameter, then it is
    constructed with no arguments passed to the ``__init__`` method.

    .. versionadded:: 2.0
    """

    __discord_app_commands_transformer__: ClassVar[bool] = True
    __discord_app_commands_is_choice__: ClassVar[bool] = False

    # This is needed to pass typing's type checks.
    # e.g. Optional[MyTransformer]
    def __call__(self) -> None:
        pass

    def __or__(self, rhs: Any) -> Any:
        return Union[self, rhs]

    @property
    def type(self) -> AppCommandOptionType:
        """:class:`~discord.AppCommandOptionType`: The option type associated with this transformer.

        This must be a :obj:`property`.

        Defaults to :attr:`~discord.AppCommandOptionType.string`.
        """
        return AppCommandOptionType.string

    @property
    def channel_types(self) -> List[ChannelType]:
        """List[:class:`~discord.ChannelType`]: A list of channel types that are allowed to this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.channel`.

        This must be a :obj:`property`.

        Defaults to an empty list.
        """
        return []

    @property
    def min_value(self) -> Optional[Union[int, float]]:
        """Optional[:class:`int`]: The minimum supported value for this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.number`
        :attr:`~discord.AppCommandOptionType.integer`, or :attr:`~discord.AppCommandOptionType.string`.

        This must be a :obj:`property`.

        Defaults to ``None``.
        """
        return None

    @property
    def max_value(self) -> Optional[Union[int, float]]:
        """Optional[:class:`int`]: The maximum supported value for this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.number`
        :attr:`~discord.AppCommandOptionType.integer`, or :attr:`~discord.AppCommandOptionType.string`.

        This must be a :obj:`property`.

        Defaults to ``None``.
        """
        return None

    @property
    def choices(self) -> Optional[List[Choice[Union[int, float, str]]]]:
        """Optional[List[:class:`~discord.app_commands.Choice`]]: A list of up to 25 choices that are allowed to this parameter.

        Only valid if the :meth:`type` returns :attr:`~discord.AppCommandOptionType.number`
        :attr:`~discord.AppCommandOptionType.integer`, or :attr:`~discord.AppCommandOptionType.string`.

        This must be a :obj:`property`.

        Defaults to ``None``.
        """
        return None

    @property
    def _error_display_name(self) -> str:
        name = self.__class__.__name__
        if name.endswith('Transformer'):
            return name[:-11]
        else:
            return name

    async def transform(self, interaction: Interaction[ClientT], value: Any, /) -> Any:
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

    async def autocomplete(
        self, interaction: Interaction[ClientT], value: Union[int, float, str], /
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


class IdentityTransformer(Transformer[ClientT]):
    def __init__(self, type: AppCommandOptionType) -> None:
        self._type = type

    @property
    def type(self) -> AppCommandOptionType:
        return self._type

    async def transform(self, interaction: Interaction[ClientT], value: Any, /) -> Any:
        return value


class RangeTransformer(IdentityTransformer):
    def __init__(
        self,
        opt_type: AppCommandOptionType,
        *,
        min: Optional[Union[int, float]] = None,
        max: Optional[Union[int, float]] = None,
    ) -> None:
        if min and max and min > max:
            raise TypeError('minimum cannot be larger than maximum')

        self._min: Optional[Union[int, float]] = min
        self._max: Optional[Union[int, float]] = max
        super().__init__(opt_type)

    @property
    def min_value(self) -> Optional[Union[int, float]]:
        return self._min

    @property
    def max_value(self) -> Optional[Union[int, float]]:
        return self._max


class LiteralTransformer(IdentityTransformer):
    def __init__(self, values: Tuple[Any, ...]) -> None:
        first = type(values[0])
        if first is int:
            opt_type = AppCommandOptionType.integer
        elif first is float:
            opt_type = AppCommandOptionType.number
        elif first is str:
            opt_type = AppCommandOptionType.string
        else:
            raise TypeError(f'expected int, str, or float values not {first!r}')

        self._choices = [Choice(name=str(v), value=v) for v in values]
        super().__init__(opt_type)

    @property
    def choices(self):
        return self._choices


class ChoiceTransformer(IdentityTransformer):
    __discord_app_commands_is_choice__: ClassVar[bool] = True

    def __init__(self, inner_type: Any) -> None:
        if inner_type is int:
            opt_type = AppCommandOptionType.integer
        elif inner_type is float:
            opt_type = AppCommandOptionType.number
        elif inner_type is str:
            opt_type = AppCommandOptionType.string
        else:
            raise TypeError(f'expected int, str, or float values not {inner_type!r}')

        super().__init__(opt_type)


class EnumValueTransformer(Transformer):
    def __init__(self, enum: Any) -> None:
        super().__init__()

        values = list(enum)
        if len(values) < 2:
            raise TypeError('enum.Enum requires at least two values.')

        first = type(values[0].value)
        if first is int:
            opt_type = AppCommandOptionType.integer
        elif first is float:
            opt_type = AppCommandOptionType.number
        elif first is str:
            opt_type = AppCommandOptionType.string
        else:
            raise TypeError(f'expected int, str, or float values not {first!r}')

        self._type: AppCommandOptionType = opt_type
        self._enum: Any = enum
        self._choices = [Choice(name=v.name, value=v.value) for v in values]

    @property
    def _error_display_name(self) -> str:
        return self._enum.__name__

    @property
    def type(self) -> AppCommandOptionType:
        return self._type

    @property
    def choices(self):
        return self._choices

    async def transform(self, interaction: Interaction, value: Any, /) -> Any:
        return self._enum(value)


class EnumNameTransformer(Transformer):
    def __init__(self, enum: Any) -> None:
        super().__init__()

        values = list(enum)
        if len(values) < 2:
            raise TypeError('enum.Enum requires at least two values.')

        self._enum: Any = enum
        self._choices = [Choice(name=v.name, value=v.name) for v in values]

    @property
    def _error_display_name(self) -> str:
        return self._enum.__name__

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    @property
    def choices(self):
        return self._choices

    async def transform(self, interaction: Interaction, value: Any, /) -> Any:
        return self._enum[value]


class InlineTransformer(Transformer[ClientT]):
    def __init__(self, annotation: Any) -> None:
        super().__init__()
        self.annotation: Any = annotation

    @property
    def _error_display_name(self) -> str:
        return self.annotation.__name__

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.string

    async def transform(self, interaction: Interaction[ClientT], value: Any, /) -> Any:
        return await self.annotation.transform(interaction, value)


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

        def __class_getitem__(cls, items) -> Transformer:
            if not isinstance(items, tuple):
                raise TypeError(f'expected tuple for arguments, received {items.__class__.__name__} instead')

            if len(items) != 2:
                raise TypeError('Transform only accepts exactly two arguments')

            _, transformer = items

            if inspect.isclass(transformer):
                if not issubclass(transformer, Transformer):
                    raise TypeError(f'second argument of Transform must be a Transformer class not {transformer!r}')
                transformer = transformer()
            elif not isinstance(transformer, Transformer):
                raise TypeError(f'second argument of Transform must be a Transformer not {transformer.__class__.__name__}')

            return transformer

    class Range:
        """A type annotation that can be applied to a parameter to require a numeric or string
        type to fit within the range provided.

        During type checking time this is equivalent to :obj:`typing.Annotated` so type checkers understand
        the intent of the code.

        Some example ranges:

        - ``Range[int, 10]`` means the minimum is 10 with no maximum.
        - ``Range[int, None, 10]`` means the maximum is 10 with no minimum.
        - ``Range[int, 1, 10]`` means the minimum is 1 and the maximum is 10.
        - ``Range[float, 1.0, 5.0]`` means the minimum is 1.0 and the maximum is 5.0.
        - ``Range[str, 1, 10]`` means the minimum length is 1 and the maximum length is 10.

        .. versionadded:: 2.0

        Examples
        ----------

        .. code-block:: python3

            @app_commands.command()
            async def range(interaction: discord.Interaction, value: app_commands.Range[int, 10, 12]):
                await interaction.response.send_message(f'Your value is {value}', ephemeral=True)
        """

        def __class_getitem__(cls, obj) -> RangeTransformer:
            if not isinstance(obj, tuple):
                raise TypeError(f'expected tuple for arguments, received {obj.__class__.__name__} instead')

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
            elif obj_type is str:
                opt_type = AppCommandOptionType.string
            else:
                raise TypeError(f'expected int, float, or str as range type, received {obj_type!r} instead')

            if obj_type in (str, int):
                cast = int
            else:
                cast = float

            transformer = RangeTransformer(
                opt_type,
                min=cast(min) if min is not None else None,
                max=cast(max) if max is not None else None,
            )
            return transformer


class MemberTransformer(Transformer[ClientT]):
    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.user

    async def transform(self, interaction: Interaction[ClientT], value: Any, /) -> Member:
        if not isinstance(value, Member):
            raise TransformerError(value, self.type, self)
        return value


class BaseChannelTransformer(Transformer[ClientT]):
    def __init__(self, *channel_types: Type[Any]) -> None:
        super().__init__()
        if len(channel_types) == 1:
            display_name = channel_types[0].__name__
            types = CHANNEL_TO_TYPES[channel_types[0]]
        else:
            display_name = _human_join([t.__name__ for t in channel_types])
            types = []

            for t in channel_types:
                try:
                    types.extend(CHANNEL_TO_TYPES[t])
                except KeyError:
                    raise TypeError('Union type of channels must be entirely made up of channels') from None

        self._types: Tuple[Type[Any], ...] = channel_types
        self._channel_types: List[ChannelType] = types
        self._display_name = display_name

    @property
    def _error_display_name(self) -> str:
        return self._display_name

    @property
    def type(self) -> AppCommandOptionType:
        return AppCommandOptionType.channel

    @property
    def channel_types(self) -> List[ChannelType]:
        return self._channel_types

    async def transform(self, interaction: Interaction[ClientT], value: Any, /):
        resolved = value.resolve()
        if resolved is None or not isinstance(resolved, self._types):
            raise TransformerError(value, AppCommandOptionType.channel, self)
        return resolved


class RawChannelTransformer(BaseChannelTransformer[ClientT]):
    async def transform(self, interaction: Interaction[ClientT], value: Any, /):
        if not isinstance(value, self._types):
            raise TransformerError(value, AppCommandOptionType.channel, self)
        return value


class UnionChannelTransformer(BaseChannelTransformer[ClientT]):
    async def transform(self, interaction: Interaction[ClientT], value: Any, /):
        if isinstance(value, self._types):
            return value

        resolved = value.resolve()
        if resolved is None or not isinstance(resolved, self._types):
            raise TransformerError(value, AppCommandOptionType.channel, self)
        return resolved


CHANNEL_TO_TYPES: Dict[Any, List[ChannelType]] = {
    AppCommandChannel: [
        ChannelType.stage_voice,
        ChannelType.voice,
        ChannelType.text,
        ChannelType.news,
        ChannelType.category,
        ChannelType.forum,
        ChannelType.media,
    ],
    GuildChannel: [
        ChannelType.stage_voice,
        ChannelType.voice,
        ChannelType.text,
        ChannelType.news,
        ChannelType.category,
        ChannelType.forum,
        ChannelType.media,
    ],
    AppCommandThread: [ChannelType.news_thread, ChannelType.private_thread, ChannelType.public_thread],
    Thread: [ChannelType.news_thread, ChannelType.private_thread, ChannelType.public_thread],
    StageChannel: [ChannelType.stage_voice],
    VoiceChannel: [ChannelType.voice],
    TextChannel: [ChannelType.text, ChannelType.news],
    CategoryChannel: [ChannelType.category],
    ForumChannel: [ChannelType.forum, ChannelType.media],
}

BUILT_IN_TRANSFORMERS: Dict[Any, Transformer] = {
    str: IdentityTransformer(AppCommandOptionType.string),
    int: IdentityTransformer(AppCommandOptionType.integer),
    float: IdentityTransformer(AppCommandOptionType.number),
    bool: IdentityTransformer(AppCommandOptionType.boolean),
    User: IdentityTransformer(AppCommandOptionType.user),
    Member: MemberTransformer(),
    Role: IdentityTransformer(AppCommandOptionType.role),
    AppCommandChannel: RawChannelTransformer(AppCommandChannel),
    AppCommandThread: RawChannelTransformer(AppCommandThread),
    GuildChannel: BaseChannelTransformer(GuildChannel),
    Thread: BaseChannelTransformer(Thread),
    StageChannel: BaseChannelTransformer(StageChannel),
    VoiceChannel: BaseChannelTransformer(VoiceChannel),
    TextChannel: BaseChannelTransformer(TextChannel),
    CategoryChannel: BaseChannelTransformer(CategoryChannel),
    ForumChannel: BaseChannelTransformer(ForumChannel),
    Attachment: IdentityTransformer(AppCommandOptionType.attachment),
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
    _mapping: Dict[Any, Transformer] = BUILT_IN_TRANSFORMERS,
) -> Tuple[Any, Any, bool]:
    """Returns an appropriate, yet supported, annotation along with an optional default value.

    The third boolean element of the tuple indicates if default values should be validated.

    This differs from the built in mapping by supporting a few more things.
    Likewise, this returns a "transformed" annotation that is ready to use with CommandParameter.transform.
    """

    try:
        return (_mapping[annotation], MISSING, True)
    except (KeyError, TypeError):
        pass

    if isinstance(annotation, Transformer):
        return (annotation, MISSING, False)

    if inspect.isclass(annotation):
        if issubclass(annotation, Transformer):
            return (annotation(), MISSING, False)
        if issubclass(annotation, (Enum, InternalEnum)):
            if all(isinstance(v.value, (str, int, float)) for v in annotation):
                return (EnumValueTransformer(annotation), MISSING, False)
            else:
                return (EnumNameTransformer(annotation), MISSING, False)
        if annotation is Choice:
            raise TypeError('Choice requires a type argument of int, str, or float')

        # Check if a transform @classmethod is given to the class
        # These flatten into simple "inline" transformers with implicit strings
        transform_classmethod = annotation.__dict__.get('transform', None)
        if isinstance(transform_classmethod, classmethod):
            params = inspect.signature(transform_classmethod.__func__).parameters
            if len(params) != 3:
                raise TypeError('Inline transformer with transform classmethod requires 3 parameters')
            if not inspect.iscoroutinefunction(transform_classmethod.__func__):
                raise TypeError('Inline transformer with transform classmethod must be a coroutine')
            return (InlineTransformer(annotation), MISSING, False)

    # Check if there's an origin
    origin = getattr(annotation, '__origin__', None)
    if origin is Literal:
        args = annotation.__args__
        return (LiteralTransformer(args), MISSING, True)

    if origin is Choice:
        arg = annotation.__args__[0]
        return (ChoiceTransformer(arg), MISSING, True)

    if origin is not Union:
        # Only Union/Optional is supported right now so bail early
        raise TypeError(f'unsupported type annotation {annotation!r}')

    default = MISSING
    args = annotation.__args__
    if args[-1] is _none:
        if len(args) == 2:
            underlying = args[0]
            inner, _, validate_default = get_supported_annotation(underlying)
            if inner is None:
                raise TypeError(f'unsupported inner optional type {underlying!r}')
            return (inner, None, validate_default)
        else:
            args = args[:-1]
            default = None

    # Check for channel union types
    if any(arg in CHANNEL_TO_TYPES for arg in args):
        # If any channel type is given, then *all* must be channel types
        return (UnionChannelTransformer(*args), default, True)

    # The only valid transformations here are:
    # [Member, User] => user
    # [Member, User, Role] => mentionable
    # [Member | User, Role] => mentionable
    supported_types: Set[Any] = {Role, Member, User}
    if not all(arg in supported_types for arg in args):
        raise TypeError(f'unsupported types given inside {annotation!r}')
    if args == (User, Member) or args == (Member, User):
        return (IdentityTransformer(AppCommandOptionType.user), default, True)

    return (IdentityTransformer(AppCommandOptionType.mentionable), default, True)


def annotation_to_parameter(annotation: Any, parameter: inspect.Parameter) -> CommandParameter:
    """Returns the appropriate :class:`CommandParameter` for the given annotation.

    The resulting ``_annotation`` attribute might not match the one given here and might
    be transformed in order to be easier to call from the ``transform`` asynchronous function
    of a command parameter.
    """

    (inner, default, validate_default) = get_supported_annotation(annotation)
    type = inner.type

    if default is MISSING or default is None:
        param_default = parameter.default
        if param_default is not parameter.empty:
            default = param_default

    # Verify validity of the default parameter
    if default is not MISSING and validate_default:
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

    choices = inner.choices
    if choices is not None:
        result.choices = choices

    # These methods should be duck typed
    if type in (AppCommandOptionType.number, AppCommandOptionType.string, AppCommandOptionType.integer):
        result.min_value = inner.min_value
        result.max_value = inner.max_value

    if type is AppCommandOptionType.channel:
        result.channel_types = inner.channel_types

    if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL):
        raise TypeError(f'unsupported parameter kind in callback: {parameter.kind!s}')

    # Check if the method is overridden
    if inner.autocomplete.__func__ is not Transformer.autocomplete:
        from .commands import validate_auto_complete_callback

        result.autocomplete = validate_auto_complete_callback(inner.autocomplete)

    return result
