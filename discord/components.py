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
    ClassVar,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Union,
)

from .asset import AssetMixin
from .enums import (
    try_enum,
    ComponentType,
    ButtonStyle,
    TextStyle,
    ChannelType,
    SelectDefaultValueType,
    SeparatorSpacing,
    MediaItemLoadingState,
)
from .flags import AttachmentFlags
from .colour import Colour
from .file import File
from .utils import get_slots, MISSING, _get_as_snowflake
from .partial_emoji import PartialEmoji, _EmojiTag

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.components import (
        Component as ComponentPayload,
        ButtonComponent as ButtonComponentPayload,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        ActionRow as ActionRowPayload,
        TextInput as TextInputPayload,
        SelectDefaultValues as SelectDefaultValuesPayload,
        SectionComponent as SectionComponentPayload,
        TextComponent as TextComponentPayload,
        MediaGalleryComponent as MediaGalleryComponentPayload,
        FileComponent as FileComponentPayload,
        SeparatorComponent as SeparatorComponentPayload,
        MediaGalleryItem as MediaGalleryItemPayload,
        ThumbnailComponent as ThumbnailComponentPayload,
        ContainerComponent as ContainerComponentPayload,
        UnfurledMediaItem as UnfurledMediaItemPayload,
        LabelComponent as LabelComponentPayload,
    )

    from .emoji import Emoji
    from .abc import Snowflake
    from .state import ConnectionState

    ActionRowChildComponentType = Union['Button', 'SelectMenu', 'TextInput']
    SectionComponentType = Union['TextDisplay']
    MessageComponentType = Union[
        ActionRowChildComponentType,
        SectionComponentType,
        'ActionRow',
        'SectionComponent',
        'ThumbnailComponent',
        'MediaGalleryComponent',
        'FileComponent',
        'SectionComponent',
        'Component',
    ]


__all__ = (
    'Component',
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'TextInput',
    'SelectDefaultValue',
    'SectionComponent',
    'ThumbnailComponent',
    'UnfurledMediaItem',
    'MediaGalleryItem',
    'MediaGalleryComponent',
    'FileComponent',
    'SectionComponent',
    'Container',
    'TextDisplay',
    'SeparatorComponent',
    'LabelComponent',
)


