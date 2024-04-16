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
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Callable,
    Union,
    Dict,
    overload,
    Sequence,
)
from contextvars import ContextVar
import inspect
import os

from .item import Item, ItemCallbackType
from ..enums import ChannelType, ComponentType, SelectDefaultValueType
from ..partial_emoji import PartialEmoji
from ..emoji import Emoji
from ..utils import MISSING, _human_join
from ..components import (
    SelectOption,
    SelectMenu,
    SelectDefaultValue,
)
from ..app_commands.namespace import Namespace
from ..member import Member
from ..object import Object
from ..role import Role
from ..user import User, ClientUser
from ..abc import GuildChannel
from ..threads import Thread

__all__ = (
    'Select',
    'UserSelect',
    'RoleSelect',
    'MentionableSelect',
    'ChannelSelect',
    'select',
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias, TypeGuard

    from .view import View
    from ..types.components import SelectMenu as SelectMenuPayload
    from ..types.interactions import SelectMessageComponentInteractionData
    from ..app_commands import AppCommandChannel, AppCommandThread
    from ..interactions import Interaction

    ValidSelectType: TypeAlias = Literal[
        ComponentType.string_select,
        ComponentType.user_select,
        ComponentType.role_select,
        ComponentType.channel_select,
        ComponentType.mentionable_select,
    ]
    PossibleValue: TypeAlias = Union[
        str, User, Member, Role, AppCommandChannel, AppCommandThread, Union[Role, Member], Union[Role, User]
    ]
    ValidDefaultValues: TypeAlias = Union[
        SelectDefaultValue,
        Object,
        Role,
        Member,
        ClientUser,
        User,
        GuildChannel,
        AppCommandChannel,
        AppCommandThread,
        Thread,
    ]

V = TypeVar('V', bound='View', covariant=True)
BaseSelectT = TypeVar('BaseSelectT', bound='BaseSelect[Any]')
SelectT = TypeVar('SelectT', bound='Select[Any]')
UserSelectT = TypeVar('UserSelectT', bound='UserSelect[Any]')
RoleSelectT = TypeVar('RoleSelectT', bound='RoleSelect[Any]')
ChannelSelectT = TypeVar('ChannelSelectT', bound='ChannelSelect[Any]')
MentionableSelectT = TypeVar('MentionableSelectT', bound='MentionableSelect[Any]')
SelectCallbackDecorator: TypeAlias = Callable[[ItemCallbackType[V, BaseSelectT]], BaseSelectT]
DefaultSelectComponentTypes = Literal[
    ComponentType.user_select,
    ComponentType.role_select,
    ComponentType.channel_select,
    ComponentType.mentionable_select,
]

selected_values: ContextVar[Dict[str, List[PossibleValue]]] = ContextVar('selected_values')


def _is_valid_object_type(
    obj: Any,
    component_type: DefaultSelectComponentTypes,
    type_to_supported_classes: Dict[ValidSelectType, Tuple[Type[ValidDefaultValues], ...]],
) -> TypeGuard[Type[ValidDefaultValues]]:
    return issubclass(obj, type_to_supported_classes[component_type])


def _handle_select_defaults(
    defaults: Sequence[ValidDefaultValues], component_type: DefaultSelectComponentTypes
) -> List[SelectDefaultValue]:
    if not defaults or defaults is MISSING:
        return []

    from ..app_commands import AppCommandChannel, AppCommandThread

    cls_to_type: Dict[Type[ValidDefaultValues], SelectDefaultValueType] = {
        User: SelectDefaultValueType.user,
        Member: SelectDefaultValueType.user,
        ClientUser: SelectDefaultValueType.user,
        Role: SelectDefaultValueType.role,
        GuildChannel: SelectDefaultValueType.channel,
        AppCommandChannel: SelectDefaultValueType.channel,
        AppCommandThread: SelectDefaultValueType.channel,
        Thread: SelectDefaultValueType.channel,
    }
    type_to_supported_classes: Dict[ValidSelectType, Tuple[Type[ValidDefaultValues], ...]] = {
        ComponentType.user_select: (User, ClientUser, Member, Object),
        ComponentType.role_select: (Role, Object),
        ComponentType.channel_select: (GuildChannel, AppCommandChannel, AppCommandThread, Thread, Object),
        ComponentType.mentionable_select: (User, ClientUser, Member, Role, Object),
    }

    values: List[SelectDefaultValue] = []
    for obj in defaults:
        if isinstance(obj, SelectDefaultValue):
            values.append(obj)
            continue

        object_type = obj.__class__ if not isinstance(obj, Object) else obj.type

        if not _is_valid_object_type(object_type, component_type, type_to_supported_classes):
            supported_classes = _human_join([c.__name__ for c in type_to_supported_classes[component_type]])
            raise TypeError(f'Expected an instance of {supported_classes} not {object_type.__name__}')

        if object_type is Object:
            if component_type is ComponentType.mentionable_select:
                raise ValueError(
                    'Object must have a type specified for the chosen select type. Please pass one using the `type`` kwarg.'
                )
            elif component_type is ComponentType.user_select:
                object_type = User
            elif component_type is ComponentType.role_select:
                object_type = Role
            elif component_type is ComponentType.channel_select:
                object_type = GuildChannel

        if issubclass(object_type, GuildChannel):
            object_type = GuildChannel

        values.append(SelectDefaultValue(id=obj.id, type=cls_to_type[object_type]))

    return values


class BaseSelect(Item[V]):
    """The base Select model that all other Select models inherit from.

    This class inherits from :class:`Item` and implements the common attributes.

    The following implement this class:

    - :class:`~discord.ui.Select`
    - :class:`~discord.ui.ChannelSelect`
    - :class:`~discord.ui.RoleSelect`
    - :class:`~discord.ui.MentionableSelect`
    - :class:`~discord.ui.UserSelect`

    .. versionadded:: 2.1

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
    __component_attributes__: Tuple[str, ...] = (
        'custom_id',
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
        options: List[SelectOption] = MISSING,
        channel_types: List[ChannelType] = MISSING,
        default_values: Sequence[SelectDefaultValue] = MISSING,
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
            channel_types=[] if channel_types is MISSING else channel_types,
            options=[] if options is MISSING else options,
            default_values=[] if default_values is MISSING else default_values,
        )

        self.row = row
        self._values: List[PossibleValue] = []

    @property
    def values(self) -> List[PossibleValue]:
        values = selected_values.get({})
        return values.get(self.custom_id, self._values)

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the select menu that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be a str')

        self._underlying.custom_id = value
        self._provided_custom_id = True

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
        """:class:`int`: The maximum number of items that can be chosen for this select menu."""
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
        payload: List[PossibleValue]
        try:
            resolved = Namespace._get_resolved_items(interaction, data['resolved'])
            payload = list(resolved.values())
        except KeyError:
            payload = data.get("values", [])  # type: ignore

        self._values = values[self.custom_id] = payload
        selected_values.set(values)

    def is_dispatchable(self) -> bool:
        return True

    @classmethod
    def from_component(cls, component: SelectMenu) -> BaseSelect[V]:
        type_to_cls: Dict[ComponentType, Type[BaseSelect[Any]]] = {
            ComponentType.string_select: Select,
            ComponentType.user_select: UserSelect,
            ComponentType.role_select: RoleSelect,
            ComponentType.channel_select: ChannelSelect,
            ComponentType.mentionable_select: MentionableSelect,
        }
        constructor = type_to_cls.get(component.type, Select)
        kwrgs = {key: getattr(component, key) for key in constructor.__component_attributes__}
        return constructor(**kwrgs)


class Select(BaseSelect[V]):
    """Represents a UI select menu with a list of custom options. This is represented
    to the user as a dropdown menu.

    .. versionadded:: 2.0

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
        Can only be up to 150 characters.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`discord.SelectOption`]
        A list of options that can be selected in this menu.
        Can only contain up to 25 items.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __component_attributes__ = BaseSelect.__component_attributes__ + ('options',)

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
            options=options,
            row=row,
        )

    @property
    def values(self) -> List[str]:
        """List[:class:`str`]: A list of values that have been selected by the user."""
        return super().values  # type: ignore

    @property
    def type(self) -> Literal[ComponentType.string_select]:
        """:class:`.ComponentType`: The type of this component."""
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
            If not given, defaults to the label.
            Can only be up to 100 characters.
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
    """Represents a UI select menu with a list of predefined options with the current members of the guild.

    If this is sent a private message, it will only allow the user to select the client
    or themselves. Every selected option in a private message will resolve to
    a :class:`discord.User`.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
        Can only be up to 150 characters.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    default_values: Sequence[:class:`~discord.abc.Snowflake`]
        A list of objects representing the users that should be selected by default.
        Number of items must be in range of ``min_values`` and ``max_values``.

        .. versionadded:: 2.4
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __component_attributes__ = BaseSelect.__component_attributes__ + ('default_values',)

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
        default_values: Sequence[ValidDefaultValues] = MISSING,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=_handle_select_defaults(default_values, self.type),
        )

    @property
    def type(self) -> Literal[ComponentType.user_select]:
        """:class:`.ComponentType`: The type of this component."""
        return ComponentType.user_select

    @property
    def values(self) -> List[Union[Member, User]]:
        """List[Union[:class:`discord.Member`, :class:`discord.User`]]: A list of members
        and users that have been selected by the user.

        If this is sent a private message, it will only allow
        the user to select the client or themselves. Every selected option in a private
        message will resolve to a :class:`discord.User`.

        If invoked in a guild, the values will always resolve to :class:`discord.Member`.
        """
        return super().values  # type: ignore

    @property
    def default_values(self) -> List[SelectDefaultValue]:
        """List[:class:`discord.SelectDefaultValue`]: A list of default values for the select menu.

        .. versionadded:: 2.4
        """
        return self._underlying.default_values

    @default_values.setter
    def default_values(self, value: Sequence[ValidDefaultValues]) -> None:
        self._underlying.default_values = _handle_select_defaults(value, self.type)


class RoleSelect(BaseSelect[V]):
    """Represents a UI select menu with a list of predefined options with the current roles of the guild.

    Please note that if you use this in a private message with a user, no roles will be displayed to the user.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
        Can only be up to 150 characters.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    default_values: Sequence[:class:`~discord.abc.Snowflake`]
        A list of objects representing the roles that should be selected by default.
        Number of items must be in range of ``min_values`` and ``max_values``.

        .. versionadded:: 2.4
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __component_attributes__ = BaseSelect.__component_attributes__ + ('default_values',)

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
        default_values: Sequence[ValidDefaultValues] = MISSING,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=_handle_select_defaults(default_values, self.type),
        )

    @property
    def type(self) -> Literal[ComponentType.role_select]:
        """:class:`.ComponentType`: The type of this component."""
        return ComponentType.role_select

    @property
    def values(self) -> List[Role]:
        """List[:class:`discord.Role`]: A list of roles that have been selected by the user."""
        return super().values  # type: ignore

    @property
    def default_values(self) -> List[SelectDefaultValue]:
        """List[:class:`discord.SelectDefaultValue`]: A list of default values for the select menu.

        .. versionadded:: 2.4
        """
        return self._underlying.default_values

    @default_values.setter
    def default_values(self, value: Sequence[ValidDefaultValues]) -> None:
        self._underlying.default_values = _handle_select_defaults(value, self.type)


