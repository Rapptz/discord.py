from discord.errors import DiscordException
from discord import Permissions
from inspect import Parameter

from .cooldowns import Cooldown

from typing import Any, Optional, List, Tuple

class CommandError(DiscordException):
    def __init__(self, message: Optional[str] = ..., *args: Any) -> None: ...

class ConversionError(DiscordException):
    converter: Any
    original: Exception

    def __init__(self, converter: Any, original: Exception) -> None: ...

class UserInputError(CommandError): ...

class CommandNotFound(CommandError): ...

class MissingRequiredArgument(UserInputError):
    param: Parameter

    def __init__(self, param: Parameter) -> None: ...

class TooManyArguments(UserInputError): ...

class BadArgument(UserInputError): ...

class CheckFailure(CommandError): ...

class PrivateMessageOnly(CheckFailure): ...

class NoPrivateMessage(CheckFailure): ...

class NotOwner(CheckFailure): ...

class DisabledCommand(CommandError): ...

class CommandInvokeError(CommandError):
    original: Exception

    def __init__(self, e: Exception) -> None: ...

class CommandOnCooldown(CommandError):
    cooldown: Cooldown
    retry_after: float

    def __init__(self, cooldown: Cooldown, retry_after: float) -> None: ...

class MissingPermissions(CheckFailure):
    missing_perms: List[Permissions]

    def __init__(self, missing_perms: List[Permissions], *args: Any) -> None: ...

class BotMissingPermissions(CheckFailure):
    missing_perms: List[Permissions]

    def __init__(self, missing_perms: List[Permissions], *args: Any) -> None: ...

class BadUnionArgument(UserInputError):
    param: Parameter
    converters: Tuple[Any, ...]
    errors: List[CommandError]

    def __init__(self, param: Parameter, converters: Tuple[Any, ...], errors: List[CommandError]) -> None: ...

class ArgumentParsingError(UserInputError): ...

class UnexpectedQuoteError(ArgumentParsingError):
    quote: str

    def __init__(self, quote: str) -> None: ...

class InvalidEndOfQuotedStringError(ArgumentParsingError):
    char: str

    def __init__(self, char: str) -> None: ...

class ExpectedClosingQuoteError(ArgumentParsingError):
    close_quote: str

    def __init__(self, close_quote: str) -> None: ...
