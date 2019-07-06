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

import asyncio
import datetime
import re
import io

from . import utils
from .reaction import Reaction
from .emoji import Emoji, PartialEmoji
from .calls import CallMessage
from .enums import MessageType, try_enum
from .errors import InvalidArgument, ClientException, HTTPException
from .embeds import Embed
from .member import Member

class Attachment:
    """Represents an attachment from Discord.

    Attributes
    ------------
    id: :class:`int`
        The attachment ID.
    size: :class:`int`
        The attachment size in bytes.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images.
    filename: :class:`str`
        The attachment's filename.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    proxy_url: :class:`str`
        The proxy URL. This is a cached version of the :attr:`~Attachment.url` in the
        case of images. When the message is deleted, this URL might be valid for a few
        minutes or not valid at all.
    """

    __slots__ = ('id', 'size', 'height', 'width', 'filename', 'url', 'proxy_url', '_http')

    def __init__(self, *, data, state):
        self.id = int(data['id'])
        self.size = data['size']
        self.height = data.get('height')
        self.width = data.get('width')
        self.filename = data['filename']
        self.url = data.get('url')
        self.proxy_url = data.get('proxy_url')
        self._http = state.http

    def is_spoiler(self):
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith('SPOILER_')

    def __repr__(self):
        return '<Attachment id={0.id} filename={0.filename!r} url={0.url!r}>'.format(self)

    async def save(self, fp, *, seek_begin=True, use_cached=False):
        """|coro|

        Saves this attachment into a file-like object.

        Parameters
        -----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this attachment to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

        Raises
        --------
        HTTPException
            Saving the attachment failed.
        NotFound
            The attachment was deleted.

        Returns
        --------
        :class:`int`
            The number of bytes written.
        """
        data = await self.read(use_cached=use_cached)
        if isinstance(fp, io.IOBase) and fp.writable():
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)

    async def read(self, *, use_cached=False):
        """|coro|

        Retrieves the content of this attachment as a :class:`bytes` object.

        .. versionadded:: 1.1.0

        Parameters
        -----------
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

        Raises
        ------
        HTTPException
            Downloading the attachment failed.
        Forbidden
            You do not have permissions to access this attachment
        NotFound
            The attachment was deleted.

        Returns
        -------
        :class:`bytes`
            The contents of the attachment.
        """
        url = self.proxy_url if use_cached else self.url
        data = await self._http.get_from_cdn(url)
        return data

def flatten_handlers(cls):
    prefix = len('_handle_')
    cls._HANDLERS = {
        key[prefix:]: value
        for key, value in cls.__dict__.items()
        if key.startswith('_handle_')
    }
    cls._CACHED_SLOTS = [
        attr for attr in cls.__slots__ if attr.startswith('_cs_')
    ]
    return cls

