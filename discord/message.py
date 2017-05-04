# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2017 Rapptz

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
import re

from . import utils
from .reaction import Reaction
from .emoji import Emoji
from .calls import CallMessage
from .enums import MessageType, try_enum
from .errors import InvalidArgument, ClientException
from .embeds import Embed

class Message:
    """Represents a message from Discord.

    There should be no need to create one of these manually.

    Attributes
    -----------
    tts: bool
        Specifies if the message was done with text-to-speech.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel, then it is a :class:`User` instead.
    content: str
        The actual contents of the message.
    nonce
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is typically non-important.
    embeds: List[:class:`Embed`]
        A list embeds the message has.
    channel
        The :class:`TextChannel` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    call: Optional[:class:`CallMessage`]
        The call that the message refers to. This is only applicable to messages of type
        :attr:`MessageType.call`.
    mention_everyone: bool
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` text is in the message itself.
            Rather this boolean indicates if the ``@everyone`` text is in the message
            **and** it did end up mentioning everyone.

    mentions: list
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a discord limitation, not one with the library.

    channel_mentions: list
        A list of :class:`Channel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: list
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: int
        The message ID.
    webhook_id: Optional[int]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: list
        A list of attachments given to a message.
    pinned: bool
        Specifies if the message is currently pinned.
    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    """

    __slots__ = ( '_edited_timestamp', 'tts', 'content', 'channel', 'webhook_id',
                  'mention_everyone', 'embeds', 'id', 'mentions', 'author',
                  '_cs_channel_mentions', '_cs_raw_mentions', 'attachments',
                  '_cs_clean_content', '_cs_raw_channel_mentions', 'nonce', 'pinned',
                  'role_mentions', '_cs_raw_role_mentions', 'type', 'call',
                  '_cs_system_content', '_cs_guild', '_state', 'reactions' )

    def __init__(self, *, state, channel, data):
        self._state = state
        self.id = int(data['id'])
        self.reactions = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self._update(channel, data)

    def __repr__(self):
        return '<Message id={0.id} pinned={0.pinned} author={0.author!r}>'.format(self)

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

    def _add_reaction(self, data):
        emoji = self._state.get_reaction_emoji(data['emoji'])
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)
        is_me = data['me'] = int(data['user_id']) == self._state.self_id

        if reaction is None:
            reaction = Reaction(message=self, data=data, emoji=emoji)
            self.reactions.append(reaction)
        else:
            reaction.count += 1
            if is_me:
                reaction.me = is_me

        return reaction

    def _remove_reaction(self, data):
        emoji = self._state.get_reaction_emoji(data['emoji'])
        reaction = utils.find(lambda r: r.emoji == emoji, self.reactions)

        if reaction is None:
            # already removed?
            raise ValueError('Emoji already removed?')

        # if reaction isn't in the list, we crash. This means discord
        # sent bad data, or we stored improperly
        reaction.count -= 1

        if int(data['user_id']) == self._state.self_id:
            reaction.me = False
        if reaction.count == 0:
            # this raises ValueError if something went wrong as well.
            self.reactions.remove(reaction)

        return reaction

    def _update(self, channel, data):
        self.channel = channel
        self._edited_timestamp = utils.parse_time(data.get('edited_timestamp'))
        self._try_patch(data, 'pinned')
        self._try_patch(data, 'mention_everyone')
        self._try_patch(data, 'tts')
        self._try_patch(data, 'type', lambda x: try_enum(MessageType, x))
        self._try_patch(data, 'content')
        self._try_patch(data, 'attachments')
        self._try_patch(data, 'embeds', lambda x: list(map(Embed.from_data, x)))
        self._try_patch(data, 'nonce')

        for handler in ('author', 'mentions', 'mention_roles', 'call'):
            try:
                getattr(self, '_handle_%s' % handler)(data[handler])
            except KeyError:
                continue

        # clear the cached properties
        cached = filter(lambda attr: attr.startswith('_cs_'), self.__slots__)
        for attr in cached:
            try:
                delattr(self, attr)
            except AttributeError:
                pass

    def _handle_author(self, author):
        self.author = self._state.store_user(author)
        if self.guild is not None:
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_mentions(self, mentions):
        self.mentions = []
        if self.guild is None:
            self.mentions = [self._state.store_user(m) for m in mentions]
            return

        for mention in mentions:
            id_search = int(mention['id'])
            member = self.guild.get_member(id_search)
            if member is not None:
                self.mentions.append(member)

    def _handle_mention_roles(self, role_mentions):
        self.role_mentions = []
        if self.guild is not None:
            for role_id in map(int, role_mentions):
                role = utils.get(self.guild.roles, id=role_id)
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
        """A property that returns an array of user IDs matched with
        the syntax of <@user_id> in the message content.

        This allows you receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r'<@!?([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self):
        """A property that returns an array of channel IDs matched with
        the syntax of <#channel_id> in the message content.
        """
        return [int(x) for x in re.findall(r'<#([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self):
        """A property that returns an array of role IDs matched with
        the syntax of <@&role_id> in the message content.
        """
        return [int(x) for x in re.findall(r'<@&([0-9]+)>', self.content)]

    @utils.cached_slot_property('_cs_channel_mentions')
    def channel_mentions(self):
        if self.guild is None:
            return []
        it = filter(None, map(lambda m: self.guild.get_channel(m), self.raw_channel_mentions))
        return utils._unique(it)

    @utils.cached_slot_property('_cs_clean_content')
    def clean_content(self):
        """A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.

        This will also transform @everyone and @here mentions into
        non-mentions.
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
        """datetime.datetime: The message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self):
        """Optional[datetime.datetime]: A naive UTC datetime object containing the edited time of the message."""
        return self._edited_timestamp

    @utils.cached_slot_property('_cs_system_content')
    def system_content(self):
        """A property that returns the content that is rendered
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
                "%s just joined the server - glhf!",
                "%s just joined. Everyone, look busy!",
                "%s just joined. Can I get a heal?",
                "%s joined your party.",
                "%s joined. You must construct additional pylons.",
                "Ermagherd. %s is here.",
                "Welcome, %s. Stay awhile and listen.",
                "Welcome, %s. We were expecting you ( ͡° ͜ʖ ͡°)",
                "Welcome, %s. We hope you brought pizza.",
                "Welcome %s. Leave your weapons by the door.",
                "A wild %s appeared.",
                "Swoooosh. %s just landed.",
                "Brace yourselves. %s just joined the server.",
                "%s just joined. Hide your bananas.",
                "%s just arrived. Seems OP - please nerf.",
                "%s just slid into the server.",
                "A %s has spawned in the server.",
                "Big %s showed up!",
                "Where’s %s? In the server!",
                "%s hopped into the server. Kangaroo!!",
                "%s just showed up. Hold my beer.",
            ]

            index = int(self.created_at.timestamp()) % len(formats)
            return formats[index] % self.author.name

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

    @asyncio.coroutine
    def delete(self):
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you need the :attr:`Permissions.manage_messages`
        permission.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        HTTPException
            Deleting the message failed.
        """
        yield from self._state.http.delete_message(self.channel.id, self.id)

    @asyncio.coroutine
    def edit(self, **fields):
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        Parameters
        -----------
        content: str
            The new content to replace the message with.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.

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

        data = yield from self._state.http.edit_message(self.id, self.channel.id, **fields)
        self._update(channel=self.channel, data=data)

    @asyncio.coroutine
    def pin(self):
        """|coro|

        Pins the message. You must have :attr:`Permissions.manage_messages`
        permissions to do this in a non-private channel context.

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

        yield from self._state.http.pin_message(self.channel.id, self.id)
        self.pinned = True

    @asyncio.coroutine
    def unpin(self):
        """|coro|

        Unpins the message. You must have :attr:`Permissions.manage_messages`
        permissions to do this in a non-private channel context.

        Raises
        -------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Unpinning the message failed.
        """

        yield from self._state.http.unpin_message(self.channel.id, self.id)
        self.pinned = False

    @asyncio.coroutine
    def add_reaction(self, emoji):
        """|coro|

        Add a reaction to the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You must have the :attr:`Permissions.add_reactions` permission to
        add new reactions to a message.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, str]
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

        if isinstance(emoji, Reaction):
            emoji = str(emoji.emoji)
        elif isinstance(emoji, Emoji):
            emoji = '%s:%s' % (emoji.name, emoji.id)
        elif isinstance(emoji, str):
            pass # this is okay
        else:
            raise InvalidArgument('emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.'.format(emoji))

        yield from self._state.http.add_reaction(self.id, self.channel.id, emoji)

    @asyncio.coroutine
    def remove_reaction(self, emoji, member):
        """|coro|

        Remove a reaction by the member from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        If the reaction is not your own (i.e. ``member`` parameter is not you) then
        the :attr:`Permissions.manage_messages` permission is needed.

        The ``member`` parameter must represent a member and meet
        the :class:`abc.Snowflake` abc.

        Parameters
        ------------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, str]
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

        if isinstance(emoji, Reaction):
            emoji = str(emoji.emoji)
        elif isinstance(emoji, Emoji):
            emoji = '%s:%s' % (emoji.name, emoji.id)
        elif isinstance(emoji, str):
            pass # this is okay
        else:
            raise InvalidArgument('emoji argument must be str, Emoji, or Reaction not {.__class__.__name__}.'.format(emoji))

        yield from self._state.http.remove_reaction(self.id, self.channel.id, emoji, member.id)

    @asyncio.coroutine
    def clear_reactions(self):
        """|coro|

        Removes all the reactions from the message.

        You need :attr:`Permissions.manage_messages` permission
        to use this.

        Raises
        --------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        yield from self._state.http.clear_reactions(self.id, self.channel.id)

    def ack(self):
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
        return state.http.ack_message(self.channel.id, self.id)
