"""
The MIT License (MIT)

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

import inspect
from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum

from ..abc import GuildChannel
from ..channel import TextChannel, VoiceChannel, StageChannel, CategoryChannel, Thread
from ..enums import ChannelType, SlashCommandOptionType, Enum as DiscordEnum

__all__ = (
    "ThreadOption",
    "Option",
    "OptionChoice",
    "option",
)

CHANNEL_TYPE_MAP = {
    TextChannel: ChannelType.text,
    VoiceChannel: ChannelType.voice,
    StageChannel: ChannelType.stage_voice,
    CategoryChannel: ChannelType.category,
    Thread: ChannelType.public_thread,
}


class ThreadOption:
    """Represents a class that can be passed as the input_type for an Option class.

    Parameters
    -----------
    thread_type: Literal["public", "private", "news"]
        The thread type to expect for this options input.
    """

    def __init__(self, thread_type: Literal["public", "private", "news"]):
        type_map = {
            "public": ChannelType.public_thread,
            "private": ChannelType.private_thread,
            "news": ChannelType.news_thread,
        }
        self._type = type_map[thread_type]


class Option:
    """Represents a selectable option for a slash command.

    Examples
    --------
    Basic usage: ::

        @bot.slash_command(guild_ids=[...])
        async def hello(
            ctx: discord.ApplicationContext,
            name: Option(str, "Enter your name"),
            age: Option(int, "Enter your age", min_value=1, max_value=99, default=18)
            # passing the default value makes an argument optional
            # you also can create optional argument using:
            # age: Option(int, "Enter your age") = 18
        ):
            await ctx.respond(f"Hello! Your name is {name} and you are {age} years old.")

    .. versionadded:: 2.0

    Attributes
    ----------
    input_type: :class:`Any`
        The type of input that is expected for this option.
    name: :class:`str`
        The name of this option visible in the UI.
        Inherits from the variable name if not provided as a parameter.
    description: Optional[:class:`str`]
        The description of this option.
        Must be 100 characters or fewer.
    choices: Optional[List[Union[:class:`Any`, :class:`OptionChoice`]]]
        The list of available choices for this option.
        Can be a list of values or :class:`OptionChoice` objects (which represent a name:value pair).
        If provided, the input from the user must match one of the choices in the list.
    required: Optional[:class:`bool`]
        Whether this option is required.
    default: Optional[:class:`Any`]
        The default value for this option. If provided, ``required`` will be considered ``False``.
    min_value: Optional[:class:`int`]
        The minimum value that can be entered.
        Only applies to Options with an input_type of ``int`` or ``float``.
    max_value: Optional[:class:`int`]
        The maximum value that can be entered.
        Only applies to Options with an input_type of ``int`` or ``float``.
    min_length: Optional[:class:`int`]
        The minimum length of the string that can be entered. Must be between 0 and 6000 (inclusive).
        Only applies to Options with an input_type of ``str``.
    max_length: Optional[:class:`int`]
        The maximum length of the string that can be entered. Must be between 1 and 6000 (inclusive).
        Only applies to Options with an input_type of ``str``.
    autocomplete: Optional[:class:`Any`]
        The autocomplete handler for the option. Accepts an iterable of :class:`str`, a callable (sync or async) that takes a
        single argument of :class:`AutocompleteContext`, or a coroutine. Must resolve to an iterable of :class:`str`.

        .. note::

            Does not validate the input value against the autocomplete results.
    name_localizations: Optional[Dict[:class:`str`, :class:`str`]]
        The name localizations for this option. The values of this should be ``"locale": "name"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.
    description_localizations: Optional[Dict[:class:`str`, :class:`str`]]
        The description localizations for this option. The values of this should be ``"locale": "description"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.
    """

    def __init__(self, input_type: Any = str, /, description: Optional[str] = None, **kwargs) -> None:
        self.name: Optional[str] = kwargs.pop("name", None)
        if self.name is not None:
            self.name = str(self.name)
        self._parameter_name = self.name  # default
        self.description = description or "No description provided"
        self.converter = None
        self._raw_type = input_type
        self.channel_types: List[ChannelType] = kwargs.pop("channel_types", [])
        enum_choices = []
        if not isinstance(input_type, SlashCommandOptionType):
            if hasattr(input_type, "convert"):
                self.converter = input_type
                self._raw_type = str
                input_type = SlashCommandOptionType.string
            elif isinstance(input_type, type) and issubclass(input_type, (Enum, DiscordEnum)):
                enum_choices = [OptionChoice(e.name, e.value) for e in input_type]
                if len(enum_choices) != len([elem for elem in enum_choices if elem.value.__class__ == enum_choices[0].value.__class__]):
                    enum_choices = [OptionChoice(e.name, str(e.value)) for e in input_type]
                    input_type = SlashCommandOptionType.string
                else:
                    input_type = SlashCommandOptionType.from_datatype(enum_choices[0].value.__class__)
            else:
                try:
                    _type = SlashCommandOptionType.from_datatype(input_type)
                except TypeError as exc:
                    from ..ext.commands.converter import CONVERTER_MAPPING

                    if input_type not in CONVERTER_MAPPING:
                        raise exc
                    self.converter = CONVERTER_MAPPING[input_type]
                    input_type = SlashCommandOptionType.string
                else:
                    if _type == SlashCommandOptionType.channel:
                        if not isinstance(input_type, tuple):
                            if hasattr(input_type, "__args__"):  # Union
                                input_type = input_type.__args__
                            else:
                                input_type = (input_type,)
                        for i in input_type:
                            if i is GuildChannel:
                                continue
                            if isinstance(i, ThreadOption):
                                self.channel_types.append(i._type)
                                continue

                            channel_type = CHANNEL_TYPE_MAP[i]
                            self.channel_types.append(channel_type)
                    input_type = _type
        self.input_type = input_type
        self.required: bool = kwargs.pop("required", True) if "default" not in kwargs else False
        self.default = kwargs.pop("default", None)
        self.choices: List[OptionChoice] = enum_choices or [
            o if isinstance(o, OptionChoice) else OptionChoice(o) for o in kwargs.pop("choices", list())
        ]

        if description is not None:
            self.description = description
        elif issubclass(self._raw_type, Enum) and (doc := inspect.getdoc(self._raw_type)) is not None:
            self.description = doc
        else:
            self.description = "No description provided"

        if self.input_type == SlashCommandOptionType.integer:
            minmax_types = (int, type(None))
        elif self.input_type == SlashCommandOptionType.number:
            minmax_types = (int, float, type(None))
        else:
            minmax_types = (type(None),)
        minmax_typehint = Optional[Union[minmax_types]]  # type: ignore

        if self.input_type == SlashCommandOptionType.string:
            minmax_length_types = (int, type(None))
        else:
            minmax_length_types = (type(None),)
        minmax_length_typehint = Optional[Union[minmax_length_types]] # type: ignore

        self.min_value: minmax_typehint = kwargs.pop("min_value", None)
        self.max_value: minmax_typehint = kwargs.pop("max_value", None)
        self.min_length: minmax_length_typehint = kwargs.pop("min_length", None)
        self.max_length: minmax_length_typehint = kwargs.pop("max_length", None)

        if (input_type != SlashCommandOptionType.integer and input_type != SlashCommandOptionType.number
                and (self.min_value or self.max_value)):
            raise AttributeError("Option does not take min_value or max_value if not of type "
                                 "SlashCommandOptionType.integer or SlashCommandOptionType.number")
        if input_type != SlashCommandOptionType.string and (self.min_length or self.max_length):
            raise AttributeError('Option does not take min_length or max_length if not of type str')

        if self.min_value is not None and not isinstance(self.min_value, minmax_types):
            raise TypeError(f'Expected {minmax_typehint} for min_value, got "{type(self.min_value).__name__}"')
        if self.max_value is not None and not isinstance(self.max_value, minmax_types):
            raise TypeError(f'Expected {minmax_typehint} for max_value, got "{type(self.max_value).__name__}"')

        if self.min_length is not None:
            if not isinstance(self.min_length, minmax_length_types):
                raise TypeError(f'Expected {minmax_length_typehint} for min_length, got "{type(self.min_length).__name__}"')
            if self.min_length < 0 or self.min_length > 6000:
                raise AttributeError("min_length must be between 0 and 6000 (inclusive)")
        if self.max_length is not None:
            if not isinstance(self.max_length, minmax_length_types):
                raise TypeError(f'Expected {minmax_length_typehint} for max_length, got "{type(self.max_length).__name__}"')
            if self.max_length < 1 or self.max_length > 6000:
                raise AttributeError("max_length must between 1 and 6000 (inclusive)")

        self.autocomplete = kwargs.pop("autocomplete", None)

        self.name_localizations = kwargs.pop("name_localizations", None)
        self.description_localizations = kwargs.pop("description_localizations", None)

    def to_dict(self) -> Dict:
        as_dict = {
            "name": self.name,
            "description": self.description,
            "type": self.input_type.value,
            "required": self.required,
            "choices": [c.to_dict() for c in self.choices],
            "autocomplete": bool(self.autocomplete),
        }
        if self.name_localizations is not None:
            as_dict["name_localizations"] = self.name_localizations
        if self.description_localizations is not None:
            as_dict["description_localizations"] = self.description_localizations
        if self.channel_types:
            as_dict["channel_types"] = [t.value for t in self.channel_types]
        if self.min_value is not None:
            as_dict["min_value"] = self.min_value
        if self.max_value is not None:
            as_dict["max_value"] = self.max_value
        if self.min_length is not None:
            as_dict["min_length"] = self.min_length
        if self.max_length is not None:
            as_dict["max_length"] = self.max_length

        return as_dict

    def __repr__(self):
        return f"<discord.commands.{self.__class__.__name__} name={self.name}>"


class OptionChoice:
    """
    Represents a name:value pairing for a selected :class:`Option`.

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The name of the choice. Shown in the UI when selecting an option.
    value: Optional[Union[:class:`str`, :class:`int`, :class:`float`]]
        The value of the choice. If not provided, will use the value of ``name``.
    name_localizations: Optional[Dict[:class:`str`, :class:`str`]]
        The name localizations for this choice. The values of this should be ``"locale": "name"``.
        See `here <https://discord.com/developers/docs/reference#locales>`_ for a list of valid locales.
    """

    def __init__(
        self,
        name: str,
        value: Optional[Union[str, int, float]] = None,
        name_localizations: Optional[Dict[str, str]] = None,
    ):
        self.name = str(name)
        self.value = value if value is not None else name
        self.name_localizations = name_localizations

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        as_dict = {"name": self.name, "value": self.value}
        if self.name_localizations is not None:
            as_dict["name_localizations"] = self.name_localizations

        return as_dict


def option(name, type=None, **kwargs):
    """A decorator that can be used instead of typehinting Option"""

    def decorator(func):
        nonlocal type
        type = type or func.__annotations__.get(name, str)
        func.__annotations__[name] = Option(type, **kwargs)
        return func

    return decorator