@flatten_handlers
class Message:
    r"""Represents a message from Discord.

    There should be no need to create one of these manually.

    Attributes
    -----------
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: :class:`abc.User`
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has the left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
    nonce
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is typically non-important.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    channel: Union[:class:`abc.Messageable`]
        The :class:`TextChannel` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    call: Optional[:class:`CallMessage`]
        The call that the message refers to. This is only applicable to messages of type
        :attr:`MessageType.call`.
    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    mentions: List[:class:`abc.User`]
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a discord limitation, not one with the library.
    channel_mentions: List[:class:`abc.GuildChannel`]
        A list of :class:`abc.GuildChannel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: List[:class:`Role`]
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: :class:`int`
        The message ID.
    webhook_id: Optional[:class:`int`]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`dict`]
        The rich presence enabled application associated with this message.

        It is a dictionary with the following keys:

        - ``id``: A string representing the application's ID.
        - ``name``: A string representing the application's name.
        - ``description``: A string representing the application's description.
        - ``icon``: A string representing the icon ID of the application.
        - ``cover_image``: A string representing the embed's image asset ID.
    """

    __slots__ = ('_edited_timestamp', 'tts', 'content', 'channel', 'webhook_id',
                 'mention_everyone', 'embeds', 'id', 'mentions', 'author',
                 '_cs_channel_mentions', '_cs_raw_mentions', 'attachments',
                 '_cs_clean_content', '_cs_raw_channel_mentions', 'nonce', 'pinned',
                 'role_mentions', '_cs_raw_role_mentions', 'type', 'call',
                 '_cs_system_content', '_cs_guild', '_state', 'reactions',
                 'application', 'activity')

    def __init__(self, *, state, channel, data):
        self._state = state
        self.id = int(data['id'])
        self.webhook_id = utils._get_as_snowflake(data, 'webhook_id')
        self.reactions = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self.attachments = [Attachment(data=a, state=self._state) for a in data['attachments']]
        self.embeds = [Embed.from_dict(a) for a in data['embeds']]
        self.application = data.get('application')
        self.activity = data.get('activity')
        self.channel = channel
        self._edited_timestamp = utils.parse_time(data['edited_timestamp'])
        self.type = try_enum(MessageType, data['type'])
        self.pinned = data['pinned']
        self.mention_everyone = data['mention_everyone']
        self.tts = data['tts']
        self.content = data['content']
        self.nonce = data.get('nonce')

        for handler in ('author', 'member', 'mentions', 'mention_roles', 'call'):
            try:
                getattr(self, '_handle_%s' % handler)(data[handler])
            except KeyError:
                continue

    def __repr__(self):
        return '<Message id={0.id} channel={0.channel!r} type={0.type!r} author={0.author!r}>'.format(self)

    def _try_patch(self, data, key, transform=None):
        try:
            value = data[key]
        except KeyError:
            pass
        else:
            if transform is None:
                setattr(self, key, value)
            else:
                setattr(self, key, transform(value))

    def _add_reaction(self, data, emoji, user_id):
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        is_me = data['me'] = user_id == self._state.self_id

        if reaction is None:
            reaction = Reaction(message=self, data=data, emoji=emoji)
            self.reactions.append(reaction)
        else:
            reaction.count += 1
            if is_me:
                reaction.me = is_me

        return reaction

    def _remove_reaction(self, data, emoji, user_id):
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)

        if reaction is None:
            # already removed?
            raise ValueError('Emoji already removed?')

        # if reaction isn't in the list, we crash. This means discord
        # sent bad data, or we stored improperly
        reaction.count -= 1

        if user_id == self._state.self_id:
            reaction.me = False
        if reaction.count == 0:
            # this raises ValueError if something went wrong as well.
            self.reactions.remove(reaction)

        return reaction

    def _update(self, data):
        handlers = self._HANDLERS
        for key, value in data.items():
            try:
                handler = handlers[key]
            except KeyError:
                continue
            else:
                handler(self, value)

        # clear the cached properties
        for attr in self._CACHED_SLOTS:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    def _handle_edited_timestamp(self, value):
        self._edited_timestamp = utils.parse_time(value)

    def _handle_pinned(self, value):
        self.pinned = value

    def _handle_application(self, value):
        self.application = value

    def _handle_activity(self, value):
        self.activity = value

    def _handle_mention_everyone(self, value):
        self.mention_everyone = value

    def _handle_tts(self, value):
        self.tts = value

    def _handle_type(self, value):
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value):
        self.content = value

    def _handle_attachments(self, value):
        self.attachments = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value):
        self.embeds = [Embed.from_dict(data) for data in value]

    def _handle_nonce(self, value):
        self.nonce = value

    def _handle_author(self, author):
        self.author = self._state.store_user(author)
        if self.guild is not None:
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member):
        # The gateway now gives us full Member objects sometimes with the following keys
        # deaf, mute, joined_at, roles
        # For the sake of performance I'm going to assume that the only
        # field that needs *updating* would be the joined_at field.
        # If there is no Member object (for some strange reason), then we can upgrade
        # ourselves to a more "partial" member object.
        author = self.author
        try:
            if author.joined_at is None:
                author.joined_at = utils.parse_time(member.get('joined_at'))
        except AttributeError:
            self.author = Member._from_message(message=self, data=member)

    def _handle_mentions(self, mentions):
        self.mentions = []
        if self.guild is None:
            self.mentions = [self._state.store_user(m) for m in mentions]
            return

        for mention in filter(None, mentions):
            id_search = int(mention['id'])
            member = self.guild.get_member(id_search)
            if member is not None:
                self.mentions.append(member)

    def _handle_mention_roles(self, role_mentions):
        self.role_mentions = []
        if self.guild is not None:
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    self.role_mentions.append(role)

    def _handle_call(self, call):
        if call is None or self.type is not MessageType.call:
            self.call = None
            return

        # we get the participant source from the mentions array or
        # the author

        participants = []
        for uid in map(int, call.get('participants', [])):
            if uid == self.author.id:
                participants.append(self.author)
            else:
                user = utils.find(lambda u: u.id == uid, self.mentions)
                if user is not None:
                    participants.append(user)

        call['participants'] = participants
        self.call = CallMessage(message=self, **call)

    @utils.cached_slot_property('_cs_guild')
    def guild(self):
        """Optional[:class:`Guild`]: The guild that the message belongs to, if applicable."""
        return getattr(self.channel, 'guild', None)

    @utils.cached_slot_property('_cs_raw_mentions')
    def raw_mentions(self):
        """List[:class:`int`]: A property that returns an array of user IDs matched with
        the syntax of ``<@user_id>`` in the message content.

        This allows you to receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r'<@!?([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self):
        """List[:class:`int`]: A property that returns an array of channel IDs matched with
        the syntax of ``<#channel_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<#([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self):
        """List[:class:`int`]: A property that returns an array of role IDs matched with
        the syntax of ``<@&role_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<@&([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_channel_mentions')
    def channel_mentions(self):
        if self.guild is None:
            return []
        it = filter(None, map(self.guild.get_channel, self.raw_channel_mentions))
        return utils._unique(it)

    @utils.cached_slot_property('_cs_clean_content')
    def clean_content(self):
        """A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.

        This will also transform @everyone and @here mentions into
        non-mentions.

        .. note::

            This *does not* escape markdown. If you want to escape
            markdown then use :func:`utils.escape_markdown` along
            with this function.
        """

        transformations = {
            re.escape('<#%s>' % channel.id): '#' + channel.name
            for channel in self.channel_mentions
        }

        mention_transforms = {
            re.escape('<@%s>' % member.id): '@' + member.display_name
            for member in self.mentions
        }

        # add the <@!user_id> cases as well..
        second_mention_transforms = {
            re.escape('<@!%s>' % member.id): '@' + member.display_name
            for member in self.mentions
        }

        transformations.update(mention_transforms)
        transformations.update(second_mention_transforms)

        if self.guild is not None:
            role_transforms = {
                re.escape('<@&%s>' % role.id): '@' + role.name
                for role in self.role_mentions
            }
            transformations.update(role_transforms)

        def repl(obj):
            return transformations.get(re.escape(obj.group(0)), '')

        pattern = re.compile('|'.join(transformations.keys()))
        result = pattern.sub(repl, self.content)

        transformations = {
            '@everyone': '@\u200beveryone',
            '@here': '@\u200bhere'
        }

        def repl2(obj):
            return transformations.get(obj.group(0), '')

        pattern = re.compile('|'.join(transformations.keys()))
        return pattern.sub(repl2, result)

    @property
    def created_at(self):
        """:class:`datetime.datetime`: The message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self):
        """Optional[:class:`datetime.datetime`]: A naive UTC datetime object containing the edited time of the message."""
        return self._edited_timestamp

    @property
    def jump_url(self):
        """:class:`str`: Returns a URL that allows the client to jump to this message."""
        guild_id = getattr(self.guild, 'id', '@me')
        return 'https://discordapp.com/channels/{0}/{1.channel.id}/{1.id}'.format(guild_id, self)

    @utils.cached_slot_property('_cs_system_content')
    def system_content(self):
        r"""A property that returns the content that is rendered
        regardless of the :attr:`Message.type`.

        In the case of :attr:`MessageType.default`\, this just returns the
        regular :attr:`Message.content`. Otherwise this returns an English
        message denoting the contents of the system message.
        """

        if self.type is MessageType.default:
            return self.content

        if self.type is MessageType.pins_add:
            return '{0.name} pinned a message to this channel.'.format(self.author)

        if self.type is MessageType.recipient_add:
            return '{0.name} added {1.name} to the group.'.format(self.author, self.mentions[0])

        if self.type is MessageType.recipient_remove:
            return '{0.name} removed {1.name} from the group.'.format(self.author, self.mentions[0])

        if self.type is MessageType.channel_name_change:
            return '{0.author.name} changed the channel name: {0.content}'.format(self)

        if self.type is MessageType.channel_icon_change:
            return '{0.author.name} changed the channel icon.'.format(self)

        if self.type is MessageType.new_member:
            formats = [
                "{0} just joined the server - glhf!",
                "{0} just joined. Everyone, look busy!",
                "{0} just joined. Can I get a heal?",
                "{0} joined your party.",
                "{0} joined. You must construct additional pylons.",
                "Ermagherd. {0} is here.",
                "Welcome, {0}. Stay awhile and listen.",
                "Welcome, {0}. We were expecting you ( ͡° ͜ʖ ͡°)",
                "Welcome, {0}. We hope you brought pizza.",
                "Welcome {0}. Leave your weapons by the door.",
                "A wild {0} appeared.",
                "Swoooosh. {0} just landed.",
                "Brace yourselves. {0} just joined the server.",
                "{0} just joined... or did they?",
                "{0} just arrived. Seems OP - please nerf.",
                "{0} just slid into the server.",
                "A {0} has spawned in the server.",
                "Big {0} showed up!",
                "Where’s {0}? In the server!",
                "{0} hopped into the server. Kangaroo!!",
                "{0} just showed up. Hold my beer.",
                "Challenger approaching - {0} has appeared!",
                "It's a bird! It's a plane! Nevermind, it's just {0}.",
                "It's {0}! Praise the sun! \\[T]/",
                "Never gonna give {0} up. Never gonna let {0} down.",
                "{0} has joined the battle bus.",
                "Cheers, love! {0}'s here!",
                "Hey! Listen! {0} has joined!",
                "We've been expecting you {0}",
                "It's dangerous to go alone, take {0}!",
                "{0} has joined the server! It's super effective!",
                "Cheers, love! {0} is here!",
                "{0} is here, as the prophecy foretold.",
                "{0} has arrived. Party's over.",
                "Ready player {0}",
                "{0} is here to kick butt and chew bubblegum. And {0} is all out of gum.",
                "Hello. Is it {0} you're looking for?",
                "{0} has joined. Stay a while and listen!",
                "Roses are red, violets are blue, {0} joined this server with you",
            ]

            # manually reconstruct the epoch with millisecond precision, because
            # datetime.datetime.timestamp() doesn't return the exact posix
            # timestamp with the precision that we need
            created_at_ms = int((self.created_at - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
            return formats[created_at_ms % len(formats)].format(self.author.name)

        if self.type is MessageType.call:
            # we're at the call message type now, which is a bit more complicated.
            # we can make the assumption that Message.channel is a PrivateChannel
            # with the type ChannelType.group or ChannelType.private
            call_ended = self.call.ended_timestamp is not None

            if self.channel.me in self.call.participants:
                return '{0.author.name} started a call.'.format(self)
            elif call_ended:
                return 'You missed a call from {0.author.name}'.format(self)
            else:
                return '{0.author.name} started a call \N{EM DASH} Join the call.'.format(self)

        if self.type is MessageType.premium_guild_subscription:
            return '{0.author.name} just boosted the server!'.format(self)

        if self.type is MessageType.premium_guild_tier_1:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 1!**'.format(self)

        if self.type is MessageType.premium_guild_tier_2:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 2!**'.format(self)

        if self.type is MessageType.premium_guild_tier_3:
            return '{0.author.name} just boosted the server! {0.guild} has achieved **Level 3!**'.format(self)

    async def delete(self, *, delay=None):
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you need the :attr:`~Permissions.manage_messages`
        permission.

        .. versionchanged:: 1.1.0
            Added the new ``delay`` keyword-only parameter.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        HTTPException
            Deleting the message failed.
        """
        if delay is not None:
            async def delete():
                await asyncio.sleep(delay, loop=self._state.loop)
                try:
                    await self._state.http.delete_message(self.channel.id, self.id)
                except HTTPException:
                    pass

            asyncio.ensure_future(delete(), loop=self._state.loop)
        else:
            await self._state.http.delete_message(self.channel.id, self.id)

    async def edit(self, **fields):
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.

        Raises
        -------
        HTTPException
            Editing the message failed.
        """

        try:
            content = fields['content']
        except KeyError:
            pass
        else:
            if content is not None:
                fields['content'] = str(content)

        try:
            embed = fields['embed']
        except KeyError:
            pass
        else:
            if embed is not None:
                fields['embed'] = embed.to_dict()

        data = await self._state.http.edit_message(self.channel.id, self.id, **fields)
        self._update(data)

        try:
            delete_after = fields['delete_after']
        except KeyError:
            pass
        else:
            if delete_after is not None:
                await self.delete(delay=delete_after)

    async def pin(self):
        """|coro|

        Pins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Raises
        -------
        Forbidden
            You do not have permissions to pin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Pinning the message failed, probably due to the channel
            having more than 50 pinned messages.
        """

        await self._state.http.pin_message(self.channel.id, self.id)
        self.pinned = True

    async def unpin(self):
        """|coro|

        Unpins the message.

        You must have the :attr:`~Permissions.manage_messages` permission to do
        this in a non-private channel context.

        Raises
        -------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Unpinning the message failed.
        """

        await self._state.http.unpin_message(self.channel.id, self.id)
        self.pinned = False

    async def add_reaction(self, emoji):
        """|coro|

        Add a reaction to the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You must have the :attr:`~Permissions.read_message_history` permission
        to use this. If nobody else has reacted to the message using this
        emoji, the :attr:`~Permissions.add_reactions` permission is required.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to react with.

        Raises
        --------
        HTTPException
            Adding the reaction failed.
        Forbidden
            You do not have the proper permissions to react to the message.
        NotFound
            The emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = self._emoji_reaction(emoji)
        await self._state.http.add_reaction(self.channel.id, self.id, emoji)

    async def remove_reaction(self, emoji, member):
        """|coro|

        Remove a reaction by the member from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        If the reaction is not your own (i.e. ``member`` parameter is not you) then
        the :attr:`~Permissions.manage_messages` permission is needed.

        The ``member`` parameter must represent a member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to remove.
        member: :class:`abc.Snowflake`
            The member for which to remove the reaction.

        Raises
        --------
        HTTPException
            Removing the reaction failed.
        Forbidden
            You do not have the proper permissions to remove the reaction.
        NotFound
            The member or emoji you specified was not found.
        InvalidArgument
            The emoji parameter is invalid.
        """

        emoji = self._emoji_reaction(emoji)

        if member.id == self._state.self_id:
            await self._state.http.remove_own_reaction(self.channel.id, self.id, emoji)
        else:
            await self._state.http.remove_reaction(self.channel.id, self.id, emoji, member.id)

    @staticmethod
    def _emoji_reaction(emoji):
        if isinstance(emoji, Reaction):
            emoji = emoji.emoji

        if isinstance(emoji, Emoji):
            return '%s:%s' % (emoji.name, emoji.id)
        if isinstance(emoji, PartialEmoji):
            return emoji._as_reaction()
        if isinstance(emoji, str):
            # Reactions can be in :name:id format, but not <:name:id>.
            # No existing emojis have <> in them, so this should be okay.
            return emoji.strip('<>')

        raise InvalidArgument('emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.'.format(emoji))

    async def clear_reactions(self):
        """|coro|

        Removes all the reactions from the message.

        You need the :attr:`~Permissions.manage_messages` permission to use this.

        Raises
        --------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        await self._state.http.clear_reactions(self.channel.id, self.id)

    async def ack(self):
        """|coro|

        Marks this message as read.

        The user must not be a bot user.

        Raises
        -------
        HTTPException
            Acking failed.
        ClientException
            You must not be a bot user.
        """

        state = self._state
        if state.is_bot:
            raise ClientException('Must not be a bot account to ack messages.')
        return await state.http.ack_message(self.channel.id, self.id)
