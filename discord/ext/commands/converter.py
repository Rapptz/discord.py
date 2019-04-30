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

import re
import inspect

import discord

from .errors import BadArgument, NoPrivateMessage

__all__ = (
    'Converter',
    'MemberConverter',
    'UserConverter',
    'MessageConverter',
    'TextChannelConverter',
    'InviteConverter',
    'RoleConverter',
    'GameConverter',
    'ColourConverter',
    'VoiceChannelConverter',
    'EmojiConverter',
    'PartialEmojiConverter',
    'CategoryChannelConverter',
    'IDConverter',
    'clean_content',
    'Greedy',
)

def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result

class Converter:
    """The base class of custom converters that require the :class:`.Context`
    to be passed to be useful.

    This allows you to implement converters that function similar to the
    special cased ``discord`` classes.

    Classes that derive from this should override the :meth:`~.Converter.convert`
    method to do its conversion logic. This method must be a coroutine.
    """

    async def convert(self, ctx, argument):
        """|coro|

        The method to override to do conversion logic.

        If an error is found while converting, it is recommended to
        raise a :exc:`.CommandError` derived exception as it will
        properly propagate to the error handlers.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context that the argument is being used in.
        argument: :class:`str`
            The argument that is being converted.
        """
        raise NotImplementedError('Derived classes need to implement this.')

class IDConverter(Converter):
    def __init__(self):
        self._id_regex = re.compile(r'([0-9]{15,21})$')
        super().__init__()

    def _get_id_match(self, argument):
        return self._id_regex.match(argument)

class MemberConverter(IDConverter):
    """Converts to a :class:`Member`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    5. Lookup by nickname
    """

    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)
        guild = ctx.guild
        result = None
        if match is None:
            # not a mention...
            if guild:
                result = guild.get_member_named(argument)
            else:
                result = _get_from_guilds(bot, 'get_member_named', argument)
        else:
            user_id = int(match.group(1))
            if guild:
                result = guild.get_member(user_id)
            else:
                result = _get_from_guilds(bot, 'get_member', user_id)

        if result is None:
            raise BadArgument('Member "{}" not found'.format(argument))

        return result

class UserConverter(IDConverter):
    """Converts to a :class:`User`.

    All lookups are via the global user cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    """
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)
        result = None
        state = ctx._state

        if match is not None:
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id)
        else:
            arg = argument
            # check for discriminator if it exists
            if len(arg) > 5 and arg[-5] == '#':
                discrim = arg[-4:]
                name = arg[:-5]
                predicate = lambda u: u.name == name and u.discriminator == discrim
                result = discord.utils.find(predicate, state._users.values())
                if result is not None:
                    return result

            predicate = lambda u: u.name == arg
            result = discord.utils.find(predicate, state._users.values())

        if result is None:
            raise BadArgument('User "{}" not found'.format(argument))

        return result

class MessageConverter(Converter):
    """Converts to a :class:`discord.Message`.

    .. versionadded:: 1.1.0

    The lookup strategy is as follows (in order):

    1. Lookup by "{channel ID}-{message ID}" (retrieved by shift-clicking on "Copy ID")
    2. Lookup by message ID (the message **must** be in the context channel)
    3. Lookup by message URL
    """

    async def convert(self, ctx, argument):
        id_regex = re.compile(r'^(?:(?P<channel_id>[0-9]{15,21})-)?(?P<message_id>[0-9]{15,21})$')
        link_regex = re.compile(
            r'^https?://(?:(ptb|canary)\.)?discordapp\.com/channels/'
            r'(?:([0-9]{15,21})|(@me))'
            r'/(?P<channel_id>[0-9]{15,21})/(?P<message_id>[0-9]{15,21})/?$'
        )
        match = id_regex.match(argument) or link_regex.match(argument)
        if not match:
            raise BadArgument('Message "{msg}" not found.'.format(msg=argument))
        message_id = int(match.group("message_id"))
        channel_id = match.group("channel_id")
        message = ctx.bot._connection._get_message(message_id)
        if message:
            return message
        channel = ctx.bot.get_channel(int(channel_id)) if channel_id else ctx.channel
        if not channel:
            raise BadArgument('Channel "{channel}" not found.'.format(channel=channel_id))
        try:
            return await channel.fetch_message(message_id)
        except discord.NotFound:
            raise BadArgument('Message "{msg}" not found.'.format(msg=argument))
        except discord.Forbidden:
            raise BadArgument("Can't read messages in {channel}".format(channel=channel.mention))

