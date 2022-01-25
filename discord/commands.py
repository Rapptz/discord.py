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

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple, runtime_checkable, TYPE_CHECKING, Union

from .enums import CommandType, ChannelType, OptionType, try_enum
from .errors import InvalidData, InvalidArgument
from .utils import _generate_session_id, time_snowflake

if TYPE_CHECKING:
    from .abc import Messageable, Snowflake
    from .interactions import Interaction
    from .message import Message
    from .state import ConnectionState

__all__ = (
    'ApplicationCommand',
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
    """An ABC that represents a useable application command.

    The following implement this ABC:

    - :class:`~discord.BaseCommand`
    - :class:`~discord.UserCommand`
    - :class:`~discord.MessageCommand`
    - :class:`~discord.SlashCommand`
    - :class:`~discord.SubCommand`

    Attributes
    -----------
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    version: :class:`int`
        The command's version.
    type: :class:`CommandType`
        The type of application command.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    """

    __slots__ = ()

    if TYPE_CHECKING:
        _state: ConnectionState
        _application_id: int
        name: str
        description: str
        version: int
        type: CommandType
        target_channel: Optional[Messageable]
        default_permission: bool

    async def __call__(self, data, channel: Optional[Messageable] = None) -> Interaction:
        channel = channel or self.target_channel
        if channel is None:
            raise TypeError('__call__() missing 1 required argument: \'channel\'')
        state = self._state
        channel = await channel._get_channel()

        payload = {
            'application_id': str(self._application_id),
            'channel_id': str(channel.id),
            'data': data,
            'nonce': str(time_snowflake(datetime.utcnow())),
            'session_id': state.session_id or _generate_session_id(),
            'type': 2,  # Should be an enum but eh
        }
        if getattr(channel, 'guild', None) is not None:
            payload['guild_id'] = str(channel.guild.id)

        state._interactions[payload['nonce']] = (2, data['name'])
        await state.http.interact(payload, form_data=True)
        try:
            i = await state.client.wait_for(
                'interaction_finish',
                check=lambda d: d.nonce == payload['nonce'],
                timeout=5,
            )
        except TimeoutError as exc:
            raise InvalidData('Did not receive a response from Discord') from exc
        return i


class BaseCommand(ApplicationCommand):
    """Represents a base command.

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    version: :class:`int`
        The command's version.
    type: :class:`CommandType`
        The type of application command.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    """

    __slots__ = (
        'name',
        'description',
        'id',
        'version',
        'type',
        'default_permission',
        '_data',
        '_state',
        '_channel',
        '_application_id',
        '_dm_permission',
        '_default_member_permissions',
    )

    def __init__(
        self, *, state: ConnectionState, data: Dict[str, Any], channel: Optional[Messageable] = None
    ) -> None:
        self._state = state
        self._data = data
        self.name = data['name']
        self.description = data['description']
        self._channel = channel
        self._application_id: int = int(data['application_id'])
        self.id: int = int(data['id'])
        self.version = int(data['version'])
        self.type = try_enum(CommandType, data['type'])
        self.default_permission: bool = data['default_permission']
        self._dm_permission = data['dm_permission']
        self._default_member_permissions = data['default_member_permissions']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name}>'

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Here for compatibility purposes.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return False

    @property
    def application(self):
        """The application this command belongs to."""
        ...
        #return self._state.get_application(self._application_id)

    @property
    def target_channel(self) -> Optional[Messageable]:
        """Optional[:class:`Messageable`]: The channel this application command will be used on.
    
        You can set this in order to use this command in a different channel without re-fetching it.
        """
        return self._channel

    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        from .abc import Messageable
        if not isinstance(value, Messageable) and value is not None:
            raise TypeError('channel must derive from Messageable')
        self._channel = value


