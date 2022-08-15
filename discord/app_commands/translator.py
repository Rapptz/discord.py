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
from typing import TYPE_CHECKING, Any, Generic, Literal, Optional, TypeVar, Union, overload
from .errors import TranslationError
from ..enums import Enum, Locale


if TYPE_CHECKING:
    from .commands import Command, ContextMenu, Group, Parameter
    from .models import Choice


__all__ = (
    'TranslationContextLocation',
    'TranslationContextTypes',
    'TranslationContext',
    'Translator',
    'locale_str',
)


class TranslationContextLocation(Enum):
    command_name = 0
    command_description = 1
    group_name = 2
    group_description = 3
    parameter_name = 4
    parameter_description = 5
    choice_name = 6
    other = 7


_L = TypeVar('_L', bound=TranslationContextLocation)
_D = TypeVar('_D')


class TranslationContext(Generic[_L, _D]):
    """A class that provides context for the :class:`locale_str` being translated.

    This is useful to determine where exactly the string is located and aid in looking
    up the actual translation.

    Attributes
    -----------
    location: :class:`TranslationContextLocation`
        The location where this string is located.
    data: Any
        The extraneous data that is being translated.
    """

    __slots__ = ('location', 'data')

    @overload
    def __init__(
        self, location: Literal[TranslationContextLocation.command_name], data: Union[Command[Any, ..., Any], ContextMenu]
    ) -> None:
        ...

    @overload
    def __init__(
        self, location: Literal[TranslationContextLocation.command_description], data: Command[Any, ..., Any]
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        location: Literal[TranslationContextLocation.group_name, TranslationContextLocation.group_description],
        data: Group,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        location: Literal[TranslationContextLocation.parameter_name, TranslationContextLocation.parameter_description],
        data: Parameter,
    ) -> None:
        ...

    @overload
    def __init__(self, location: Literal[TranslationContextLocation.choice_name], data: Choice[Any]) -> None:
        ...

    @overload
    def __init__(self, location: Literal[TranslationContextLocation.other], data: Any) -> None:
        ...

    def __init__(self, location: _L, data: _D) -> None:
        self.location: _L = location
        self.data: _D = data


# For type checking purposes, it makes sense to allow the user to leverage type narrowing
# So code like this works as expected:
#
# if context.type == TranslationContextLocation.command_name:
#    reveal_type(context.data)  # Revealed type is Command | ContextMenu
#
# This requires a union of types
CommandNameTranslationContext = TranslationContext[
    Literal[TranslationContextLocation.command_name], Union['Command[Any, ..., Any]', 'ContextMenu']
]
CommandDescriptionTranslationContext = TranslationContext[
    Literal[TranslationContextLocation.command_description], 'Command[Any, ..., Any]'
]
GroupTranslationContext = TranslationContext[
    Literal[TranslationContextLocation.group_name, TranslationContextLocation.group_description], 'Group'
]
ParameterTranslationContext = TranslationContext[
    Literal[TranslationContextLocation.parameter_name, TranslationContextLocation.parameter_description], 'Parameter'
]
ChoiceTranslationContext = TranslationContext[Literal[TranslationContextLocation.choice_name], 'Choice[Any]']
OtherTranslationContext = TranslationContext[Literal[TranslationContextLocation.other], Any]

TranslationContextTypes = Union[
    CommandNameTranslationContext,
    CommandDescriptionTranslationContext,
    GroupTranslationContext,
    ParameterTranslationContext,
    ChoiceTranslationContext,
    OtherTranslationContext,
]


