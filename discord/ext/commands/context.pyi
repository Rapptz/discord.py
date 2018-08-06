from typing import Any, Optional, List, Dict, Union

import discord

from .core import Command
from .bot import Bot

class Context(discord.abc.Messageable):
    message: discord.Message
    bot: Bot
    args: List[Any]
    kwargs: Dict[str, Any]
    prefix: str
    command: Command
    invoked_with: Optional[str]
    invoked_subcommand: Optional[Command]
    subcommand_passed: Optional[str]
    command_failed: bool

    async def invoke(self, command: Command, *args: Any, **kwargs: Any) -> Any: ...

    async def reinvoke(self, *, call_hooks: bool = ..., restart: bool = ...) -> None: ...

    @property
    def valid(self) -> bool: ...

    @property
    def cog(self) -> Optional[Any]: ...

    @property
    def guild(self) -> Optional[discord.Guild]: ...

    @property
    def channel(self) -> Union[discord.TextChannel, discord.DMChannel, discord.GroupChannel]: ...

    @property
    def author(self) -> Union[discord.User, discord.Member]: ...

    @property
    def me(self) -> Union[discord.Member, discord.ClientUser]: ...

    @property
    def voice_client(self) -> Optional[discord.VoiceClient]: ...
