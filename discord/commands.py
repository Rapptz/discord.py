"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Tuple, Type, Union, runtime_checkable

from .enums import AppCommandOptionType, AppCommandType, ChannelType, InteractionType, try_enum
from .interactions import _wrapped_interaction
from .mixins import Hashable
from .permissions import Permissions
from .utils import _generate_nonce, _get_as_snowflake

if TYPE_CHECKING:
    from .abc import Messageable, Snowflake
    from .application import IntegrationApplication
    from .file import File
    from .guild import Guild
    from .interactions import Interaction
    from .message import Attachment, Message
    from .state import ConnectionState


__all__ = (
    'BaseCommand',
    'UserCommand',
    'MessageCommand',
    'SlashCommand',
    'SubCommand',
    'Option',
    'OptionChoice',
)


@runtime_checkable
class ApplicationCommand(Protocol):
    """An ABC that represents a usable application command.

    The following implement this ABC:

    - :class:`~discord.UserCommand`
    - :class:`~discord.MessageCommand`
    - :class:`~discord.SlashCommand`
    - :class:`~discord.SubCommand`

    .. versionadded:: 2.0

    Attributes
    -----------
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`~discord.AppCommandType`
        The type of application command.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    dm_permission: :class:`bool`
        Whether the command is enabled in DMs.
    nsfw: :class:`bool`
        Whether the command is marked NSFW and only available in NSFW channels.
    application: Optional[:class:`~discord.IntegrationApplication`]
        The application this command belongs to.
        Only available if requested.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    """

    __slots__ = ()

    if TYPE_CHECKING:
        _state: ConnectionState
        _channel: Optional[Messageable]
        _default_member_permissions: Optional[int]
        name: str
        description: str
        version: int
        type: AppCommandType
        default_permission: bool
        dm_permission: bool
        nsfw: bool
        application_id: int
        application: Optional[IntegrationApplication]
        mention: str
        guild_id: Optional[int]

    def __str__(self) -> str:
        return self.name

    async def __call__(
        self, data: dict, files: Optional[List[File]] = None, channel: Optional[Messageable] = None
    ) -> Interaction:
        channel = channel or self.target_channel
        if channel is None:
            raise TypeError('__call__() missing 1 required argument: \'channel\'')

        return await _wrapped_interaction(
            self._state,
            _generate_nonce(),
            InteractionType.application_command,
            data['name'],
            await channel._get_channel(),  # type: ignore # acc_channel is always correct here
            data,
            files=files,
            application_id=self.application_id,
        )

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: Returns the guild this command is registered to
        if it exists.
        """
        return self._state._get_guild(self.guild_id)

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return False

    @property
    def target_channel(self) -> Optional[Messageable]:
        """Optional[:class:`.abc.Messageable`]: The channel this application command will be used on.

        You can set this in order to use this command in a different channel without re-fetching it.
        """
        return self._channel

    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        from .abc import Messageable

        if not isinstance(value, Messageable) and value is not None:
            raise TypeError('channel must derive from Messageable')
        self._channel = value

    @property
    def default_member_permissions(self) -> Optional[Permissions]:
        """Optional[:class:`~discord.Permissions`]: The default permissions required to use this command.

        .. note::
            This may be overrided on a guild-by-guild basis.
        """
        perms = self._default_member_permissions
        return Permissions(perms) if perms is not None else None


class BaseCommand(ApplicationCommand, Hashable):
    __slots__ = (
        'name',
        'description',
        'id',
        'version',
        'type',
        'default_permission',
        'application',
        'application_id',
        'dm_permission',
        'nsfw',
        'guild_id',
        '_data',
        '_state',
        '_channel',
        '_default_member_permissions',
    )

    def __init__(
        self, *, state: ConnectionState, data: Dict[str, Any], channel: Optional[Messageable] = None, **kwargs
    ) -> None:
        self._state = state
        self._data = data
        self.name = data['name']
        self.description = data['description']
        self._channel = channel
        self.application_id: int = int(data['application_id'])
        self.id: int = int(data['id'])
        self.version = int(data['version'])
        self.type = try_enum(AppCommandType, data['type'])

        application = data.get('application')
        self.application = state.create_integration_application(application) if application else None

        self._default_member_permissions = _get_as_snowflake(data, 'default_member_permissions')
        self.default_permission: bool = data.get('default_permission', True)
        dm_permission = data.get('dm_permission')  # Null means true?
        self.dm_permission = dm_permission if dm_permission is not None else True
        self.nsfw: bool = data.get('nsfw', False)
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the command."""
        return f'</{self.name}:{self.id}>'


