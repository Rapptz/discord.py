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

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)

from .item import Item, ContainedItemCallbackType as ItemCallbackType
from .button import Button, button as _button
from .select import select as _select, Select, UserSelect, RoleSelect, ChannelSelect, MentionableSelect
from ..components import ActionRow as ActionRowComponent
from ..enums import ButtonStyle, ComponentType, ChannelType
from ..partial_emoji import PartialEmoji
from ..utils import MISSING, get as _utils_get

if TYPE_CHECKING:
    from typing_extensions import Self

    from .view import LayoutView
    from .select import (
        BaseSelectT,
        ValidDefaultValues,
        MentionableSelectT,
        ChannelSelectT,
        RoleSelectT,
        UserSelectT,
        SelectT,
    )
    from ..emoji import Emoji
    from ..components import SelectOption
    from ..interactions import Interaction
    from .container import Container
    from .dynamic import DynamicItem

    SelectCallbackDecorator = Callable[[ItemCallbackType['S', BaseSelectT]], BaseSelectT]

S = TypeVar('S', bound=Union['ActionRow', 'Container', 'LayoutView'], covariant=True)
V = TypeVar('V', bound='LayoutView', covariant=True)

__all__ = ('ActionRow',)


class _ActionRowCallback:
    __slots__ = ('row', 'callback', 'item')

    def __init__(self, callback: ItemCallbackType[S, Any], row: ActionRow, item: Item[Any]) -> None:
        self.callback: ItemCallbackType[Any, Any] = callback
        self.row: ActionRow = row
        self.item: Item[Any] = item

    def __call__(self, interaction: Interaction) -> Coroutine[Any, Any, Any]:
        return self.callback(self.row, interaction, self.item)


