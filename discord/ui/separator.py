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

from typing import TYPE_CHECKING, Literal, Optional, TypeVar

from .item import Item
from ..components import SeparatorComponent
from ..enums import SeparatorSpacing, ComponentType

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('Separator',)


class Separator(Item[V]):
    """Represents a UI separator.

    This is a top-level layout component that can only be used on :class:`LayoutView`.

    .. versionadded:: 2.6

    Parameters
    ----------
    visible: :class:`bool`
        Whether this separator is visible. On the client side this
        is whether a divider line should be shown or not.
    spacing: :class:`.SeparatorSpacing`
        The spacing of this separator.
    row: Optional[:class:`int`]
        The relative row this separator belongs to. By default
        items are arranged automatically into those rows. If you'd
        like to control the relative positioning of the row then
        passing an index is advised. For example, row=1 will show
        up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 39 (i.e. zero indexed)
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __item_repr_attributes__ = (
        'visible',
        'spacing',
        'row',
        'id',
    )

    def __init__(
        self,
        *,
        visible: bool = True,
        spacing: SeparatorSpacing = SeparatorSpacing.small,
        row: Optional[int] = None,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._underlying = SeparatorComponent._raw_construct(
            spacing=spacing,
            visible=visible,
            id=id,
        )

        self.row = row
        self.id = id

    def _is_v2(self):
        return True

    @property
    def visible(self) -> bool:
        """:class:`bool`: Whether this separator is visible.

        On the client side this is whether a divider line should
        be shown or not.
        """
        return self._underlying.visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._underlying.visible = value

    @property
    def spacing(self) -> SeparatorSpacing:
        """:class:`.SeparatorSpacing`: The spacing of this separator."""
        return self._underlying.spacing

    @spacing.setter
    def spacing(self, value: SeparatorSpacing) -> None:
        self._underlying.spacing = value

    @property
    def width(self):
        return 5

    @property
    def type(self) -> Literal[ComponentType.separator]:
        return self._underlying.type

    def to_component_dict(self):
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: SeparatorComponent) -> Self:
        return cls(
            visible=component.visible,
            spacing=component.spacing,
            id=component.id,
        )
