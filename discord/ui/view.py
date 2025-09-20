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
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Set,
    Tuple,
    Type,
    Union,
)
from functools import partial
from itertools import groupby

import asyncio
import logging
import sys
import time
import os

from .item import Item, ItemCallbackType
from .select import Select
from .dynamic import DynamicItem
from ..components import (
    Component,
    ActionRow as ActionRowComponent,
    _component_factory,
    Button as ButtonComponent,
    SelectMenu as SelectComponent,
    SectionComponent,
    TextDisplay as TextDisplayComponent,
    MediaGalleryComponent,
    FileComponent,
    SeparatorComponent,
    ThumbnailComponent,
    Container as ContainerComponent,
    LabelComponent,
)
from ..utils import get as _utils_get, find as _utils_find

# fmt: off
__all__ = (
    'View',
    'LayoutView',
)
# fmt: on


if TYPE_CHECKING:
    from typing_extensions import Self
    import re

    from ..interactions import Interaction
    from ..message import Message
    from ..types.components import ComponentBase as ComponentBasePayload
    from ..types.interactions import ModalSubmitComponentInteractionData as ModalSubmitComponentInteractionDataPayload
    from ..state import ConnectionState
    from .modal import Modal

    ItemLike = Union[ItemCallbackType[Any, Any], Item[Any]]


_log = logging.getLogger(__name__)


def _walk_all_components(components: List[Component]) -> Iterator[Component]:
    for item in components:
        if isinstance(item, ActionRowComponent):
            yield from item.children
        elif isinstance(item, ContainerComponent):
            yield from _walk_all_components(item.children)
        elif isinstance(item, SectionComponent):
            yield from item.children
            yield item.accessory
        else:
            yield item


def _component_to_item(component: Component, parent: Optional[Item] = None) -> Item:
    if isinstance(component, ActionRowComponent):
        from .action_row import ActionRow

        item = ActionRow.from_component(component)
    elif isinstance(component, ButtonComponent):
        from .button import Button

        item = Button.from_component(component)
    elif isinstance(component, SelectComponent):
        from .select import BaseSelect

        item = BaseSelect.from_component(component)
    elif isinstance(component, SectionComponent):
        from .section import Section

        item = Section.from_component(component)
    elif isinstance(component, TextDisplayComponent):
        from .text_display import TextDisplay

        item = TextDisplay.from_component(component)
    elif isinstance(component, MediaGalleryComponent):
        from .media_gallery import MediaGallery

        item = MediaGallery.from_component(component)
    elif isinstance(component, FileComponent):
        from .file import File

        item = File.from_component(component)
    elif isinstance(component, SeparatorComponent):
        from .separator import Separator

        item = Separator.from_component(component)
    elif isinstance(component, ThumbnailComponent):
        from .thumbnail import Thumbnail

        item = Thumbnail.from_component(component)
    elif isinstance(component, ContainerComponent):
        from .container import Container

        item = Container.from_component(component)
    elif isinstance(component, LabelComponent):
        from .label import Label

        item = Label.from_component(component)
    else:
        item = Item.from_component(component)

    item._parent = parent
    return item


class _ViewWeights:
    # fmt: off
    __slots__ = (
        'weights',
    )
    # fmt: on

    def __init__(self, children: List[Item]):
        self.weights: List[int] = [0, 0, 0, 0, 0]

        key = lambda i: sys.maxsize if i.row is None else i.row
        children = sorted(children, key=key)
        for row, group in groupby(children, key=key):
            for item in group:
                self.add_item(item)

    def find_open_space(self, item: Item) -> int:
        for index, weight in enumerate(self.weights):
            if weight + item.width <= 5:
                return index

        raise ValueError('could not find open space for item')

    def add_item(self, item: Item) -> None:
        if item.row is not None:
            total = self.weights[item.row] + item.width
            if total > 5:
                raise ValueError(f'item would not fit at row {item.row} ({total} > 5 width)')
            self.weights[item.row] = total
            item._rendered_row = item.row
        else:
            index = self.find_open_space(item)
            self.weights[index] += item.width
            item._rendered_row = index

    def remove_item(self, item: Item) -> None:
        if item._rendered_row is not None:
            self.weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self.weights = [0, 0, 0, 0, 0]


