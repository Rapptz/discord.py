import aiohttp
import websockets  # type: ignore

from typing import Optional, Dict, Any, Union


class DiscordException(Exception):
    ...


class ClientException(DiscordException):
    ...


class NoMoreItems(DiscordException):
    ...


class GatewayNotFound(DiscordException):
    ...


def flatten_error_dict(d: Dict[str, Any], key: str = ...) -> Dict[str, Any]: ...


class HTTPException(DiscordException):
    response: aiohttp.ClientResponse
    text: str
    status: int
    code: int

    def __init__(self, response: aiohttp.ClientResponse, message: Union[str, Dict[str, Any]]) -> None: ...


class Forbidden(HTTPException):
    ...


class NotFound(HTTPException):
    ...


class InvalidArgument(ClientException):
    ...


class LoginFailure(ClientException):
    ...


class ConnectionClosed(ClientException):
    code: int
    reason: str
    shard_id: Optional[int]

    def __init__(self, original: websockets.exceptions.ConnectionClosed, *, shard_id: Optional[int]) -> None: ...


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

    def __init__(self, name: str, original: ImportError) -> None: ...
