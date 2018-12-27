import aiohttp
import asyncio
import datetime

from .abc import User as ABCUser
from .guild import Guild
from .channel import TextChannel
from .embeds import Embed
from .file import File
from .message import Message
from .types import RawWebhookDict
from .state import ConnectionState
from .user import User

from typing import Any, Optional, Union, Dict, List, Tuple, Coroutine, ClassVar, BinaryIO, TypeVar, Type, overload

class WebhookAdapter:
    BASE: ClassVar[str]

    webhook: Webhook

    def request(self, verb: str, url: str, payload: Optional[Dict[str, Any]] = ...,
                multipart: Optional[Dict[str, Any]] = ...) -> Any: ...

    def delete_webhook(self) -> Any: ...

    def edit_webhook(self, **payload: Any) -> Any: ...

    def handle_execution_response(self, data: Any, *, wait: bool) -> Any: ...

    def execute_webhook(self, *, payload: Dict[str, Any], wait: bool = ..., file: Optional[Tuple[str, BinaryIO, str]] = ...,
                        files: Optional[List[Tuple[str, BinaryIO, str]]] = ...) -> Any: ...


class AsyncWebhookAdapter(WebhookAdapter):
    session: aiohttp.ClientSession
    loop: asyncio.AbstractEventLoop

    def __init__(self, session: aiohttp.ClientSession) -> None: ...

    async def request(self, verb: str, url: str, payload: Optional[Dict[str, Any]] = ...,
                      multipart: Optional[Dict[str, Any]] = ...) -> Any: ...

    async def handle_execution_response(self, data: Any, *, wait: bool) -> Message: ...


class RequestsWebhookAdapter(WebhookAdapter):
    session: Any

    def __init__(self, session: Optional[Any] = ..., *, sleep: bool = ...) -> None: ...

    def request(self, verb: str, url: str, payload: Optional[Dict[str, Any]] = ..., multipart: Optional[Dict[str, Any]] = ...) -> Any: ...

    def handle_execution_response(self, response: Any, *, wait: bool) -> Message: ...

_T = TypeVar('_T', bound=Webhook)

class Webhook:
    id: int
    token: str
    channel_id: Optional[int]
    guild_id: Optional[int]
    name: Optional[str]
    avatar: Optional[str]
    user: Optional[ABCUser]

    def __repr__(self) -> str: ...

    @property
    def url(self) -> str: ...

    @classmethod
    def partial(cls: Type[_T], id: int, token: str, *, adapter: WebhookAdapter) -> _T: ...

    @classmethod
    def from_url(cls: Type[_T], url: str, *, adapter: WebhookAdapter) -> _T: ...

    @classmethod
    def from_state(cls: Type[_T], data: RawWebhookDict, state: ConnectionState) -> _T: ...

    @property
    def guild(self) -> Optional[Guild]: ...

    @property
    def channel(self) -> Optional[TextChannel]: ...

    @property
    def created_at(self) -> datetime.datetime: ...

    @property
    def avatar_url(self) -> str: ...

    def avatar_url_as(self, *, format: Optional[str] = ..., size: int = ...) -> str: ...

    def delete(self) -> Coroutine[Any, Any, None]: ...

    def edit(self, **kwargs: Any) -> Union[RawWebhookDict, Coroutine[Any, Any, RawWebhookDict]]: ...

    @overload
    def send(self, content: Optional[str] = ..., *, wait: bool = ..., username: Optional[str] = ...,
             avatar_url: Optional[str] = ..., tts: bool = ..., file: Optional[File] = ...,
             embed: Optional[Embed] = ...) -> Union[Message, Coroutine[Any, Any, Message]]: ...

    @overload
    def send(self, content: Optional[str] = ..., *, wait: bool = ..., username: Optional[str] = ...,
             avatar_url: Optional[str] = ..., tts: bool = ..., files: Optional[List[File]] = ...,
             embed: Optional[Embed] = ...) -> Union[Message, Coroutine[Any, Any, Message]]: ...

    @overload
    def send(self, content: Optional[str] = ..., *, wait: bool = ..., username: Optional[str] = ...,
             avatar_url: Optional[str] = ..., tts: bool = ..., file: Optional[File] = ...,
             embeds: Optional[List[Embed]] = ...) -> Union[Message, Coroutine[Any, Any, Message]]: ...

    @overload
    def send(self, content: Optional[str] = ..., *, wait: bool = ..., username: Optional[str] = ...,
             avatar_url: Optional[str] = ..., tts: bool = ..., files: Optional[List[File]] = ...,
             embeds: Optional[List[Embed]] = ...) -> Union[Message, Coroutine[Any, Any, Message]]: ...

    def execute(self, *args: Any, **kwargs: Any) -> Any: ...
