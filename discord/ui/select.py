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
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Tuple, Type, TypeVar, Union, overload

from typing_extensions import TypeAlias

from ..app_commands.namespace import Namespace
from ..components import SelectMenu, SelectOption
from ..emoji import Emoji
from ..enums import ChannelType, ComponentType
from ..partial_emoji import PartialEmoji
from ..utils import MISSING
from .item import Item, ItemCallbackType

__all__ = (
    'BaseSelect',
    'Select',
    'UserSelect',
    'RoleSelect',
    'MentionableSelect',
    'ChannelSelect',
    'select',
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from discord import Interaction, Member, Role, User

    from ..app_commands import AppCommandChannel, AppCommandThread
    from ..types.components import SelectMenu as SelectMenuPayload
    from ..types.interactions import SelectMessageComponentInteractionData
    from .view import View

    ValidSelectType: TypeAlias = Literal[
        ComponentType.string_select,
        ComponentType.user_select,
        ComponentType.role_select,
        ComponentType.channel_select,
        ComponentType.mentionable_select,
    ]


V = TypeVar('V', bound='View', covariant=True)
BaseSelectT = TypeVar('BaseSelectT', bound='BaseSelect')
SelectT = TypeVar('SelectT', bound='Select')
UserSelectT = TypeVar('UserSelectT', bound='UserSelect')
RoleSelectT = TypeVar('RoleSelectT', bound='RoleSelect')
ChannelSelectT = TypeVar('ChannelSelectT', bound='ChannelSelect')
MentionableSelectT = TypeVar('MentionableSelectT', bound='MentionableSelect')
SelectCallbackDecorator: TypeAlias = Callable[
    [ItemCallbackType[V, BaseSelectT]],
    ItemCallbackType[V, BaseSelectT],
]

selected_values: ContextVar[Dict[str, List[Any]]] = ContextVar('selected_values')


class BaseSelect(Item[V]):
    """The base Select model that all other Select models inherit from.

    This class inherits from :class:`Item` and implements the common attributes.

    The following implement this class:

    - :class:`~discord.ui.Select`
    - :class:`~discord.ui.ChannelSelect`
    - :class:`~discord.ui.RoleSelect`
    - :class:`~discord.ui.MentionableSelect`
    - :class:`~discord.ui.UserSelect`

    .. versionadded:: 2.2

    Attributes
    ------------
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __slots__ = ('_provided_custom_id', '_underlying', 'row', '_values')

    __item_repr_attributes__: Tuple[str, ...] = (
        'placeholder',
        'min_values',
        'max_values',
        'disabled',
    )

    def __init__(
        self,
        type: ValidSelectType,
        *,
        custom_id: str = MISSING,
        row: Optional[int] = None,
        placeholder: Optional[str] = None,
        min_values: Optional[int] = None,
        max_values: Optional[int] = None,
        disabled: bool = False,
        **extras: Any,
    ) -> None:
        super().__init__()
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        if not isinstance(custom_id, str):
            raise TypeError(f'expected custom_id to be str not {custom_id.__class__.__name__}')

        self._underlying = SelectMenu._raw_construct(
            type=type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            **extras,
        )

        self.row = row
        self._values: List[Any] = []

    @property
    def values(self) -> List[Any]:
        """The values the user has selected. This will be an empty list if the user has not selected anything.

        If you want to determine what objects list will contain,
        see the documentation for the subclass you're using.

        Type
        -----
        List[Any]
        """
        values = selected_values.get({})
        return values.get(self.custom_id, self._values)

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the select menu that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be None or str')

        self._underlying.custom_id = value
        self._provided_custom_id = value is not None

    @property
    def placeholder(self) -> Optional[str]:
        """Optional[:class:`str`]: The placeholder text that is shown if nothing is selected, if any."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        if value is not None and not isinstance(value, str):
            raise TypeError('placeholder must be None or str')

        self._underlying.placeholder = value

    @property
    def min_values(self) -> int:
        """:class:`int`: The minimum number of items that must be chosen for this select menu."""
        return self._underlying.min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        self._underlying.min_values = int(value)

    @property
    def max_values(self) -> int:
        """:class:`int`: The maximum number of items that must be chosen for this select menu."""
        return self._underlying.max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        self._underlying.max_values = int(value)

    @property
    def disabled(self) -> bool:
        """:class:`bool`: Whether the select is disabled or not."""
        return self._underlying.disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._underlying.disabled = bool(value)

    @property
    def width(self) -> int:
        return 5

    def to_component_dict(self) -> SelectMenuPayload:
        return self._underlying.to_dict()

    def _refresh_component(self, component: SelectMenu) -> None:
        self._underlying = component

    def _refresh_state(self, interaction: Interaction, data: SelectMessageComponentInteractionData) -> None:
        values = selected_values.get({})
        payload = []
        if "resolved" in data:
            resolved = Namespace._get_resolved_items(interaction, data["resolved"])
            payload = list(resolved.values())
        else:
            payload = data.get("values", [])

        self._values = values[self.custom_id] = payload
        selected_values.set(values)

    def is_dispatchable(self) -> bool:
        return True

    @classmethod
    def from_component(cls, component: SelectMenu) -> Self:
        return cls(
            **{k: getattr(component, k) for k in cls.__item_repr_attributes__},
            row=None,
        )


class Select(BaseSelect[V]):
    """Represents a UI "string" select menu with a list of custom options. This is represented
    to the user as a dropdown menu.

    .. versionadded:: 2.0

    .. versionchanged:: 2.1
        This class now inherits from :class:`BaseSelect` instead of :class:`Item`.

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`discord.SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__ = BaseSelect.__item_repr_attributes__ + ('options',)

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        options: List[SelectOption] = MISSING,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            options=[] if options is MISSING else options,
            row=row,
        )

    @property
    def values(self) -> List[str]:
        """List[:class:`str`]: A list of values that have been selected by the user."""
        return super().values

    @property
    def type(self) -> Literal[ComponentType.string_select]:
        return ComponentType.string_select

    @property
    def options(self) -> List[SelectOption]:
        """List[:class:`discord.SelectOption`]: A list of options that can be selected in this menu."""
        return self._underlying.options

    @options.setter
    def options(self, value: List[SelectOption]) -> None:
        if not isinstance(value, list):
            raise TypeError('options must be a list of SelectOption')
        if not all(isinstance(obj, SelectOption) for obj in value):
            raise TypeError('all list items must subclass SelectOption')

        self._underlying.options = value

    def add_option(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        """Adds an option to the select menu.

        To append a pre-existing :class:`discord.SelectOption` use the
        :meth:`append_option` method instead.

        Parameters
        -----------
        label: :class:`str`
            The label of the option. This is displayed to users.
            Can only be up to 100 characters.
        value: :class:`str`
            The value of the option. This is not displayed to users.
            If not given, defaults to the label. Can only be up to 100 characters.
        description: Optional[:class:`str`]
            An additional description of the option, if any.
            Can only be up to 100 characters.
        emoji: Optional[Union[:class:`str`, :class:`.Emoji`, :class:`.PartialEmoji`]]
            The emoji of the option, if available. This can either be a string representing
            the custom or unicode emoji or an instance of :class:`.PartialEmoji` or :class:`.Emoji`.
        default: :class:`bool`
            Whether this option is selected by default.

        Raises
        -------
        ValueError
            The number of options exceeds 25.
        """

        option = SelectOption(
            label=label,
            value=value,
            description=description,
            emoji=emoji,
            default=default,
        )

        self.append_option(option)

    def append_option(self, option: SelectOption) -> None:
        """Appends an option to the select menu.

        Parameters
        -----------
        option: :class:`discord.SelectOption`
            The option to append to the select menu.

        Raises
        -------
        ValueError
            The number of options exceeds 25.
        """

        if len(self._underlying.options) > 25:
            raise ValueError('maximum number of options already provided')

        self._underlying.options.append(option)


class UserSelect(BaseSelect[V]):
    """Represents a UI "user" select menu with a list of predefined options representing members of the guild.

    If this is presented to the user in a private message, it will only allow the user to select the client,
    or themselves. Every selected option in a private message will resolve to
    a :class:`discord.User` regardless of intents.
    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )

    @property
    def type(self) -> Literal[ComponentType.user_select]:
        return ComponentType.user_select

    @property
    def values(self) -> List[Union[Member, User]]:
        """A list of members and users that have been selected by the user.

        If this is presented to the user in a private message, it will only allow
        the user to select the client or themselves. Every selected option in a private
        message will resolve to a :class:`discord.User` regardless of intents.

        If invoked in a guild, the values will always resolve to :class:`discord.Member`
        regardless of the :attr:`discord.Intents.members` intent.

        Type
        --------
        List[Union[:class:`discord.Member`, :class:`discord.User`]]
        """
        return super().values


