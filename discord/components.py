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

from typing import List, Optional, TYPE_CHECKING, Tuple, Type, TypeVar
from .enums import try_enum, ComponentType, ButtonStyle
from .partial_emoji import PartialEmoji

if TYPE_CHECKING:
    from .types.components import (
        Component as ComponentPayload,
        ButtonComponent as ButtonComponentPayload,
        ComponentContainer as ComponentContainerPayload,
    )


__all__ = (
    'Component',
    'Button',
)

C = TypeVar('C', bound='Component')

class Component:
    """Represents a Discord Bot UI Kit Component.

    Currently, the only components supported by Discord are buttons and button groups.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`ComponentType`
        The type of component.
    children: List[:class:`Component`]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = (
        'type',
        'children',
    )

    def __init__(self, data: ComponentPayload):
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.children: List[Component] = [_component_factory(d) for d in data.get('components', [])]

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__slots__)
        return f'<{self.__class__.__name__} type={self.type!r} {attrs}>'

    def to_dict(self) -> ComponentContainerPayload:
        return {
            'type': int(self.type),
            'components': [child.to_dict() for child in self.children],
        }  # type: ignore


    @classmethod
    def _raw_construct(cls: Type[C], **kwargs) -> C:
        self: C = cls.__new__(cls)
        slots = cls.__slots__
        for attr, value in kwargs.items():
            if attr in slots:
                setattr(self, attr, value)
        return self


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    -----------
    style: :class:`ComponentButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: :class:`str`
        The label of the button.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    """

    __slots__: Tuple[str, ...] = Component.__slots__ + (
        'style',
        'custom_id',
        'url',
        'disabled',
        'label',
        'emoji',
    )

    def __init__(self, data: ButtonComponentPayload):
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.style: ButtonStyle = try_enum(ButtonStyle, data['style'])
        self.custom_id: Optional[str] = data.get('custom_id')
        self.url: Optional[str] = data.get('url')
        self.disabled: bool = data.get('disabled', False)
        self.label: str = data['label']
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

        return payload  # type: ignore

def _component_factory(data: ComponentPayload) -> Component:
    component_type = data['type']
    if component_type == 1:
        return Component(data)
    elif component_type == 2:
        return Button(data)  # type: ignore
    else:
        return Component(data)