class Translator:
    """A class that handles translations for commands, parameters, and choices.

    Translations are done lazily in order to allow for async enabled translations as well
    as supporting a wide array of translation systems such as :mod:`gettext` and
    `Project Fluent <https://projectfluent.org>`_.

    In order for a translator to be used, it must be set using the :meth:`CommandTree.set_translator`
    method. The translation flow for a string is as follows:

    1. Use :class:`locale_str` instead of :class:`str` in areas of a command you want to be translated.
        - Currently, these are command names, command descriptions, parameter names, parameter descriptions, and choice names.
        - This can also be used inside the :func:`~discord.app_commands.describe` decorator.
    2. Call :meth:`CommandTree.set_translator` to the translator instance that will handle the translations.
    3. Call :meth:`CommandTree.sync`
    4. The library will call :meth:`Translator.translate` on all the relevant strings being translated.

    .. versionadded:: 2.0
    """

    async def load(self) -> None:
        """|coro|

        An asynchronous setup function for loading the translation system.

        The default implementation does nothing.

        This is invoked when :meth:`CommandTree.set_translator` is called.
        """
        pass

    async def unload(self) -> None:
        """|coro|

        An asynchronous teardown function for unloading the translation system.

        The default implementation does nothing.

        This is invoked when :meth:`CommandTree.set_translator` is called
        if a tree already has a translator or when :meth:`discord.Client.close` is called.
        """
        pass

    async def _checked_translate(
        self, string: locale_str, locale: Locale, context: TranslationContextTypes
    ) -> Optional[str]:
        try:
            return await self.translate(string, locale, context)
        except TranslationError:
            raise
        except Exception as e:
            raise TranslationError(string=string, locale=locale, context=context) from e

    async def translate(self, string: locale_str, locale: Locale, context: TranslationContextTypes) -> Optional[str]:
        """|coro|

        Translates the given string to the specified locale.

        If the string cannot be translated, ``None`` should be returned.

        The default implementation returns ``None``.

        If an exception is raised in this method, it should inherit from :exc:`TranslationError`.
        If it doesn't, then when this is called the exception will be chained with it instead.

        Parameters
        ------------
        string: :class:`locale_str`
            The string being translated.
        locale: :class:`~discord.Locale`
            The locale being requested for translation.
        context: :class:`TranslationContext`
            The translation context where the string originated from.
            For better type checking ergonomics, the ``TranslationContextTypes``
            type can be used instead to aid with type narrowing. It is functionally
            equivalent to :class:`TranslationContext`.
        """

        return None


class locale_str:
    """Marks a string as ready for translation.

    This is done lazily and is not actually translated until :meth:`CommandTree.sync` is called.

    The sync method then ultimately defers the responsibility of translating to the :class:`Translator`
    instance used by the :class:`CommandTree`. For more information on the translation flow, see the
    :class:`Translator` documentation.

    .. container:: operations

        .. describe:: str(x)

            Returns the message passed to the string.

        .. describe:: x == y

            Checks if the string is equal to another string.

        .. describe:: x != y

            Checks if the string is not equal to another string.

        .. describe:: hash(x)

            Returns the hash of the string.

    .. versionadded:: 2.0

    Attributes
    ------------
    message: :class:`str`
        The message being translated. Once set, this cannot be changed.

        .. warning::

            This must be the default "message" that you send to Discord.
            Discord sends this message back to the library and the library
            uses it to access the data in order to dispatch commands.

            For example, in a command name context, if the command
            name is ``foo`` then the message *must* also be ``foo``.
            For other translation systems that require a message ID such
            as Fluent, consider using a keyword argument to pass it in.
    extras: :class:`dict`
        A dict of user provided extras to attach to the translated string.
        This can be used to add more context, information, or any metadata necessary
        to aid in actually translating the string.

        Since these are passed via keyword arguments, the keys are strings.
    """

    __slots__ = ('__message', 'extras')

    def __init__(self, message: str, /, **kwargs: Any) -> None:
        self.__message: str = message
        self.extras: dict[str, Any] = kwargs

    @property
    def message(self) -> str:
        return self.__message

    def __str__(self) -> str:
        return self.__message

    def __repr__(self) -> str:
        kwargs = ', '.join(f'{k}={v!r}' for k, v in self.extras.items())
        if kwargs:
            return f'{self.__class__.__name__}({self.__message!r}, {kwargs})'
        return f'{self.__class__.__name__}({self.__message!r})'

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, locale_str) and self.message == obj.message

    def __hash__(self) -> int:
        return hash(self.__message)