class RoleSelect(BaseSelect[V]):
    """Represents a UI select menu in which the user can select roles
    by searching and clicking on them.

    Please note that this type of select does not work in direct messages.
    If presented to a user in a direct message, the select menu will not give
    the user any roles to select.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )

    @property
    def type(self) -> Literal[ComponentType.role_select]:
        return ComponentType.role_select

    @property
    def values(self) -> List[Role]:
        """List[:class:`discord.Role`]: A list of roles that have been selected by the user."""
        return super().values


class MentionableSelect(BaseSelect[V]):
    """Represents a UI "mentionable" select menu with a list of predefined options representing members and roles in the guild.

    If this is presented to the user in a private message, it will only allow
    the user to select the client, or themselves. Every selected option in a private
    message will resolve to a :class:`discord.User`. It will not give the user any roles
    to select.

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that get9 received during an interaction.
        If not given then one is generated for you.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
        )

    @property
    def type(self) -> Literal[ComponentType.mentionable_select]:
        return ComponentType.mentionable_select

    @property
    def values(self) -> List[Union[Member, User, Role]]:
        """A list of roles, members, and users that have been selected by the user.

        If this is presented to the user in a private message, it will only allow
        the user to select the client or themselves. Every selected option in a private
        message will resolve to a :class:`discord.User` regardless of intents.

        If invoked in a guild, the values will always resolve to :class:`discord.Member`
        regardless of the :attr:`discord.Intents.members` intent.

        Type
        ----
        List[Union[:class:`discord.Role`, :class:`discord.Member`, :class:`discord.User`]]
        """
        return super().values