class ActionRow(Item[V]):
    r"""Represents a UI action row.

    This is a top-level layout component that can only be used on :class:`LayoutView`
    and can contain :class:`Button`\s and :class:`Select`\s in it.

    Action rows can only have 5 children. This can be inherited.

    .. versionadded:: 2.6

    Examples
    --------

    .. code-block:: python3

        import discord
        from discord import ui

        # you can subclass it and add components with the decorators
        class MyActionRow(ui.ActionRow):
            @ui.button(label='Click Me!')
            async def click_me(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message('You clicked me!')

        # or use it directly on LayoutView
        class MyView(ui.LayoutView):
            row = ui.ActionRow()
            # or you can use your subclass:
            # row = MyActionRow()

            # you can add items with row.button and row.select
            @row.button(label='A button!')
            async def row_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message('You clicked a button!')

    Parameters
    ----------
    \*children: :class:`Item`
        The initial children of this action row.
    id: Optional[:class:`int`]
        The ID of this component. This must be unique across the view.
    """

    __action_row_children_items__: ClassVar[List[ItemCallbackType[Self, Any]]] = []
    __discord_ui_action_row__: ClassVar[bool] = True
    __item_repr_attributes__ = ('id',)

    def __init__(
        self,
        *children: Item[V],
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._children: List[Item[V]] = self._init_children()
        self._children.extend(children)
        self._weight: int = sum(i.width for i in self._children)

        if self._weight > 5:
            raise ValueError('maximum number of children exceeded')

        self.id = id

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, ItemCallbackType[Self, Any]] = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if hasattr(member, '__discord_ui_model_type__'):
                    children[name] = member

        if len(children) > 5:
            raise TypeError('ActionRow cannot have more than 5 children')

        cls.__action_row_children_items__ = list(children.values())

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} children={len(self._children)}>'

    def _init_children(self) -> List[Item[Any]]:
        children = []

        for func in self.__action_row_children_items__:
            item: Item = func.__discord_ui_model_type__(**func.__discord_ui_model_kwargs__)
            item.callback = _ActionRowCallback(func, self, item)  # type: ignore
            item._parent = getattr(func, '__discord_ui_parent__', self)
            setattr(self, func.__name__, item)
            children.append(item)
        return children

    def _update_view(self, view) -> None:
        self._view = view
        for child in self._children:
            child._view = view

    def _has_children(self):
        return True

    def _is_v2(self) -> bool:
        # although it is not really a v2 component the only usecase here is for
        # LayoutView which basically represents the top-level payload of components
        # and ActionRow is only allowed there anyways.
        # If the user tries to add any V2 component to a View instead of LayoutView
        # it should error anyways.
        return True

    def _swap_item(self, base: Item, new: DynamicItem, custom_id: str) -> None:
        child_index = self._children.index(base)
        self._children[child_index] = new  # type: ignore

    @property
    def width(self):
        return 5

    @property
    def _total_count(self) -> int:
        # 1 for self and all children
        return 1 + len(self._children)

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        return ComponentType.action_row

    @property
    def children(self) -> List[Item[V]]:
        """List[:class:`Item`]: The list of children attached to this action row."""
        return self._children.copy()

    def walk_children(self) -> Generator[Item[V], Any, None]:
        """An iterator that recursively walks through all the children of this action row
        and its children, if applicable.

        Yields
        ------
        :class:`Item`
            An item in the action row.
        """

        for child in self.children:
            yield child

    def content_length(self) -> int:
        """:class:`int`: Returns the total length of all text content in this action row."""
        from .text_display import TextDisplay

        return sum(len(item.content) for item in self._children if isinstance(item, TextDisplay))

    def add_item(self, item: Item[Any]) -> Self:
        """Adds an item to this action row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to add to the action row.

        Raises
        ------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded (5)
            or (40) for the entire view.
        """

        if (self._weight + item.width) > 5:
            raise ValueError('maximum number of children exceeded')

        if len(self._children) >= 5:
            raise ValueError('maximum number of children exceeded')

        if not isinstance(item, Item):
            raise TypeError(f'expected Item not {item.__class__.__name__}')

        if self._view:
            self._view._add_count(1)

        item._update_view(self.view)
        item._parent = self
        self._weight += 1
        self._children.append(item)

        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from the action row.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        item: :class:`Item`
            The item to remove from the action row.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            if self._view:
                self._view._add_count(-1)
            self._weight -= 1

        return self

    def find_item(self, id: int, /) -> Optional[Item[V]]:
        """Gets an item with :attr:`Item.id` set as ``id``, or ``None`` if
        not found.

        .. warning::

            This is **not the same** as ``custom_id``.

        Parameters
        ----------
        id: :class:`int`
            The ID of the component.

        Returns
        -------
        Optional[:class:`Item`]
            The item found, or ``None``.
        """
        return _utils_get(self.walk_children(), id=id)

    def clear_items(self) -> Self:
        """Removes all items from the action row.

        This function returns the class instance to allow for fluent-style
        chaining.
        """
        if self._view:
            self._view._add_count(-len(self._children))
        self._children.clear()
        self._weight = 0
        return self

    def to_component_dict(self) -> Dict[str, Any]:
        components = []
        for component in self.children:
            components.append(component.to_component_dict())

        base = {
            'type': self.type.value,
            'components': components,
        }
        if self.id is not None:
            base['id'] = self.id
        return base

    def button(
        self,
        *,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        disabled: bool = False,
        style: ButtonStyle = ButtonStyle.secondary,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        id: Optional[int] = None,
    ) -> Callable[[ItemCallbackType[S, Button[V]]], Button[V]]:
        """A decorator that attaches a button to the action row.

        The function being decorated should have three parameters, ``self`` representing
        the :class:`discord.ui.ActionRow`, the :class:`discord.Interaction` you receive and
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
        id: Optional[:class:`int`]
            The ID of the component. This must be unique across the view.

            .. versionadded:: 2.6
        """

        def decorator(func: ItemCallbackType[S, Button[V]]) -> ItemCallbackType[S, Button[V]]:
            ret = _button(
                label=label,
                custom_id=custom_id,
                disabled=disabled,
                style=style,
                emoji=emoji,
                row=None,
                id=id,
            )(func)
            ret.__discord_ui_parent__ = self  # type: ignore
            return ret  # type: ignore

        return decorator  # type: ignore

    @overload
    def select(
        self,
        *,
        cls: Type[SelectT] = Select[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = ...,
        placeholder: Optional[str] = ...,
        custom_id: str = ...,
        min_values: int = ...,
        max_values: int = ...,
        disabled: bool = ...,
        id: Optional[int] = ...,
    ) -> SelectCallbackDecorator[S, SelectT]: ...

    @overload
    def select(
        self,
        *,
        cls: Type[UserSelectT] = UserSelect[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = ...,
        placeholder: Optional[str] = ...,
        custom_id: str = ...,
        min_values: int = ...,
        max_values: int = ...,
        disabled: bool = ...,
        default_values: Sequence[ValidDefaultValues] = ...,
        id: Optional[int] = ...,
    ) -> SelectCallbackDecorator[S, UserSelectT]: ...

    @overload
    def select(
        self,
        *,
        cls: Type[RoleSelectT] = RoleSelect[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = ...,
        placeholder: Optional[str] = ...,
        custom_id: str = ...,
        min_values: int = ...,
        max_values: int = ...,
        disabled: bool = ...,
        default_values: Sequence[ValidDefaultValues] = ...,
        id: Optional[int] = ...,
    ) -> SelectCallbackDecorator[S, RoleSelectT]: ...

    @overload
    def select(
        self,
        *,
        cls: Type[ChannelSelectT] = ChannelSelect[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = ...,
        placeholder: Optional[str] = ...,
        custom_id: str = ...,
        min_values: int = ...,
        max_values: int = ...,
        disabled: bool = ...,
        default_values: Sequence[ValidDefaultValues] = ...,
        id: Optional[int] = ...,
    ) -> SelectCallbackDecorator[S, ChannelSelectT]: ...

    @overload
    def select(
        self,
        *,
        cls: Type[MentionableSelectT] = MentionableSelect[Any],
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = MISSING,
        placeholder: Optional[str] = ...,
        custom_id: str = ...,
        min_values: int = ...,
        max_values: int = ...,
        disabled: bool = ...,
        default_values: Sequence[ValidDefaultValues] = ...,
        id: Optional[int] = ...,
    ) -> SelectCallbackDecorator[S, MentionableSelectT]: ...

    def select(
        self,
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
        id: Optional[int] = None,
    ) -> SelectCallbackDecorator[S, BaseSelectT]:
        """A decorator that attaches a select menu to the action row.

        The function being decorated should have three parameters, ``self`` representing
        the :class:`discord.ui.ActionRow`, the :class:`discord.Interaction` you receive and
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

        Example
        ---------
        .. code-block:: python3

            class MyView(discord.ui.LayoutView):
                action_row = discord.ui.ActionRow()

                @action_row.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text])
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
        id: Optional[:class:`int`]
            The ID of the component. This must be unique across the view.

            .. versionadded:: 2.6
        """

        def decorator(func: ItemCallbackType[S, BaseSelectT]) -> ItemCallbackType[S, BaseSelectT]:
            r = _select(  # type: ignore
                cls=cls,  # type: ignore
                placeholder=placeholder,
                custom_id=custom_id,
                min_values=min_values,
                max_values=max_values,
                options=options,
                channel_types=channel_types,
                disabled=disabled,
                default_values=default_values,
                id=id,
            )(func)
            r.__discord_ui_parent__ = self
            return r

        return decorator  # type: ignore

    @classmethod
    def from_component(cls, component: ActionRowComponent) -> ActionRow:
        from .view import _component_to_item

        self = cls(id=component.id)
        for cmp in component.children:
            self.add_item(_component_to_item(cmp, self))
        return self
