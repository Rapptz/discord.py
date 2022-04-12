"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import BasicAuth

# fmt: off
__all__ = (
    'CaptchaHandler',
)
# fmt: on


class CaptchaHandler:
    """A class that represents a captcha handler.

    This class allows you to implement a protocol to solve captchas required by Discord.
    This is an abstract class. The library provides no concrete implementation.

    These classes are passed to :class:`Client`.
    """

    async def startup(self):
        """|coro|

        An abstract method that is called by the library at startup.

        This is meant to provide an async startup method for the handler.
        This isn't guaranteed to be run once.

        The default implementation does nothing.
        """
        pass

    async def prefetch_token(self, proxy: Optional[str], proxy_auth: Optional[BasicAuth], /) -> None:
        """|coro|

        An abstract method that is called a bit before a captcha token is required.
        Not guaranteed to be called.

        It's meant to signal the handler to begin preparing for the fetching of a token, if applicable.
        Keep in mind that Discord has multiple captcha sitekeys.

        The default implementation does nothing.

        Parameters
        ----------
        proxy: Optional[:class:`str`]
            The current proxy of the client.
        proxy_auth: Optional[:class:`aiohttp.BasicAuth`]
            The proxy's auth.
        """
        pass

    async def fetch_token(
        self,
        data: Dict[str, Any],
        proxy: Optional[str],
        proxy_auth: Optional[BasicAuth],
        /,
    ) -> str:
        """|coro|

        An abstract method that is called to fetch a captcha token.

        If there is no token available, it should wait until one is
        generated before returning.

        Parameters
        ------------
        data: Dict[:class:`str`, :class:`Any`]
            The raw error from Discord containing the captcha info.
        proxy: Optional[:class:`str`]
            The current proxy of the client.
        proxy_auth: Optional[:class:`aiohttp.BasicAuth`]
            The proxy's auth.

        Returns
        --------
        :class:`str`
            A captcha token.
        """
        raise NotImplementedError
