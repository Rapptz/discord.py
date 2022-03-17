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

from typing import Any, ClassVar, Dict, List, Optional, TYPE_CHECKING, Tuple, Union
from .enums import try_enum, ComponentType, ButtonStyle, TextStyle
from .utils import get_slots, MISSING
from .partial_emoji import PartialEmoji, _EmojiTag

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.components import (
        Component as ComponentPayload,
        ButtonComponent as ButtonComponentPayload,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        ActionRow as ActionRowPayload,
        TextInput as TextInputPayload,
    )
    from .emoji import Emoji


__all__ = (
    'Component',
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'TextInput',
)


class Component:
    """Represents a Discord Bot UI Kit Component.

    Currently, the only components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`ComponentType`
        The type of component.
    """

    __slots__: Tuple[str, ...] = ('type',)

    __repr_info__: ClassVar[Tuple[str, ...]]
    type: ComponentType

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__repr_info__)
        return f'<{self.__class__.__name__} {attrs}>'

    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError


class ActionRow(Component):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`ComponentType`
        The type of component.
    children: List[:class:`Component`]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = ('children',)

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ComponentPayload):
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.children: List[Component] = [_component_factory(d) for d in data.get('components', [])]

    def to_dict(self) -> ActionRowPayload:
        return {
            'type': int(self.type),
            'components': [child.to_dict() for child in self.children],
        }  # type: ignore - Type checker does not understand these are the same


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a button is :class:`discord.ui.Button`
        not this one.

    .. versionadded:: 2.0

    Attributes
    -----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    """

    __slots__: Tuple[str, ...] = (
        'style',
        'custom_id',
        'url',
        'disabled',
        'label',
        'emoji',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonComponentPayload):
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.style: ButtonStyle = try_enum(ButtonStyle, data['style'])
        self.custom_id: Optional[str] = data.get('custom_id')
        self.url: Optional[str] = data.get('url')
        self.disabled: bool = data.get('disabled', False)
        self.label: Optional[str] = data.get('label')
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data['emoji'])
        except KeyError:
            self.emoji = None

    def to_dict(self) -> ButtonComponentPayload:
        payload = {
            'type': 2,
            'style': int(self.style),
            'label': self.label,
            'disabled': self.disabled,
        }
        if self.custom_id:
            payload['custom_id'] = self.custom_id

        if self.url:
            payload['url'] = self.url

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()

        return payload  # type: ignore - Type checker does not understand these are the same


class SelectMenu(Component):
    """Represents a select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`discord.ui.Select` not this one.

    .. versionadded:: 2.0

    Attributes
    ------------
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    """

    __slots__: Tuple[str, ...] = (
        'custom_id',
        'placeholder',
        'min_values',
        'max_values',
        'options',
        'disabled',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuPayload):
        self.type = ComponentType.select
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.min_values: int = data.get('min_values', 1)
        self.max_values: int = data.get('max_values', 1)
        self.options: List[SelectOption] = [SelectOption.from_dict(option) for option in data.get('options', [])]
        self.disabled: bool = data.get('disabled', False)

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            'type': self.type.value,
            'custom_id': self.custom_id,
            'min_values': self.min_values,
            'max_values': self.max_values,
            'options': [op.to_dict() for op in self.options],
            'disabled': self.disabled,
        }

        if self.placeholder:
            payload['placeholder'] = self.placeholder

        return payload


class SelectOption:
    """Represents a select menu's option.

    These can be created by users.

    .. versionadded:: 2.0

    Attributes
    -----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label. Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        'label',
        'value',
        'description',
        'emoji',
        'default',
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description

        if emoji is not None:
            if isinstance(emoji, str):
                emoji = PartialEmoji.from_str(emoji)
            elif isinstance(emoji, _EmojiTag):
                emoji = emoji._to_partial()
            else:
                raise TypeError(f'expected emoji to be str, Emoji, or PartialEmoji not {emoji.__class__}')

        self.emoji: Optional[Union[str, Emoji, PartialEmoji]] = emoji
        self.default: bool = default

    def __repr__(self) -> str:
        return (
            f'<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} '
            f'emoji={self.emoji!r} default={self.default!r}>'
        )

    def __str__(self) -> str:
        if self.emoji:
            base = f'{self.emoji} {self.label}'
        else:
            base = self.label

        if self.description:
            return f'{base}\n{self.description}'
        return base

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data['emoji'])
        except KeyError:
            emoji = None

        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),
            emoji=emoji,
            default=data.get('default', False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            'label': self.label,
            'value': self.value,
            'default': self.default,
        }

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()  # type: ignore - This Dict[str, Any] is compatible with PartialEmoji

        if self.description:
            payload['description'] = self.description

        return payload


class TextInput(Component):
    """Represents a text input from the Discord Bot UI Kit.

    .. note::
        The user constructible and usable type to create a text input is
        :class:`discord.ui.TextInput` not this one.

    .. versionadded:: 2.0

    Attributes
    ------------
    custom_id: Optional[:class:`str`]
        The ID of the text input that gets received during an interaction.
    label: :class:`str`
        The label to display above the text input.
    style: :class:`TextStyle`
        The style of the text input.
    placeholder: Optional[:class:`str`]
        The placeholder text to display when the text input is empty.
    value: Optional[:class:`str`]
        The default value of the text input.
    required: :class:`bool`
        Whether the text input is required.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    """

    __slots__: Tuple[str, ...] = (
        'style',
        'label',
        'custom_id',
        'placeholder',
        'value',
        'required',
        'min_length',
        'max_length',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputPayload) -> None:
        self.type: ComponentType = ComponentType.text_input
        self.style: TextStyle = try_enum(TextStyle, data['style'])
        self.label: str = data['label']
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.value: Optional[str] = data.get('value')
        self.required: bool = data.get('required', True)
        self.min_length: Optional[int] = data.get('min_length')
        self.max_length: Optional[int] = data.get('max_length')

    def to_dict(self) -> TextInputPayload:
        payload: TextInputPayload = {
            'type': self.type.value,
            'style': self.style.value,
            'label': self.label,
            'custom_id': self.custom_id,
            'required': self.required,
        }

        if self.placeholder:
            payload['placeholder'] = self.placeholder

        if self.value:
            payload['value'] = self.value

        if self.min_length:
            payload['min_length'] = self.min_length

        if self.max_length:
            payload['max_length'] = self.max_length

        return payload

    @property
    def default(self) -> Optional[str]:
        """Optional[:class:`str`]: The default value of the text input.

        This is an alias to :attr:`value`.
        """
        return self.value


def _component_factory(data: ComponentPayload) -> Component:
    component_type = data['type']
    if component_type == 1:
        return ActionRow(data)
    elif component_type == 2:
        # The type checker does not properly do narrowing here.
        return Button(data)  # type: ignore
    elif component_type == 3:
        # The type checker does not properly do narrowing here.
        return SelectMenu(data)  # type: ignore
    elif component_type == 4:
        # The type checker does not properly do narrowing here.
        return TextInput(data)  # type: ignore
    else:
        as_enum = try_enum(ComponentType, component_type)
        return Component._raw_construct(type=as_enum)
