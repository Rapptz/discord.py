# -*- coding: utf-8 -*-

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

class DiscordException(Exception):
    """Base exception class for discord.py

    Ideally speaking, this could be caught to handle any exceptions thrown from this library.
    """
    pass

class ClientException(DiscordException):
    """Exception that's thrown when an operation in the :class:`Client` fails.

    These are usually for exceptions that happened due to user input.
    """
    pass

class NoMoreItems(DiscordException):
    """Exception that is thrown when an async iteration operation has no more
    items."""
    pass

class GatewayNotFound(DiscordException):
    """An exception that is usually thrown when the gateway hub
    for the :class:`Client` websocket is not found."""
    def __init__(self):
        message = 'The gateway to connect to discord was not found.'
        super(GatewayNotFound, self).__init__(message)

def flatten_error_dict(d, key=''):
    items = []
    for k, v in d.items():
        new_key = key + '.' + k if key else k

        if isinstance(v, dict):
            try:
                _errors = v['_errors']
            except KeyError:
                items.extend(flatten_error_dict(v, new_key).items())
            else:
                items.append((new_key, ' '.join(x.get('message', '') for x in _errors)))
        else:
            items.append((new_key, v))

    return dict(items)

class HTTPException(DiscordException):
    """Exception that's thrown when an HTTP request operation fails.

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
    """

    def __init__(self, response, message):
        self.response = response
        self.status = response.status
        if isinstance(message, dict):
            self.code = message.get('code', 0)
            base = message.get('message', '')
            errors = message.get('errors')
            if errors:
                errors = flatten_error_dict(errors)
                helpful = '\n'.join('In %s: %s' % t for t in errors.items())
                self.text = base + '\n' + helpful
            else:
                self.text = base
        else:
            self.text = message
            self.code = 0

        fmt = '{0.status} {0.reason} (error code: {1})'
        if len(self.text):
            fmt += ': {2}'

        super().__init__(fmt.format(self.response, self.code, self.text))

class Forbidden(HTTPException):
    """Exception that's thrown for when status code 403 occurs.

    Subclass of :exc:`HTTPException`
    """
    pass

class NotFound(HTTPException):
    """Exception that's thrown for when status code 404 occurs.

    Subclass of :exc:`HTTPException`
    """
    pass

class DiscordServerError(HTTPException):
    """Exception that's thrown for when a 500 range status code occurs.

    Subclass of :exc:`HTTPException`.

    .. versionadded:: 1.5
    """
    pass

class InvalidData(ClientException):
    """Exception that's raised when the library encounters unknown
    or invalid data from Discord.
    """
    pass

class InvalidArgument(ClientException):
    """Exception that's thrown when an argument to a function
    is invalid some way (e.g. wrong value or wrong type).

    This could be considered the analogous of ``ValueError`` and
    ``TypeError`` except inherited from :exc:`ClientException` and thus
    :exc:`DiscordException`.
    """
    pass

class LoginFailure(ClientException):
    """Exception that's thrown when the :meth:`Client.login` function
    fails to log you in from improper credentials or some other misc.
    failure.
    """
    pass

class ConnectionClosed(ClientException):
    """Exception that's thrown when the gateway connection is
    closed for reasons that could not be handled internally.

    Attributes
    -----------
    code: :class:`int`
        The close code of the websocket.
    reason: :class:`str`
        The reason provided for the closure.
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """
    def __init__(self, socket, *, shard_id, code=None):
        # This exception is just the same exception except
        # reconfigured to subclass ClientException for users
        self.code = code or socket.close_code
        # aiohttp doesn't seem to consistently provide close reason
        self.reason = ''
        self.shard_id = shard_id
        super().__init__('Shard ID %s WebSocket closed with %s' % (self.shard_id, self.code))

class PrivilegedIntentsRequired(ClientException):
    """Exception that's thrown when the gateway is requesting privileged intents
    but they're not ticked in the developer page yet.

    Go to https://discord.com/developers/applications/ and enable the intents
    that are required. Currently these are as follows:

    - :attr:`Intents.members`
    - :attr:`Intents.presences`

    Attributes
    -----------
    shard_id: Optional[:class:`int`]
        The shard ID that got closed if applicable.
    """

    def __init__(self, shard_id):
        self.shard_id = shard_id
        msg = 'Shard ID %s is requesting privileged intents that have not been explicitly enabled in the ' \
              'developer portal. It is recommended to go to https://discord.com/developers/applications/ ' \
              'and explicitly enable the privileged intents within your application\'s page. If this is not ' \
              'possible, then consider disabling the privileged intents instead.'
        super().__init__(msg % shard_id)