class ChannelSelect(BaseSelect[V]):
    """Represents a UI "channel" select menu with a list of predefined options representing channels in the guild.
    It is possible to filter the channels that are shown per type by passing the ``channel_types`` parameter.

    Please note that if you use this in a direct message with a user, no channels will be displayed to the user
    and they will not be able to invoke the select menu.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
    channel_types: List[:class:`~discord.ChannelType`]
        The types of channels to show in the select menu. If not given then all channel types are shown.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__ = BaseSelect.__item_repr_attributes__ + ('channel_types',)

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        channel_types: List[ChannelType] = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            channel_types=[] if channel_types is MISSING else channel_types,
        )

    @property
    def type(self) -> Literal[ComponentType.channel_select]:
        return ComponentType.channel_select

    @property
    def channel_types(self) -> List[ChannelType]:
        """List[:class:`~discord.ChannelType`]: A list of channel types that can be selected."""
        return self._underlying.channel_types

    @property
    def values(self) -> List[Union[AppCommandChannel, AppCommandThread]]:
        """List[Union[:class:`~discord.app_commands.AppCommandChannel`, :class:`~discord.app_commands.AppCommandThread`]]: A list of channels selected by the user."""
        return super().values


@overload
def select(
    *,
    cls: Type[SelectT] = Select,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = ...,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, SelectT]:
    ...


@overload
def select(
    *,
    cls: Type[UserSelectT] = UserSelect,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = ...,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, UserSelectT]:
    ...


@overload
def select(
    *,
    cls: Type[RoleSelectT] = RoleSelect,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = ...,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, RoleSelectT]:
    ...


@overload
def select(
    *,
    cls: Type[ChannelSelectT] = ChannelSelect,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = ...,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, ChannelSelectT]:
    ...


@overload
def select(
    *,
    cls: Type[MentionableSelectT] = MentionableSelect,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = MISSING,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, MentionableSelectT]:
    ...


def select(
    *,
    cls: Type[BaseSelectT] = Select,
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = MISSING,
    placeholder: Optional[str] = None,
    custom_id: str = MISSING,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
    row: Optional[int] = None,
) -> SelectCallbackDecorator[V, BaseSelectT]:
    """A decorator that attaches a select menu to a component.

    The function being decorated should have three parameters, ``self`` representing
    the :class:`discord.ui.View`, the :class:`discord.Interaction` you receive and
    the :class:`discord.ui.BaseSelect` being used.

    In order to get the selected items that the user has chosen within the callback
    use :meth:`~discord.ui.BaseSelect.values`.

    +----------------------------------------+--------------------------------------------------------------------------------------------------------------- +
    | Select Type                            | Resolved Value                                                                                                 |
    +========================================+=============================================================================================================== +
    | :class:`discord.ui.Select`             | List[:class:`str`]                                                                                             |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------- +
    | :class:`discord.ui.UserSelect`         | List[Union[:class:`discord.Member`, :class:`discord.User`]]                                                    |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------- +
    | :class:`discord.ui.RoleSelect`         | List[:class:`discord.Role`]                                                                                    |
    +----------------------------------------+--------------------------------------------------------------------------------------------------------------- +
    | :class:`discord.ui.MentionableSelect`  | List[Union[:class:`discord.Role`, :class:`discord.Member`, :class:`discord.User`]]                             |
    +----------------------------------------+----------------------------------------------------------------------------------------------------------------+
    | :class:`discord.ui.ChannelSelect`      | List[Union[:class:`~discord.app_commands.AppCommandChannel`, :class:`~discord.app_commands.AppCommandThread`]] |
    +----------------------------------------+----------------------------------------------------------------------------------------------------------------+

    Parameters
    ------------
    cls: Type[:class:`discord.ui.BaseSelect`]
        The class to use for the select menu. Defaults to :class:`discord.ui.Select`. You can use other
        select types to display different select menus to the user. See the table above for the different
        values you can get from each select type. Subclasses work as well, however the callback in the subclass will
        get overridden.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        It is recommended not to set this parameter to prevent conflicts.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`discord.SelectOption`]
        A list of options that can be selected in this menu. This can not be used with
        :class:`ChannelSelect` instances.
    channel_types: List[:class:`~discord.ChannelType`]
        The types of channels you want to limit the selection to. This can only be used
        with :class:`ChannelSelect` instances.
    disabled: :class:`bool`
        Whether the select is disabled or not. Defaults to ``False``.
    """

    def decorator(func: ItemCallbackType[V, BaseSelectT]) -> ItemCallbackType[V, BaseSelectT]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError('select function must be a coroutine function')
        if not issubclass(cls, BaseSelect):
            raise TypeError(f'cls must be a subclass of BaseSelect, {cls.__name__} can not be used.')

        payload = {
            'placeholder': placeholder,
            'custom_id': custom_id,
            'row': row,
            'min_values': min_values,
            'max_values': max_values,
            'disabled': disabled,
        }
        if issubclass(cls, ChannelSelect):
            payload['channel_types'] = channel_types
        if issubclass(cls, Select):
            payload['options'] = options

        func.__discord_ui_model_type__ = cls
        func.__discord_ui_model_kwargs__ = payload

        return func

    return decorator
