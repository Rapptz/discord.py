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
from typing import Callable, Dict, List, Literal, Optional, TYPE_CHECKING, Tuple, Type, Union, overload


from .namespace import Namespace
from .models import AppCommand
from .commands import Command, ContextMenu, Group, _shorten
from .enums import AppCommandType
from .errors import CommandAlreadyRegistered, CommandNotFound, CommandSignatureMismatch
from ..errors import ClientException
from ..utils import MISSING

if TYPE_CHECKING:
    from ..types.interactions import ApplicationCommandInteractionData, ApplicationCommandInteractionDataOption
    from ..interactions import Interaction
    from ..client import Client
    from ..abc import Snowflake
    from .commands import ContextMenuCallback, CommandCallback, P, T

__all__ = ('CommandTree',)


class CommandTree:
    """Represents a container that holds application command information.

    Parameters
    -----------
    client: :class:`Client`
        The client instance to get application command information from.
    """

    def __init__(self, client: Client):
        self.client = client
        self._http = client.http
        self._state = client._connection
        self._state._command_tree = self
        self._guild_commands: Dict[int, Dict[str, Union[Command, Group]]] = {}
        self._global_commands: Dict[str, Union[Command, Group]] = {}
        # (name, guild_id, command_type): Command
        # The above two mappings can use this structure too but we need fast retrieval
        # by name and guild_id in the above case while here it isn't as important since
        # it's uncommon and N=5 anyway.
        self._context_menus: Dict[Tuple[str, Optional[int], int], ContextMenu] = {}

    async def fetch_commands(self, *, guild: Optional[Snowflake] = None) -> List[AppCommand]:
        """|coro|

        Fetches the application's current commands.

        If no guild is passed then global commands are fetched, otherwise
        the guild's commands are fetched instead.

        .. note::

            This includes context menu commands.

        Parameters
        -----------
        guild: Optional[:class:`abc.Snowflake`]
            The guild to fetch the commands from. If not passed then global commands
            are fetched instead.

        Raises
        -------
        HTTPException
            Fetching the commands failed.
        ClientException
            The application ID could not be found.

        Returns
        --------
        List[:class:`~discord.app_commands.AppCommand`]
            The application's commands.
        """
        if self.client.application_id is None:
            raise ClientException('Client does not have an application ID set')

        if guild is None:
            commands = await self._http.get_global_commands(self.client.application_id)
        else:
            commands = await self._http.get_guild_commands(self.client.application_id, guild.id)

        return [AppCommand(data=data, state=self._state) for data in commands]

    def add_command(
        self,
        command: Union[Command, ContextMenu, Group],
        /,
        *,
        guild: Optional[Snowflake] = None,
        override: bool = False,
    ):
        """Adds an application command to the tree.

        This only adds the command locally -- in order to sync the commands
        and enable them in the client, :meth:`sync` must be called.

        The root parent of the command is added regardless of the type passed.

        Parameters
        -----------
        command: Union[:class:`Command`, :class:`Group`]
            The application command or group to add.
        guild: Optional[:class:`abc.Snowflake`]
            The guild to add the command to. If not given then it
            becomes a global command instead.
        override: :class:`bool`
            Whether to override a command with the same name. If ``False``
            an exception is raised. Default is ``False``.

        Raises
        --------
        ~discord.CommandAlreadyRegistered
            The command was already registered and no override was specified.
        TypeError
            The application command passed is not a valid application command.
        ValueError
            The maximum number of commands was reached globally or for that guild.
            This is currently 100 for slash commands and 5 for context menu commands.
        """

        if isinstance(command, ContextMenu):
            guild_id = None if guild is None else guild.id
            type = command.type.value
            key = (command.name, guild_id, type)
            found = key in self._context_menus
            if found and not override:
                raise CommandAlreadyRegistered(command.name, guild_id)

            total = sum(1 for _, g, t in self._context_menus if g == guild_id and t == type)
            if total + found > 5:
                raise ValueError('maximum number of context menu commands exceeded (5)')
            self._context_menus[key] = command
            return
        elif not isinstance(command, (Command, Group)):
            raise TypeError(f'Expected a application command, received {command.__class__!r} instead')

        # todo: validate application command groups having children (required)

        root = command.root_parent or command
        name = root.name
        if guild is not None:
            commands = self._guild_commands.setdefault(guild.id, {})
            found = name in commands
            if found and not override:
                raise CommandAlreadyRegistered(name, guild.id)
            if len(commands) + found > 100:
                raise ValueError('maximum number of slash commands exceeded (100)')
            commands[name] = root
        else:
            found = name in self._global_commands
            if found and not override:
                raise CommandAlreadyRegistered(name, None)
            if len(self._global_commands) + found > 100:
                raise ValueError('maximum number of slash commands exceeded (100)')
            self._global_commands[name] = root

    @overload
    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user] = ...,
    ) -> Optional[ContextMenu]:
        ...

    @overload
    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> Optional[Union[Command, Group]]:
        ...

    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Optional[Union[Command, ContextMenu, Group]]:
        """Removes an application command from the tree.

        This only removes the command locally -- in order to sync the commands
        and remove them in the client, :meth:`sync` must be called.

        Parameters
        -----------
        command: :class:`str`
            The name of the root command to remove.
        guild: Optional[:class:`abc.Snowflake`]
            The guild to remove the command from. If not given then it
            removes a global command instead.
        type: :class:`AppCommandType`
            The type of command to remove. Defaults to :attr:`AppCommandType.chat_input`,
            i.e. slash commands.

        Returns
        ---------
        Optional[Union[:class:`Command`, :class:`ContextMenu`, :class:`Group`]]
            The application command that got removed.
            If nothing was removed then ``None`` is returned instead.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                return self._global_commands.pop(command, None)
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return None
                else:
                    return commands.pop(command, None)
        elif type in (AppCommandType.user, AppCommandType.message):
            guild_id = None if guild is None else guild.id
            key = (command, guild_id, type.value)
            return self._context_menus.pop(key, None)

    @overload
    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user] = ...,
    ) -> Optional[ContextMenu]:
        ...

    @overload
    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> Optional[Union[Command, Group]]:
        ...

    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Optional[Union[Command, ContextMenu, Group]]:
        """Gets a application command from the tree.

        Parameters
        -----------
        command: :class:`str`
            The name of the root command to get.
        guild: Optional[:class:`abc.Snowflake`]
            The guild to get the command from. If not given then it
            gets a global command instead.
        type: :class:`AppCommandType`
            The type of command to get. Defaults to :attr:`AppCommandType.chat_input`,
            i.e. slash commands.

        Returns
        ---------
        Optional[Union[:class:`Command`, :class:`ContextMenu`, :class:`Group`]]
            The application command that was found.
            If nothing was found then ``None`` is returned instead.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                return self._global_commands.get(command)
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return None
                else:
                    return commands.get(command)
        elif type in (AppCommandType.user, AppCommandType.message):
            guild_id = None if guild is None else guild.id
            key = (command, guild_id, type.value)
            return self._context_menus.get(key)

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user] = ...,
    ) -> List[ContextMenu]:
        ...

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> List[Union[Command, Group]]:
        ...

    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Union[List[Union[Command, Group]], List[ContextMenu]]:
        """Gets all application commands from the tree.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to get the commands from. If not given then it
            gets all global commands instead.
        type: :class:`AppCommandType`
            The type of commands to get. Defaults to :attr:`AppCommandType.chat_input`,
            i.e. slash commands.

        Returns
        ---------
        Union[List[:class:`ContextMenu`], List[Union[:class:`Command`, :class:`Group`]]
            The application commands from the tree.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                return list(self._global_commands.values())
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return []
                else:
                    return list(commands.values())
        else:
            guild_id = None if guild is None else guild.id
            value = type.value
            return [command for ((_, g, t), command) in self._context_menus.items() if g == guild_id and t == value]

    def _get_all_commands(self, *, guild: Optional[Snowflake] = None) -> List[Union[Command, Group, ContextMenu]]:
        if guild is None:
            base: List[Union[Command, Group, ContextMenu]] = list(self._global_commands.values())
            base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g is None)
            return base
        else:
            try:
                commands = self._guild_commands[guild.id]
            except KeyError:
                return [cmd for ((_, g, _), cmd) in self._context_menus.items() if g is None]
            else:
                base: List[Union[Command, Group, ContextMenu]] = list(commands.values())
                guild_id = guild.id
                base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g == guild_id)
                return base

    def command(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        guild: Optional[Snowflake] = None,
    ) -> Callable[[CommandCallback[Group, P, T]], Command[Group, P, T]]:
        """Creates an application command directly under this tree.

        Parameters
        ------------
        name: :class:`str`
            The name of the application command. If not given, it defaults to a lower-case
            version of the callback name.
        description: :class:`str`
            The description of the application command. This shows up in the UI to describe
            the application command. If not given, it defaults to the first line of the docstring
            of the callback shortened to 100 characters.
        guild: Optional[:class:`.abc.Snowflake`]
            The guild to add the command to. If not given then it
            becomes a global command instead.
        """

        def decorator(func: CommandCallback[Group, P, T]) -> Command[Group, P, T]:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('command function must be a coroutine function')

            if description is MISSING:
                if func.__doc__ is None:
                    desc = '...'
                else:
                    desc = _shorten(func.__doc__)
            else:
                desc = description

            command = Command(
                name=name if name is not MISSING else func.__name__,
                description=desc,
                callback=func,
                parent=None,
            )
            self.add_command(command, guild=guild)
            return command

        return decorator

    def context_menu(
        self, *, name: str = MISSING, guild: Optional[Snowflake] = None
    ) -> Callable[[ContextMenuCallback], ContextMenu]:
        """Creates a application command context menu from a regular function directly under this tree.

        This function must have a signature of :class:`~discord.Interaction` as its first parameter
        and taking either a :class:`~discord.Member`, :class:`~discord.User`, or :class:`~discord.Message`,
        or a :obj:`typing.Union` of ``Member`` and ``User`` as its second parameter.

        Examples
        ---------

        .. code-block:: python3

            @app_commands.context_menu()
            async def react(interaction: discord.Interaction, message: discord.Message):
                await interaction.response.send_message('Very cool message!', ephemeral=True)

            @app_commands.context_menu()
            async def ban(interaction: discord.Interaction, user: discord.Member):
                await interaction.response.send_message(f'Should I actually ban {user}...', ephemeral=True)

        Parameters
        ------------
        name: :class:`str`
            The name of the context menu command. If not given, it defaults to a title-case
            version of the callback name. Note that unlike regular slash commands this can
            have spaces and upper case characters in the name.
        guild: Optional[:class:`.abc.Snowflake`]
            The guild to add the command to. If not given then it
            becomes a global command instead.
        """

        def decorator(func: ContextMenuCallback) -> ContextMenu:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('context menu function must be a coroutine function')

            context_menu = ContextMenu._from_decorator(func, name=name)
            self.add_command(context_menu, guild=guild)
            return context_menu

        return decorator

    async def sync(self, *, guild: Optional[Snowflake]) -> List[AppCommand]:
        """|coro|

        Syncs the application commands to Discord.

        This must be called for the application commands to show up.

        Global commands take up to 1-hour to propagate but guild
        commands propagate instantly.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to sync the commands to. If ``None`` then it
            syncs all global commands instead.

        Raises
        -------
        HTTPException
            Syncing the commands failed.
        ClientException
            The client does not have an application ID.

        Returns
        --------
        List[:class:`~discord.AppCommand`]
            The application's commands that got synced.
        """

        if self.client.application_id is None:
            raise ClientException('Client does not have an application ID set')

        commands = self._get_all_commands(guild=guild)
        payload = [command.to_dict() for command in commands]
        if guild is None:
            data = await self._http.bulk_upsert_global_commands(self.client.application_id, payload=payload)
        else:
            data = await self._http.bulk_upsert_guild_commands(self.client.application_id, guild.id, payload=payload)

        return [AppCommand(data=d, state=self._state) for d in data]

    def _from_interaction(self, interaction: Interaction):
        async def wrapper():
            try:
                await self.call(interaction)
            except Exception as e:
                print(f'Error:', e)

        self.client.loop.create_task(wrapper(), name='CommandTree-invoker')

    async def _call_context_menu(self, interaction: Interaction, data: ApplicationCommandInteractionData, type: int):
        name = data['name']
        guild_id = interaction.guild_id
        ctx_menu = self._context_menus.get((name, guild_id, type))
        if ctx_menu is None:
            raise CommandNotFound(name, [], AppCommandType(type))

        resolved = Namespace._get_resolved_items(interaction, data.get('resolved', {}))
        # This will always work at runtime
        value = resolved.get(data.get('target_id'))  # type: ignore
        if ctx_menu.type.value != type:
            raise CommandSignatureMismatch(ctx_menu)

        if value is None:
            raise RuntimeError('This should not happen if Discord sent well-formed data.')

        # I assume I don't have to type check here.
        await ctx_menu._invoke(interaction, value)

    async def call(self, interaction: Interaction):
        """|coro|

        Given an :class:`~discord.Interaction`, calls the matching
        application command that's being invoked.

        This is usually called automatically by the library.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction to dispatch from.

        Raises
        --------
        CommandNotFound
            The application command referred to could not be found.
        CommandSignatureMismatch
            The interaction data referred to a parameter that was not found in the
            application command definition.
        """
        data: ApplicationCommandInteractionData = interaction.data  # type: ignore
        type = data.get('type', 1)
        if type != 1:
            # Context menu command...
            await self._call_context_menu(interaction, data, type)
            return

        parents: List[str] = []
        name = data['name']
        command = self._global_commands.get(name)
        if interaction.guild_id:
            try:
                guild_commands = self._guild_commands[interaction.guild_id]
            except KeyError:
                pass
            else:
                command = guild_commands.get(name) or command

        # If it's not found at this point then it's not gonna be found at any point
        if command is None:
            raise CommandNotFound(name, parents)

        # This could be done recursively but it'd be a bother due to the state needed
        # to be tracked above like the parents, the actual command type, and the
        # resulting options we care about
        searching = True
        options: List[ApplicationCommandInteractionDataOption] = data.get('options', [])
        while searching:
            for option in options:
                # Find subcommands
                if option.get('type', 0) in (1, 2):
                    parents.append(name)
                    name = option['name']
                    command = command._get_internal_command(name)
                    if command is None:
                        raise CommandNotFound(name, parents)
                    options = option.get('options', [])
                    break
                else:
                    searching = False
                    break
            else:
                break

        if isinstance(command, Group):
            # Right now, groups can't be invoked. This is a Discord limitation in how they
            # do slash commands. So if we're here and we have a Group rather than a Command instance
            # then something in the code is out of date from the data that Discord has.
            raise CommandSignatureMismatch(command)

        # At this point options refers to the arguments of the command
        # and command refers to the class type we care about
        namespace = Namespace(interaction, data.get('resolved', {}), options)
        await command._invoke_with_namespace(interaction, namespace)