class SlashMixin(ApplicationCommand, Protocol):
    if TYPE_CHECKING:
        _parent: SlashCommand
        options: List[Option]
        children: List[SubCommand]

    async def __call__(
        self,
        options: List[dict],
        files: Optional[List[File]],
        attachments: List[Attachment],
        channel: Optional[Messageable] = None,
    ) -> Interaction:
        obj = self._parent
        command = obj._data
        command['name_localized'] = command['name']
        data = {
            'application_command': command,
            'attachments': attachments,
            'id': str(obj.id),
            'name': obj.name,
            'options': options,
            'type': obj.type.value,
            'version': str(obj.version),
        }
        if self.guild_id:
            data['guild_id'] = str(self.guild_id)
        return await super().__call__(data, files, channel)

    def _parse_kwargs(self, kwargs: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[File], List[Attachment]]:
        possible_options = {o.name: o for o in self.options}
        kwargs = {k: v for k, v in kwargs.items() if k in possible_options}
        options = []
        files = []

        for k, v in kwargs.items():
            option = possible_options[k]
            type = option.type

            if type in {
                AppCommandOptionType.user,
                AppCommandOptionType.channel,
                AppCommandOptionType.role,
                AppCommandOptionType.mentionable,
            }:
                v = str(v.id)
            elif type is AppCommandOptionType.boolean:
                v = bool(v)
            elif type is AppCommandOptionType.attachment:
                files.append(v)
                v = len(files) - 1
            else:
                v = option._convert(v)

            if type is AppCommandOptionType.string:
                v = str(v)
            elif type is AppCommandOptionType.integer:
                v = int(v)
            elif type is AppCommandOptionType.number:
                v = float(v)

            options.append({'name': k, 'value': v, 'type': type.value})

        attachments = []
        for index, file in enumerate(files):
            attachments.append(file.to_dict(index))

        return options, files, attachments

    def _unwrap_options(self, data: List[Dict[str, Any]]) -> None:
        options = []
        children = []
        for option in data:
            type = try_enum(AppCommandOptionType, option['type'])
            if type in {
                AppCommandOptionType.sub_command,
                AppCommandOptionType.sub_command_group,
            }:
                children.append(SubCommand(parent=self, data=option))
            else:
                options.append(Option(option))

        self.options = options
        self.children = children


class UserCommand(BaseCommand):
    """Represents a user command.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    version: :class:`int`
        The command's version.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`AppCommandType`
        The type of application command. This will always be :attr:`AppCommandType.user`.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    dm_permission: :class:`bool`
        Whether the command is enabled in DMs.
    nsfw: :class:`bool`
        Whether the command is marked NSFW and only available in NSFW channels.
    application: Optional[:class:`IntegrationApplication`]
        The application this command belongs to.
        Only available if requested.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    """

    __slots__ = ('_user',)

    def __init__(self, *, target: Optional[Snowflake] = None, **kwargs):
        super().__init__(**kwargs)
        self._user = target

    async def __call__(self, user: Optional[Snowflake] = None, *, channel: Optional[Messageable] = None):
        """|coro|

        Use the user command.

        Parameters
        ----------
        user: Optional[:class:`User`]
            The user to use the command on. Overrides :attr:`target_user`.
            Required if :attr:`target_user` is not set.
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.

        Returns
        -------
        :class:`Interaction`
            The interaction that was created.
        """
        user = user or self._user
        if user is None:
            raise TypeError('__call__() missing 1 required positional argument: \'user\'')

        command = self._data
        data = {
            'application_command': command,
            'attachments': [],
            'id': str(self.id),
            'name': self.name,
            'options': [],
            'target_id': str(user.id),
            'type': self.type.value,
            'version': str(self.version),
        }
        return await super().__call__(data, None, channel)

    @property
    def target_user(self) -> Optional[Snowflake]:
        """Optional[:class:`~abc.Snowflake`]: The user this application command will be used on.

        You can set this in order to use this command on a different user without re-fetching it.
        """
        return self._user

    @target_user.setter
    def target_user(self, value: Optional[Snowflake]) -> None:
        from .abc import Snowflake

        if not isinstance(value, Snowflake) and value is not None:
            raise TypeError('user must be Snowflake')
        self._user = value