class MentionableSelect(BaseSelect[V]):
    """Represents a UI select menu with a list of predefined options with the current members and roles in the guild.

    If this is sent in a private message, it will only allow the user to select
    the client or themselves. Every selected option in a private message
    will resolve to a :class:`discord.User`. It will not give the user any roles
    to select.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
        Can only be up to 150 characters.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    default_values: Sequence[:class:`~discord.abc.Snowflake`]
        A list of objects representing the users/roles that should be selected by default.
        if :class:`.Object` is passed, then the type must be specified in the constructor.
        Number of items must be in range of ``min_values`` and ``max_values``.

        .. versionadded:: 2.4
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __component_attributes__ = BaseSelect.__component_attributes__ + ('default_values',)

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        row: Optional[int] = None,
        default_values: Sequence[ValidDefaultValues] = MISSING,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            default_values=_handle_select_defaults(default_values, self.type),
        )

    @property
    def type(self) -> Literal[ComponentType.mentionable_select]:
        """:class:`.ComponentType`: The type of this component."""
        return ComponentType.mentionable_select

    @property
    def values(self) -> List[Union[Member, User, Role]]:
        """List[Union[:class:`discord.Role`, :class:`discord.Member`, :class:`discord.User`]]: A list of roles, members,
        and users that have been selected by the user.

        If this is sent a private message, it will only allow
        the user to select the client or themselves. Every selected option in a private
        message will resolve to a :class:`discord.User`.

        If invoked in a guild, the values will always resolve to :class:`discord.Member`.
        """
        return super().values  # type: ignore

    @property
    def default_values(self) -> List[SelectDefaultValue]:
        """List[:class:`discord.SelectDefaultValue`]: A list of default values for the select menu.

        .. versionadded:: 2.4
        """
        return self._underlying.default_values

    @default_values.setter
    def default_values(self, value: Sequence[ValidDefaultValues]) -> None:
        self._underlying.default_values = _handle_select_defaults(value, self.type)


class ChannelSelect(BaseSelect[V]):
    """Represents a UI select menu with a list of predefined options with the current channels in the guild.

    Please note that if you use this in a private message with a user, no channels will be displayed to the user.

    .. versionadded:: 2.1

    Parameters
    ------------
    custom_id: :class:`str`
        The ID of the select menu that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.
    channel_types: List[:class:`~discord.ChannelType`]
        The types of channels to show in the select menu. Defaults to all channels.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
        Can only be up to 150 characters.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    default_values: Sequence[:class:`~discord.abc.Snowflake`]
        A list of objects representing the channels that should be selected by default.
        Number of items must be in range of ``min_values`` and ``max_values``.

        .. versionadded:: 2.4
    row: Optional[:class:`int`]
        The relative row this select menu belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __component_attributes__ = BaseSelect.__component_attributes__ + (
        'channel_types',
        'default_values',
    )

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
        default_values: Sequence[ValidDefaultValues] = MISSING,
    ) -> None:
        super().__init__(
            self.type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            disabled=disabled,
            row=row,
            channel_types=channel_types,
            default_values=_handle_select_defaults(default_values, self.type),
        )

    @property
    def type(self) -> Literal[ComponentType.channel_select]:
        """:class:`.ComponentType`: The type of this component."""
        return ComponentType.channel_select

    @property
    def channel_types(self) -> List[ChannelType]:
        """List[:class:`~discord.ChannelType`]: A list of channel types that can be selected."""
        return self._underlying.channel_types

    @channel_types.setter
    def channel_types(self, value: List[ChannelType]) -> None:
        if not isinstance(value, list):
            raise TypeError('channel_types must be a list of ChannelType')
        if not all(isinstance(obj, ChannelType) for obj in value):
            raise TypeError('all list items must be a ChannelType')

        self._underlying.channel_types = value

    @property
    def values(self) -> List[Union[AppCommandChannel, AppCommandThread]]:
        """List[Union[:class:`~discord.app_commands.AppCommandChannel`, :class:`~discord.app_commands.AppCommandThread`]]: A list of channels selected by the user."""
        return super().values  # type: ignore

    @property
    def default_values(self) -> List[SelectDefaultValue]:
        """List[:class:`discord.SelectDefaultValue`]: A list of default values for the select menu.

        .. versionadded:: 2.4
        """
        return self._underlying.default_values

    @default_values.setter
    def default_values(self, value: Sequence[ValidDefaultValues]) -> None:
        self._underlying.default_values = _handle_select_defaults(value, self.type)