class TextChannelConverter(IDConverter):
    """Converts to a :class:`TextChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.text_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.TextChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.TextChannel):
            raise BadArgument('Channel "{}" not found.'.format(argument))

        return result

class VoiceChannelConverter(IDConverter):
    """Converts to a :class:`VoiceChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot
        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.voice_channels, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.VoiceChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.VoiceChannel):
            raise BadArgument('Channel "{}" not found.'.format(argument))

        return result

class CategoryChannelConverter(IDConverter):
    """Converts to a :class:`CategoryChannel`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)
        result = None
        guild = ctx.guild

        if match is None:
            # not a mention
            if guild:
                result = discord.utils.get(guild.categories, name=argument)
            else:
                def check(c):
                    return isinstance(c, discord.CategoryChannel) and c.name == argument
                result = discord.utils.find(check, bot.get_all_channels())
        else:
            channel_id = int(match.group(1))
            if guild:
                result = guild.get_channel(channel_id)
            else:
                result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.CategoryChannel):
            raise BadArgument('Channel "{}" not found.'.format(argument))

        return result

class ColourConverter(Converter):
    """Converts to a :class:`Colour`.

    The following formats are accepted:

    - ``0x<hex>``
    - ``#<hex>``
    - ``0x#<hex>``
    - Any of the ``classmethod`` in :class:`Colour`

        - The ``_`` in the name can be optionally replaced with spaces.
    """
    async def convert(self, ctx, argument):
        arg = argument.replace('0x', '').lower()

        if arg[0] == '#':
            arg = arg[1:]
        try:
            value = int(arg, base=16)
            if not (0 <= value <= 0xFFFFFF):
                raise BadArgument('Colour "{}" is invalid.'.format(arg))
            return discord.Colour(value=value)
        except ValueError:
            arg = arg.replace(' ', '_')
            method = getattr(discord.Colour, arg, None)
            if arg.startswith('from_') or method is None or not inspect.ismethod(method):
                raise BadArgument('Colour "{}" is invalid.'.format(arg))
            return method()

class RoleConverter(IDConverter):
    """Converts to a :class:`Role`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        guild = ctx.guild
        if not guild:
            raise NoPrivateMessage()

        match = self._get_id_match(argument) or re.match(r'<@&([0-9]+)>$', argument)
        if match:
            result = guild.get_role(int(match.group(1)))
        else:
            result = discord.utils.get(guild._roles.values(), name=argument)

        if result is None:
            raise BadArgument('Role "{}" not found.'.format(argument))
        return result

class GameConverter(Converter):
    """Converts to :class:`Game`."""
    async def convert(self, ctx, argument):
        return discord.Game(name=argument)

class InviteConverter(Converter):
    """Converts to a :class:`Invite`.

    This is done via an HTTP request using :meth:`.Bot.fetch_invite`.
    """
    async def convert(self, ctx, argument):
        try:
            invite = await ctx.bot.fetch_invite(argument)
            return invite
        except Exception as exc:
            raise BadArgument('Invite is invalid or expired') from exc

class EmojiConverter(IDConverter):
    """Converts to a :class:`Emoji`.

    All lookups are done for the local guild first, if available. If that lookup
    fails, then it checks the client's global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by extracting ID from the emoji.
    3. Lookup by name
    """
    async def convert(self, ctx, argument):
        match = self._get_id_match(argument) or re.match(r'<a?:[a-zA-Z0-9\_]+:([0-9]+)>$', argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild

        if match is None:
            # Try to get the emoji by name. Try local guild first.
            if guild:
                result = discord.utils.get(guild.emojis, name=argument)

            if result is None:
                result = discord.utils.get(bot.emojis, name=argument)
        else:
            emoji_id = int(match.group(1))

            # Try to look up emoji by id.
            if guild:
                result = discord.utils.get(guild.emojis, id=emoji_id)

            if result is None:
                result = discord.utils.get(bot.emojis, id=emoji_id)

        if result is None:
            raise BadArgument('Emoji "{}" not found.'.format(argument))

        return result

class PartialEmojiConverter(Converter):
    """Converts to a :class:`PartialEmoji`.

    This is done by extracting the animated flag, name and ID from the emoji.
    """
    async def convert(self, ctx, argument):
        match = re.match(r'<(a?):([a-zA-Z0-9\_]+):([0-9]+)>$', argument)

        if match:
            emoji_animated = bool(match.group(1))
            emoji_name = match.group(2)
            emoji_id = int(match.group(3))

            return discord.PartialEmoji.with_state(ctx.bot._connection, animated=emoji_animated, name=emoji_name,
                                                   id=emoji_id)

        raise BadArgument('Couldn\'t convert "{}" to PartialEmoji.'.format(argument))

class clean_content(Converter):
    """Converts the argument to mention scrubbed version of
    said content.

    This behaves similarly to :attr:`.Message.clean_content`.

    Attributes
    ------------
    fix_channel_mentions: :class:`bool`
        Whether to clean channel mentions.
    use_nicknames: :class:`bool`
        Whether to use nicknames when transforming mentions.
    escape_markdown: :class:`bool`
        Whether to also escape special markdown characters.
    """
    def __init__(self, *, fix_channel_mentions=False, use_nicknames=True, escape_markdown=False):
        self.fix_channel_mentions = fix_channel_mentions
        self.use_nicknames = use_nicknames
        self.escape_markdown = escape_markdown

    async def convert(self, ctx, argument):
        message = ctx.message
        transformations = {}

        if self.fix_channel_mentions and ctx.guild:
            def resolve_channel(id, *, _get=ctx.guild.get_channel):
                ch = _get(id)
                return ('<#%s>' % id), ('#' + ch.name if ch else '#deleted-channel')

            transformations.update(resolve_channel(channel) for channel in message.raw_channel_mentions)

        if self.use_nicknames and ctx.guild:
            def resolve_member(id, *, _get=ctx.guild.get_member):
                m = _get(id)
                return '@' + m.display_name if m else '@deleted-user'
        else:
            def resolve_member(id, *, _get=ctx.bot.get_user):
                m = _get(id)
                return '@' + m.name if m else '@deleted-user'


        transformations.update(
            ('<@%s>' % member_id, resolve_member(member_id))
            for member_id in message.raw_mentions
        )

        transformations.update(
            ('<@!%s>' % member_id, resolve_member(member_id))
            for member_id in message.raw_mentions
        )

        if ctx.guild:
            def resolve_role(_id, *, _find=ctx.guild.get_role):
                r = _find(_id)
                return '@' + r.name if r else '@deleted-role'

            transformations.update(
                ('<@&%s>' % role_id, resolve_role(role_id))
                for role_id in message.raw_role_mentions
            )

        def repl(obj):
            return transformations.get(obj.group(0), '')

        pattern = re.compile('|'.join(transformations.keys()))
        result = pattern.sub(repl, argument)

        if self.escape_markdown:
            result = discord.utils.escape_markdown(result)

        # Completely ensure no mentions escape:
        return discord.utils.escape_mentions(result)

class _Greedy:
    __slots__ = ('converter',)

    def __init__(self, *, converter=None):
        self.converter = converter

    def __getitem__(self, params):
        if not isinstance(params, tuple):
            params = (params,)
        if len(params) != 1:
            raise TypeError('Greedy[...] only takes a single argument')
        converter = params[0]

        if not (callable(converter) or isinstance(converter, Converter) or hasattr(converter, '__origin__')):
            raise TypeError('Greedy[...] expects a type or a Converter instance.')

        if converter is str or converter is type(None) or converter is _Greedy:
            raise TypeError('Greedy[%s] is invalid.' % converter.__name__)

        return self.__class__(converter=converter)

Greedy = _Greedy()