class MessageCommand(BaseCommand):
    """Represents a message command.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    version: :class:`int`
        The command's version.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`AppCommandType`
        The type of application command. This will always be :attr:`AppCommandType.message`.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    dm_permission: :class:`bool`
        Whether the command is enabled in DMs.
    nsfw: :class:`bool`
        Whether the command is marked NSFW and only available in NSFW channels.
    application: Optional[:class:`IntegrationApplication`]
        The application this command belongs to.
        Only available if requested.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    """

    __slots__ = ('_message',)

    def __init__(self, *, target: Optional[Message] = None, **kwargs):
        super().__init__(**kwargs)
        self._message = target

    async def __call__(self, message: Optional[Message] = None, *, channel: Optional[Messageable] = None):
        """|coro|

        Use the message command.

        Parameters
        ----------
        message: Optional[:class:`Message`]
            The message to use the command on. Overrides :attr:`target_message`.
            Required if :attr:`target_message` is not set.
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.

        Returns
        -------
        :class:`Interaction`
            The interaction that was created.
        """
        message = message or self._message
        if message is None:
            raise TypeError('__call__() missing 1 required positional argument: \'message\'')

        command = self._data
        command['name_localized'] = command['name']
        data = {
            'application_command': command,
            'attachments': [],
            'id': str(self.id),
            'name': self.name,
            'options': [],
            'target_id': str(message.id),
            'type': self.type.value,
            'version': str(self.version),
        }
        return await super().__call__(data, None, channel)

    @property
    def target_message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: The message this application command will be used on.

        You can set this in order to use this command on a different message without re-fetching it.
        """
        return self._message

    @target_message.setter
    def target_message(self, value: Optional[Message]) -> None:
        from .message import Message

        if not isinstance(value, Message) and value is not None:
            raise TypeError('message must be Message')
        self._message = value


class SlashCommand(BaseCommand, SlashMixin):
    """Represents a slash command.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    version: :class:`int`
        The command's version.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`AppCommandType`
        The type of application command.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    dm_permission: :class:`bool`
        Whether the command is enabled in DMs.
    nsfw: :class:`bool`
        Whether the command is marked NSFW and only available in NSFW channels.
    application: Optional[:class:`IntegrationApplication`]
        The application this command belongs to.
        Only available if requested.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    options: List[:class:`Option`]
        The command's options.
    children: List[:class:`SubCommand`]
        The command's subcommands. If a command has subcommands, it is a group and cannot be used.
    """

    __slots__ = ('_parent', 'options', 'children')

    def __init__(self, *, data: Dict[str, Any], **kwargs) -> None:
        super().__init__(data=data, **kwargs)
        self._parent = self
        self._unwrap_options(data.get('options', []))

    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r"""|coro|

        Use the slash command.

        Parameters
        ----------
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.
        \*\*kwargs: Any
            The options to use. These will be casted to the correct type.
            If an option has choices, they are automatically converted from name to value for you.

        Raises
        ------
        TypeError
            Attempted to use a group.

        Returns
        -------
        :class:`Interaction`
            The interaction that was created.
        """
        if self.is_group():
            raise TypeError('Cannot use a group')

        return await super().__call__(*self._parse_kwargs(kwargs), channel)

    def __repr__(self) -> str:
        BASE = f'<SlashCommand id={self.id} name={self.name!r}'
        if self.options:
            BASE += f' options={len(self.options)}'
        if self.children:
            BASE += f' children={len(self.children)}'
        return BASE + '>'

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return bool(self.children)


class SubCommand(SlashMixin):
    """Represents a slash command child.

    .. versionadded:: 2.0

    This could be a subcommand, or a subgroup.

    .. container:: operations

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    name: :class:`str`
        The subcommand's name.
    description: :class:`str`
        The subcommand's description, if any.
    type: :class:`AppCommandType`
        The type of application command. Always :attr:`AppCommandType.chat_input`.
    parent: Union[:class:`SlashCommand`, :class:`SubCommand`]
        The parent command.
    options: List[:class:`Option`]
        The subcommand's options.
    children: List[:class:`SubCommand`]
        The subcommand's subcommands. If a subcommand has subcommands, it is a group and cannot be used.
    """

    __slots__ = (
        '_parent',
        '_state',
        '_type',
        'parent',
        'options',
        'children',
        'type',
    )

    def __init__(self, *, parent, data):
        self.name = data['name']
        self.description = data.get('description')
        self._state = parent._state
        self.parent: Union[SlashCommand, SubCommand] = parent
        self._parent: SlashCommand = getattr(parent, 'parent', parent)  # type: ignore
        self.type = AppCommandType.chat_input  # Avoid confusion I guess
        self._type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self._unwrap_options(data.get('options', []))

    def __str__(self) -> str:
        return self.name

    def _walk_parents(self):
        parent = self.parent
        while True:
            if isinstance(parent, SlashCommand):
                break
            else:
                yield parent
                parent = parent.parent

    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r"""|coro|

        Use the sub command.

        Parameters
        ----------
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.
        \*\*kwargs: Any
            The options to use. These will be casted to the correct type.
            If an option has choices, they are automatically converted from name to value for you.

        Raises
        ------
        TypeError
            Attempted to use a group.

        Returns
        -------
        :class:`Interaction`
            The interaction that was created.
        """
        if self.is_group():
            raise TypeError('Cannot use a group')

        options, files, attachments = self._parse_kwargs(kwargs)

        options = [
            {
                'type': self._type.value,
                'name': self.name,
                'options': options,
            }
        ]
        for parent in self._walk_parents():
            options = [
                {
                    'type': parent._type.value,
                    'name': parent.name,
                    'options': options,
                }
            ]

        return await super().__call__(options, files, attachments, channel)

    def __repr__(self) -> str:
        BASE = f'<SubCommand name={self.name!r}'
        if self.options:
            BASE += f' options={len(self.options)}'
        if self.children:
            BASE += f' children={len(self.children)}'
        return BASE + '>'

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the fully qualified command name.
        The qualified name includes the parent name as well. For example,
        in a command like ``/foo bar`` the qualified name is ``foo bar``.
        """
        names = [self.name, self.parent.name]
        if isinstance(self.parent, SubCommand):
            names.append(self._parent.name)
        return ' '.join(reversed(names))

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the subcommand."""
        return f'</{self.qualified_name}:{self._parent.id}>'

    @property
    def _default_member_permissions(self) -> Optional[int]:
        return self._parent._default_member_permissions

    @property
    def application_id(self) -> int:
        """:class:`int`: The ID of the application this command belongs to."""
        return self._parent.application_id

    @property
    def version(self) -> int:
        """:class:`int`: The version of the command."""
        return self._parent.version

    @property
    def default_permission(self) -> bool:
        """:class:`bool`: Whether the command is enabled in guilds by default."""
        return self._parent.default_permission

    @property
    def dm_permission(self) -> bool:
        """:class:`bool`: Whether the command is enabled in DMs."""
        return self._parent.dm_permission

    @property
    def nsfw(self) -> bool:
        """:class:`bool`: Whether the command is marked NSFW and only available in NSFW channels."""
        return self._parent.nsfw

    @property
    def guild_id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command."""
        return self._parent.guild_id

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: Returns the guild this command is registered to
        if it exists.
        """
        return self._parent.guild

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return self._type is AppCommandOptionType.sub_command_group

    @property
    def application(self):
        """Optional[:class:`IntegrationApplication`]: The application this command belongs to.
        Only available if requested.
        """
        return self._parent.application

    @property
    def target_channel(self) -> Optional[Messageable]:
        """Optional[:class:`.abc.Messageable`]: The channel this command will be used on.

        You can set this in order to use this command on a different channel without re-fetching it.
        """
        return self._parent.target_channel

    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        self._parent.target_channel = value


class Option:
    """Represents a command option.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the option's name.

    Attributes
    ----------
    name: :class:`str`
        The option's name.
    description: :class:`str`
        The option's description, if any.
    type: :class:`AppCommandOptionType`
        The type of option.
    required: :class:`bool`
        Whether the option is required.
    min_value: Optional[Union[:class:`int`, :class:`float`]]
        Minimum value of the option. Only applicable to :attr:`AppCommandOptionType.integer` and :attr:`AppCommandOptionType.number`.
    max_value: Optional[Union[:class:`int`, :class:`float`]]
        Maximum value of the option. Only applicable to :attr:`AppCommandOptionType.integer` and :attr:`AppCommandOptionType.number`.
    choices: List[:class:`OptionChoice`]
        A list of possible choices to choose from. If these are present, you must choose one from them.

        Only applicable to :attr:`AppCommandOptionType.string`, :attr:`AppCommandOptionType.integer`, and :attr:`AppCommandOptionType.number`.
    channel_types: List[:class:`ChannelType`]
        A list of channel types that you can choose from. If these are present, you must choose a channel that is one of these types.

        Only applicable to :attr:`AppCommandOptionType.channel`.
    autocomplete: :class:`bool`
        Whether the option autocompletes.

        Only applicable to :attr:`AppCommandOptionType.string`, :attr:`AppCommandOptionType.integer`, and :attr:`AppCommandOptionType.number`.
        Always ``False`` if :attr:`choices` are present.
    """

    __slots__ = (
        'name',
        'description',
        'type',
        'required',
        'min_value',
        'max_value',
        'choices',
        'channel_types',
        'autocomplete',
    )

    def __init__(self, data):
        self.name: str = data['name']
        self.description: str = data['description']
        self.type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self.required: bool = data.get('required', False)
        self.min_value: Optional[Union[int, float]] = data.get('min_value')
        self.max_value: Optional[int] = data.get('max_value')
        self.choices = [OptionChoice(choice, self.type) for choice in data.get('choices', [])]
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, c) for c in data.get('channel_types', [])]
        self.autocomplete: bool = data.get('autocomplete', False)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Option name={self.name!r} type={self.type!r} required={self.required}>'

    def _convert(self, value):
        for choice in self.choices:
            if (new_value := choice._convert(value)) != value:
                return new_value
        return value


class OptionChoice:
    """Represents a choice for an option.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: str(x)

            Returns the choice's name.

    Attributes
    ----------
    name: :class:`str`
        The choice's displayed name.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        The choice's value. The type of this depends on the option's type.
    """

    __slots__ = ('name', 'value')

    def __init__(self, data: Dict[str, str], type: AppCommandOptionType):
        self.name: str = data['name']
        self.value: Union[str, int, float]
        if type is AppCommandOptionType.string:
            self.value = data['value']
        elif type is AppCommandOptionType.integer:
            self.value = int(data['value'])
        elif type is AppCommandOptionType.number:
            self.value = float(data['value'])

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<OptionChoice name={self.name!r} value={self.value!r}>'

    def _convert(self, value):
        if value == self.name:
            return self.value
        return value


def _command_factory(command_type: int) -> Tuple[AppCommandType, Type[BaseCommand]]:
    value = try_enum(AppCommandType, command_type)
    if value is AppCommandType.chat_input:
        return value, SlashCommand
    elif value is AppCommandType.user:
        return value, UserCommand
    elif value is AppCommandType.message:
        return value, MessageCommand
    else:
        return value, BaseCommand  # IDK about this