class SlashMixin(ApplicationCommand, Protocol):
    if TYPE_CHECKING:
        _parent: SlashCommand
        options: List[Option]
        children: List[SubCommand]

    async def __call__(self, options, channel=None):
        obj = self._parent
        command = obj._data
        command['name_localized'] = command['name']
        data = {
            'application_command': command,
            'attachments': [],
            'id': str(obj.id),
            'name': obj.name,
            'options': options,
            'type': obj.type.value,
            'version': str(obj.version),
        }
        return await super().__call__(data, channel)

    def _parse_kwargs(self, kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        possible_options = {o.name: o for o in self.options}
        kwargs = {k: v for k, v in kwargs.items() if k in possible_options}
        options = []

        for k, v in kwargs.items():
            option = possible_options[k]
            type = option.type

            if type in {
                OptionType.user,
                OptionType.channel,
                OptionType.role,
                OptionType.mentionable,
            }:
                v = str(v.id)
            elif type is OptionType.boolean:
                v = bool(v)
            else:
                v = option._convert(v)

            if type is OptionType.string:
                v = str(v)
            elif type is OptionType.integer:
                v = int(v)
            elif type is OptionType.number:
                v = float(v)

            options.append({'name': k, 'value': v, 'type': type.value})

        return options

    def _unwrap_options(self, data: List[Dict[str, Any]]) -> None:
        options = []
        children = []
        for option in data:
            type = try_enum(OptionType, option['type'])
            if type in {
                OptionType.sub_command,
                OptionType.sub_command_group,
            }:
                children.append(SubCommand(parent=self, data=option))
            else:
                options.append(Option(option))

        for child in children:
            setattr(self, child.name, child)

        self.options = options
        self.children = children


class UserCommand(BaseCommand):
    """Represents a user command."""

    __slots__ = ('_user',)

    def __init__(self, *, user: Optional[Snowflake] = None, **kwargs):
        super().__init__(**kwargs)
        self._user = user

    async def __call__(
        self, user: Optional[Snowflake] = None, *, channel: Optional[Messageable] = None
    ):
        """Use the user command.

        Parameters
        ----------
        user: Optional[:class:`User`]
            The user to use the command on. Overrides :attr:`target_user`.
            Required if :attr:`target_user` is not set.
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.
        """
        user = user or self._user
        if user is None:
            raise TypeError('__call__() missing 1 required positional argument: \'user\'')

        command = self._data
        command['name_localized'] = command['name']
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
        return await super().__call__(data, channel)

    @property
    def target_user(self) -> Optional[Snowflake]:
        """Optional[:class:`Snowflake`]: The user this application command will be used on.
    
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

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`CommandType`
        The type of application command. Always :class:`CommandType.message`.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    """

    __slots__ = ('_message',)

    def __init__(self, *, message: Optional[Message] = None, **kwargs):
        super().__init__(**kwargs)
        self._message = message

    async def __call__(
        self, message: Optional[Message] = None, *, channel: Optional[Messageable] = None
    ):
        """Use the message command.

        Parameters
        ----------
        message: Optional[:class:`Message`]
            The message to use the command on. Overrides :attr:`target_message`.
            Required if :attr:`target_message` is not set.
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_channel` is not set.
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
        return await super().__call__(data, channel)

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

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`CommandType`
        The type of application command. Always :class:`CommandType.chat_input`.
    default_permission: :class:`bool`
        Whether the command is enabled in guilds by default.
    options: List[:class:`Option`]
        The command's options.
    children: List[:class:`SubCommand`]
        The command's subcommands. If a command has subcommands, it is a group and cannot be used.
        You can access (and use) subcommands directly as attributes of the class.
    """

    __slots__ = ('_parent', 'options', 'children')

    def __init__(
        self, *, data: Dict[str, Any], **kwargs
    ) -> None:
        super().__init__(data=data, **kwargs)
        self._parent = self
        self._unwrap_options(data.get('options', []))

    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r"""Use the slash command.

        Parameters
        ----------
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_message` is not set.
        \*\*kwargs: Any
            The options to use. These will be casted to the correct type.
            If an option has choices, they are automatically converted from name to value for you.

        Raises
        ------
        InvalidArgument
            Attempted to use a group.
        """
        if self.is_group():
            raise InvalidArgument('Cannot use a group')

        return await super().__call__(self._parse_kwargs(kwargs), channel)

    def __repr__(self) -> str:
        BASE = f'<SlashCommand id={self.id} name={self.name}'
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

    This could be a subcommand, or a subgroup.

    Attributes
    ----------
    parent: :class:`SlashCommand`
        The parent command.
    name: :class:`str`
        The command's name.
    description: :class:`str`
        The command's description, if any.
    type: :class:`CommandType`
        The type of application command. Always :class:`CommandType.chat_input`.
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
        self.type = CommandType.chat_input  # Avoid confusion I guess
        self._type: OptionType = try_enum(OptionType, data['type'])
        self._unwrap_options(data.get('options', []))

    def _walk_parents(self):
        parent = self.parent
        while True:
            if isinstance(parent, SlashCommand):
                break
            else:
                yield parent
                parent = parent.parent

    async def __call__(self, channel: Optional[Messageable] = None, /, **kwargs):
        r"""Use the sub command.

        Parameters
        ----------
        channel: Optional[:class:`abc.Messageable`]
            The channel to use the command on. Overrides :attr:`target_channel`.
            Required if :attr:`target_message` is not set.
        \*\*kwargs: Any
            The options to use. These will be casted to the correct type.
            If an option has choices, they are automatically converted from name to value for you.

        Raises
        ------
        InvalidArgument
            Attempted to use a group.
        """
        if self.is_group():
            raise InvalidArgument('Cannot use a group')

        options = [{
            'type': self._type.value,
            'name': self.name,
            'options': self._parse_kwargs(kwargs),
        }]
        for parent in self._walk_parents():
            options = [{
                'type': parent._type.value,
                'name': parent.name,
                'options': options,
            }]

        return await super().__call__(options, channel)

    def __repr__(self) -> str:
        BASE = f'<SubCommand name={self.name}'
        if self.options:
            BASE += f' options={len(self.options)}'
        if self.children:
            BASE += f' children={len(self.children)}'
        return BASE + '>'

    @property
    def _application_id(self) -> int:
        return self._parent._application_id

    @property
    def version(self) -> int:
        """:class:`int`: The version of the command."""
        return self._parent.version

    @property
    def default_permission(self) -> bool:
        """:class:`bool`: Whether the command is enabled in guilds by default."""
        return self._parent.default_permission

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return self._type is OptionType.sub_command_group

    @property
    def application(self):
        """The application this command belongs to."""
        return self._parent.application

    @property
    def target_channel(self) -> Optional[Messageable]:
        """Optional[:class:`abc.Messageable`]: The channel this command will be used on.

        You can set this in order to use this command on a different channel without re-fetching it.
        """
        return self._parent.target_channel

    @target_channel.setter
    def target_channel(self, value: Optional[Messageable]) -> None:
        self._parent.target_channel = value


class Option:
    """Represents a command option.

    Attributes
    ----------
    name: :class:`str`
        The option's name.
    description: :class:`str`
        The option's description, if any.
    type: :class:`OptionType`
        The type of option.
    required: :class:`bool`
        Whether the option is required.
    min_value: Optional[Union[:class:`int`, :class:`float`]]
        Minimum value of the option. Only applicable to :attr:`OptionType.integer` and :attr:`OptionType.number`.
    max_value: Optional[Union[:class:`int`, :class:`float`]]
        Maximum value of the option. Only applicable to :attr:`OptionType.integer` and :attr:`OptionType.number`.
    choices: List[:class:`OptionChoice`]
        A list of possible choices to choose from. If these are present, you must choose one from them.
        Only applicable to :attr:`OptionType.string`, :attr:`OptionType.integer`, and :attr:`OptionType.number`.
    channel_types: List[:class:`ChannelType`]
        A list of channel types that you can choose from. If these are present, you must choose a channel that is one of these types.
        Only applicable to :attr:`OptionType.channel`.
    autocomplete: :class:`bool`
        Whether the option autocompletes. Always ``False`` if :attr:`choices` are present.
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
        self.type: OptionType = try_enum(OptionType, data['type'])
        self.required: bool = data.get('required', False)
        self.min_value: Optional[Union[int, float]] = data.get('min_value')
        self.max_value: Optional[int] = data.get('max_value')
        self.choices = [OptionChoice(choice, self.type) for choice in data.get('choices', [])]
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, c) for c in data.get('channel_types', [])]
        self.autocomplete: bool = data.get('autocomplete', False)

    def __repr__(self) -> str:
        return f'<Option name={self.name} type={self.type} required={self.required}>'

    def _convert(self, value):
        for choice in self.choices:
            if (new_value := choice._convert(value)) != value:
                return new_value
        return value


class OptionChoice:
    """Represents a choice for an option.

    Attributes
    ----------
    name: :class:`str`
        The choice's displayed name.
    value: Any
        The choice's value. The type of this depends on the option's type.
    """

    __slots__ = ('name', 'value')

    def __init__(self, data: Dict[str, str], type: OptionType):
        self.name: str = data['name']
        if type is OptionType.string:
            self.value: str = data['value']  # type: ignore
        elif type is OptionType.integer:
            self.value: int = int(data['value'])  # type: ignore
        elif type is OptionType.number:
            self.value: float = float(data['value'])  # type: ignore

    def __repr__(self) -> str:
        return f'<OptionChoice name={self.name} value={self.value}>'

    def _convert(self, value):
        if value == self.name:
            return self.value
        return value


def _command_factory(command_type: int) -> Tuple[CommandType, BaseCommand]:
    value = try_enum(CommandType, command_type)
    if value is CommandType.chat_input:
        return value, SlashCommand
    elif value is CommandType.user:
        return value, UserCommand
    elif value is CommandType.message:
        return value, MessageCommand
    else:
        return value, BaseCommand  # IDK about this