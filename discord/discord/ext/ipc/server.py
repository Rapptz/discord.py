from __future__ import annotations

import asyncio
import logging

from aiohttp import WSMessage
from .errors import *
from .objects import ClientPayload

from typing import TYPE_CHECKING, Any,  Optional, Callable, ClassVar, TypeVar, Dict, Union, Type
from aiohttp.web import WebSocketResponse, Application, AppRunner, TCPSite, Request
from aiohttp.web_urldispatcher import Handler
from discord.ext.commands import Bot, AutoShardedBot, Cog

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, TypeAlias
    
    P = ParamSpec('P')
    T = TypeVar('T')
    
    RouteFunc: TypeAlias = Callable[P, T]

class Server:
    """|class|
    
    The inter-process communication server. Usually used on the bot process for receiving
    requests from the client.

    Parameters:
    ----------
    bot: :class:`discord.ext.commands.Bot`
        Your bot instance
    host: :str:`str`
        The IP adress to start the server (the default is `127.0.0.1`).
    secret_key: :str:`str`
        Used for authentication when handling requests.
    standard_port: :str:`int`
        The port to run the standard server (the default is `1025`)
    multicast_port: :int:`int`
        The port to run the multicasting server (the default is `20000`)
    do_multicast: :bool:`bool`
        Should the multicasting be allowed (the default is `True`)
    """

    endpoints: ClassVar[Dict[str, Tuple[RouteFunc, Type[ClientPayload]]]] = {}

    def __init__(
        self, 
        bot: Union[Bot, AutoShardedBot], 
        host: str = "127.0.0.1", 
        secret_key: Union[str, None] = None, 
        standard_port: int = 1025,
        multicast_port: int = 20000,
        do_multicast: bool = True
    ) -> None:
        self.bot = bot
        self.host = host
        self.secret_key = secret_key
        self.standard_port = standard_port
        self.multicast_port = multicast_port
        self.do_multicast = do_multicast

        self.logger = logging.getLogger(__name__)

        self.__servers__: Dict[str, Application] = {}
        self.__runners__: Dict[str, AppRunner] = {}
        self.__webservers__: Dict[str, AppRunner] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} endpoints={len(self.endpoints)} started={self.started} standard_port={self.standard_port!r} multicast_port={self.multicast_port!r} do_multicast={self.do_multicast}>"

    def __get_parent__(self, func: RouteFunc) -> Optional[Cog]:
        for cog in self.bot.cogs.values():
            if func.__name__ in dir(cog):
                return cog
        return self.bot

    @classmethod
    def route(cls, name: Optional[str] = None, multicast: Optional[bool] = True) -> Callable[[RouteFunc], RouteFunc]:
        """|method|

        Used to register a coroutine as an endpoint

        Parameters
        ----------
        name: :class:`str`
            The endpoint name. If not provided the method name will be used.
        multicast :class:`bool`
            Should the enpoint be avaiable for multicast or not. If this is set to False only standard connection can access it.
        """
        def decorator(func: RouteFunc) -> RouteFunc:
            for _cls in func.__annotations__.values():
                if isinstance(_cls, ClientPayload):
                    payload_cls = _cls
                    break
            else:
                payload_cls = ClientPayload
            func.__multicasted__ = multicast

            cls.endpoints[name or func.__name__] = (func, payload_cls)
            return func
        return decorator

    @property
    def started(self) -> bool:
        return len(self.__servers__) > 0

    async def __handle_standard__(self, original_request: Request) -> None:
        self.logger.debug("Handing new IPC request")

        websocket = WebSocketResponse()
        await websocket.prepare(original_request)

        async for message in websocket:
            asyncio.create_task(self.__process_request__(websocket, message, False))

    async def __handle_multicast__(self, original_request: Request) -> None:
        self.logger.debug("Handing new IPC request")

        websocket = WebSocketResponse()
        await websocket.prepare(original_request)

        async for message in websocket:
            asyncio.create_task(self.__process_request__(websocket, message, True))

    async def __process_request__(self, websocket: WebSocketResponse, message: WSMessage, multicast: bool) -> None:
        request = message.json()

        self.logger.debug(f"Receiving request: {request!r}")

        endpoint: Optional[RouteFunc] = request.get("endpoint")
        secret_key: Optional[str] = websocket._req.headers.get("Secret-Key")

        if request.get("connection_test"):
            return await websocket.send_json({"code": 200})

        elif secret_key != self.secret_key:
            self.bot.dispatch("ipc_error", endpoint, IPCError("Received unauthorized request (invalid token provided)!"))
            response = {
                "error": "Received unauthorized request (invalid token provided)!", 
                "code": 403
            }
        else:
            if not endpoint:
                self.bot.dispatch("ipc_error", endpoint, IPCError("Received invalid request (no endpoint provided)!"))
                response = {
                    "error": "Received invalid request (no endpoint provided)!",
                    "code": 404
                }

            elif not (_endpoint_ := self.endpoints.get(endpoint)):
                self.bot.dispatch("ipc_error", endpoint, IPCError("Received invalid request (invalid endpoint requested)!"))
                response = {
                    "error": "Received invalid request (invalid endpoint requested)!",
                    "code": 404
                }

            elif multicast and not _endpoint_[0].__multicasted__:
                self.bot.dispatch("ipc_error", endpoint, IPCError("The requested is not available for multicast connections!"))
                response = {
                    "error": "The requested route is not available for multicast connections!",
                    "code": 403
                }
                
            else:
                endpoint, payload_cls = self.endpoints.get(endpoint)
                attempted_cls = self.__get_parent__(endpoint)
                    
                if attempted_cls:
                    arguments = (attempted_cls, payload_cls(request))
                else:
                    # Client support
                    arguments = (payload_cls(request),)

                try:
                    response: Union[Dict, Any] = await endpoint(*arguments)
                except Exception as exception:
                    self.bot.dispatch("ipc_error", endpoint, exception)
                    response = {
                        "error": "Something went wrong while calling the route!",
                        "code": 500,
                    }

                    self.logger.error(f"Received error while executing {endpoint!r}", exc_info=exception)
        try:
            response = response or {} 
            if not isinstance(response, Dict):
                exception = f"Expected type `Dict` as response, got {response.__class__.__name__!r} instead!"
                
                self.bot.dispatch("ipc_error", endpoint, JSONEncodeError(exception))

                response = {
                    "error": exception, 
                    "code": 500
                }

                self.logger.debug(f"Sending Response: {response!r}")
                return await websocket.send_json(response)

            if not response.get("code"):
                response["code"] = 200

            response["__bot__"] = self.bot.user.id

            await websocket.send_json(response)
        except Exception:
            self.bot.dispatch("ipc_error", endpoint, IPCError("Could not send JSON data to websocket!"))
        else:
            self.logger.debug(f"Sending response: {response!r}")

    async def __create_server__(self, name: str, port: int, handler: Handler) -> None:
        self.__servers__[name] = Application()
        self.__servers__[name].router.add_route("GET", "/", handler)

        self.__runners__[name] = AppRunner(self.__servers__[name])
        await self.__runners__[name].setup()

        self.__webservers__[name] = TCPSite(self.__runners__[name], self.host, port)
        await self.__webservers__[name].start()

        self.logger.info(f"{name.title()!r} server is ready for use")

    async def start(self) -> None:
        """|coro|
        
        Starts all necessary processes for the servers and runners to work properly

        """
        self.loop = asyncio.get_event_loop()
        await self.__create_server__("standard", self.standard_port, self.__handle_standard__)
        
        if self.do_multicast:
            await self.__create_server__("mutlicast", self.multicast_port, self.__handle_multicast__)
        
        if self.bot.is_ready():
            self.bot.dispatch("ipc_ready")
        else:
            self.loop.create_task(self.bot.wait_until_ready())
            self.bot.dispatch("ipc_ready")

    async def stop(self) -> None:
        """|coro|

        Takes care of shutting down the servers and cleaning up the runners

        """

        for server, runner in zip(self.__servers__.items(), self.__runners__.items()):
            self.logger.info(f"Stopping {server[0]} server")
            await server[1].shutdown()

            self.logger.info(f"Stopping {runner[0]} runner")
            await runner[1].cleanup()

        self.__servers__ = self.__runners__ = self.__webservers__ = {}
