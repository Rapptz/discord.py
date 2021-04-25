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

from typing import Callable, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, Union
import inspect
import re
import os


from .item import Item, ItemCallbackType
from ..enums import ButtonStyle, ComponentType
from ..partial_emoji import PartialEmoji
from ..components import Button as ButtonComponent

__all__ = (
    'Button',
    'button',
)

if TYPE_CHECKING:
    from ..components import Component

_custom_emoji = re.compile(r'<?(?P<animated>a)?:?(?P<name>[A-Za-z0-9\_]+):(?P<id>[0-9]{13,20})>?')


def _to_partial_emoji(obj: Union[str, PartialEmoji], *, _custom_emoji=_custom_emoji) -> PartialEmoji:
    if isinstance(obj, PartialEmoji):
        return obj

    obj = str(obj)
    match = _custom_emoji.match(obj)
    if match is not None:
        groups = match.groupdict()
        animated = bool(groups['animated'])
        emoji_id = int(groups['id'])
        name = groups['name']
        return PartialEmoji(name=name, animated=animated, id=emoji_id)

    return PartialEmoji(name=obj, id=None, animated=False)


B = TypeVar('B', bound='Button')


class Button(Item):
    """Represents a UI button.

    .. versionadded:: 2.0

    Parameters
    ------------
    style: :class:`discord.ButtonStyle`
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

    __slots__: Tuple[str, ...] = Item.__slots__ + ('_underlying',)

    __item_repr_attributes__: Tuple[str, ...] = (
        'style',
        'url',
        'disabled',
        'label',
        'emoji',
        'group_id',
    )

    def __init__(
        self,
        *,
        style: ButtonStyle,
        label: str,
        disabled: bool = False,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, PartialEmoji]] = None,
        group: Optional[int] = None,
    ):
        super().__init__()
        if custom_id is not None and url is not None:
            raise TypeError('cannot mix both url and custom_id with Button')

        if url is None and custom_id is None:
            custom_id = os.urandom(16).hex()

        self._underlying = ButtonComponent._raw_construct(
            type=ComponentType.button,
            custom_id=custom_id,
            url=url,
            disabled=disabled,
            label=label,
            style=style,
            emoji=None if emoji is None else _to_partial_emoji(emoji),
        )
        self.group_id = group

    @property
    def style(self) -> ButtonStyle:
        """:class:`discord.ButtonStyle`: The style of the button."""
        return self._underlying.style

    @style.setter
    def style(self, value: ButtonStyle):
        self._underlying.style = value

    @property
    def custom_id(self) -> Optional[str]:
        """Optional[:class:`str`]: The ID of the button that gets received during an interaction.

        If this button is for a URL, it does not have a custom ID.
        """
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError('custom_id must be None or str')

        self._underlying.custom_id = value

    @property
    def url(self) -> Optional[str]:
        """Optional[:class:`str`]: The URL this button sends you to."""
        return self._underlying.url

    @url.setter
    def url(self, value: Optional[str]):
        if value is not None and not isinstance(value, str):
            raise TypeError('url must be None or str')
        self._underlying.url = value

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether the button is disabled or not."""
        return self._underlying.disabled

    @disabled.setter
    def disabled(self, value: bool):
        self._underlying.disabled = bool(value)

    @property
    def label(self) -> str:
        """:class:`str`: The label of the button."""
        return self._underlying.label

    @label.setter
    def label(self, value: str):
        self._underlying.label = str(value)

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`PartialEmoji`]: The emoji of the button, if available."""
        return self._underlying.emoji

    @emoji.setter
    def emoji(self, value: Optional[Union[str, PartialEmoji]]):  # type: ignore
        if value is not None:
            self._underlying.emoji = _to_partial_emoji(value)
        else:
            self._underlying.emoji = None

    def copy(self: B) -> B:
        button = self.__class__(
            style=self.style,
            label=self.label,
            disabled=self.disabled,
            custom_id=self.custom_id,
            url=self.url,
            emoji=self.emoji,
            group=self.group_id,
        )
        button.callback = self.callback
        return button

    @classmethod
    def from_component(cls: Type[B], button: ButtonComponent) -> B:
        return cls(
            style=button.style,
            label=button.label,
            disabled=button.disabled,
            custom_id=button.custom_id,
            url=button.url,
            emoji=button.emoji,
            group=None,
        )

    @property
    def type(self) -> ComponentType:
        return self._underlying.type

    def to_component_dict(self):
        return self._underlying.to_dict()

    def is_dispatchable(self) -> bool:
        return True

    def refresh_state(self, button: ButtonComponent) -> None:
        self._underlying = button


def button(
    label: str,
    *,
    custom_id: Optional[str] = None,
    disabled: bool = False,
    style: ButtonStyle = ButtonStyle.grey,
    emoji: Optional[Union[str, PartialEmoji]] = None,
    group: Optional[int] = None,
) -> Callable[[ItemCallbackType], Button]:
    """A decorator that attaches a button to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`discord.ui.View`, the :class:`discord.ui.Button` being pressed and
    the :class:`discord.Interaction` you receive.

    .. note::

        Buttons with a URL cannot be created with this function.
        Consider creating a :class:`Button` manually instead.
        This is because buttons with a URL do not have a callback
        associated with them since Discord does not do any processing
        with it.

    Parameters
    ------------
    label: :class:`str`
        The label of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        It is recommended not to set this parameter to prevent conflicts.
    style: :class:`ButtonStyle`
        The style of the button. Defaults to :attr:`ButtonStyle.grey`.
    disabled: :class:`bool`
        Whether the button is disabled or not. Defaults to ``False``.
    emoji: Optional[Union[:class:`str`, :class:`PartialEmoji`]]
        The emoji of the button. This can be in string form or a :class:`PartialEmoji`.
    group: Optional[:class:`int`]
        The relative group this button belongs to. A Discord component can only have 5
        groups. By default, items are arranged automatically into those 5 groups. If you'd
        like to control the relative positioning of the group then passing an index is advised.
        For example, group=1 will show up before group=2. Defaults to ``None``, which is automatic
        ordering.
    """

    def decorator(func: ItemCallbackType) -> Button:
        nonlocal custom_id
        if not inspect.iscoroutinefunction(func):
            raise TypeError('button function must be a coroutine function')

        custom_id = custom_id or os.urandom(32).hex()
        button = Button(style=style, custom_id=custom_id, url=None, disabled=disabled, label=label, emoji=emoji, group=group)
        button.callback = func
        return button

    return decorator
