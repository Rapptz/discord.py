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
from datetime import datetime

from .errors import MissingApplicationID
from ..permissions import Permissions
from ..enums import AppCommandOptionType, AppCommandType, ChannelType, try_enum
from ..mixins import Hashable
from ..utils import _get_as_snowflake, parse_time, snowflake_time, MISSING
from typing import Generic, List, TYPE_CHECKING, Optional, TypeVar, Union

__all__ = (
    'AppCommand',
    'AppCommandGroup',
    'AppCommandChannel',
    'AppCommandThread',
    'Argument',
    'Choice',
    'AllChannels',
)

ChoiceT = TypeVar('ChoiceT', str, int, float, Union[str, int, float])


def is_app_command_argument_type(value: int) -> bool:
    return 11 >= value >= 3


if TYPE_CHECKING:
    from ..types.command import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOptionChoice,
        ApplicationCommandOption,
    )
    from ..types.interactions import (
        PartialChannel,
        PartialThread,
    )
    from ..types.threads import (
        ThreadMetadata,
        ThreadArchiveDuration,
    )
    from ..state import ConnectionState
    from ..guild import GuildChannel, Guild
    from ..channel import TextChannel
    from ..threads import Thread

    ApplicationCommandParent = Union['AppCommand', 'AppCommandGroup']


class AllChannels:
    """Represents all channels for application command permissions.

    .. versionadded:: 2.0

    Attributes
    -----------
    guild: :class:`~discord.Guild`
        The guild the application command permission is for.
    """

    __slots__ = ('guild',)

    def __init__(self, guild: Guild):
        self.guild = guild

    @property
    def id(self) -> int:
        """:class:`int`: The ID sentinel used to represent all channels. Equivalent to the guild's ID minus 1."""
        return self.guild.id - 1

    def __repr__(self):
        return f'<AllChannels guild={self.guild}>'


