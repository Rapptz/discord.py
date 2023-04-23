
from __future__ import annotations #type: ignore

import time
import asyncio
import logging

from types import TracebackType
from typing import Any, Dict, Optional, Type
from aiohttp import ClientConnectorError, ClientConnectionError, ClientSession, WSCloseCode,WSMsgType, ClientWebSocketResponse
from .errors import NotConnected

class Session:
    def __init__(self, url: str, secret_key: Optional[str] = None) -> None:
        self.url = url
        self.secret_key = secret_key

        self.logger = logging.getLogger(__name__)
        self.session: Optional[ClientSession] = None
        self.ws: Optional[ClientWebSocketResponse] = None
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} started={True if self.session else False} ws={self.ws}>"

    async def __aenter__(self) -> Session:
        await self.__init_socket__(ClientSession())
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def __init_socket__(self, session: ClientSession) -> None:
        self.logger.debug("Initiating websocket connection")
        self.session = session
        try:
            self.ws = await self.session.ws_connect(
                self.url, 
                autoclose=False,
                headers={
                    "Secret-Key": self.secret_key
                }
            )
        except (ClientConnectionError, ClientConnectorError):
            await self.session.close()
            raise NotConnected("WebSocket connection failed, the server is unreachable.")

        if await self.is_alive():
            self.logger.debug(f"Client connected to {self.url!r}")
        else:
            await self.session.close()
            raise NotConnected("WebSocket connection failed, the server is unreachable.")
    
    async def __retry__(self, endpoint, **kwargs) -> WSCloseCode:
        payload = {
            "endpoint": endpoint,
            "data": kwargs
        }
        try:
            await self.ws.send_json(payload)
        except Exception as e:
            self.logger.error("Failed to send payload", exc_info=e)
            return WSCloseCode.INTERNAL_ERROR
        return WSCloseCode.OK

    async def is_alive(self) -> bool:
        payload = {"connection_test": True}

        start = time.perf_counter()
        await self.ws.send_json(payload)
        r = await self.ws.receive()
        self.logger.debug(f"Connection to websocket took {time.perf_counter() - start:,} seconds")

        if r.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
            return False
        return True

    async def request(self, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """|coro|
        Make a request to the IPC server process.
        Parameters
        ----------
        endpoint: `str`
            The endpoint to request on the server
        **kwargs
            The data to send to the endpoint
        """
        self.logger.debug(f"Sending request to {endpoint!r} with %r", kwargs)

        payload = {
            "endpoint": endpoint,
            "data": kwargs
        }

        try:
            await self.ws.send_json(payload)
        except ConnectionResetError:
            self.logger.error(
                "Cannot write to closing transport, restarting the connection in 3 seconds. "
                "(Could be raised if the client is on different machine that the server)"
            )
            
            return await self.__retry__(endpoint, **kwargs)

        recv = await self.ws.receive()

        self.logger.debug("Receiving response: %r", recv)

        if recv.type is WSMsgType.CLOSED:
            self.logger.error("WebSocket connection unexpectedly closed, attempting to retry in 3 seconds.")
            await asyncio.sleep(3)

            if (await self.__retry__(endpoint, **kwargs)== WSCloseCode.INTERNAL_ERROR):
                self.logger.error("Could not do perform the request after reattempt")

        elif recv.type is WSMsgType.ERROR:
            self.logger.error("Received WSMsgType of ERROR, instead of TEXT/BYTES!")

        else:
            data = recv.json()
            if int(data["code"]) != 200:
                self.logger.warning(f"Received code {data['code']!r} insted of usual 200")
            return data

    async def close(self) -> None:
        await self.ws.close()
        await self.session.close()