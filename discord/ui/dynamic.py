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
from typing import ClassVar, Dict, Generic, Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Any, Union
import re

from .item import Item
from .._types import ClientT

__all__ = ('DynamicItem',)

BaseT = TypeVar('BaseT', bound='Item[Any]', covariant=True)

if TYPE_CHECKING:
    from typing_extensions import TypeVar, Self
    from ..interactions import Interaction
    from ..components import Component
    from ..enums import ComponentType
    from .view import View, LayoutView
else:
    View = LayoutView = Any


class DynamicItem(Generic[BaseT], Item[Union[View, LayoutView]]):
    """Represents an item with a dynamic ``custom_id`` that can be used to store state within
    that ``custom_id``.

    The ``custom_id`` parsing is done using the ``re`` module by passing a ``template``
    parameter to the class parameter list.

    This item is generated every time the component is dispatched. This means that
    any variable that holds an instance of this class will eventually be out of date
    and should not be used long term. Their only purpose is to act as a "template"
    for the actual dispatched item.

    When this item is generated, :attr:`view` is set to a regular :class:`View` instance,
    but to a :class:`LayoutView` if the component was sent with one, this is obtained from
    the original message given from the interaction. This means that custom view subclasses
    cannot be accessed from this item.

    .. versionadded:: 2.4

    Parameters
    ------------
    item: :class:`Item`
        The item to wrap with dynamic custom ID parsing.
    template: Union[:class:`str`, ``re.Pattern``]
        The template to use for parsing the ``custom_id``. This can be a string or a compiled
        regular expression. This must be passed as a keyword argument to the class creation.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).

    Attributes
    -----------
    item: :class:`Item`
        The item that is wrapped with dynamic custom ID parsing.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'item',
        'template',
    )

    __discord_ui_compiled_template__: ClassVar[re.Pattern[str]]

    def __init_subclass__(cls, *, template: Union[str, re.Pattern[str]]) -> None:
        super().__init_subclass__()
        cls.__discord_ui_compiled_template__ = re.compile(template) if isinstance(template, str) else template
        if not isinstance(cls.__discord_ui_compiled_template__, re.Pattern):
            raise TypeError('template must be a str or a re.Pattern')

    def __init__(
        self,
        item: BaseT,
        *,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.item: BaseT = item
        if row is not None:
            self.row = row

        if not self.item.is_dispatchable():
            raise TypeError('item must be dispatchable, e.g. not a URL button')

        if not self.template.match(self.custom_id):
            raise ValueError(f'item custom_id {self.custom_id!r} must match the template {self.template.pattern!r}')

    @property
    def template(self) -> re.Pattern[str]:
        """``re.Pattern``: The compiled regular expression that is used to parse the ``custom_id``."""
        return self.__class__.__discord_ui_compiled_template__

    def to_component_dict(self) -> Dict[str, Any]:
        return self.item.to_component_dict()

    def _refresh_component(self, component: Component) -> None:
        self.item._refresh_component(component)

    def _refresh_state(self, interaction: Interaction, data: Dict[str, Any]) -> None:
        self.item._refresh_state(interaction, data)

    @classmethod
    def from_component(cls: Type[Self], component: Component) -> Self:
        raise TypeError('Dynamic items cannot be created from components')

    @property
    def type(self) -> ComponentType:
        return self.item.type

    def is_dispatchable(self) -> bool:
        return self.item.is_dispatchable()

    def is_persistent(self) -> bool:
        return True

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the dynamic item that gets received during an interaction."""
        return self.item.custom_id  # type: ignore  # This attribute exists for dispatchable items

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be a str')

        if not self.template.match(value):
            raise ValueError(f'custom_id must match the template {self.template.pattern!r}')

        self.item.custom_id = value  # type: ignore  # This attribute exists for dispatchable items
        self._provided_custom_id = True

    @property
    def row(self) -> Optional[int]:
        return self.item._row

    @row.setter
    def row(self, value: Optional[int]) -> None:
        self.item.row = value

    @property
    def width(self) -> int:
        return self.item.width

    @property
    def _total_count(self) -> int:
        return self.item._total_count

    @classmethod
    async def from_custom_id(
        cls: Type[Self], interaction: Interaction[ClientT], item: Item[Any], match: re.Match[str], /
    ) -> Self:
        """|coro|

        A classmethod that is called when the ``custom_id`` of a component matches the
        ``template`` of the class. This is called when the component is dispatched.

        It must return a new instance of the :class:`DynamicItem`.

        Subclasses *must* implement this method.

        Exceptions raised in this method are logged and ignored.

        .. warning::

            This method is called before the callback is dispatched, therefore
            it means that it is subject to the same timing restrictions as the callback.
            Ergo, you must reply to an interaction within 3 seconds of it being
            dispatched.

        Parameters
        ------------
        interaction: :class:`~discord.Interaction`
            The interaction that the component belongs to.
        item: :class:`~discord.ui.Item`
            The base item that is being dispatched.
        match: ``re.Match``
            The match object that was created from the ``template``
            matching the ``custom_id``.

        Returns
        --------
        :class:`DynamicItem`
            The new instance of the :class:`DynamicItem` with information
            from the ``match`` object.
        """
        raise NotImplementedError

    async def callback(self, interaction: Interaction[ClientT]) -> Any:
        return await self.item.callback(interaction)

    async def interaction_check(self, interaction: Interaction[ClientT], /) -> bool:
        return await self.item.interaction_check(interaction)