class Component:
    """Represents a Discord Bot UI Kit Component.

    The components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`TextInput`
    - :class:`SectionComponent`
    - :class:`TextDisplay`
    - :class:`ThumbnailComponent`
    - :class:`MediaGalleryComponent`
    - :class:`FileComponent`
    - :class:`SeparatorComponent`
    - :class:`Container`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]]

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__repr_info__)
        return f'<{self.__class__.__name__} {attrs}>'

    @property
    def type(self) -> ComponentType:
        """:class:`ComponentType`: The type of component."""
        raise NotImplementedError

    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> ComponentPayload:
        raise NotImplementedError


class ActionRow(Component):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ------------
    children: List[Union[:class:`Button`, :class:`SelectMenu`, :class:`TextInput`]]
        The children components that this holds, if any.
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 2.6
    """

    __slots__: Tuple[str, ...] = ('children', 'id')

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ActionRowPayload, /) -> None:
        self.id: Optional[int] = data.get('id')
        self.children: List[ActionRowChildComponentType] = []

        for component_data in data.get('components', []):
            component = _component_factory(component_data)

            if component is not None:
                self.children.append(component)  # type: ignore # should be the correct type here

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.action_row

    def to_dict(self) -> ActionRowPayload:
        payload: ActionRowPayload = {
            'type': self.type.value,
            'components': [child.to_dict() for child in self.children],
        }
        if self.id is not None:
            payload['id'] = self.id
        return payload


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a button is :class:`discord.ui.Button`
        not this one.

    .. versionadded:: 2.0

    Attributes
    -----------
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    sku_id: Optional[:class:`int`]
        The SKU ID this button sends you to, if available.

        .. versionadded:: 2.4
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 2.6
    """

    __slots__: Tuple[str, ...] = (
        'style',
        'custom_id',
        'url',
        'disabled',
        'label',
        'emoji',
        'sku_id',
        'id',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonComponentPayload, /) -> None:
        self.id: Optional[int] = data.get('id')
        self.style: ButtonStyle = try_enum(ButtonStyle, data['style'])
        self.custom_id: Optional[str] = data.get('custom_id')
        self.url: Optional[str] = data.get('url')
        self.disabled: bool = data.get('disabled', False)
        self.label: Optional[str] = data.get('label')
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data['emoji'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.emoji = None

        try:
            self.sku_id: Optional[int] = int(data['sku_id'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.sku_id = None

    @property
    def type(self) -> Literal[ComponentType.button]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.button

    def to_dict(self) -> ButtonComponentPayload:
        payload: ButtonComponentPayload = {
            'type': 2,
            'style': self.style.value,
            'disabled': self.disabled,
        }

        if self.id is not None:
            payload['id'] = self.id

        if self.sku_id:
            payload['sku_id'] = str(self.sku_id)

        if self.label:
            payload['label'] = self.label

        if self.custom_id:
            payload['custom_id'] = self.custom_id

        if self.url:
            payload['url'] = self.url

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()

        return payload


class SelectMenu(Component):
    """Represents a select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. note::

        The user constructible and usable type to create a select menu is
        :class:`discord.ui.Select` not this one.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`ComponentType`
        The type of component.
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    channel_types: List[:class:`.ChannelType`]
        A list of channel types that are allowed to be chosen in this select menu.
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 2.6
    required: :class:`bool`
        Whether the select is required. Only applicable within modals.

        .. versionadded:: 2.6
    """

    __slots__: Tuple[str, ...] = (
        'type',
        'custom_id',
        'placeholder',
        'min_values',
        'max_values',
        'options',
        'disabled',
        'channel_types',
        'default_values',
        'required',
        'id',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuPayload, /) -> None:
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.min_values: int = data.get('min_values', 1)
        self.max_values: int = data.get('max_values', 1)
        self.required: bool = data.get('required', False)
        self.options: List[SelectOption] = [SelectOption.from_dict(option) for option in data.get('options', [])]
        self.disabled: bool = data.get('disabled', False)
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, t) for t in data.get('channel_types', [])]
        self.default_values: List[SelectDefaultValue] = [
            SelectDefaultValue.from_dict(d) for d in data.get('default_values', [])
        ]
        self.id: Optional[int] = data.get('id')

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            'type': self.type.value,  # type: ignore # we know this is a select menu.
            'custom_id': self.custom_id,
            'min_values': self.min_values,
            'max_values': self.max_values,
            'disabled': self.disabled,
            'required': self.required,
        }
        if self.id is not None:
            payload['id'] = self.id
        if self.placeholder:
            payload['placeholder'] = self.placeholder
        if self.options:
            payload['options'] = [op.to_dict() for op in self.options]
        if self.channel_types:
            payload['channel_types'] = [t.value for t in self.channel_types]
        if self.default_values:
            payload['default_values'] = [v.to_dict() for v in self.default_values]

        return payload


class SelectOption:
    """Represents a select menu's option.

    These can be created by users.

    .. versionadded:: 2.0

    Parameters
    -----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the label.
        Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.

    Attributes
    -----------
    label: :class:`str`
        The label of the option. This is displayed to users.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        'label',
        'value',
        'description',
        '_emoji',
        'default',
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description

        self.emoji = emoji
        self.default: bool = default

    def __repr__(self) -> str:
        return (
            f'<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} '
            f'emoji={self.emoji!r} default={self.default!r}>'
        )

    def __str__(self) -> str:
        if self.emoji:
            base = f'{self.emoji} {self.label}'
        else:
            base = self.label

        if self.description:
            return f'{base}\n{self.description}'
        return base

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`.PartialEmoji`]: The emoji of the option, if available."""
        return self._emoji

    @emoji.setter
    def emoji(self, value: Optional[Union[str, Emoji, PartialEmoji]]) -> None:
        if value is not None:
            if isinstance(value, str):
                self._emoji = PartialEmoji.from_str(value)
            elif isinstance(value, _EmojiTag):
                self._emoji = value._to_partial()
            else:
                raise TypeError(f'expected str, Emoji, or PartialEmoji, received {value.__class__.__name__} instead')
        else:
            self._emoji = None

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data['emoji'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            emoji = None

        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),
            emoji=emoji,
            default=data.get('default', False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            'label': self.label,
            'value': self.value,
            'default': self.default,
        }

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()

        if self.description:
            payload['description'] = self.description

        return payload

    def copy(self) -> SelectOption:
        return self.__class__.from_dict(self.to_dict())


class TextInput(Component):
    """Represents a text input from the Discord Bot UI Kit.

    .. note::
        The user constructible and usable type to create a text input is
        :class:`discord.ui.TextInput` not this one.

    .. versionadded:: 2.0

    Attributes
    ------------
    custom_id: Optional[:class:`str`]
        The ID of the text input that gets received during an interaction.
    label: Optional[:class:`str`]
        The label to display above the text input.
    style: :class:`TextStyle`
        The style of the text input.
    placeholder: Optional[:class:`str`]
        The placeholder text to display when the text input is empty.
    value: Optional[:class:`str`]
        The default value of the text input.
    required: :class:`bool`
        Whether the text input is required.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 2.6
    """

    __slots__: Tuple[str, ...] = (
        'style',
        'label',
        'custom_id',
        'placeholder',
        'value',
        'required',
        'min_length',
        'max_length',
        'id',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputPayload, /) -> None:
        self.style: TextStyle = try_enum(TextStyle, data['style'])
        self.label: Optional[str] = data.get('label')
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.value: Optional[str] = data.get('value')
        self.required: bool = data.get('required', True)
        self.min_length: Optional[int] = data.get('min_length')
        self.max_length: Optional[int] = data.get('max_length')
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.text_input]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.text_input

    def to_dict(self) -> TextInputPayload:
        payload: TextInputPayload = {
            'type': self.type.value,
            'style': self.style.value,
            'label': self.label,
            'custom_id': self.custom_id,
            'required': self.required,
        }

        if self.id is not None:
            payload['id'] = self.id

        if self.placeholder:
            payload['placeholder'] = self.placeholder

        if self.value:
            payload['value'] = self.value

        if self.min_length:
            payload['min_length'] = self.min_length

        if self.max_length:
            payload['max_length'] = self.max_length

        return payload

    @property
    def default(self) -> Optional[str]:
        """Optional[:class:`str`]: The default value of the text input.

        This is an alias to :attr:`value`.
        """
        return self.value


class SelectDefaultValue:
    """Represents a select menu's default value.

    These can be created by users.

    .. versionadded:: 2.4

    Parameters
    -----------
    id: :class:`int`
        The id of a role, user, or channel.
    type: :class:`SelectDefaultValueType`
        The type of value that ``id`` represents.
    """

    def __init__(
        self,
        *,
        id: int,
        type: SelectDefaultValueType,
    ) -> None:
        self.id: int = id
        self._type: SelectDefaultValueType = type

    @property
    def type(self) -> SelectDefaultValueType:
        """:class:`SelectDefaultValueType`: The type of value that ``id`` represents."""
        return self._type

    @type.setter
    def type(self, value: SelectDefaultValueType) -> None:
        if not isinstance(value, SelectDefaultValueType):
            raise TypeError(f'expected SelectDefaultValueType, received {value.__class__.__name__} instead')

        self._type = value

    def __repr__(self) -> str:
        return f'<SelectDefaultValue id={self.id!r} type={self.type!r}>'

    @classmethod
    def from_dict(cls, data: SelectDefaultValuesPayload) -> SelectDefaultValue:
        return cls(
            id=data['id'],
            type=try_enum(SelectDefaultValueType, data['type']),
        )

    def to_dict(self) -> SelectDefaultValuesPayload:
        return {
            'id': self.id,
            'type': self._type.value,
        }

    @classmethod
    def from_channel(cls, channel: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.channel`.

        Parameters
        -----------
        channel: :class:`~discord.abc.Snowflake`
            The channel to create the default value for.

        Returns
        --------
        :class:`SelectDefaultValue`
            The default value created with the channel.
        """
        return cls(
            id=channel.id,
            type=SelectDefaultValueType.channel,
        )

    @classmethod
    def from_role(cls, role: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.role`.

        Parameters
        -----------
        role: :class:`~discord.abc.Snowflake`
            The role to create the default value for.

        Returns
        --------
        :class:`SelectDefaultValue`
            The default value created with the role.
        """
        return cls(
            id=role.id,
            type=SelectDefaultValueType.role,
        )

    @classmethod
    def from_user(cls, user: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.user`.

        Parameters
        -----------
        user: :class:`~discord.abc.Snowflake`
            The user to create the default value for.

        Returns
        --------
        :class:`SelectDefaultValue`
            The default value created with the user.
        """
        return cls(
            id=user.id,
            type=SelectDefaultValueType.user,
        )


class SectionComponent(Component):
    """Represents a section from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a section is :class:`discord.ui.Section`
        not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    children: List[:class:`TextDisplay`]
        The components on this section.
    accessory: :class:`Component`
        The section accessory.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        'children',
        'accessory',
        'id',
    )

    __repr_info__ = __slots__

    def __init__(self, data: SectionComponentPayload, state: Optional[ConnectionState]) -> None:
        self.children: List[SectionComponentType] = []
        self.accessory: Component = _component_factory(data['accessory'], state)  # type: ignore
        self.id: Optional[int] = data.get('id')

        for component_data in data['components']:
            component = _component_factory(component_data, state)
            if component is not None:
                self.children.append(component)  # type: ignore # should be the correct type here

    @property
    def type(self) -> Literal[ComponentType.section]:
        return ComponentType.section

    def to_dict(self) -> SectionComponentPayload:
        payload: SectionComponentPayload = {
            'type': self.type.value,
            'components': [c.to_dict() for c in self.children],
            'accessory': self.accessory.to_dict(),
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class ThumbnailComponent(Component):
    """Represents a Thumbnail from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a thumbnail is :class:`discord.ui.Thumbnail`
        not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The media for this thumbnail.
    description: Optional[:class:`str`]
        The description shown within this thumbnail.
    spoiler: :class:`bool`
        Whether this thumbnail is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        'media',
        'spoiler',
        'description',
        'id',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: ThumbnailComponentPayload,
        state: Optional[ConnectionState],
    ) -> None:
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data['media'], state)
        self.description: Optional[str] = data.get('description')
        self.spoiler: bool = data.get('spoiler', False)
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        return ComponentType.thumbnail

    def to_dict(self) -> ThumbnailComponentPayload:
        payload = {
            'media': self.media.to_dict(),
            'description': self.description,
            'spoiler': self.spoiler,
            'type': self.type.value,
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload  # type: ignore


class TextDisplay(Component):
    """Represents a text display from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type to create a text display is
        :class:`discord.ui.TextDisplay` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    content: :class:`str`
        The content that this display shows.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = ('content', 'id')

    __repr_info__ = __slots__

    def __init__(self, data: TextComponentPayload) -> None:
        self.content: str = data['content']
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return ComponentType.text_display

    def to_dict(self) -> TextComponentPayload:
        payload: TextComponentPayload = {
            'type': self.type.value,
            'content': self.content,
        }
        if self.id is not None:
            payload['id'] = self.id
        return payload


class UnfurledMediaItem(AssetMixin):
    """Represents an unfurled media item.

    .. versionadded:: 2.6

    Parameters
    ----------
    url: :class:`str`
        The URL of this media item. This can be an arbitrary url or a reference to a local
        file uploaded as an attachment within the message, which can be accessed with the
        ``attachment://<filename>`` format.

    Attributes
    ----------
    url: :class:`str`
        The URL of this media item.
    proxy_url: Optional[:class:`str`]
        The proxy URL. This is a cached version of the :attr:`.url` in the
        case of images. When the message is deleted, this URL might be valid for a few minutes
        or not valid at all.
    height: Optional[:class:`int`]
        The media item's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The media item's width, in pixels. Only applicable to images and videos.
    content_type: Optional[:class:`str`]
        The media item's `media type <https://en.wikipedia.org/wiki/Media_type>`_
    placeholder: Optional[:class:`str`]
        The media item's placeholder.
    loading_state: Optional[:class:`MediaItemLoadingState`]
        The loading state of this media item.
    attachment_id: Optional[:class:`int`]
        The attachment id this media item points to, only available if the url points to a local file
        uploaded within the component message.
    """

    __slots__ = (
        'url',
        'proxy_url',
        'height',
        'width',
        'content_type',
        '_flags',
        'placeholder',
        'loading_state',
        'attachment_id',
        '_state',
    )

    def __init__(self, url: str) -> None:
        self.url: str = url

        self.proxy_url: Optional[str] = None
        self.height: Optional[int] = None
        self.width: Optional[int] = None
        self.content_type: Optional[str] = None
        self._flags: int = 0
        self.placeholder: Optional[str] = None
        self.loading_state: Optional[MediaItemLoadingState] = None
        self.attachment_id: Optional[int] = None
        self._state: Optional[ConnectionState] = None

    @property
    def flags(self) -> AttachmentFlags:
        """:class:`AttachmentFlags`: This media item's flags."""
        return AttachmentFlags._from_value(self._flags)

    @classmethod
    def _from_data(cls, data: UnfurledMediaItemPayload, state: Optional[ConnectionState]):
        self = cls(data['url'])
        self._update(data, state)
        return self

    def _update(self, data: UnfurledMediaItemPayload, state: Optional[ConnectionState]) -> None:
        self.proxy_url = data.get('proxy_url')
        self.height = data.get('height')
        self.width = data.get('width')
        self.content_type = data.get('content_type')
        self._flags = data.get('flags', 0)
        self.placeholder = data.get('placeholder')

        loading_state = data.get('loading_state')
        if loading_state is not None:
            self.loading_state = try_enum(MediaItemLoadingState, loading_state)
        self.attachment_id = _get_as_snowflake(data, 'attachment_id')
        self._state = state

    def __repr__(self) -> str:
        return f'<UnfurledMediaItem url={self.url}>'

    def to_dict(self):
        return {
            'url': self.url,
        }


class MediaGalleryItem:
    """Represents a :class:`MediaGalleryComponent` media item.

    .. versionadded:: 2.6

    Parameters
    ----------
    media: Union[:class:`str`, :class:`discord.File`, :class:`UnfurledMediaItem`]
        The media item data. This can be a string representing a local
        file uploaded as an attachment in the message, which can be accessed
        using the ``attachment://<filename>`` format, or an arbitrary url.
    description: Optional[:class:`str`]
        The description to show within this item. Up to 256 characters. Defaults
        to ``None``.
    spoiler: :class:`bool`
        Whether this item should be flagged as a spoiler.
    """

    __slots__ = (
        '_media',
        'description',
        'spoiler',
        '_state',
    )

    def __init__(
        self,
        media: Union[str, File, UnfurledMediaItem],
        *,
        description: Optional[str] = MISSING,
        spoiler: bool = MISSING,
    ) -> None:
        self.media = media

        if isinstance(media, File):
            if description is MISSING:
                description = media.description
            if spoiler is MISSING:
                spoiler = media.spoiler

        self.description: Optional[str] = None if description is MISSING else description
        self.spoiler: bool = bool(spoiler)
        self._state: Optional[ConnectionState] = None

    def __repr__(self) -> str:
        return f'<MediaGalleryItem media={self.media!r}>'

    @property
    def media(self) -> UnfurledMediaItem:
        """:class:`UnfurledMediaItem`: This item's media data."""
        return self._media

    @media.setter
    def media(self, value: Union[str, File, UnfurledMediaItem]) -> None:
        if isinstance(value, str):
            self._media = UnfurledMediaItem(value)
        elif isinstance(value, UnfurledMediaItem):
            self._media = value
        elif isinstance(value, File):
            self._media = UnfurledMediaItem(value.uri)
        else:
            raise TypeError(f'Expected a str or UnfurledMediaItem, not {value.__class__.__name__}')

    @classmethod
    def _from_data(cls, data: MediaGalleryItemPayload, state: Optional[ConnectionState]) -> MediaGalleryItem:
        media = data['media']
        self = cls(
            media=UnfurledMediaItem._from_data(media, state),
            description=data.get('description'),
            spoiler=data.get('spoiler', False),
        )
        self._state = state
        return self

    @classmethod
    def _from_gallery(
        cls,
        items: List[MediaGalleryItemPayload],
        state: Optional[ConnectionState],
    ) -> List[MediaGalleryItem]:
        return [cls._from_data(item, state) for item in items]

    def to_dict(self) -> MediaGalleryItemPayload:
        payload: MediaGalleryItemPayload = {
            'media': self.media.to_dict(),  # type: ignore
            'spoiler': self.spoiler,
        }

        if self.description:
            payload['description'] = self.description

        return payload


class MediaGalleryComponent(Component):
    """Represents a Media Gallery component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for creating a media gallery is
        :class:`discord.ui.MediaGallery` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    items: List[:class:`MediaGalleryItem`]
        The items this gallery has.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = ('items', 'id')

    __repr_info__ = __slots__

    def __init__(self, data: MediaGalleryComponentPayload, state: Optional[ConnectionState]) -> None:
        self.items: List[MediaGalleryItem] = MediaGalleryItem._from_gallery(data['items'], state)
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.media_gallery]:
        return ComponentType.media_gallery

    def to_dict(self) -> MediaGalleryComponentPayload:
        payload: MediaGalleryComponentPayload = {
            'type': self.type.value,
            'items': [item.to_dict() for item in self.items],
        }
        if self.id is not None:
            payload['id'] = self.id
        return payload


class FileComponent(Component):
    """Represents a File component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for create a file component is
        :class:`discord.ui.File` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The unfurled attachment contents of the file.
    spoiler: :class:`bool`
        Whether this file is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    name: Optional[:class:`str`]
        The displayed file name, only available when received from the API.
    size: Optional[:class:`int`]
        The file size in MiB, only available when received from the API.
    """

    __slots__ = (
        'media',
        'spoiler',
        'id',
        'name',
        'size',
    )

    __repr_info__ = __slots__

    def __init__(self, data: FileComponentPayload, state: Optional[ConnectionState]) -> None:
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data['file'], state)
        self.spoiler: bool = data.get('spoiler', False)
        self.id: Optional[int] = data.get('id')
        self.name: Optional[str] = data.get('name')
        self.size: Optional[int] = data.get('size')

    @property
    def type(self) -> Literal[ComponentType.file]:
        return ComponentType.file

    def to_dict(self) -> FileComponentPayload:
        payload: FileComponentPayload = {
            'type': self.type.value,
            'file': self.media.to_dict(),  # type: ignore
            'spoiler': self.spoiler,
        }
        if self.id is not None:
            payload['id'] = self.id
        return payload


class SeparatorComponent(Component):
    """Represents a Separator from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for creating a separator is
        :class:`discord.ui.Separator` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    spacing: :class:`SeparatorSpacing`
        The spacing size of the separator.
    visible: :class:`bool`
        Whether this separator is visible and shows a divider.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        'spacing',
        'visible',
        'id',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: SeparatorComponentPayload,
    ) -> None:
        self.spacing: SeparatorSpacing = try_enum(SeparatorSpacing, data.get('spacing', 1))
        self.visible: bool = data.get('divider', True)
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.separator]:
        return ComponentType.separator

    def to_dict(self) -> SeparatorComponentPayload:
        payload: SeparatorComponentPayload = {
            'type': self.type.value,
            'divider': self.visible,
            'spacing': self.spacing.value,
        }
        if self.id is not None:
            payload['id'] = self.id
        return payload


