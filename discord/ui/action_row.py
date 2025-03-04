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
import os
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
    Sequence,
    Type,
    TypeVar,
    Union,
)

from .item import Item, ItemCallbackType
from .button import Button
from .select import Select, SelectCallbackDecorator
from ..enums import ButtonStyle, ComponentType, ChannelType
from ..partial_emoji import PartialEmoji
from ..utils import MISSING

if TYPE_CHECKING:
    from .view import LayoutView
    from .select import (
        BaseSelectT,
        ValidDefaultValues,
        MentionableSelectT,
        ChannelSelectT,
        RoleSelectT,
        UserSelectT,
        SelectT
    )
    from ..emoji import Emoji
    from ..components import SelectOption
    from ..interactions import Interaction

V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('ActionRow',)


class _ActionRowCallback:
    __slots__ = ('row', 'callback', 'item')

    def __init__(self, callback: ItemCallbackType[Any, Any], row: ActionRow, item: Item[Any]) -> None:
        self.callback: ItemCallbackType[Any, Any] = callback
        self.row: ActionRow = row
        self.item: Item[Any] = item

    def __call__(self, interaction: Interaction) -> Coroutine[Any, Any, Any]:
        return self.callback(self.row, interaction, self.item)


class ActionRow(Item[V]):
    """Represents a UI action row.

    This object can be inherited.

    .. versionadded:: 2.6

    Parameters
    ----------
    id: Optional[:class:`str`]
        The ID of this action row. Defaults to ``None``.
    """

    __action_row_children_items__: ClassVar[List[ItemCallbackType[Any, Any]]] = []
    __discord_ui_action_row__: ClassVar[bool] = True

    def __init__(self, *, id: Optional[str] = None) -> None:
        super().__init__()

        self.id: str = id or os.urandom(16).hex()
        self._children: List[Item[Any]] = self._init_children()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, ItemCallbackType[Any, Any]] = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if hasattr(member, '__discord_ui_model_type__'):
                    children[name] = member

        if len(children) > 5:
            raise TypeError('ActionRow cannot have more than 5 children')

        cls.__action_row_children_items__ = list(children.values())

    def _init_children(self) -> List[Item[Any]]:
        children = []

        for func in self.__action_row_children_items__:
            item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
            item.callback = _ActionRowCallback(func, self, item)
            item._parent = self  # type: ignore
            setattr(self, func.__name__, item)
            children.append(item)
        return children

    def _update_children_view(self, view: LayoutView) -> None:
        for child in self._children:
            child._view = view

    def _is_v2(self) -> bool:
        # although it is not really a v2 component the only usecase here is for
        # LayoutView which basically represents the top-level payload of components
        # and ActionRow is only allowed there anyways.
        # If the user tries to add any V2 component to a View instead of LayoutView
        # it should error anyways.
        return True

    @property
    def width(self):
        return 5

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        return ComponentType.action_row

    def button(
        self,
        *,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        disabled: bool = False,
        style: ButtonStyle = ButtonStyle.secondary,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
    ) -> Callable[[ItemCallbackType[V, Button[V]]], Button[V]]:
        """A decorator that attaches a button to a component.

        The function being decorated should have three parameters, ``self`` representing
        the :class:`discord.ui.LayoutView`, the :class:`discord.Interaction` you receive and
        the :class:`discord.ui.Button` being pressed.

        .. note::

            Buttons with a URL or a SKU cannot be created with this function.
            Consider creating a :class:`Button` manually and adding it via
            :meth:`ActionRow.add_item` instead. This is beacuse these buttons
            cannot have a callback associated with them since Discord does not
            do any processing with them.

        Parameters
        ----------
        label: Optional[:class:`str`]
            The label of the button, if any.
            Can only be up to 80 characters.
        custom_id: Optional[:class:`str`]
            The ID of the button that gets received during an interaction.
            It is recommended to not set this parameters to prevent conflicts.
            Can only be up to 100 characters.
        style: :class:`.ButtonStyle`
            The style of the button. Defaults to :attr:`.ButtonStyle.grey`.
        disabled: :class:`bool`
            Whether the button is disabled or not. Defaults to ``False``.
        emoji: Optional[Union[:class:`str`, :class:`.Emoji`, :class:`.PartialEmoji`]]
            The emoji of the button. This can be in string form or a :class:`.PartialEmoji`
            or a full :class:`.Emoji`.
        """

        def decorator(func: ItemCallbackType[V, Button[V]]) -> ItemCallbackType[V, Button[V]]:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('button function must be a coroutine function')

            func.__discord_ui_modal_type__ = Button
            func.__discord_ui_model_kwargs__ = {
                'style': style,
                'custom_id': custom_id,
                'url': None,
                'disabled': disabled,
                'label': label,
                'emoji': emoji,
                'row': None,
                'sku_id': None,
            }
            return func

        return decorator  # type: ignore

    def select(
        *,
        cls: Type[BaseSelectT] = Select[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = MISSING,
        placeholder: Optional[str] = None,
        custom_id: str = MISSING,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        default_values: Sequence[ValidDefaultValues] = MISSING,
    ) -> SelectCallbackDecorator[V, BaseSelectT]:
        """A decorator that attaches a select menu to a component.

        The function being decorated should have three parameters, ``self`` representing
        the :class:`discord.ui.View`, the :class:`discord.Interaction` you receive and
        the chosen select class.

        To obtain the selected values inside the callback, you can use the ``values`` attribute of the chosen class in the callback. The list of values
        will depend on the type of select menu used. View the table below for more information.

        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
        | Select Type                            | Resolved Values                                                                                                 |
        +========================================+=================================================================================================================+
        | :class:`discord.ui.Select`             | List[:class:`str`]                                                                                              |
        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
        | :class:`discord.ui.UserSelect`         | List[Union[:class:`discord.Member`, :class:`discord.User`]]                                                     |
        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
        | :class:`discord.ui.RoleSelect`         | List[:class:`discord.Role`]                                                                                     |
        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
        | :class:`discord.ui.MentionableSelect`  | List[Union[:class:`discord.Role`, :class:`discord.Member`, :class:`discord.User`]]                              |
        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+
        | :class:`discord.ui.ChannelSelect`      | List[Union[:class:`~discord.app_commands.AppCommandChannel`, :class:`~discord.app_commands.AppCommandThread`]]  |
        +----------------------------------------+-----------------------------------------------------------------------------------------------------------------+

        .. versionchanged:: 2.1
            Added the following keyword-arguments: ``cls``, ``channel_types``

        Example
        ---------
        .. code-block:: python3

            class ActionRow(discord.ui.ActionRow):

                @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text])
                async def select_channels(self, interaction: discord.Interaction, select: ChannelSelect):
                    return await interaction.response.send_message(f'You selected {select.values[0].mention}')

        Parameters
        ------------
        cls: Union[Type[:class:`discord.ui.Select`], Type[:class:`discord.ui.UserSelect`], Type[:class:`discord.ui.RoleSelect`], \
            Type[:class:`discord.ui.MentionableSelect`], Type[:class:`discord.ui.ChannelSelect`]]
            The class to use for the select menu. Defaults to :class:`discord.ui.Select`. You can use other
            select types to display different select menus to the user. See the table above for the different
            values you can get from each select type. Subclasses work as well, however the callback in the subclass will
            get overridden.
        placeholder: Optional[:class:`str`]
            The placeholder text that is shown if nothing is selected, if any.
            Can only be up to 150 characters.
        custom_id: :class:`str`
            The ID of the select menu that gets received during an interaction.
            It is recommended not to set this parameter to prevent conflicts.
            Can only be up to 100 characters.
        min_values: :class:`int`
            The minimum number of items that must be chosen for this select menu.
            Defaults to 1 and must be between 0 and 25.
        max_values: :class:`int`
            The maximum number of items that must be chosen for this select menu.
            Defaults to 1 and must be between 1 and 25.
        options: List[:class:`discord.SelectOption`]
            A list of options that can be selected in this menu. This can only be used with
            :class:`Select` instances.
            Can only contain up to 25 items.
        channel_types: List[:class:`~discord.ChannelType`]
            The types of channels to show in the select menu. Defaults to all channels. This can only be used
            with :class:`ChannelSelect` instances.
        disabled: :class:`bool`
            Whether the select is disabled or not. Defaults to ``False``.
        default_values: Sequence[:class:`~discord.abc.Snowflake`]
            A list of objects representing the default values for the select menu. This cannot be used with regular :class:`Select` instances.
            If ``cls`` is :class:`MentionableSelect` and :class:`.Object` is passed, then the type must be specified in the constructor.
            Number of items must be in range of ``min_values`` and ``max_values``.
        """