class _ViewCallback:
    __slots__ = ('view', 'callback', 'item')

    def __init__(self, callback: ItemCallbackType[Any, Any], view: BaseView, item: Item[BaseView]) -> None:
        self.callback: ItemCallbackType[Any, Any] = callback
        self.view: BaseView = view
        self.item: Item[BaseView] = item

    def __call__(self, interaction: Interaction) -> Coroutine[Any, Any, Any]:
        return self.callback(self.view, interaction, self.item)


class BaseView:
    __discord_ui_view__: ClassVar[bool] = False
    __discord_ui_modal__: ClassVar[bool] = False
    __view_children_items__: ClassVar[Dict[str, ItemLike]] = {}

    def __init__(self, *, timeout: Optional[float] = 180.0) -> None:
        self.__timeout = timeout
        self._children: List[Item[Self]] = self._init_children()
        self.id: str = os.urandom(16).hex()
        self._cache_key: Optional[int] = None
        self.__cancel_callback: Optional[Callable[[BaseView], None]] = None
        self.__timeout_expiry: Optional[float] = None
        self.__timeout_task: Optional[asyncio.Task[None]] = None
        self.__stopped: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self._total_children: int = len(tuple(self.walk_children()))

    def _is_layout(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} timeout={self.timeout} children={len(self._children)}>'

    def _init_children(self) -> List[Item[Self]]:
        children = []
        parents = {}

        for name, raw in self.__view_children_items__.items():
            if isinstance(raw, Item):
                item = raw.copy()
                setattr(self, name, item)
                item._update_view(self)
                parent = getattr(item, '__discord_ui_parent__', None)
                if parent and parent._view is None:
                    parent._view = self
                children.append(item)
                parents[raw] = item
            else:
                item: Item = raw.__discord_ui_model_type__(**raw.__discord_ui_model_kwargs__)
                item.callback = _ViewCallback(raw, self, item)  # type: ignore
                item._view = self
                if isinstance(item, Select):
                    item.options = [option.copy() for option in item.options]
                setattr(self, raw.__name__, item)
                parent = getattr(raw, '__discord_ui_parent__', None)
                if parent:
                    parents.get(parent, parent)._children.append(item)
                    continue
                children.append(item)

        return children

    async def __timeout_task_impl(self) -> None:
        while True:
            # Guard just in case someone changes the value of the timeout at runtime
            if self.timeout is None:
                return

            if self.__timeout_expiry is None:
                return self._dispatch_timeout()

            # Check if we've elapsed our currently set timeout
            now = time.monotonic()
            if now >= self.__timeout_expiry:
                return self._dispatch_timeout()

            # Wait N seconds to see if timeout data has been refreshed
            await asyncio.sleep(self.__timeout_expiry - now)

    def is_dispatchable(self) -> bool:
        # checks whether any interactable items (buttons or selects) are present
        # in this view, and check whether this requires a state attached in case
        # of webhooks and if the view should be stored in the view store
        return any(item.is_dispatchable() for item in self.walk_children())

    def has_components_v2(self) -> bool:
        return any(c._is_v2() for c in self.children)

    def to_components(self) -> List[Dict[str, Any]]:
        return NotImplemented

    def _refresh_timeout(self) -> None:
        if self.__timeout:
            self.__timeout_expiry = time.monotonic() + self.__timeout

    def _swap_item(self, base: Item, new: DynamicItem, custom_id: str) -> None:
        # if an error is raised it is catched by the try/except block that calls
        # this function
        child_index = self._children.index(base)
        self._children[child_index] = new  # type: ignore

    @property
    def timeout(self) -> Optional[float]:
        """Optional[:class:`float`]: The timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
        """
        return self.__timeout

    @timeout.setter
    def timeout(self, value: Optional[float]) -> None:
        # If the timeout task is already running this allows it to update
        # the expiry while it's running
        if self.__timeout_task is not None:
            if value is not None:
                self.__timeout_expiry = time.monotonic() + value
            else:
                self.__timeout_expiry = None

        self.__timeout = value

    def _add_count(self, value: int) -> None:
        self._total_children = max(0, self._total_children + value)

    @property
    def children(self) -> List[Item[Self]]:
        """List[:class:`Item`]: The list of children attached to this view."""
        return self._children.copy()

    @property
    def total_children_count(self) -> int:
        """:class:`int`: The total number of children in this view, including those from nested items.

        .. versionadded:: 2.6"""
        return self._total_children

    @classmethod
    def from_message(cls, message: Message, /, *, timeout: Optional[float] = 180.0) -> Union[View, LayoutView]:
        """Converts a message's components into a :class:`View`
        or :class:`LayoutView`.

        The :attr:`.Message.components` of a message are read-only
        and separate types from those in the ``discord.ui`` namespace.
        In order to modify and edit message components they must be
        converted into a :class:`View` or :class:`LayoutView` first.

        If the message has any v2 components, then you must use
        :class:`LayoutView` in order for them to be converted into
        their respective items. :class:`View` does not support v2 components.

        Parameters
        -----------
        message: :class:`discord.Message`
            The message with components to convert into a view.
        timeout: Optional[:class:`float`]
            The timeout of the converted view.

        Returns
        -------
        Union[:class:`View`, :class:`LayoutView`]
            The converted view. This will always return one of :class:`View` or
            :class:`LayoutView`, and not one of its subclasses.
        """

        if issubclass(cls, View):
            view_cls = View
        elif issubclass(cls, LayoutView):
            view_cls = LayoutView
        else:
            raise TypeError('unreachable exception')

        view = view_cls(timeout=timeout)
        row = 0

        for component in message.components:
            if not view._is_layout() and isinstance(component, ActionRowComponent):
                for child in component.children:
                    item = _component_to_item(child)
                    item.row = row
                    # this error should never be raised, because ActionRows can only
                    # contain items that View accepts, but check anyways
                    if item._is_v2():
                        raise ValueError(f'{item.__class__.__name__} cannot be added to {view.__class__.__name__}')
                    view.add_item(item)
                row += 1
                continue

            item = _component_to_item(component)
            item.row = row

            if item._is_v2() and not view._is_layout():
                raise ValueError(f'{item.__class__.__name__} cannot be added to {view.__class__.__name__}')

            view.add_item(item)
            row += 1

        return view

    def add_item(self, item: Item[Any]) -> Self:
        """Adds an item to the view.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        item: :class:`Item`
            The item to add to the view.

        Raises
        --------
        TypeError
            An :class:`Item` was not passed.
        ValueError
            Maximum number of children has been exceeded, the
            row the item is trying to be added to is full or the item
            you tried to add is not allowed in this View.
        """

        if not isinstance(item, Item):
            raise TypeError(f'expected Item not {item.__class__.__name__}')

        item._update_view(self)
        self._add_count(item._total_count)
        self._children.append(item)
        return self

    def remove_item(self, item: Item[Any]) -> Self:
        """Removes an item from the view.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        -----------
        item: :class:`Item`
            The item to remove from the view.
        """

        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            self._add_count(-item._total_count)

        return self

    def clear_items(self) -> Self:
        """Removes all items from the view.

        This function returns the class instance to allow for fluent-style
        chaining.
        """
        self._children.clear()
        self._total_children = 0
        return self

    def find_item(self, id: int, /) -> Optional[Item[Self]]:
        """Gets an item with :attr:`Item.id` set as ``id``, or ``None`` if
        not found.

        .. warning::

            This is **not the same** as ``custom_id``.

        .. versionadded:: 2.6

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

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        """|coro|

        A callback that is called when an interaction happens within the view
        that checks whether the view should process item callbacks for the interaction.

        This is useful to override if, for example, you want to ensure that the
        interaction author is a given user.

        The default implementation of this returns ``True``.

        .. note::

            If an exception occurs within the body then the check
            is considered a failure and :meth:`on_error` is called.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that occurred.

        Returns
        ---------
        :class:`bool`
            Whether the view children's callbacks should be called.
        """
        return True

    async def on_timeout(self) -> None:
        """|coro|

        A callback that is called when a view's timeout elapses without being explicitly stopped.
        """
        pass

    async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any], /) -> None:
        """|coro|

        A callback that is called when an item's callback or :meth:`interaction_check`
        fails with an error.

        The default implementation logs to the library logger.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that led to the failure.
        error: :class:`Exception`
            The exception that was raised.
        item: :class:`Item`
            The item that failed the dispatch.
        """
        _log.error('Ignoring exception in view %r for item %r', self, item, exc_info=error)

    async def _scheduled_task(self, item: Item, interaction: Interaction):
        try:
            item._refresh_state(interaction, interaction.data)  # type: ignore

            allow = await item._run_checks(interaction) and await self.interaction_check(interaction)
            if not allow:
                return

            if self.timeout:
                self.__timeout_expiry = time.monotonic() + self.timeout

            await item.callback(interaction)
        except Exception as e:
            return await self.on_error(interaction, e, item)

    def _start_listening_from_store(self, store: ViewStore) -> None:
        self.__cancel_callback = partial(store.remove_view)  # type: ignore
        if self.timeout:
            if self.__timeout_task is not None:
                self.__timeout_task.cancel()

            self.__timeout_expiry = time.monotonic() + self.timeout
            self.__timeout_task = asyncio.create_task(self.__timeout_task_impl())

    def _dispatch_timeout(self):
        if self.__stopped.done():
            return

        if self.__cancel_callback:
            self.__cancel_callback(self)
            self.__cancel_callback = None

        self.__stopped.set_result(True)
        asyncio.create_task(self.on_timeout(), name=f'discord-ui-view-timeout-{self.id}')

    def _dispatch_item(self, item: Item, interaction: Interaction) -> Optional[asyncio.Task[None]]:
        if self.__stopped.done():
            return

        return asyncio.create_task(self._scheduled_task(item, interaction), name=f'discord-ui-view-dispatch-{self.id}')

    def _refresh(self, components: List[Component]) -> None:
        # fmt: off
        old_state: Dict[str, Item[Any]] = {
            item.custom_id: item  # type: ignore
            for item in self.walk_children()
            if item.is_dispatchable()
        }
        # fmt: on

        for component in _walk_all_components(components):
            custom_id = getattr(component, 'custom_id', None)
            if custom_id is None:
                continue

            try:
                older = old_state[custom_id]
            except KeyError:
                _log.debug('View interaction referenced an unknown item custom_id %s. Discarding', custom_id)
                continue
            else:
                older._refresh_component(component)

    def stop(self) -> None:
        """Stops listening to interaction events from this view.

        This operation cannot be undone.
        """
        if not self.__stopped.done():
            self.__stopped.set_result(False)

        self.__timeout_expiry = None
        if self.__timeout_task is not None:
            self.__timeout_task.cancel()
            self.__timeout_task = None

        if self.__cancel_callback:
            self.__cancel_callback(self)
            self.__cancel_callback = None

    def is_finished(self) -> bool:
        """:class:`bool`: Whether the view has finished interacting."""
        return self.__stopped.done()

    def is_dispatching(self) -> bool:
        """:class:`bool`: Whether the view has been added for dispatching purposes."""
        return self.__cancel_callback is not None

    def is_persistent(self) -> bool:
        """:class:`bool`: Whether the view is set up as persistent.

        A persistent view has all their components with a set ``custom_id`` and
        a :attr:`timeout` set to ``None``.
        """
        return self.timeout is None and all(item.is_persistent() for item in self._children)

    async def wait(self) -> bool:
        """|coro|

        Waits until the view has finished interacting.

        A view is considered finished when :meth:`stop` is called
        or it times out.

        Returns
        --------
        :class:`bool`
            If ``True``, then the view timed out. If ``False`` then
            the view finished normally.
        """
        return await self.__stopped

    def walk_children(self) -> Generator[Item[Any], None, None]:
        """An iterator that recursively walks through all the children of this view
        and its children, if applicable.

        .. versionadded:: 2.6

        Yields
        ------
        :class:`Item`
            An item in the view.
        """

        for child in self.children:
            yield child

            if child._has_children():
                yield from child.walk_children()  # type: ignore


class View(BaseView):
    """Represents a UI view.

    This object must be inherited to create a UI within Discord.

    .. versionadded:: 2.0

    Parameters
    -----------
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    """

    __discord_ui_view__: ClassVar[bool] = True

    if TYPE_CHECKING:

        @classmethod
        def from_message(cls, message: Message, /, *, timeout: Optional[float] = 180.0) -> View: ...

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, ItemLike] = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if hasattr(member, '__discord_ui_model_type__'):
                    children[name] = member
                elif isinstance(member, Item) and member._is_v2():
                    raise ValueError(f'{name} cannot be added to this View')

        if len(children) > 25:
            raise TypeError('View cannot have more than 25 children')

        cls.__view_children_items__ = children

    def __init__(self, *, timeout: Optional[float] = 180.0):
        super().__init__(timeout=timeout)
        self.__weights = _ViewWeights(self._children)

    def to_components(self) -> List[Dict[str, Any]]:
        def key(item: Item) -> int:
            return item._rendered_row or 0

        children = sorted(self._children, key=key)
        components: List[Dict[str, Any]] = []
        for _, group in groupby(children, key=key):
            children = [item.to_component_dict() for item in group]
            if not children:
                continue

            components.append(
                {
                    'type': 1,
                    'components': children,
                }
            )

        return components

    def add_item(self, item: Item[Any]) -> Self:
        if len(self._children) >= 25:
            raise ValueError('maximum number of children exceeded')

        if item._is_v2():
            raise ValueError('v2 items cannot be added to this view')

        super().add_item(item)
        try:
            self.__weights.add_item(item)
        except ValueError as e:
            # if the item has no space left then remove it from _children
            self._children.remove(item)
            raise e

        return self

    def remove_item(self, item: Item[Any]) -> Self:
        try:
            self._children.remove(item)
        except ValueError:
            pass
        else:
            self.__weights.remove_item(item)
        return self

    def clear_items(self) -> Self:
        super().clear_items()
        self.__weights.clear()
        return self


class LayoutView(BaseView):
    """Represents a layout view for components.

    This object must be inherited to create a UI within Discord.

    This differs from a :class:`View` in that it supports all component types
    and uses what Discord refers to as "v2 components".

    You can find usage examples in the :resource:`repository <examples>`

    .. versionadded:: 2.6

    Parameters
    ----------
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    """

    if TYPE_CHECKING:

        @classmethod
        def from_message(cls, message: Message, /, *, timeout: Optional[float] = 180.0) -> LayoutView: ...

    def __init__(self, *, timeout: Optional[float] = 180.0) -> None:
        super().__init__(timeout=timeout)

        if self._total_children > 40:
            raise ValueError('maximum number of children exceeded (40)')

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        children: Dict[str, ItemLike] = {}
        callback_children: Dict[str, ItemCallbackType[Any, Any]] = {}

        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if isinstance(member, Item):
                    if member._parent is not None:
                        continue

                    member._rendered_row = member._row
                    children[name] = member
                elif hasattr(member, '__discord_ui_model_type__') and getattr(member, '__discord_ui_parent__', None):
                    callback_children[name] = member

        children.update(callback_children)
        cls.__view_children_items__ = children

    def _is_layout(self) -> bool:
        return True

    def _add_count(self, value: int) -> None:
        if self._total_children + value > 40:
            raise ValueError('maximum number of children exceeded (40)')

        self._total_children = max(0, self._total_children + value)

    def to_components(self):
        components: List[Dict[str, Any]] = []
        for i in self._children:
            components.append(i.to_component_dict())

        return components

    def add_item(self, item: Item[Any]) -> Self:
        if self._total_children >= 40:
            raise ValueError('maximum number of children exceeded (40)')
        super().add_item(item)
        return self

    def content_length(self) -> int:
        """:class:`int`: Returns the total length of all text content in the view's items.

        A view is allowed to have a maximum of 4000 display characters across all its items.
        """
        from .text_display import TextDisplay

        return sum(len(item.content) for item in self.walk_children() if isinstance(item, TextDisplay))


class ViewStore:
    def __init__(self, state: ConnectionState):
        # entity_id: {(component_type, custom_id): Item}
        self._views: Dict[Optional[int], Dict[Tuple[int, str], Item[BaseView]]] = {}
        # message_id: View
        self._synced_message_views: Dict[int, BaseView] = {}
        # custom_id: Modal
        self._modals: Dict[str, Modal] = {}
        # component_type is the key
        self._dynamic_items: Dict[re.Pattern[str], Type[DynamicItem[Item[Any]]]] = {}
        self._state: ConnectionState = state
        self.__tasks: Set[asyncio.Task[None]] = set()

    @property
    def persistent_views(self) -> Sequence[BaseView]:
        # fmt: off
        views = {
            item.view.id: item.view
            for items in self._views.values()
            for item in items.values()
            if item.view and item.view.is_persistent()
        }
        # fmt: on
        return list(views.values())

    def add_task(self, task: asyncio.Task[None]) -> None:
        self.__tasks.add(task)
        task.add_done_callback(self.__tasks.discard)

    def add_dynamic_items(self, *items: Type[DynamicItem[Item[Any]]]) -> None:
        for item in items:
            pattern = item.__discord_ui_compiled_template__
            self._dynamic_items[pattern] = item

    def remove_dynamic_items(self, *items: Type[DynamicItem[Item[Any]]]) -> None:
        for item in items:
            pattern = item.__discord_ui_compiled_template__
            self._dynamic_items.pop(pattern, None)

    def add_view(self, view: BaseView, message_id: Optional[int] = None) -> None:
        view._start_listening_from_store(self)
        if view.__discord_ui_modal__:
            self._modals[view.custom_id] = view  # type: ignore
            return

        dispatch_info = self._views.setdefault(message_id, {})
        is_fully_dynamic = True
        for item in view.walk_children():
            if isinstance(item, DynamicItem):
                pattern = item.__discord_ui_compiled_template__
                self._dynamic_items[pattern] = item.__class__
            elif item.is_dispatchable():
                dispatch_info[(item.type.value, item.custom_id)] = item  # type: ignore
                is_fully_dynamic = False

        view._cache_key = message_id
        if message_id is not None and not is_fully_dynamic:
            self._synced_message_views[message_id] = view

    def remove_view(self, view: View) -> None:
        if view.__discord_ui_modal__:
            self._modals.pop(view.custom_id, None)  # type: ignore
            return

        dispatch_info = self._views.get(view._cache_key)
        if dispatch_info:
            for item in view._children:
                if isinstance(item, DynamicItem):
                    pattern = item.__discord_ui_compiled_template__
                    self._dynamic_items.pop(pattern, None)
                elif item.is_dispatchable():
                    dispatch_info.pop((item.type.value, item.custom_id), None)  # type: ignore

            if len(dispatch_info) == 0:
                self._views.pop(view._cache_key, None)

        self._synced_message_views.pop(view._cache_key, None)  # type: ignore

    async def schedule_dynamic_item_call(
        self,
        component_type: int,
        factory: Type[DynamicItem[Item[Any]]],
        interaction: Interaction,
        custom_id: str,
        match: re.Match[str],
    ) -> None:
        if interaction.message is None:
            return

        view_cls = View if not interaction.message.flags.components_v2 else LayoutView
        view = view_cls.from_message(interaction.message, timeout=None)

        base_item = _utils_find(
            lambda i: i.type.value == component_type and getattr(i, 'custom_id', None) == custom_id,
            view.walk_children(),
        )

        # if the item is not found then return
        if not base_item:
            return

        try:
            item = await factory.from_custom_id(interaction, base_item, match)
        except Exception:
            _log.exception('Ignoring exception in dynamic item creation for %r', factory)
            return

        # Swap the item in the view or parent with our new dynamic item
        # Prioritize the item parent:
        parent = base_item._parent or view

        try:
            parent._swap_item(base_item, item, custom_id)
        except ValueError:
            return

        item._view = view
        item._rendered_row = base_item._rendered_row
        item._refresh_state(interaction, interaction.data)  # type: ignore

        try:
            allow = await item.interaction_check(interaction)
        except Exception:
            allow = False

        if not allow:
            return

        try:
            await item.callback(interaction)
        except Exception:
            _log.exception('Ignoring exception in dynamic item callback for %r', item)

    def dispatch_dynamic_items(self, component_type: int, custom_id: str, interaction: Interaction) -> None:
        for pattern, item in self._dynamic_items.items():
            match = pattern.fullmatch(custom_id)
            if match is not None:
                self.add_task(
                    asyncio.create_task(
                        self.schedule_dynamic_item_call(component_type, item, interaction, custom_id, match),
                        name=f'discord-ui-dynamic-item-{item.__name__}-{custom_id}',
                    )
                )

    def dispatch_view(self, component_type: int, custom_id: str, interaction: Interaction) -> None:
        self.dispatch_dynamic_items(component_type, custom_id, interaction)
        interaction_id: Optional[int] = None
        message_id: Optional[int] = None
        # Realistically, in a component based interaction the Interaction.message will never be None
        # However, this guard is just in case Discord screws up somehow
        msg = interaction.message
        if msg is not None:
            message_id = msg.id
            if msg.interaction_metadata:
                interaction_id = msg.interaction_metadata.id

        key = (component_type, custom_id)

        # The entity_id can either be message_id, interaction_id, or None in that priority order.
        item: Optional[Item[BaseView]] = None
        if message_id is not None:
            item = self._views.get(message_id, {}).get(key)

        if item is None and interaction_id is not None:
            try:
                items = self._views.pop(interaction_id)
            except KeyError:
                item = None
            else:
                item = items.get(key)
                # If we actually got the items, then these keys should probably be moved
                # to the proper message_id instead of the interaction_id as they are now.
                # An interaction_id is only used as a temporary stop gap for
                # InteractionResponse.send_message so multiple view instances do not
                # override each other.
                # NOTE: Fix this mess if /callback endpoint ever gets proper return types
                self._views.setdefault(message_id, {}).update(items)

        if item is None:
            # Fallback to None message_id searches in case a persistent view
            # was added without an associated message_id
            item = self._views.get(None, {}).get(key)

        # If 3 lookups failed at this point then just discard it
        if item is None:
            return

        # Note, at this point the View is *not* None
        task = item.view._dispatch_item(item, interaction)  # type: ignore
        if task is not None:
            self.add_task(task)

    def dispatch_modal(
        self,
        custom_id: str,
        interaction: Interaction,
        components: List[ModalSubmitComponentInteractionDataPayload],
    ) -> None:
        modal = self._modals.get(custom_id)
        if modal is None:
            _log.debug('Modal interaction referencing unknown custom_id %s. Discarding', custom_id)
            return

        self.add_task(modal._dispatch_submit(interaction, components))

    def remove_interaction_mapping(self, interaction_id: int) -> None:
        # This is called before re-adding the view
        self._views.pop(interaction_id, None)
        self._synced_message_views.pop(interaction_id, None)

    def is_message_tracked(self, message_id: int) -> bool:
        return message_id in self._synced_message_views

    def remove_message_tracking(self, message_id: int) -> Optional[BaseView]:
        return self._synced_message_views.pop(message_id, None)

    def update_from_message(self, message_id: int, data: List[ComponentBasePayload]) -> None:
        components: List[Component] = []

        for component_data in data:
            component = _component_factory(component_data, self._state)  # type: ignore

            if component is not None:
                components.append(component)

        # pre-req: is_message_tracked == true
        view = self._synced_message_views[message_id]
        view._refresh(components)
