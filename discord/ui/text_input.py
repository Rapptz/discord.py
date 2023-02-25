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

import os
from typing import TYPE_CHECKING, Literal, Optional, Tuple, TypeVar

from ..components import TextInput as TextInputComponent
from ..enums import ComponentType, TextStyle
from ..utils import MISSING
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..types.components import TextInput as TextInputPayload
    from ..types.interactions import ModalSubmitTextInputInteractionData as ModalSubmitTextInputInteractionDataPayload
    from .view import View
    from ..interactions import Interaction


# fmt: off
__all__ = (
    'TextInput',
)
# fmt: on

V = TypeVar('V', bound='View', covariant=True)


class TextInput(Item[V]):
    """Represents a UI text input.

    .. container:: operations

        .. describe:: str(x)

            Returns the value of the text input or an empty string if the value is ``None``.

    .. versionadded:: 2.0

    Parameters
    ------------
    label: :class:`str`
        The label to display above the text input.
    custom_id: :class:`str`
        The ID of the text input that gets received during an interaction.
        If not given then one is generated for you.
    style: :class:`discord.TextStyle`
        The style of the text input.
    placeholder: Optional[:class:`str`]
        The placeholder text to display when the text input is empty.
    default: Optional[:class:`str`]
        The default value of the text input.
    required: :class:`bool`
        Whether the text input is required.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    row: Optional[:class:`int`]
        The relative row this text input belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'label',
        'placeholder',
        'required',
    )

    def __init__(
        self,
        *,
        label: str,
        style: TextStyle = TextStyle.short,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._value: Optional[str] = default
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        if not isinstance(custom_id, str):
            raise TypeError(f'expected custom_id to be str not {custom_id.__class__.__name__}')

        self._underlying = TextInputComponent._raw_construct(
            label=label,
            style=style,
            custom_id=custom_id,
            placeholder=placeholder,
            value=default,
            required=required,
            min_length=min_length,
            max_length=max_length,
        )
        self.row = row

    def __str__(self) -> str:
        return self.value

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the text input that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be None or str')

        self._underlying.custom_id = value

    @property
    def width(self) -> int:
        return 5

    @property
    def value(self) -> str:
        """:class:`str`: The value of the text input."""
        return self._value or ''

    @property
    def label(self) -> str:
        """:class:`str`: The label of the text input."""
        return self._underlying.label

    @label.setter
    def label(self, value: str) -> None:
        self._underlying.label = value

    @property
    def placeholder(self) -> Optional[str]:
        """:class:`str`: The placeholder text to display when the text input is empty."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        self._underlying.placeholder = value

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the text input is required."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool) -> None:
        self._underlying.required = value

    @property
    def min_length(self) -> Optional[int]:
        """:class:`int`: The minimum length of the text input."""
        return self._underlying.min_length

    @min_length.setter
    def min_length(self, value: Optional[int]) -> None:
        self._underlying.min_length = value

    @property
    def max_length(self) -> Optional[int]:
        """:class:`int`: The maximum length of the text input."""
        return self._underlying.max_length

    @max_length.setter
    def max_length(self, value: Optional[int]) -> None:
        self._underlying.max_length = value

    @property
    def style(self) -> TextStyle:
        """:class:`discord.TextStyle`: The style of the text input."""
        return self._underlying.style

    @style.setter
    def style(self, value: TextStyle) -> None:
        self._underlying.style = value

    @property
    def default(self) -> Optional[str]:
        """:class:`str`: The default value of the text input."""
        return self._underlying.value

    @default.setter
    def default(self, value: Optional[str]) -> None:
        self._underlying.value = value

    def to_component_dict(self) -> TextInputPayload:
        return self._underlying.to_dict()

    def _refresh_component(self, component: TextInputComponent) -> None:
        self._underlying = component

    def _refresh_state(self, interaction: Interaction, data: ModalSubmitTextInputInteractionDataPayload) -> None:
        self._value = data.get('value', None)

    @classmethod
    def from_component(cls, component: TextInputComponent) -> Self:
        return cls(
            label=component.label,
            style=component.style,
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            default=component.value,
            required=component.required,
            min_length=component.min_length,
            max_length=component.max_length,
            row=None,
        )

    @property
    def type(self) -> Literal[ComponentType.text_input]:
        return self._underlying.type

    def is_dispatchable(self) -> bool:
        return False