class Container(Component):
    """Represents a Container from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for creating a container is
        :class:`discord.ui.Container` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    children: :class:`Component`
        This container's children.
    spoiler: :class:`bool`
        Whether this container is flagged as a spoiler.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        'children',
        'id',
        'spoiler',
        '_colour',
    )

    __repr_info__ = (
        'children',
        'id',
        'spoiler',
        'accent_colour',
    )

    def __init__(self, data: ContainerComponentPayload, state: Optional[ConnectionState]) -> None:
        self.children: List[Component] = []
        self.id: Optional[int] = data.get('id')

        for child in data['components']:
            comp = _component_factory(child, state)

            if comp:
                self.children.append(comp)

        self.spoiler: bool = data.get('spoiler', False)

        colour = data.get('accent_color')
        self._colour: Optional[Colour] = None
        if colour is not None:
            self._colour = Colour(colour)

    @property
    def accent_colour(self) -> Optional[Colour]:
        """Optional[:class:`Colour`]: The container's accent colour."""
        return self._colour

    accent_color = accent_colour

    @property
    def type(self) -> Literal[ComponentType.container]:
        return ComponentType.container

    def to_dict(self) -> ContainerComponentPayload:
        payload: ContainerComponentPayload = {
            'type': self.type.value,
            'spoiler': self.spoiler,
            'components': [c.to_dict() for c in self.children],  # pyright: ignore[reportAssignmentType]
        }
        if self.id is not None:
            payload['id'] = self.id
        if self._colour:
            payload['accent_color'] = self._colour.value
        return payload


