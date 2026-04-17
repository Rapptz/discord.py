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
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Tuple, TypeVar, Dict

import os

from ..utils import MISSING
from ..components import RadioGroupComponent, RadioGroupOption
from ..enums import ComponentType
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..interactions import Interaction
    from ..types.interactions import (
        ModalSubmitRadioGroupInteractionData as ModalSubmitRadioGroupInteractionDataPayload,
    )
    from ..types.components import RadioGroupComponent as RadioGroupComponentPayload
    from .view import BaseView
    from ..app_commands.namespace import ResolveKey


# fmt: off
__all__ = (
    'RadioGroup',
)
# fmt: on

V = TypeVar('V', bound='BaseView', covariant=True)


class RadioGroup(Item[V]):
    """Represents a radio group component within a modal.

    .. versionadded:: 2.7

    Parameters
    ------------
    id: Optional[:class:`int`]
        The ID of the component. This must be unique across the view.
    custom_id: Optional[:class:`str`]
        The custom ID of the component.
    options: List[:class:`discord.RadioGroupOption`]
        A list of options that can be selected in this radio group.
        Can contain between 2 and 10 items.
    required: :class:`bool`
        Whether this component is required to be filled before submitting the modal.
        Defaults to ``True``.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'id',
        'custom_id',
        'options',
        'required',
    )

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        required: bool = True,
        options: List[RadioGroupOption] = MISSING,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        if not isinstance(custom_id, str):
            raise TypeError(f'expected custom_id to be str not {custom_id.__class__.__name__}')

        self._underlying: RadioGroupComponent = RadioGroupComponent._raw_construct(
            id=id,
            custom_id=custom_id,
            required=required,
            options=options or [],
        )
        self.id = id
        self._value: Optional[str] = None

    @property
    def id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of this component."""
        return self._underlying.id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        self._underlying.id = value

    @property
    def value(self) -> Optional[str]:
        """Optional[:class:`str`]: The value have been selected by the user, if any."""
        return self._value

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the component that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be a str')

        self._underlying.custom_id = value
        self._provided_custom_id = True

    @property
    def type(self) -> Literal[ComponentType.radio_group]:
        """:class:`.ComponentType`: The type of this component."""
        return ComponentType.radio_group

    @property
    def options(self) -> List[RadioGroupOption]:
        """List[:class:`discord.RadioGroupOption`]: A list of options that can be selected in this radio group."""
        return self._underlying.options

    @options.setter
    def options(self, value: List[RadioGroupOption]) -> None:
        if not isinstance(value, list) or not all(isinstance(obj, RadioGroupOption) for obj in value):
            raise TypeError('options must be a list of RadioGroupOption')

        self._underlying.options = value

    def add_option(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        default: bool = False,
    ) -> None:
        """Adds an option to the group.

        To append a pre-existing :class:`discord.RadioGroupOption` use the
        :meth:`append_option` method instead.

        Parameters
        -----------
        label: :class:`str`
            The label of the option. This is displayed to users.
            Can only be up to 100 characters.
        value: :class:`str`
            The value of the option. This is not displayed to users.
            If not given, defaults to the label.
            Can only be up to 100 characters.
        description: Optional[:class:`str`]
            An additional description of the option, if any.
            Can only be up to 100 characters.
        default: :class:`bool`
            Whether this option is selected by default.

        Raises
        -------
        ValueError
            The number of options exceeds 10.
        """

        option = RadioGroupOption(
            label=label,
            value=value,
            description=description,
            default=default,
        )

        self.append_option(option)

    def append_option(self, option: RadioGroupOption) -> None:
        """Appends an option to the group.

        Parameters
        -----------
        option: :class:`discord.RadioGroupOption`
            The option to append to the group.

        Raises
        -------
        ValueError
            The number of options exceeds 10.
        """

        if len(self._underlying.options) >= 10:
            raise ValueError('maximum number of options already provided (10)')

        self._underlying.options.append(option)

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the component is required or not."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool) -> None:
        self._underlying.required = bool(value)

    @property
    def width(self) -> int:
        return 5

    def to_component_dict(self) -> RadioGroupComponentPayload:
        return self._underlying.to_dict()

    def _refresh_component(self, component: RadioGroupComponent) -> None:
        self._underlying = component

    def _handle_submit(
        self, interaction: Interaction, data: ModalSubmitRadioGroupInteractionDataPayload, resolved: Dict[ResolveKey, Any]
    ) -> None:
        self._value = data.get('value')

    @classmethod
    def from_component(cls, component: RadioGroupComponent) -> Self:
        self = cls(
            id=component.id,
            custom_id=component.custom_id,
            options=component.options,
            required=component.required,
        )
        return self

    def is_dispatchable(self) -> bool:
        return False
