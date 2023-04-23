from __future__ import annotations

import asyncio
import logging
import time

from .pool import Session
from types import TracebackType
from typing import Any, Dict, Optional, Type,  Union
from aiohttp import ClientConnectorError, ClientConnectionError, ClientSession, WSCloseCode,WSMsgType

class Client:
    """|class|
    
    Handles the web application side requests to the bot process 
    (intented to work as asynchronous context manager)

    Parameters:
    ----------
    host: :str:`str`
        The IP adress that hosts the server (the default is `127.0.0.1`).
    secret_key: :str:`str`
        The authentication that is used when creating the server (the default is `None`).
    standard_port: :str:`int`
        The port for the standard server (the default is `1025`)
    multicast_port: :int:`int`
        The port for the multicasting server (the default is `20000`)
    do_multicast: :bool:`bool`
        Should the client perform standard or multicast connection (the default is `True`)
        
        Please keep in mind that multicast clients cannot request routes that are only allowed for standard connections!
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        secret_key: Union[str, None] = None,
        standard_port: int = 1025,
        multicast_port: int = 20000,
        do_multicast: bool = True
    ) -> None:
        self.host = host
        self.standard_port = standard_port
        self.secret_key = secret_key
        self.multicast_port = multicast_port
        self.do_multicast = do_multicast

        self.logger = logging.getLogger(__name__)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} standard_port={self.standard_port!r} multicast_port={self.multicast_port!r} do_multicast={self.do_multicast}>"

    @property
    def url(self) -> str:
        if self.do_multicast:
            return f"ws://{self.host}:{self.multicast_port}"
        return f"ws://{self.host}:{self.standard_port}"

    async def is_alive(self) -> bool:
        """|coro|

        Performs a test to the connetion state
        
        """
        async with Session(self.url, self.secret_key) as session:
            return await session.is_alive()

    async def request(self, endpoint: str, **kwargs: Any) -> Optional[Dict]:
        """|coro|
        
        Make a request to the server process.

        ----------
        endpoint: `str`
            The endpoint to request on the server
        **kwargs: `Any`
            The data for the endpoint
        """
        async with Session(self.url, self.secret_key) as session:
            return await session.request(endpoint, **kwargs)
