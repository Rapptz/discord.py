from discord.errors import ClientException, DiscordException
from discord import Permissions, abc
from inspect import Parameter

from .cooldowns import Cooldown, BucketType

from typing import Any, Optional, Union, List, Tuple

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

class CheckAnyFailure(CheckFailure): ...

class PrivateMessageOnly(CheckFailure): ...

class NoPrivateMessage(CheckFailure):
    def __init__(self, message: Optional[str] = ...) -> None: ...

class NotOwner(CheckFailure): ...

class DisabledCommand(CommandError): ...

class CommandInvokeError(CommandError):
    original: Exception

    def __init__(self, e: Exception) -> None: ...

class CommandOnCooldown(CommandError):
    cooldown: Cooldown
    retry_after: float

    def __init__(self, cooldown: Cooldown, retry_after: float) -> None: ...

class MaxConcurrencyReached(CommandError):
    number: int
    per: BucketType

    def __init__(self, number: int, per: BucketType) -> None: ...

class MissingRole(CheckFailure):
    missing_role: Union[str, int]

    def __init__(self, missing_role: Union[str, int]) -> None: ...

class BotMissingRole(CheckFailure):
    missing_role: Union[str, int]

    def __init__(self, missing_role: Union[str, int]) -> None: ...

class MissingAnyRole(CheckFailure):
    missing_roles: List[Union[str, int]]

    def __init__(self, missing_roles: List[Union[str, int]]) -> None: ...

class BotMissingAnyRole(CheckFailure):
    missing_roles: List[Union[str, int]]

    def __init__(self, missing_roles: List[Union[str, int]]) -> None: ...

class NSFWChannelRequired(CheckFailure):
    channel: abc.GuildChannel

    def __init__(self, channel: abc.GuildChannel) -> None: ...

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

class ExtensionError(DiscordException):
    name: str

class ExtensionAlreadyLoaded(ExtensionError):
    def __init__(self, name: str) -> None: ...

class ExtensionNotLoaded(ExtensionError):
    def __init__(self, name: str) -> None: ...

class NoEntryPointError(ExtensionError):
    def __init__(self, name: str) -> None: ...

class ExtensionFailed(ExtensionError):
    original: Exception

    def __init__(self, name: str, original: Exception) -> None: ...

class ExtensionNotFound(ExtensionError):
    original: ImportError

    def __init__(self, name: str, original: Optional[ImportError] = ...) -> None: ...

class CommandRegistrationError(ClientException):
    alias_conflict: bool

    def __init__(self, name: str, *, alias_conflict: bool = ...) -> None: ...
