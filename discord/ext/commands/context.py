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

import re
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Collection,
    Dict,
    Generic,
    List,
    Optional,
    overload,
    Sequence,
    TypeVar,
    Union,
)

import discord.abc
import discord.utils
from discord.message import Message
from discord.utils import MISSING

from ._types import BotT

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeGuard

    from discord.abc import MessageableChannel
    from discord.commands import MessageCommand
    from discord.file import File
    from discord.guild import Guild
    from discord.member import Member
    from discord.mentions import AllowedMentions
    from discord.state import ConnectionState
    from discord.sticker import GuildSticker, StickerItem
    from discord.user import ClientUser, User
    from discord.voice_client import VoiceProtocol

    from .cog import Cog
    from .core import Command
    from .parameters import Parameter
    from .view import StringView

# fmt: off
__all__ = (
    'Context',
)
# fmt: on


T = TypeVar('T')
CogT = TypeVar('CogT', bound="Cog")

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


def is_cog(obj: Any) -> TypeGuard[Cog]:
    return hasattr(obj, '__cog_commands__')


class Context(discord.abc.Messageable, Generic[BotT]):
    r"""Represents the context in which a command is being invoked under.

    This class contains a lot of meta data to help you understand more about
    the invocation context. This class is not created manually and is instead
    passed around to commands as the first parameter.

    This class implements the :class:`~discord.abc.Messageable` ABC.

    Attributes
    -----------
    message: :class:`.Message`
        The message that triggered the command being executed.
    bot: :class:`.Bot`
        The bot that contains the command being executed.
    args: :class:`list`
        The list of transformed arguments that were passed into the command.
        If this is accessed during the :func:`.on_command_error` event
        then this list could be incomplete.
    kwargs: :class:`dict`
        A dictionary of transformed arguments that were passed into the command.
        Similar to :attr:`args`\, if this is accessed in the
        :func:`.on_command_error` event then this dict could be incomplete.
    current_parameter: Optional[:class:`Parameter`]
        The parameter that is currently being inspected and converted.
        This is only of use for within converters.

        .. versionadded:: 2.0
    current_argument: Optional[:class:`str`]
        The argument string of the :attr:`current_parameter` that is currently being converted.
        This is only of use for within converters.

        .. versionadded:: 2.0
    prefix: Optional[:class:`str`]
        The prefix that was used to invoke the command.
    command: Optional[:class:`Command`]
        The command that is being invoked currently.
    invoked_with: Optional[:class:`str`]
        The command name that triggered this invocation. Useful for finding out
        which alias called the command.
    invoked_parents: List[:class:`str`]
        The command names of the parents that triggered this invocation. Useful for
        finding out which aliases called the command.

        For example in commands ``?a b c test``, the invoked parents are ``['a', 'b', 'c']``.

        .. versionadded:: 1.7

    invoked_subcommand: Optional[:class:`Command`]
        The subcommand that was invoked.
        If no valid subcommand was invoked then this is equal to ``None``.
    subcommand_passed: Optional[:class:`str`]
        The string that was attempted to call a subcommand. This does not have
        to point to a valid registered subcommand and could just point to a
        nonsense string. If nothing was passed to attempt a call to a
        subcommand then this is set to ``None``.
    command_failed: :class:`bool`
        A boolean that indicates if the command failed to be parsed, checked,
        or invoked.
    """

    def __init__(
        self,
        *,
        message: Message,
        bot: BotT,
        view: StringView,
        args: List[Any] = MISSING,
        kwargs: Dict[str, Any] = MISSING,
        prefix: Optional[str] = None,
        command: Optional[Command[Any, ..., Any]] = None,
        invoked_with: Optional[str] = None,
        invoked_parents: List[str] = MISSING,
        invoked_subcommand: Optional[Command[Any, ..., Any]] = None,
        subcommand_passed: Optional[str] = None,
        command_failed: bool = False,
        current_parameter: Optional[Parameter] = None,
        current_argument: Optional[str] = None,
    ):
        self.message: Message = message
        self.bot: BotT = bot
        self.args: List[Any] = args or []
        self.kwargs: Dict[str, Any] = kwargs or {}
        self.prefix: Optional[str] = prefix
        self.command: Optional[Command[Any, ..., Any]] = command
        self.view: StringView = view
        self.invoked_with: Optional[str] = invoked_with
        self.invoked_parents: List[str] = invoked_parents or []
        self.invoked_subcommand: Optional[Command[Any, ..., Any]] = invoked_subcommand
        self.subcommand_passed: Optional[str] = subcommand_passed
        self.command_failed: bool = command_failed
        self.current_parameter: Optional[Parameter] = current_parameter
        self.current_argument: Optional[str] = current_argument
        self._state: ConnectionState = self.message._state

    async def invoke(self, command: Command[CogT, P, T], /, *args: P.args, **kwargs: P.kwargs) -> T:
        r"""|coro|

        Calls a command with the arguments given.

        This is useful if you want to just call the callback that a
        :class:`.Command` holds internally.

        .. note::

            This does not handle converters, checks, cooldowns, pre-invoke,
            or after-invoke hooks in any matter. It calls the internal callback
            directly as-if it was a regular function.

            You must take care in passing the proper arguments when
            using this function.

        .. versionchanged:: 2.0

            ``command`` parameter is now positional-only.

        Parameters
        -----------
        command: :class:`.Command`
            The command that is going to be called.
        \*args
            The arguments to use.
        \*\*kwargs
            The keyword arguments to use.

        Raises
        -------
        TypeError
            The command argument to invoke is missing.
        """
        return await command(self, *args, **kwargs)

    async def reinvoke(self, *, call_hooks: bool = False, restart: bool = True) -> None:
        """|coro|

        Calls the command again.

        This is similar to :meth:`~.Context.invoke` except that it bypasses
        checks, cooldowns, and error handlers.

        .. note::

            If you want to bypass :exc:`.UserInputError` derived exceptions,
            it is recommended to use the regular :meth:`~.Context.invoke`
            as it will work more naturally. After all, this will end up
            using the old arguments the user has used and will thus just
            fail again.

        Parameters
        ------------
        call_hooks: :class:`bool`
            Whether to call the before and after invoke hooks.
        restart: :class:`bool`
            Whether to start the call chain from the very beginning
            or where we left off (i.e. the command that caused the error).
            The default is to start where we left off.

        Raises
        -------
        ValueError
            The context to reinvoke is not valid.
        """
        cmd = self.command
        view = self.view
        if cmd is None:
            raise ValueError('This context is not valid.')

        # some state to revert to when we're done
        index, previous = view.index, view.previous
        invoked_with = self.invoked_with
        invoked_subcommand = self.invoked_subcommand
        invoked_parents = self.invoked_parents
        subcommand_passed = self.subcommand_passed

        if restart:
            to_call = cmd.root_parent or cmd
            view.index = len(self.prefix or '')
            view.previous = 0
            self.invoked_parents = []
            self.invoked_with = view.get_word()  # advance to get the root command
        else:
            to_call = cmd

        try:
            await to_call.reinvoke(self, call_hooks=call_hooks)
        finally:
            self.command = cmd
            view.index = index
            view.previous = previous
            self.invoked_with = invoked_with
            self.invoked_subcommand = invoked_subcommand
            self.invoked_parents = invoked_parents
            self.subcommand_passed = subcommand_passed

    @property
    def valid(self) -> bool:
        """:class:`bool`: Checks if the invocation context is valid to be invoked with."""
        return self.prefix is not None and self.command is not None

    async def _get_channel(self) -> discord.abc.Messageable:
        return self.channel

    @property
    def clean_prefix(self) -> str:
        """:class:`str`: The cleaned up invoke prefix. i.e. mentions are ``@name`` instead of ``<@id>``.

        .. versionadded:: 2.0
        """
        if self.prefix is None:
            return ''

        user = self.me
        # this breaks if the prefix mention is not the bot itself but I
        # consider this to be an *incredibly* strange use case. I'd rather go
        # for this common use case rather than waste performance for the
        # odd one.
        pattern = re.compile(r"<@!?%s>" % user.id)
        return pattern.sub("@%s" % user.display_name.replace('\\', r'\\'), self.prefix)

    @property
    def cog(self) -> Optional[Cog]:
        """Optional[:class:`.Cog`]: Returns the cog associated with this context's command. None if it does not exist."""

        if self.command is None:
            return None
        return self.command.cog

    @discord.utils.cached_property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`.Guild`]: Returns the guild associated with this context's command. None if not available."""
        return self.message.guild

    @discord.utils.cached_property
    def channel(self) -> MessageableChannel:
        """Union[:class:`.abc.Messageable`]: Returns the channel associated with this context's command.
        Shorthand for :attr:`.Message.channel`.
        """
        return self.message.channel

    @discord.utils.cached_property
    def author(self) -> Union[User, Member]:
        """Union[:class:`~discord.User`, :class:`.Member`]:
        Returns the author associated with this context's command. Shorthand for :attr:`.Message.author`
        """
        return self.message.author

    @discord.utils.cached_property
    def me(self) -> Union[Member, ClientUser]:
        """Union[:class:`.Member`, :class:`.ClientUser`]:
        Similar to :attr:`.Guild.me` except it may return the :class:`.ClientUser` in private message contexts.
        """
        # bot.user will never be None at this point.
        return self.guild.me if self.guild is not None else self.bot.user  # type: ignore

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        r"""Optional[:class:`.VoiceProtocol`]: A shortcut to :attr:`.Guild.voice_client`\, if applicable."""
        g = self.guild
        return g.voice_client if g else None

    async def send_help(self, *args: Any) -> Any:
        """send_help(entity=<bot>)

        |coro|

        Shows the help command for the specified entity if given.
        The entity can be a command or a cog.

        If no entity is given, then it'll show help for the
        entire bot.

        If the entity is a string, then it looks up whether it's a
        :class:`Cog` or a :class:`Command`.

        .. note::

            Due to the way this function works, instead of returning
            something similar to :meth:`~.commands.HelpCommand.command_not_found`
            this returns :class:`None` on bad input or no help command.

        Parameters
        ------------
        entity: Optional[Union[:class:`Command`, :class:`Cog`, :class:`str`]]
            The entity to show help for.

        Returns
        --------
        Any
            The result of the help command, if any.
        """
        from .core import Command, Group, wrap_callback
        from .errors import CommandError

        bot = self.bot
        cmd = bot.help_command

        if cmd is None:
            return None

        cmd = cmd.copy()
        cmd.context = self

        if len(args) == 0:
            await cmd.prepare_help_command(self, None)
            mapping = cmd.get_bot_mapping()
            injected = wrap_callback(cmd.send_bot_help)
            try:
                return await injected(mapping)
            except CommandError as e:
                await cmd.on_help_command_error(self, e)
                return None

        entity = args[0]
        if isinstance(entity, str):
            entity = bot.get_cog(entity) or bot.get_command(entity)

        if entity is None:
            return None

        try:
            entity.qualified_name
        except AttributeError:
            # if we're here then it's not a cog, group, or command.
            return None

        await cmd.prepare_help_command(self, entity.qualified_name)

        try:
            if is_cog(entity):
                injected = wrap_callback(cmd.send_cog_help)
                return await injected(entity)
            elif isinstance(entity, Group):
                injected = wrap_callback(cmd.send_group_help)
                return await injected(entity)
            elif isinstance(entity, Command):
                injected = wrap_callback(cmd.send_command_help)
                return await injected(entity)
            else:
                return None
        except CommandError as e:
            await cmd.on_help_command_error(self, e)

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        mention_author: bool = ...,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> Message:
        ...

    @discord.utils.copy_doc(Message.reply)
    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        return await self.message.reply(content, **kwargs)

    @discord.utils.copy_doc(Message.message_commands)
    def message_commands(
        self,
        query: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        command_ids: Optional[Collection[int]] = None,
        application: Optional[discord.abc.Snowflake] = None,
        with_applications: bool = True,
    ) -> AsyncIterator[MessageCommand]:
        return self.message.message_commands(
            query, limit=limit, command_ids=command_ids, with_applications=with_applications, application=application
        )
