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

import datetime
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict

import aiohttp

from ...http import HTTPClient
from ...utils import utcnow
from .token import Token


class Exchanger:
    """Exchanger object to exchange a code for an access token.

    Parameters
    ----------
    client_id: :class:`int`
        The client ID of your bot.
    client_secret: :class:`str`
        The client secret of your bot.
    redirect_uri: :class:`str`
        The redirect URI for your oauth2 application.
    """

    def __init__(self, client_id: int, client_secret: str, redirect_uri: str) -> None:
        self.client_id: int = client_id
        self.client_secret: str = client_secret
        self.redirect_uri: str = redirect_uri

    async def __aenter__(self) -> Exchanger:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.__session = aiohttp.ClientSession(headers=headers)
        self.http_client: HTTPClient = HTTPClient(self.__session.loop, access_token=True)
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.__session.close()

    def expired(self, token: Token, /) -> bool:
        """Checks if the provided token is expired.

        Parameters
        ----------
        token: :class:`Token`
            The token to check if it is expired.
        """
        return token.expired

    @asynccontextmanager
    async def exchange(self, code: str, /) -> AsyncIterator[Token]:
        """Exchange a code for an access token.

        Parameters
        ----------
        code: :class:`str`
            The code to exchange.
        """
        data: Dict[str, Any] = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': code,
        }
        async with self.__session.post('https://discordapp.com/api/v9/oauth2/token', data=data) as resp:
            data = await resp.json()
        expires_in = data.get('expires_in')
        if expires_in is not None:
            data['expires_in'] = utcnow() + datetime.timedelta(seconds=expires_in)
        token = Token(**data)
        await self.http_client.static_login(str(token))
        yield token

    @asynccontextmanager
    async def refresh(self, refresh_token: str, /) -> AsyncIterator[Token]:
        """Refresh an access token.

        Parameters
        ----------
        refresh_token: :class:`str`
            The refresh token to use.
        """
        data: Dict[str, Any] = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        async with self.__session.post('https://discordapp.com/api/v9/oauth2/token', data=data) as resp:
            data = await resp.json()
        expires_in = data.get('expires_in')
        if expires_in is not None:
            data['expires_in'] = utcnow() + datetime.timedelta(seconds=expires_in)
        token = Token(**data)
        await self.http_client.static_login(str(token))
        yield token
