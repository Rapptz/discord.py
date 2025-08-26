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

from typing import TYPE_CHECKING, Generator, Literal, Optional, Tuple, TypeVar

from ..components import LabelComponent
from ..enums import ComponentType
from ..utils import MISSING
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..types.components import LabelComponent as LabelComponentPayload
    from .view import BaseView


# fmt: off
__all__ = (
    'Label',
)
# fmt: on

V = TypeVar('V', bound='BaseView', covariant=True)


class Label(Item[V]):
    """Represents a UI label within a modal.

    .. versionadded:: 2.6

    Parameters
    ------------
    text: :class:`str`
        The text to display above the input field.
        Can only be up to 45 characters.
    description: Optional[:class:`str`]
        The description text to display right below the label text.
        Can only be up to 100 characters.
    component: Union[:class:`discord.ui.TextInput`, :class:`discord.ui.Select`]
        The component to display below the label.
    id: Optional[:class:`int`]
        The ID of the component. This must be unique across the view.

    Attributes
    ------------
    text: :class:`str`
        The text to display above the input field.
        Can only be up to 45 characters.
    description: Optional[:class:`str`]
        The description text to display right below the label text.
        Can only be up to 100 characters.
    component: :class:`Item`
        The component to display below the label. Currently only
        supports :class:`TextInput` and :class:`Select`.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'text',
        'description',
        'component',
    )

    def __init__(
        self,
        *,
        text: str,
        component: Item[V],
        description: Optional[str] = None,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.component: Item[V] = component
        self.text: str = text
        self.description: Optional[str] = description
        self.id = id

    @property
    def width(self) -> int:
        return 5

    def _has_children(self) -> bool:
        return True

    def walk_children(self) -> Generator[Item[V], None, None]:
        yield self.component

    def to_component_dict(self) -> LabelComponentPayload:
        payload: LabelComponentPayload = {
            'type': ComponentType.label.value,
            'label': self.text,
            'component': self.component.to_component_dict(),  # type: ignore
        }
        if self.description:
            payload['description'] = self.description
        if self.id is not None:
            payload['id'] = self.id
        return payload

    @classmethod
    def from_component(cls, component: LabelComponent) -> Self:
        from .view import _component_to_item

        self = cls(
            text=component.label,
            component=MISSING,
            description=component.description,
        )
        self.component = _component_to_item(component.component, self)
        return self

    @property
    def type(self) -> Literal[ComponentType.label]:
        return ComponentType.label

    def is_dispatchable(self) -> bool:
        return False
