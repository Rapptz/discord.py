# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

from .errors import MissingRequiredArgument

__all__ = (
    'CustomDefault',
    'Author',
    'CurrentChannel',
    'CurrentGuild',
    'Call',
)

class CustomDefault:
    """The base class of custom defaults that require the :class:`.Context`.

    Classes that derive from this should override the :meth:`~.CustomDefault.default`
    method to do its conversion logic. This method must be a coroutine.
    """

    async def default(self, ctx, param):
        """|coro|

        The method to override to do conversion logic.

        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        """
        raise NotImplementedError('Derived classes need to implement this.')


class Author(CustomDefault):
    """Default parameter which returns the author for this context."""

    async def default(self, ctx, param):
        return ctx.author

class CurrentChannel(CustomDefault):
    """Default parameter which returns the channel for this context."""

    async def default(self, ctx, param):
        return ctx.channel

class CurrentGuild(CustomDefault):
    """Default parameter which returns the guild for this context."""

    async def default(self, ctx, param):
        if ctx.guild:
            return ctx.guild
        raise MissingRequiredArgument(param)

class Call(CustomDefault):
    """Easy wrapper for lambdas/inline defaults."""

    def __init__(self, callback):
        self._callback = callback

    async def default(self, ctx, param):
        return self._callback(ctx, param)