@overload
def select(
    *,
    cls: Type[SelectT] = Select[Any],
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
    cls: Type[UserSelectT] = UserSelect[Any],
    options: List[SelectOption] = MISSING,
    channel_types: List[ChannelType] = ...,
    placeholder: Optional[str] = ...,
    custom_id: str = ...,
    min_values: int = ...,
    max_values: int = ...,
    disabled: bool = ...,
    default_values: Sequence[ValidDefaultValues] = ...,
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, UserSelectT]:
    ...


@overload
def select(
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
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, RoleSelectT]:
    ...


@overload
def select(
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
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, ChannelSelectT]:
    ...


@overload
def select(
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
    row: Optional[int] = ...,
) -> SelectCallbackDecorator[V, MentionableSelectT]:
    ...


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
    row: Optional[int] = None,
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

        class View(discord.ui.View):

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

        .. versionadded:: 2.4
    """

    def decorator(func: ItemCallbackType[V, BaseSelectT]) -> ItemCallbackType[V, BaseSelectT]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError('select function must be a coroutine function')
        callback_cls = getattr(cls, '__origin__', cls)
        if not issubclass(callback_cls, BaseSelect):
            supported_classes = ', '.join(['ChannelSelect', 'MentionableSelect', 'RoleSelect', 'Select', 'UserSelect'])
            raise TypeError(f'cls must be one of {supported_classes} or a subclass of one of them, not {cls.__name__}.')

        func.__discord_ui_model_type__ = callback_cls
        func.__discord_ui_model_kwargs__ = {
            'placeholder': placeholder,
            'custom_id': custom_id,
            'row': row,
            'min_values': min_values,
            'max_values': max_values,
            'disabled': disabled,
        }
        if issubclass(callback_cls, Select):
            func.__discord_ui_model_kwargs__['options'] = options
        if issubclass(callback_cls, ChannelSelect):
            func.__discord_ui_model_kwargs__['channel_types'] = channel_types
        if not issubclass(callback_cls, Select):
            cls_to_type: Dict[
                Type[BaseSelect],
                Literal[
                    ComponentType.user_select,
                    ComponentType.channel_select,
                    ComponentType.role_select,
                    ComponentType.mentionable_select,
                ],
            ] = {
                UserSelect: ComponentType.user_select,
                RoleSelect: ComponentType.role_select,
                MentionableSelect: ComponentType.mentionable_select,
                ChannelSelect: ComponentType.channel_select,
            }
            func.__discord_ui_model_kwargs__['default_values'] = (
                MISSING if default_values is MISSING else _handle_select_defaults(default_values, cls_to_type[callback_cls])
            )

        return func

    return decorator  # type: ignore
