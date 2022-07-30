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
from typing import Dict, List, Optional, TYPE_CHECKING, Any, Tuple, Union

from .utils import _get_as_snowflake

if TYPE_CHECKING:
    from aiohttp import ClientResponse, ClientWebSocketResponse
    from requests import Response

    _ResponseType = Union[ClientResponse, Response]

__all__ = (
    'DiscordException',
    'ClientException',
    'GatewayNotFound',
    'HTTPException',
    'RateLimited',
    'Forbidden',
    'NotFound',
    'DiscordServerError',
    'InvalidData',
    'AuthFailure',
    'LoginFailure',
    'ConnectionClosed',
    'CaptchaRequired',
)


class DiscordException(Exception):
    """Base exception class for discord.py

    Ideally speaking, this could be caught to handle any exceptions raised from this library.
    """

    pass


class ClientException(DiscordException):
    """Exception that's raised when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """

    pass


class GatewayNotFound(DiscordException):
    """An exception that is raised when the gateway for Discord could not be found"""

    def __init__(self):
        message = 'The gateway to connect to Discord was not found.'
        super().__init__(message)


def _flatten_error_dict(d: Dict[str, Any], key: str = '') -> Dict[str, str]:
    items: List[Tuple[str, str]] = []

    if '_errors' in d:
        items.append(('miscallenous', ' '.join(x.get('message', '') for x in d['_errors'])))
        d.pop('_errors')

    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors: List[Dict[str, Any]] = v['_errors']
            except KeyError:
                items.extend(_flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)


class HTTPException(DiscordException):
    """Exception that's raised when an HTTP request operation fails.

    Attributes
    ------------
    response: :class:`aiohttp.ClientResponse`
        The response of the failed HTTP request. This is an
        instance of :class:`aiohttp.ClientResponse`. In some cases
        this could also be a :class:`requests.Response`.
    text: :class:`str`
        The text of the error. Could be an empty string.
    status: :class:`int`
        The status code of the HTTP request.
    code: :class:`int`
        The Discord specific error code for the failure.
    json: :class:`dict`
        The raw error JSON.

        .. versionadded:: 2.0
    payment_id: Optional[:class:`int`]
        The ID of the payment that requires verification to continue.

        .. versionadded:: 2.0
    """

    def __init__(self, response: _ResponseType, message: Optional[Union[str, Dict[str, Any]]]):
        self.response: _ResponseType = response
        self.status: int = response.status  # type: ignore # This attribute is filled by the library even if using requests
        self.code: int
        self.text: str
        self.json: Dict[str, Any]
        self.payment_id: Optional[int]
        if isinstance(message, dict):
            self.json = message
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = _flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
            self.payment_id = _get_as_snowflake(message, 'payment_id')
        else:
            self.text = message or ''
            self.code = 0
            self.json = {}
            self.payment_id = None

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ': {2}'

        super().__init__(fmt.format(self.response, self.code, self.text))


class RateLimited(DiscordException):
    """Exception that's raised for when status code 429 occurs
    and the timeout is greater than the configured maximum using
    the ``max_ratelimit_timeout`` parameter in :class:`Client`.

    This is not raised during global ratelimits.

    Since sometimes requests are halted pre-emptively before they're
    even made, this **does not** subclass :exc:`HTTPException`.

    .. versionadded:: 2.0

    Attributes
    ------------
    retry_after: :class:`float`
        The amount of seconds that the client should wait before retrying
        the request.
    """

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f'Too many requests. Retry in {retry_after:.2f} seconds.')


class Forbidden(HTTPException):
    """Exception that's raised for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """

    pass


class NotFound(HTTPException):
    """Exception that's raised for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """

    pass


class DiscordServerError(HTTPException):
    """Exception that's raised for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """

    pass


class CaptchaRequired(HTTPException):
    """Exception that's raised when a captcha is required and isn't handled.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 2.0
    """

    def __init__(self, response: _ResponseType, message: Dict[str, Any]):
        super().__init__(response, {'code': -1, 'message': 'Captcha required'})
        self.json = message


class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """

    pass


class LoginFailure(ClientException):
    """Exception that's raised when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """

    pass


AuthFailure = LoginFailure


class ConnectionClosed(ClientException):
    """Exception that's raised when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    -----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    """

    def __init__(self, socket: ClientWebSocketResponse, *, code: Optional[int] = None):
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code: int = code or socket.close_code or -1
        # aiohttp doesn't seem to consistently provide close reason
        self.reason: str = ''
        super().__init__(f'WebSocket closed with {self.code}')