class AppCommand(Hashable):
    """Represents a application command.

    In common parlance this is referred to as a "Slash Command" or a
    "Context Menu Command".

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two application commands are equal.

        .. describe:: x != y

            Checks if two application commands are not equal.

        .. describe:: hash(x)

            Returns the application command's hash.

        .. describe:: str(x)

            Returns the application command's name.

    Attributes
    -----------
    id: :class:`int`
        The application command's ID.
    application_id: :class:`int`
        The application command's application's ID.
    type: :class:`~discord.AppCommandType`
        The application command's type.
    name: :class:`str`
        The application command's name.
    description: :class:`str`
        The application command's description.
    default_member_permissions: Optional[:class:`~discord.Permissions`]
        The default member permissions that can run this command.
    dm_permission: :class:`bool`
        A boolean that indicates whether this command can be run in direct messages.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    nsfw: :class:`bool`
        Whether the command is NSFW and should only work in NSFW channels.
    """

    __slots__ = (
        'id',
        'type',
        'application_id',
        'name',
        'description',
        'guild_id',
        'options',
        'default_member_permissions',
        'dm_permission',
        'nsfw',
        '_state',
    )

    def __init__(self, *, data: ApplicationCommandPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, data: ApplicationCommandPayload) -> None:
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.type: AppCommandType = try_enum(AppCommandType, data.get('type', 1))
        self.options: List[Union[Argument, AppCommandGroup]] = [
            app_command_option_factory(data=d, parent=self, state=self._state) for d in data.get('options', [])
        ]
        self.default_member_permissions: Optional[Permissions]
        permissions = data.get('default_member_permissions')
        if permissions is None:
            self.default_member_permissions = None
        else:
            self.default_member_permissions = Permissions(int(permissions))

        dm_permission = data.get('dm_permission')
        # For some reason this field can be explicit null and mean True
        if dm_permission is None:
            dm_permission = True

        self.dm_permission: bool = dm_permission
        self.nsfw: bool = data.get('nsfw', False)

    def to_dict(self) -> ApplicationCommandPayload:
        return {
            'id': self.id,
            'type': self.type.value,
            'application_id': self.application_id,
            'name': self.name,
            'description': self.description,
            'options': [opt.to_dict() for opt in self.options],
        }  # type: ignore # Type checker does not understand this literal.

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self.type!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: Returns the guild this command is registered to
        if it exists.
        """
        return self._state._get_guild(self.guild_id)

    async def delete(self) -> None:
        """|coro|

        Deletes the application command.

        Raises
        -------
        NotFound
            The application command was not found.
        Forbidden
            You do not have permission to delete this application command.
        HTTPException
            Deleting the application command failed.
        MissingApplicationID
            The client does not have an application ID.
        """
        state = self._state
        if not state.application_id:
            raise MissingApplicationID

        if self.guild_id:
            await state.http.delete_guild_command(
                state.application_id,
                self.guild_id,
                self.id,
            )
        else:
            await state.http.delete_global_command(
                state.application_id,
                self.id,
            )

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        options: List[Union[Argument, AppCommandGroup]] = MISSING,
    ) -> AppCommand:
        """|coro|

        Edits the application command.

        Parameters
        -----------
        name: :class:`str`
            The new name for the application command.
        description: :class:`str`
            The new description for the application command.
        default_member_permissions: Optional[:class:`~discord.Permissions`]
            The new default permissions needed to use this application command.
            Pass value of ``None`` to remove any permission requirements.
        dm_permission: :class:`bool`
            Indicates if the application command can be used in DMs.
        options: List[Union[:class:`Argument`, :class:`AppCommandGroup`]]
            List of new options for this application command.

        Raises
        -------
        NotFound
            The application command was not found.
        Forbidden
            You do not have permission to edit this application command.
        HTTPException
            Editing the application command failed.
        MissingApplicationID
            The client does not have an application ID.

        Returns
        --------
        :class:`AppCommand`
            The newly edited application command.
        """
        state = self._state
        if not state.application_id:
            raise MissingApplicationID

        payload = {}

        if name is not MISSING:
            payload['name'] = name

        if description is not MISSING:
            payload['description'] = description

        if default_member_permissions is not MISSING:
            if default_member_permissions is not None:
                payload['default_member_permissions'] = default_member_permissions.value
            else:
                payload['default_member_permissions'] = None

        if self.guild_id is None and dm_permission is not MISSING:
            payload['dm_permission'] = dm_permission

        if options is not MISSING:
            payload['options'] = [option.to_dict() for option in options]

        if not payload:
            return self

        if self.guild_id:
            data = await state.http.edit_guild_command(
                state.application_id,
                self.guild_id,
                self.id,
                payload,
            )
        else:
            data = await state.http.edit_global_command(
                state.application_id,
                self.id,
                payload,
            )
        return AppCommand(data=data, state=state)


class Choice(Generic[ChoiceT]):
    """Represents an application command argument choice.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two choices are equal.

        .. describe:: x != y

            Checks if two choices are not equal.

        .. describe:: hash(x)

            Returns the choice's hash.

    Parameters
    -----------
    name: :class:`str`
        The name of the choice. Used for display purposes.
    value: Union[:class:`int`, :class:`str`, :class:`float`]
        The value of the choice.
    """

    __slots__ = ('name', 'value')

    def __init__(self, *, name: str, value: ChoiceT):
        self.name: str = name
        self.value: ChoiceT = value

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Choice) and self.name == o.name and self.value == o.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r}, value={self.value!r})'

    @property
    def _option_type(self) -> AppCommandOptionType:
        if isinstance(self.value, int):
            return AppCommandOptionType.integer
        elif isinstance(self.value, float):
            return AppCommandOptionType.number
        elif isinstance(self.value, str):
            return AppCommandOptionType.string
        else:
            raise TypeError(
                f'invalid Choice value type given, expected int, str, or float but received {self.value.__class__!r}'
            )

    def to_dict(self) -> ApplicationCommandOptionChoice:
        return {
            'name': self.name,
            'value': self.value,
        }


class AppCommandChannel(Hashable):
    """Represents an application command partially resolved channel object.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    -----------
    id: :class:`int`
        The ID of the channel.
    type: :class:`~discord.ChannelType`
        The type of channel.
    name: :class:`str`
        The name of the channel.
    permissions: :class:`~discord.Permissions`
        The resolved permissions of the user who invoked
        the application command in that channel.
    guild_id: :class:`int`
        The guild ID this channel belongs to.
    """

    __slots__ = (
        'id',
        'type',
        'name',
        'permissions',
        'guild_id',
        '_state',
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: PartialChannel,
        guild_id: int,
    ):
        self._state: ConnectionState = state
        self.guild_id: int = guild_id
        self.id: int = int(data['id'])
        self.type: ChannelType = try_enum(ChannelType, data['type'])
        self.name: str = data['name']
        self.permissions: Permissions = Permissions(int(data['permissions']))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} type={self.type!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: The channel's guild, from cache, if found."""
        return self._state._get_guild(self.guild_id)

    def resolve(self) -> Optional[GuildChannel]:
        """Resolves the application command channel to the appropriate channel
        from cache if found.

        Returns
        --------
        Optional[:class:`.abc.GuildChannel`]
            The resolved guild channel or ``None`` if not found in cache.
        """
        guild = self._state._get_guild(self.guild_id)
        if guild is not None:
            return guild.get_channel(self.id)
        return None

    async def fetch(self) -> GuildChannel:
        """|coro|

        Fetches the partial channel to a full :class:`.abc.GuildChannel`.

        Raises
        --------
        NotFound
            The channel was not found.
        Forbidden
            You do not have the permissions required to get a channel.
        HTTPException
            Retrieving the channel failed.

        Returns
        --------
        :class:`.abc.GuildChannel`
            The full channel.
        """
        client = self._state._get_client()
        return await client.fetch_channel(self.id)  # type: ignore # This is explicit narrowing

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: An aware timestamp of when this channel was created in UTC."""
        return snowflake_time(self.id)


class AppCommandThread(Hashable):
    """Represents an application command partially resolved thread object.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two thread are equal.

        .. describe:: x != y

            Checks if two thread are not equal.

        .. describe:: hash(x)

            Returns the thread's hash.

        .. describe:: str(x)

            Returns the thread's name.

    Attributes
    -----------
    id: :class:`int`
        The ID of the thread.
    type: :class:`~discord.ChannelType`
        The type of thread.
    name: :class:`str`
        The name of the thread.
    parent_id: :class:`int`
        The parent text channel ID this thread belongs to.
    permissions: :class:`~discord.Permissions`
        The resolved permissions of the user who invoked
        the application command in that thread.
    guild_id: :class:`int`
        The guild ID this thread belongs to.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    invitable: :class:`bool`
        Whether non-moderators can add other non-moderators to this thread.
        This is always ``True`` for public threads.
    archiver_id: Optional[:class:`int`]
        The user's ID that archived this thread.
    auto_archive_duration: :class:`int`
        The duration in minutes until the thread is automatically archived due to inactivity.
        Usually a value of 60, 1440, 4320 and 10080.
    archive_timestamp: :class:`datetime.datetime`
        An aware timestamp of when the thread's archived status was last updated in UTC.
    """

    __slots__ = (
        'id',
        'type',
        'name',
        'permissions',
        'guild_id',
        'parent_id',
        'archived',
        'archiver_id',
        'auto_archive_duration',
        'archive_timestamp',
        'locked',
        'invitable',
        '_created_at',
        '_state',
    )

    def __init__(
        self,
        *,
        state: ConnectionState,
        data: PartialThread,
        guild_id: int,
    ):
        self._state: ConnectionState = state
        self.guild_id: int = guild_id
        self.id: int = int(data['id'])
        self.parent_id: int = int(data['parent_id'])
        self.type: ChannelType = try_enum(ChannelType, data['type'])
        self.name: str = data['name']
        self.permissions: Permissions = Permissions(int(data['permissions']))
        self._unroll_metadata(data['thread_metadata'])

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} name={self.name!r} archived={self.archived} type={self.type!r}>'

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~discord.Guild`]: The channel's guild, from cache, if found."""
        return self._state._get_guild(self.guild_id)

    def _unroll_metadata(self, data: ThreadMetadata) -> None:
        self.archived: bool = data['archived']
        self.archiver_id: Optional[int] = _get_as_snowflake(data, 'archiver_id')
        self.auto_archive_duration: ThreadArchiveDuration = data['auto_archive_duration']
        self.archive_timestamp: datetime = parse_time(data['archive_timestamp'])
        self.locked: bool = data.get('locked', False)
        self.invitable: bool = data.get('invitable', True)
        self._created_at: Optional[datetime] = parse_time(data.get('create_timestamp'))

    @property
    def parent(self) -> Optional[TextChannel]:
        """Optional[:class:`~discord.TextChannel`]: The parent channel this thread belongs to."""
        return self.guild.get_channel(self.parent_id)  # type: ignore

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the thread."""
        return f'<#{self.id}>'

    @property
    def created_at(self) -> Optional[datetime]:
        """An aware timestamp of when the thread was created in UTC.

        .. note::

            This timestamp only exists for threads created after 9 January 2022, otherwise returns ``None``.
        """
        return self._created_at

    def resolve(self) -> Optional[Thread]:
        """Resolves the application command channel to the appropriate channel
        from cache if found.

        Returns
        --------
        Optional[:class:`.abc.GuildChannel`]
            The resolved guild channel or ``None`` if not found in cache.
        """
        guild = self._state._get_guild(self.guild_id)
        if guild is not None:
            return guild.get_thread(self.id)
        return None

    async def fetch(self) -> Thread:
        """|coro|

        Fetches the partial channel to a full :class:`~discord.Thread`.

        Raises
        --------
        NotFound
            The thread was not found.
        Forbidden
            You do not have the permissions required to get a thread.
        HTTPException
            Retrieving the thread failed.

        Returns
        --------
        :class:`~discord.Thread`
            The full thread.
        """
        client = self._state._get_client()
        return await client.fetch_channel(self.id)  # type: ignore # This is explicit narrowing


class Argument:
    """Represents a application command argument.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`~discord.AppCommandOptionType`
        The type of argument.
    name: :class:`str`
        The name of the argument.
    description: :class:`str`
        The description of the argument.
    required: :class:`bool`
        Whether the argument is required.
    choices: List[:class:`Choice`]
        A list of choices for the command to choose from for this argument.
    parent: Union[:class:`AppCommand`, :class:`AppCommandGroup`]
        The parent application command that has this argument.
    """

    __slots__ = (
        'type',
        'name',
        'description',
        'required',
        'choices',
        'parent',
        '_state',
    )

    def __init__(
        self, *, parent: ApplicationCommandParent, data: ApplicationCommandOption, state: Optional[ConnectionState] = None
    ) -> None:
        self._state: Optional[ConnectionState] = state
        self.parent: ApplicationCommandParent = parent
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} type={self.type!r} required={self.required}>'

    def _from_data(self, data: ApplicationCommandOption) -> None:
        self.type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.required: bool = data.get('required', False)
        self.choices: List[Choice[Union[int, float, str]]] = [
            Choice(name=d['name'], value=d['value']) for d in data.get('choices', [])
        ]

    def to_dict(self) -> ApplicationCommandOption:
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'required': self.required,
            'choices': [choice.to_dict() for choice in self.choices],
            'options': [],
        }  # type: ignore # Type checker does not understand this literal.


class AppCommandGroup:
    """Represents a application command subcommand.

    .. versionadded:: 2.0

    Attributes
    ------------
    type: :class:`~discord.AppCommandOptionType`
        The type of subcommand.
    name: :class:`str`
        The name of the subcommand.
    description: :class:`str`
        The description of the subcommand.
    required: :class:`bool`
        Whether the subcommand is required.
    choices: List[:class:`Choice`]
        A list of choices for the command to choose from for this subcommand.
    arguments: List[:class:`Argument`]
        A list of arguments.
    parent: Union[:class:`AppCommand`, :class:`AppCommandGroup`]
        The parent application command.
    """

    __slots__ = (
        'type',
        'name',
        'description',
        'required',
        'choices',
        'arguments',
        'parent',
        '_state',
    )

    def __init__(
        self, *, parent: ApplicationCommandParent, data: ApplicationCommandOption, state: Optional[ConnectionState] = None
    ) -> None:
        self.parent: ApplicationCommandParent = parent
        self._state: Optional[ConnectionState] = state
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} type={self.type!r} required={self.required}>'

    def _from_data(self, data: ApplicationCommandOption) -> None:
        self.type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.required: bool = data.get('required', False)
        self.choices: List[Choice[Union[int, float, str]]] = [
            Choice(name=d['name'], value=d['value']) for d in data.get('choices', [])
        ]
        self.arguments: List[Argument] = [
            Argument(parent=self, state=self._state, data=d)
            for d in data.get('options', [])
            if is_app_command_argument_type(d['type'])
        ]

    def to_dict(self) -> 'ApplicationCommandOption':
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'required': self.required,
            'choices': [choice.to_dict() for choice in self.choices],
            'options': [arg.to_dict() for arg in self.arguments],
        }  # type: ignore # Type checker does not understand this literal.


def app_command_option_factory(
    parent: ApplicationCommandParent, data: ApplicationCommandOption, *, state: Optional[ConnectionState] = None
) -> Union[Argument, AppCommandGroup]:
    if is_app_command_argument_type(data['type']):
        return Argument(parent=parent, data=data, state=state)
    else:
        return AppCommandGroup(parent=parent, data=data, state=state)