class LabelComponent(Component):
    """Represents a label component from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. note::

        The user constructible and usable type for creating a label is
        :class:`discord.ui.Label` not this one.

    .. versionadded:: 2.6

    Attributes
    ----------
    label: :class:`str`
        The label text to display.
    description: Optional[:class:`str`]
        The description text to display below the label, if any.
    component: :class:`Component`
        The component that this label is associated with.
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = (
        'label',
        'description',
        'component',
        'id',
    )

    __repr_info__ = ('label', 'description', 'component', 'id,')

    def __init__(self, data: LabelComponentPayload, state: Optional[ConnectionState]) -> None:
        self.component: Component = _component_factory(data['component'], state)  # type: ignore
        self.label: str = data['label']
        self.id: Optional[int] = data.get('id')
        self.description: Optional[str] = data.get('description')

    @property
    def type(self) -> Literal[ComponentType.label]:
        return ComponentType.label

    def to_dict(self) -> LabelComponentPayload:
        payload: LabelComponentPayload = {
            'type': self.type.value,
            'label': self.label,
            'component': self.component.to_dict(),  # type: ignore
        }
        if self.description:
            payload['description'] = self.description
        if self.id is not None:
            payload['id'] = self.id
        return payload


def _component_factory(data: ComponentPayload, state: Optional[ConnectionState] = None) -> Optional[Component]:
    if data['type'] == 1:
        return ActionRow(data)
    elif data['type'] == 2:
        return Button(data)
    elif data['type'] == 4:
        return TextInput(data)
    elif data['type'] in (3, 5, 6, 7, 8):
        return SelectMenu(data)  # type: ignore
    elif data['type'] == 9:
        return SectionComponent(data, state)
    elif data['type'] == 10:
        return TextDisplay(data)
    elif data['type'] == 11:
        return ThumbnailComponent(data, state)
    elif data['type'] == 12:
        return MediaGalleryComponent(data, state)
    elif data['type'] == 13:
        return FileComponent(data, state)
    elif data['type'] == 14:
        return SeparatorComponent(data)
    elif data['type'] == 17:
        return Container(data, state)
    elif data['type'] == 18:
        return LabelComponent(data, state)
