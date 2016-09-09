# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

import discord
import asyncio
import re
import inspect

from .errors import BadArgument, NoPrivateMessage

__all__ = [ 'Converter', 'MemberConverter', 'UserConverter',
            'ChannelConverter', 'InviteConverter', 'RoleConverter',
            'GameConverter', 'ColourConverter' ]

def _get_from_servers(bot, getter, argument):
    result = None
    for server in bot.servers:
        result = getattr(server, getter)(argument)
        if result:
            return result
    return result

class Converter:
    """The base class of custom converters that require the :class:`Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``discord`` classes.

    Classes that derive from this should override the :meth:`convert` method
    to do its conversion logic. This method could be a coroutine or a regular
    function.

    Attributes
    -----------
    ctx: :class:`Context`
        The invocation context that the argument is being used in.
    argument: str
        The argument that is being converted.
    """
    def __init__(self, ctx, argument):
        self.ctx = ctx
        self.argument = argument

    def convert(self):
        raise NotImplementedError('Derived classes need to implement this.')

class IDConverter(Converter):
    def __init__(self, ctx, argument):
        super().__init__(ctx, argument)
        self._id_regex = re.compile(r'([0-9]{15,21})$')

    def _get_id_match(self):
        return self._id_regex.match(self.argument)

class MemberConverter(IDConverter):
    def convert(self):
        message = self.ctx.message
        bot = self.ctx.bot
        match = self._get_id_match() or re.match(r'<@!?([0-9]+)>$', self.argument)
        server = message.server
        result = None
        if match is None:
            # not a mention...
            if server:
                result = server.get_member_named(self.argument)
            else:
                result = _get_from_servers(bot, 'get_member_named', self.argument)
        else:
            user_id = match.group(1)
            if server:
                result = server.get_member(user_id)
            else:
                result = _get_from_servers(bot, 'get_member', user_id)

        if result is None:
            raise BadArgument('Member "{}" not found'.format(self.argument))

        return result

UserConverter = MemberConverter

class ChannelConverter(IDConverter):
    def convert(self):
        message = self.ctx.message
        bot = self.ctx.bot

        match = self._get_id_match() or re.match(r'<#([0-9]+)>$', self.argument)
        result = None
        server = message.server
        if match is None:
            # not a mention
            if server:
                result = discord.utils.get(server.channels, name=self.argument)
            else:
                result = discord.utils.get(bot.get_all_channels(), name=self.argument)
        else:
            channel_id = match.group(1)
            if server:
                result = server.get_channel(channel_id)
            else:
                result = _get_from_servers(bot, 'get_channel', channel_id)

        if result is None:
            raise BadArgument('Channel "{}" not found.'.format(self.argument))

        return result

class ColourConverter(Converter):
    def convert(self):
        arg = self.argument.replace('0x', '').lower()

        if arg[0] == '#':
            arg = arg[1:]
        try:
            value = int(arg, base=16)
            return discord.Colour(value=value)
        except ValueError:
            method = getattr(discord.Colour, arg, None)
            if method is None or not inspect.ismethod(method):
                raise BadArgument('Colour "{}" is invalid.'.format(arg))
            return method()

class RoleConverter(IDConverter):
    def convert(self):
        server = self.ctx.message.server
        if not server:
            raise NoPrivateMessage()

        match = self._get_id_match() or re.match(r'<@&([0-9]+)>$', self.argument)
        params = dict(id=match.group(1)) if match else dict(name=self.argument)
        result = discord.utils.get(server.roles, **params)
        if result is None:
            raise BadArgument('Role "{}" not found.'.format(self.argument))
        return result

class GameConverter(Converter):
    def convert(self):
        return discord.Game(name=self.argument)

class InviteConverter(Converter):
    @asyncio.coroutine
    def convert(self):
        try:
            invite = yield from self.ctx.bot.get_invite(self.argument)
            return invite
        except Exception as e:
            raise BadArgument('Invite is invalid or expired') from e

class EmojiConverter(IDConverter):
    @asyncio.coroutine
    def convert(self):
        message = self.ctx.message
        bot = self.ctx.bot

        match = self._get_id_match() or re.match(r'<:[a-zA-Z0-9]+:([0-9]+)>$', self.argument)
        result = None
        server = message.server
        if match is None:
            # Try to get the emoji by name. Try local server first.
            if server:
                result = discord.utils.get(server.emojis, name=self.argument)

            if result is None:
                result = discord.utils.get(bot.get_all_emojis(), name=self.argument)
        else:
            emoji_id = match.group(1)

            # Try to look up emoji by id.
            if server:
                result = discord.utils.get(server.emojis, id=emoji_id)

            if result is None:
                result = discord.utils.get(bot.get_all_emojis(), id=emoji_id)

        if result is None:
            raise BadArgument('Emoji "{}" not found.'.format(self.argument))

        return result
