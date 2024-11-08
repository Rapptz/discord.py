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

import asyncio
import datetime
import re
import io
from os import PathLike
from typing import (
    Dict,
    TYPE_CHECKING,
    Literal,
    Sequence,
    Union,
    List,
    Optional,
    Any,
    Callable,
    Tuple,
    ClassVar,
    Type,
    overload,
)

from . import utils
from .asset import Asset
from .reaction import Reaction
from .emoji import Emoji
from .partial_emoji import PartialEmoji
from .enums import InteractionType, MessageReferenceType, MessageType, ChannelType, try_enum
from .errors import HTTPException
from .components import _component_factory
from .embeds import Embed
from .member import Member
from .flags import MessageFlags, AttachmentFlags
from .file import File
from .utils import escape_mentions, MISSING, deprecated
from .http import handle_message_parameters
from .guild import Guild
from .mixins import Hashable
from .sticker import StickerItem, GuildSticker
from .threads import Thread
from .channel import PartialMessageable
from .poll import Poll

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.message import (
        Message as MessagePayload,
        Attachment as AttachmentPayload,
        MessageReference as MessageReferencePayload,
        MessageSnapshot as MessageSnapshotPayload,
        MessageApplication as MessageApplicationPayload,
        MessageActivity as MessageActivityPayload,
        RoleSubscriptionData as RoleSubscriptionDataPayload,
        MessageInteractionMetadata as MessageInteractionMetadataPayload,
        CallMessage as CallMessagePayload,
        PurchaseNotificationResponse as PurchaseNotificationResponsePayload,
        GuildProductPurchase as GuildProductPurchasePayload,
    )

    from .types.interactions import MessageInteraction as MessageInteractionPayload

    from .types.components import Component as ComponentPayload
    from .types.threads import ThreadArchiveDuration
    from .types.member import (
        Member as MemberPayload,
        UserWithMember as UserWithMemberPayload,
    )
    from .types.user import User as UserPayload
    from .types.embed import Embed as EmbedPayload
    from .types.gateway import MessageReactionRemoveEvent, MessageUpdateEvent
    from .abc import Snowflake
    from .abc import GuildChannel, MessageableChannel
    from .components import ActionRow, ActionRowChildComponentType
    from .state import ConnectionState
    from .mentions import AllowedMentions
    from .user import User
    from .role import Role
    from .ui.view import View

    EmojiInputType = Union[Emoji, PartialEmoji, str]
    MessageComponentType = Union[ActionRow, ActionRowChildComponentType]


__all__ = (
    'Attachment',
    'Message',
    'PartialMessage',
    'MessageInteraction',
    'MessageReference',
    'MessageSnapshot',
    'DeletedReferencedMessage',
    'MessageApplication',
    'RoleSubscriptionInfo',
    'MessageInteractionMetadata',
    'CallMessage',
    'GuildProductPurchase',
    'PurchaseNotification',
)


def convert_emoji_reaction(emoji: Union[EmojiInputType, Reaction]) -> str:
    if isinstance(emoji, Reaction):
        emoji = emoji.emoji

    if isinstance(emoji, Emoji):
        return f'{emoji.name}:{emoji.id}'
    if isinstance(emoji, PartialEmoji):
        return emoji._as_reaction()
    if isinstance(emoji, str):
        # Reactions can be in :name:id format, but not <:name:id>.
        # No existing emojis have <> in them, so this should be okay.
        return emoji.strip('<>')

    raise TypeError(f'emoji argument must be str, Emoji, or Reaction not {emoji.__class__.__name__}.')


class Attachment(Hashable):
    """Represents an attachment from Discord.

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the attachment.

        .. describe:: x == y

            Checks if the attachment is equal to another attachment.

        .. describe:: x != y

            Checks if the attachment is not equal to another attachment.

        .. describe:: hash(x)

            Returns the hash of the attachment.

    .. versionchanged:: 1.7
        Attachment can now be casted to :class:`str` and is hashable.

    Attributes
    ------------
    id: :class:`int`
        The attachment ID.
    size: :class:`int`
        The attachment size in bytes.
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    filename: :class:`str`
        The attachment's filename.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    proxy_url: :class:`str`
        The proxy URL. This is a cached version of the :attr:`~Attachment.url` in the
        case of images. When the message is deleted, this URL might be valid for a few
        minutes or not valid at all.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_

        .. versionadded:: 1.7
    description: Optional[:class:`str`]
        The attachment's description. Only applicable to images.

        .. versionadded:: 2.0
    ephemeral: :class:`bool`
        Whether the attachment is ephemeral.

        .. versionadded:: 2.0
    duration: Optional[:class:`float`]
        The duration of the audio file in seconds. Returns ``None`` if it's not a voice message.

        .. versionadded:: 2.3
    waveform: Optional[:class:`bytes`]
        The waveform (amplitudes) of the audio in bytes. Returns ``None`` if it's not a voice message.

        .. versionadded:: 2.3
    title: Optional[:class:`str`]
        The normalised version of the attachment's filename.

        .. versionadded:: 2.5
    """

    __slots__ = (
        'id',
        'size',
        'height',
        'width',
        'filename',
        'url',
        'proxy_url',
        '_http',
        'content_type',
        'description',
        'ephemeral',
        'duration',
        'waveform',
        '_flags',
        'title',
    )

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = int(data['id'])
        self.size: int = data['size']
        self.height: Optional[int] = data.get('height')
        self.width: Optional[int] = data.get('width')
        self.filename: str = data['filename']
        self.url: str = data['url']
        self.proxy_url: str = data['proxy_url']
        self._http = state.http
        self.content_type: Optional[str] = data.get('content_type')
        self.description: Optional[str] = data.get('description')
        self.ephemeral: bool = data.get('ephemeral', False)
        self.duration: Optional[float] = data.get('duration_secs')
        self.title: Optional[str] = data.get('title')

        waveform = data.get('waveform')
        self.waveform: Optional[bytes] = utils._base64_to_bytes(waveform) if waveform is not None else None

        self._flags: int = data.get('flags', 0)

    @property
    def flags(self) -> AttachmentFlags:
        """:class:`AttachmentFlags`: The attachment's flags."""
        return AttachmentFlags._from_value(self._flags)

    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.filename.startswith('SPOILER_')

    def is_voice_message(self) -> bool:
        """:class:`bool`: Whether this attachment is a voice message."""
        return self.duration is not None and 'voice-message' in self.url

    def __repr__(self) -> str:
        return f'<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>'

    def __str__(self) -> str:
        return self.url or ''

    async def save(
        self,
        fp: Union[io.BufferedIOBase, PathLike[Any]],
        *,
        seek_begin: bool = True,
        use_cached: bool = False,
    ) -> int:
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
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)

    async def read(self, *, use_cached: bool = False) -> bytes:
        """|coro|

        Retrieves the content of this attachment as a :class:`bytes` object.

        .. versionadded:: 1.1

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

    async def to_file(
        self,
        *,
        filename: Optional[str] = MISSING,
        description: Optional[str] = MISSING,
        use_cached: bool = False,
        spoiler: bool = False,
    ) -> File:
        """|coro|

        Converts the attachment into a :class:`File` suitable for sending via
        :meth:`abc.Messageable.send`.

        .. versionadded:: 1.3

        Parameters
        -----------
        filename: Optional[:class:`str`]
            The filename to use for the file. If not specified then the filename
            of the attachment is used instead.

            .. versionadded:: 2.0
        description: Optional[:class:`str`]
            The description to use for the file. If not specified then the
            description of the attachment is used instead.

            .. versionadded:: 2.0
        use_cached: :class:`bool`
            Whether to use :attr:`proxy_url` rather than :attr:`url` when downloading
            the attachment. This will allow attachments to be saved after deletion
            more often, compared to the regular URL which is generally deleted right
            after the message is deleted. Note that this can still fail to download
            deleted attachments if too much time has passed and it does not work
            on some types of attachments.

            .. versionadded:: 1.4
        spoiler: :class:`bool`
            Whether the file is a spoiler.

            .. versionadded:: 1.4

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
        :class:`File`
            The attachment as a file suitable for sending.
        """

        data = await self.read(use_cached=use_cached)
        file_filename = filename if filename is not MISSING else self.filename
        file_description = description if description is not MISSING else self.description
        return File(io.BytesIO(data), filename=file_filename, description=file_description, spoiler=spoiler)

    def to_dict(self) -> AttachmentPayload:
        result: AttachmentPayload = {
            'filename': self.filename,
            'id': self.id,
            'proxy_url': self.proxy_url,
            'size': self.size,
            'url': self.url,
            'spoiler': self.is_spoiler(),
        }
        if self.height:
            result['height'] = self.height
        if self.width:
            result['width'] = self.width
        if self.content_type:
            result['content_type'] = self.content_type
        if self.description is not None:
            result['description'] = self.description
        return result


class DeletedReferencedMessage:
    """A special sentinel type given when the resolved message reference
    points to a deleted message.

    The purpose of this class is to separate referenced messages that could not be
    fetched and those that were previously fetched but have since been deleted.

    .. versionadded:: 1.6
    """

    __slots__ = ('_parent',)

    def __init__(self, parent: MessageReference):
        self._parent: MessageReference = parent

    def __repr__(self) -> str:
        return f"<DeletedReferencedMessage id={self.id} channel_id={self.channel_id} guild_id={self.guild_id!r}>"

    @property
    def id(self) -> int:
        """:class:`int`: The message ID of the deleted referenced message."""
        # the parent's message id won't be None here
        return self._parent.message_id  # type: ignore

    @property
    def channel_id(self) -> int:
        """:class:`int`: The channel ID of the deleted referenced message."""
        return self._parent.channel_id

    @property
    def guild_id(self) -> Optional[int]:
        """Optional[:class:`int`]: The guild ID of the deleted referenced message."""
        return self._parent.guild_id


class MessageSnapshot:
    """Represents a message snapshot attached to a forwarded message.

    .. versionadded:: 2.5

    Attributes
    -----------
    type: :class:`MessageType`
        The type of the forwarded message.
    content: :class:`str`
        The actual contents of the forwarded message.
    embeds: List[:class:`Embed`]
        A list of embeds the forwarded message has.
    attachments: List[:class:`Attachment`]
        A list of attachments given to the forwarded message.
    created_at: :class:`datetime.datetime`
        The forwarded message's time of creation.
    flags: :class:`MessageFlags`
        Extra features of the the message snapshot.
    stickers: List[:class:`StickerItem`]
        A list of sticker items given to the message.
    components: List[Union[:class:`ActionRow`, :class:`Button`, :class:`SelectMenu`]]
        A list of components in the message.
    """

    __slots__ = (
        '_cs_raw_channel_mentions',
        '_cs_cached_message',
        '_cs_raw_mentions',
        '_cs_raw_role_mentions',
        '_edited_timestamp',
        'attachments',
        'content',
        'embeds',
        'flags',
        'created_at',
        'type',
        'stickers',
        'components',
        '_state',
    )

    @classmethod
    def _from_value(
        cls,
        state: ConnectionState,
        message_snapshots: Optional[List[Dict[Literal['message'], MessageSnapshotPayload]]],
    ) -> List[Self]:
        if not message_snapshots:
            return []

        return [cls(state, snapshot['message']) for snapshot in message_snapshots]

    def __init__(self, state: ConnectionState, data: MessageSnapshotPayload):
        self.type: MessageType = try_enum(MessageType, data['type'])
        self.content: str = data['content']
        self.embeds: List[Embed] = [Embed.from_dict(a) for a in data['embeds']]
        self.attachments: List[Attachment] = [Attachment(data=a, state=state) for a in data['attachments']]
        self.created_at: datetime.datetime = utils.parse_time(data['timestamp'])
        self._edited_timestamp: Optional[datetime.datetime] = utils.parse_time(data['edited_timestamp'])
        self.flags: MessageFlags = MessageFlags._from_value(data.get('flags', 0))
        self.stickers: List[StickerItem] = [StickerItem(data=d, state=state) for d in data.get('stickers_items', [])]

        self.components: List[MessageComponentType] = []
        for component_data in data.get('components', []):
            component = _component_factory(component_data)
            if component is not None:
                self.components.append(component)

        self._state: ConnectionState = state

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f'<{name} type={self.type!r} created_at={self.created_at!r} flags={self.flags!r}>'

    @utils.cached_slot_property('_cs_raw_mentions')
    def raw_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of user IDs matched with
        the syntax of ``<@user_id>`` in the message content.

        This allows you to receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r'<@!?([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of channel IDs matched with
        the syntax of ``<#channel_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<#([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of role IDs matched with
        the syntax of ``<@&role_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<@&([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_cached_message')
    def cached_message(self) -> Optional[Message]:
        """Optional[:class:`Message`]: Returns the cached message this snapshot points to, if any."""
        state = self._state
        return (
            utils.find(
                lambda m: (
                    m.created_at == self.created_at
                    and m.edited_at == self.edited_at
                    and m.content == self.content
                    and m.embeds == self.embeds
                    and m.components == self.components
                    and m.stickers == self.stickers
                    and m.attachments == self.attachments
                    and m.flags == self.flags
                ),
                reversed(state._messages),
            )
            if state._messages
            else None
        )

    @property
    def edited_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: An aware UTC datetime object containing the edited time of the forwarded message."""
        return self._edited_timestamp


class MessageReference:
    """Represents a reference to a :class:`~discord.Message`.

    .. versionadded:: 1.5

    .. versionchanged:: 1.6
        This class can now be constructed by users.

    Attributes
    -----------
    type: :class:`MessageReferenceType`
        The type of message reference.

        .. versionadded:: 2.5
    message_id: Optional[:class:`int`]
        The id of the message referenced.
    channel_id: :class:`int`
        The channel id of the message referenced.
    guild_id: Optional[:class:`int`]
        The guild id of the message referenced.
    fail_if_not_exists: :class:`bool`
        Whether the referenced message should raise :class:`HTTPException`
        if the message no longer exists or Discord could not fetch the message.

        .. versionadded:: 1.7

    resolved: Optional[Union[:class:`Message`, :class:`DeletedReferencedMessage`]]
        The message that this reference resolved to. If this is ``None``
        then the original message was not fetched either due to the Discord API
        not attempting to resolve it or it not being available at the time of creation.
        If the message was resolved at a prior point but has since been deleted then
        this will be of type :class:`DeletedReferencedMessage`.

        .. versionadded:: 1.6
    """

    __slots__ = ('type', 'message_id', 'channel_id', 'guild_id', 'fail_if_not_exists', 'resolved', '_state')

    def __init__(
        self,
        *,
        message_id: int,
        channel_id: int,
        guild_id: Optional[int] = None,
        fail_if_not_exists: bool = True,
        type: MessageReferenceType = MessageReferenceType.reply,
    ):
        self._state: Optional[ConnectionState] = None
        self.type: MessageReferenceType = type
        self.resolved: Optional[Union[Message, DeletedReferencedMessage]] = None
        self.message_id: Optional[int] = message_id
        self.channel_id: int = channel_id
        self.guild_id: Optional[int] = guild_id
        self.fail_if_not_exists: bool = fail_if_not_exists

    @classmethod
    def with_state(cls, state: ConnectionState, data: MessageReferencePayload) -> Self:
        self = cls.__new__(cls)
        self.type = try_enum(MessageReferenceType, data.get('type', 0))
        self.message_id = utils._get_as_snowflake(data, 'message_id')
        self.channel_id = int(data['channel_id'])
        self.guild_id = utils._get_as_snowflake(data, 'guild_id')
        self.fail_if_not_exists = data.get('fail_if_not_exists', True)
        self._state = state
        self.resolved = None
        return self

    @classmethod
    def from_message(
        cls,
        message: PartialMessage,
        *,
        fail_if_not_exists: bool = True,
        type: MessageReferenceType = MessageReferenceType.reply,
    ) -> Self:
        """Creates a :class:`MessageReference` from an existing :class:`~discord.Message`.

        .. versionadded:: 1.6

        Parameters
        ----------
        message: :class:`~discord.Message`
            The message to be converted into a reference.
        fail_if_not_exists: :class:`bool`
            Whether the referenced message should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7
        type: :class:`~discord.MessageReferenceType`
            The type of message reference this is.

            .. versionadded:: 2.5

        Returns
        -------
        :class:`MessageReference`
            A reference to the message.
        """
        self = cls(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=getattr(message.guild, 'id', None),
            fail_if_not_exists=fail_if_not_exists,
            type=type,
        )
        self._state = message._state
        return self

    @property
    def cached_message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The cached message, if found in the internal message cache."""
        return self._state and self._state._get_message(self.message_id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the referenced message.

        .. versionadded:: 1.7
        """
        guild_id = self.guild_id if self.guild_id is not None else '@me'
        return f'https://discord.com/channels/{guild_id}/{self.channel_id}/{self.message_id}'

    def __repr__(self) -> str:
        return f'<MessageReference message_id={self.message_id!r} channel_id={self.channel_id!r} guild_id={self.guild_id!r}>'

    def to_dict(self) -> MessageReferencePayload:
        result: Dict[str, Any] = (
            {'type': self.type.value, 'message_id': self.message_id} if self.message_id is not None else {}
        )
        result['channel_id'] = self.channel_id
        if self.guild_id is not None:
            result['guild_id'] = self.guild_id
        if self.fail_if_not_exists is not None:
            result['fail_if_not_exists'] = self.fail_if_not_exists
        return result  # type: ignore # Type checker doesn't understand these are the same.

    to_message_reference_dict = to_dict


class MessageInteraction(Hashable):
    """Represents the interaction that a :class:`Message` is a response to.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two message interactions are equal.

        .. describe:: x != y

            Checks if two message interactions are not equal.

        .. describe:: hash(x)

            Returns the message interaction's hash.

    Attributes
    -----------
    id: :class:`int`
        The interaction ID.
    type: :class:`InteractionType`
        The interaction type.
    name: :class:`str`
        The name of the interaction.
    user: Union[:class:`User`, :class:`Member`]
        The user or member that invoked the interaction.
    """

    __slots__: Tuple[str, ...] = ('id', 'type', 'name', 'user')

    def __init__(self, *, state: ConnectionState, guild: Optional[Guild], data: MessageInteractionPayload) -> None:
        self.id: int = int(data['id'])
        self.type: InteractionType = try_enum(InteractionType, data['type'])
        self.name: str = data['name']
        self.user: Union[User, Member] = MISSING

        try:
            payload = data['member']
        except KeyError:
            self.user = state.create_user(data['user'])
        else:
            if guild is None:
                # This is an unfortunate data loss, but it's better than giving bad data
                # This is also an incredibly rare scenario.
                self.user = state.create_user(data['user'])
            else:
                payload['user'] = data['user']
                self.user = Member(data=payload, guild=guild, state=state)  # type: ignore

    def __repr__(self) -> str:
        return f'<MessageInteraction id={self.id} name={self.name!r} type={self.type!r} user={self.user!r}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The interaction's creation time in UTC."""
        return utils.snowflake_time(self.id)


class MessageInteractionMetadata(Hashable):
    """Represents the interaction metadata of a :class:`Message` if
    it was sent in response to an interaction.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two message interactions are equal.

        .. describe:: x != y

            Checks if two message interactions are not equal.

        .. describe:: hash(x)

            Returns the message interaction's hash.

    Attributes
    -----------
    id: :class:`int`
        The interaction ID.
    type: :class:`InteractionType`
        The interaction type.
    user: :class:`User`
        The user that invoked the interaction.
    original_response_message_id: Optional[:class:`int`]
        The ID of the original response message if the message is a follow-up.
    interacted_message_id: Optional[:class:`int`]
        The ID of the message that containes the interactive components, if applicable.
    modal_interaction: Optional[:class:`.MessageInteractionMetadata`]
        The metadata of the modal submit interaction that triggered this interaction, if applicable.
    target_user: Optional[:class:`User`]
        The user the command was run on, only applicable to user context menus.

        .. versionadded:: 2.5
    target_message_id: Optional[:class:`int`]
        The ID of the message the command was run on, only applicable to message context menus.

        .. versionadded:: 2.5
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'type',
        'user',
        'original_response_message_id',
        'interacted_message_id',
        'modal_interaction',
        'target_user',
        'target_message_id',
        '_integration_owners',
        '_state',
        '_guild',
    )

    def __init__(self, *, state: ConnectionState, guild: Optional[Guild], data: MessageInteractionMetadataPayload) -> None:
        self._guild: Optional[Guild] = guild
        self._state: ConnectionState = state

        self.id: int = int(data['id'])
        self.type: InteractionType = try_enum(InteractionType, data['type'])
        self.user: User = state.create_user(data['user'])
        self._integration_owners: Dict[int, int] = {
            int(key): int(value) for key, value in data.get('authorizing_integration_owners', {}).items()
        }

        self.original_response_message_id: Optional[int] = None
        try:
            self.original_response_message_id = int(data['original_response_message_id'])  # type: ignore # EAFP
        except KeyError:
            pass

        self.interacted_message_id: Optional[int] = None
        try:
            self.interacted_message_id = int(data['interacted_message_id'])  # type: ignore # EAFP
        except KeyError:
            pass

        self.modal_interaction: Optional[MessageInteractionMetadata] = None
        try:
            self.modal_interaction = MessageInteractionMetadata(
                state=state, guild=guild, data=data['triggering_interaction_metadata']  # type: ignore # EAFP
            )
        except KeyError:
            pass

        self.target_user: Optional[User] = None
        try:
            self.target_user = state.create_user(data['target_user'])  # type: ignore # EAFP
        except KeyError:
            pass

        self.target_message_id: Optional[int] = None
        try:
            self.target_message_id = int(data['target_message_id'])  # type: ignore # EAFP
        except KeyError:
            pass

    def __repr__(self) -> str:
        return f'<MessageInteraction id={self.id} type={self.type!r} user={self.user!r}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The interaction's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def original_response_message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The original response message if the message
        is a follow-up and is found in cache.
        """
        if self.original_response_message_id:
            return self._state._get_message(self.original_response_message_id)
        return None

    @property
    def interacted_message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The message that
        containes the interactive components, if applicable and is found in cache.
        """
        if self.interacted_message_id:
            return self._state._get_message(self.interacted_message_id)
        return None

    @property
    def target_message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The target message, if applicable and is found in cache.

        .. versionadded:: 2.5
        """
        if self.target_message_id:
            return self._state._get_message(self.target_message_id)
        return None

    def is_guild_integration(self) -> bool:
        """:class:`bool`: Returns ``True`` if the interaction is a guild integration."""
        if self._guild:
            return self._guild.id == self._integration_owners.get(0)

        return False

    def is_user_integration(self) -> bool:
        """:class:`bool`: Returns ``True`` if the interaction is a user integration."""
        return self.user.id == self._integration_owners.get(1)


def flatten_handlers(cls: Type[Message]) -> Type[Message]:
    prefix = len('_handle_')
    handlers = [
        (key[prefix:], value)
        for key, value in cls.__dict__.items()
        if key.startswith('_handle_') and key != '_handle_member'
    ]

    # store _handle_member last
    handlers.append(('member', cls._handle_member))
    cls._HANDLERS = handlers
    cls._CACHED_SLOTS = [attr for attr in cls.__slots__ if attr.startswith('_cs_')]
    return cls


class MessageApplication:
    """Represents a message's application data from a :class:`~discord.Message`.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The application ID.
    description: :class:`str`
        The application description.
    name: :class:`str`
        The application's name.
    """

    __slots__ = ('_state', '_icon', '_cover_image', 'id', 'description', 'name')

    def __init__(self, *, state: ConnectionState, data: MessageApplicationPayload) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.description: str = data['description']
        self.name: str = data['name']
        self._icon: Optional[str] = data['icon']
        self._cover_image: Optional[str] = data.get('cover_image')

    def __repr__(self) -> str:
        return f'<MessageApplication id={self.id} name={self.name!r}>'

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: The application's icon, if any."""
        if self._icon:
            return Asset._from_app_icon(state=self._state, object_id=self.id, icon_hash=self._icon, asset_type='icon')
        return None

    @property
    def cover(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: The application's cover image, if any."""
        if self._cover_image:
            return Asset._from_app_icon(
                state=self._state, object_id=self.id, icon_hash=self._cover_image, asset_type='cover_image'
            )
        return None


class CallMessage:
    """Represents a message's call data in a private channel from a :class:`~discord.Message`.

    .. versionadded:: 2.5

    Attributes
    -----------
    ended_timestamp: Optional[:class:`datetime.datetime`]
        The timestamp the call has ended.
    participants: List[:class:`User`]
        A list of users that participated in the call.
    """

    __slots__ = ('_message', 'ended_timestamp', 'participants')

    def __repr__(self) -> str:
        return f'<CallMessage participants={self.participants!r}>'

    def __init__(self, *, state: ConnectionState, message: Message, data: CallMessagePayload):
        self._message: Message = message
        self.ended_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('ended_timestamp'))
        self.participants: List[User] = []

        for user_id in data['participants']:
            user_id = int(user_id)
            if user_id == self._message.author.id:
                self.participants.append(self._message.author)  # type: ignore # can't be a Member here
            else:
                user = state.get_user(user_id)
                if user is not None:
                    self.participants.append(user)

    @property
    def duration(self) -> datetime.timedelta:
        """:class:`datetime.timedelta`: The duration the call has lasted or is already ongoing."""
        if self.ended_timestamp is None:
            return utils.utcnow() - self._message.created_at
        else:
            return self.ended_timestamp - self._message.created_at

    def is_ended(self) -> bool:
        """:class:`bool`: Whether the call is ended or not."""
        return self.ended_timestamp is not None


class RoleSubscriptionInfo:
    """Represents a message's role subscription information.

    This is currently only attached to messages of type :attr:`MessageType.role_subscription_purchase`.

    .. versionadded:: 2.0

    Attributes
    -----------
    role_subscription_listing_id: :class:`int`
        The ID of the SKU and listing that the user is subscribed to.
    tier_name: :class:`str`
        The name of the tier that the user is subscribed to.
    total_months_subscribed: :class:`int`
        The cumulative number of months that the user has been subscribed for.
    is_renewal: :class:`bool`
        Whether this notification is for a renewal rather than a new purchase.
    """

    __slots__ = (
        'role_subscription_listing_id',
        'tier_name',
        'total_months_subscribed',
        'is_renewal',
    )

    def __init__(self, data: RoleSubscriptionDataPayload) -> None:
        self.role_subscription_listing_id: int = int(data['role_subscription_listing_id'])
        self.tier_name: str = data['tier_name']
        self.total_months_subscribed: int = data['total_months_subscribed']
        self.is_renewal: bool = data['is_renewal']


class GuildProductPurchase:
    """Represents a message's guild product that the user has purchased.

    .. versionadded:: 2.5

    Attributes
    -----------
    listing_id: :class:`int`
        The ID of the listing that the user has purchased.
    product_name: :class:`str`
        The name of the product that the user has purchased.
    """

    __slots__ = ('listing_id', 'product_name')

    def __init__(self, data: GuildProductPurchasePayload) -> None:
        self.listing_id: int = int(data['listing_id'])
        self.product_name: str = data['product_name']

    def __hash__(self) -> int:
        return self.listing_id >> 22

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GuildProductPurchase) and other.listing_id == self.listing_id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


class PurchaseNotification:
    """Represents a message's purchase notification data.

    This is currently only attached to messages of type :attr:`MessageType.purchase_notification`.

    .. versionadded:: 2.5

    Attributes
    -----------
    guild_product_purchase: Optional[:class:`GuildProductPurchase`]
        The guild product purchase that prompted the message.
    """

    __slots__ = ('_type', 'guild_product_purchase')

    def __init__(self, data: PurchaseNotificationResponsePayload) -> None:
        self._type: int = data['type']

        self.guild_product_purchase: Optional[GuildProductPurchase] = None
        guild_product_purchase = data.get('guild_product_purchase')
        if guild_product_purchase is not None:
            self.guild_product_purchase = GuildProductPurchase(guild_product_purchase)


class PartialMessage(Hashable):
    """Represents a partial message to aid with working messages when only
    a message and channel ID are present.

    There are two ways to construct this class. The first one is through
    the constructor itself, and the second is via the following:

    - :meth:`TextChannel.get_partial_message`
    - :meth:`VoiceChannel.get_partial_message`
    - :meth:`StageChannel.get_partial_message`
    - :meth:`Thread.get_partial_message`
    - :meth:`DMChannel.get_partial_message`

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 1.6

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messages are equal.

        .. describe:: x != y

            Checks if two partial messages are not equal.

        .. describe:: hash(x)

            Returns the partial message's hash.

    Attributes
    -----------
    channel: Union[:class:`PartialMessageable`, :class:`TextChannel`, :class:`StageChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`]
        The channel associated with this partial message.
    id: :class:`int`
        The message ID.
    guild: Optional[:class:`Guild`]
        The guild that the partial message belongs to, if applicable.
    """

    __slots__ = ('channel', 'id', '_cs_guild', '_state', 'guild')

    def __init__(self, *, channel: MessageableChannel, id: int) -> None:
        if not isinstance(channel, PartialMessageable) and channel.type not in (
            ChannelType.text,
            ChannelType.voice,
            ChannelType.stage_voice,
            ChannelType.news,
            ChannelType.private,
            ChannelType.news_thread,
            ChannelType.public_thread,
            ChannelType.private_thread,
        ):
            raise TypeError(
                f'expected PartialMessageable, TextChannel, StageChannel, VoiceChannel, DMChannel or Thread not {type(channel)!r}'
            )

        self.channel: MessageableChannel = channel
        self._state: ConnectionState = channel._state
        self.id: int = id

        self.guild: Optional[Guild] = getattr(channel, 'guild', None)

    def _update(self, data: MessageUpdateEvent) -> None:
        # This is used for duck typing purposes.
        # Just do nothing with the data.
        pass

    # Also needed for duck typing purposes
    # n.b. not exposed
    pinned: Any = property(None, lambda x, y: None)

    def __repr__(self) -> str:
        return f'<PartialMessage id={self.id} channel={self.channel!r}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The partial message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to this message."""
        guild_id = getattr(self.guild, 'id', '@me')
        return f'https://discord.com/channels/{guild_id}/{self.channel.id}/{self.id}'

    @property
    def thread(self) -> Optional[Thread]:
        """Optional[:class:`Thread`]: The public thread created from this message, if it exists.

        .. note::

            This does not retrieve archived threads, as they are not retained in the internal
            cache. Use :meth:`fetch_thread` instead.

        .. versionadded:: 2.4
        """
        if self.guild is not None:
            return self.guild.get_thread(self.id)

    async def fetch(self) -> Message:
        """|coro|

        Fetches the partial message to a full :class:`Message`.

        Raises
        --------
        NotFound
            The message was not found.
        Forbidden
            You do not have the permissions required to get a message.
        HTTPException
            Retrieving the message failed.

        Returns
        --------
        :class:`Message`
            The full message.
        """

        data = await self._state.http.get_message(self.channel.id, self.id)
        return self._state.create_message(channel=self.channel, data=data)

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        Your own messages could be deleted without any proper permissions. However to
        delete other people's messages, you must have :attr:`~Permissions.manage_messages`.

        .. versionchanged:: 1.1
            Added the new ``delay`` keyword-only parameter.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message. If the deletion fails then it is silently ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already
        HTTPException
            Deleting the message failed.
        """
        if delay is not None:

            async def delete(delay: float):
                await asyncio.sleep(delay)
                try:
                    await self._state.http.delete_message(self.channel.id, self.id)
                except HTTPException:
                    pass

            asyncio.create_task(delete(delay))
        else:
            await self._state.http.delete_message(self.channel.id, self.id)

    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        embed: Optional[Embed] = ...,
        attachments: Sequence[Union[Attachment, File]] = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        view: Optional[View] = ...,
    ) -> Message:
        ...

    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        embeds: Sequence[Embed] = ...,
        attachments: Sequence[Union[Attachment, File]] = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        view: Optional[View] = ...,
    ) -> Message:
        ...

    async def edit(
        self,
        *,
        content: Optional[str] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        view: Optional[View] = MISSING,
    ) -> Message:
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited message is returned instead.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        embeds: List[:class:`Embed`]
            The new embeds to replace the original with. Must be a maximum of 10.
            To remove all embeds ``[]`` should be passed.

            .. versionadded:: 2.0
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list of attachments to keep in the message as well as new files to upload. If ``[]`` is passed
            then all attachments are removed.

            .. note::

                New files will always appear after current attachments.

            .. versionadded:: 2.0
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress a message without permissions or
            edited a message's content or embed that isn't yours.
        NotFound
            This message does not exist.
        TypeError
            You specified both ``embed`` and ``embeds``

        Returns
        --------
        :class:`Message`
            The newly edited message.
        """

        if content is not MISSING:
            previous_allowed_mentions = self._state.allowed_mentions
        else:
            previous_allowed_mentions = None

        if view is not MISSING:
            self._state.prevent_view_updates_for(self.id)

        with handle_message_parameters(
            content=content,
            embed=embed,
            embeds=embeds,
            attachments=attachments,
            view=view,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
        ) as params:
            data = await self._state.http.edit_message(self.channel.id, self.id, params=params)
            message = Message(state=self._state, channel=self.channel, data=data)

        if view and not view.is_finished():
            interaction: Optional[MessageInteraction] = getattr(self, 'interaction', None)
            if interaction is not None:
                self._state.store_view(view, self.id, interaction_id=interaction.id)
            else:
                self._state.store_view(view, self.id)

        if delete_after is not None:
            await self.delete(delay=delete_after)

        return message

    async def publish(self) -> None:
        """|coro|

        Publishes this message to the channel's followers.

        The message must have been sent in a news channel.
        You must have :attr:`~Permissions.send_messages` to do this.

        If the message is not your own then :attr:`~Permissions.manage_messages`
        is also needed.

        Raises
        -------
        Forbidden
            You do not have the proper permissions to publish this message
            or the channel is not a news channel.
        HTTPException
            Publishing the message failed.
        """

        await self._state.http.publish_message(self.channel.id, self.id)

    async def pin(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Pins the message.

        You must have :attr:`~Permissions.manage_messages` to do
        this in a non-private channel context.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for pinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

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

        await self._state.http.pin_message(self.channel.id, self.id, reason=reason)
        # pinned exists on PartialMessage for duck typing purposes
        self.pinned = True

    async def unpin(self, *, reason: Optional[str] = None) -> None:
        """|coro|

        Unpins the message.

        You must have :attr:`~Permissions.manage_messages` to do
        this in a non-private channel context.

        Parameters
        -----------
        reason: Optional[:class:`str`]
            The reason for unpinning the message. Shows up on the audit log.

            .. versionadded:: 1.4

        Raises
        -------
        Forbidden
            You do not have permissions to unpin the message.
        NotFound
            The message or channel was not found or deleted.
        HTTPException
            Unpinning the message failed.
        """

        await self._state.http.unpin_message(self.channel.id, self.id, reason=reason)
        # pinned exists on PartialMessage for duck typing purposes
        self.pinned = False

    async def add_reaction(self, emoji: Union[EmojiInputType, Reaction], /) -> None:
        """|coro|

        Adds a reaction to the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You must have :attr:`~Permissions.read_message_history`
        to do this. If nobody else has reacted to the message using this
        emoji, :attr:`~Permissions.add_reactions` is required.

        .. versionchanged:: 2.0

            ``emoji`` parameter is now positional-only.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

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
        TypeError
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.add_reaction(self.channel.id, self.id, emoji)

    async def remove_reaction(self, emoji: Union[EmojiInputType, Reaction], member: Snowflake) -> None:
        """|coro|

        Remove a reaction by the member from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        If the reaction is not your own (i.e. ``member`` parameter is not you) then
        :attr:`~Permissions.manage_messages` is needed.

        The ``member`` parameter must represent a member and meet
        the :class:`abc.Snowflake` abc.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

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
        TypeError
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)

        if member.id == self._state.self_id:
            await self._state.http.remove_own_reaction(self.channel.id, self.id, emoji)
        else:
            await self._state.http.remove_reaction(self.channel.id, self.id, emoji, member.id)

    async def clear_reaction(self, emoji: Union[EmojiInputType, Reaction]) -> None:
        """|coro|

        Clears a specific reaction from the message.

        The emoji may be a unicode emoji or a custom guild :class:`Emoji`.

        You must have :attr:`~Permissions.manage_messages` to do this.

        .. versionadded:: 1.3

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        emoji: Union[:class:`Emoji`, :class:`Reaction`, :class:`PartialEmoji`, :class:`str`]
            The emoji to clear.

        Raises
        --------
        HTTPException
            Clearing the reaction failed.
        Forbidden
            You do not have the proper permissions to clear the reaction.
        NotFound
            The emoji you specified was not found.
        TypeError
            The emoji parameter is invalid.
        """

        emoji = convert_emoji_reaction(emoji)
        await self._state.http.clear_single_reaction(self.channel.id, self.id, emoji)

    async def clear_reactions(self) -> None:
        """|coro|

        Removes all the reactions from the message.

        You must have :attr:`~Permissions.manage_messages` to do this.

        Raises
        --------
        HTTPException
            Removing the reactions failed.
        Forbidden
            You do not have the proper permissions to remove all the reactions.
        """
        await self._state.http.clear_reactions(self.channel.id, self.id)

    async def create_thread(
        self,
        *,
        name: str,
        auto_archive_duration: ThreadArchiveDuration = MISSING,
        slowmode_delay: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Thread:
        """|coro|

        Creates a public thread from this message.

        You must have :attr:`~discord.Permissions.create_public_threads` in order to
        create a public thread from a message.

        The channel this message belongs in must be a :class:`TextChannel`.

        .. versionadded:: 2.0

        Parameters
        -----------
        name: :class:`str`
            The name of the thread.
        auto_archive_duration: :class:`int`
            The duration in minutes before a thread is automatically hidden from the channel list.
            If not provided, the channel's default auto archive duration is used.

            Must be one of ``60``, ``1440``, ``4320``, or ``10080``, if provided.
        slowmode_delay: Optional[:class:`int`]
            Specifies the slowmode rate limit for user in this channel, in seconds.
            The maximum value possible is ``21600``. By default no slowmode rate limit
            if this is ``None``.
        reason: Optional[:class:`str`]
            The reason for creating a new thread. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You do not have permissions to create a thread.
        HTTPException
            Creating the thread failed.
        ValueError
            This message does not have guild info attached.

        Returns
        --------
        :class:`.Thread`
            The created thread.
        """
        if self.guild is None:
            raise ValueError('This message does not have guild info attached.')

        default_auto_archive_duration: ThreadArchiveDuration = getattr(self.channel, 'default_auto_archive_duration', 1440)
        data = await self._state.http.start_thread_with_message(
            self.channel.id,
            self.id,
            name=name,
            auto_archive_duration=auto_archive_duration or default_auto_archive_duration,
            rate_limit_per_user=slowmode_delay,
            reason=reason,
        )
        return Thread(guild=self.guild, state=self._state, data=data)

    async def fetch_thread(self) -> Thread:
        """|coro|

        Retrieves the public thread attached to this message.

        .. note::

            This method is an API call. For general usage, consider :attr:`thread` instead.

        .. versionadded:: 2.4

        Raises
        -------
        InvalidData
            An unknown channel type was received from Discord
            or the guild the thread belongs to is not the same
            as the one in this object points to.
        HTTPException
            Retrieving the thread failed.
        NotFound
            There is no thread attached to this message.
        Forbidden
            You do not have permission to fetch this channel.

        Returns
        --------
        :class:`.Thread`
            The public thread attached to this message.
        """
        if self.guild is None:
            raise ValueError('This message does not have guild info attached.')

        return await self.guild.fetch_channel(self.id)  # type: ignore  # Can only be Thread in this case

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def reply(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    async def reply(self, content: Optional[str] = None, **kwargs: Any) -> Message:
        """|coro|

        A shortcut method to :meth:`.abc.Messageable.send` to reply to the
        :class:`.Message`.

        .. versionadded:: 1.6

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` or
            :exc:`ValueError` instead of ``InvalidArgument``.

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ValueError
            The ``files`` list is not of the appropriate size
        TypeError
            You specified both ``file`` and ``files``.

        Returns
        ---------
        :class:`.Message`
            The message that was sent.
        """

        return await self.channel.send(content, reference=self, **kwargs)

    async def end_poll(self) -> Message:
        """|coro|

        Ends the :class:`Poll` attached to this message.

        This can only be done if you are the message author.

        If the poll was successfully ended, then it returns the updated :class:`Message`.

        Raises
        ------
        ~discord.HTTPException
            Ending the poll failed.

        Returns
        -------
        :class:`.Message`
            The updated message.
        """

        data = await self._state.http.end_poll(self.channel.id, self.id)

        return Message(state=self._state, channel=self.channel, data=data)

    def to_reference(
        self,
        *,
        fail_if_not_exists: bool = True,
        type: MessageReferenceType = MessageReferenceType.reply,
    ) -> MessageReference:
        """Creates a :class:`~discord.MessageReference` from the current message.

        .. versionadded:: 1.6

        Parameters
        ----------
        fail_if_not_exists: :class:`bool`
            Whether the referenced message should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

            .. versionadded:: 1.7
        type: :class:`MessageReferenceType`
            The type of message reference.

            .. versionadded:: 2.5

        Returns
        ---------
        :class:`~discord.MessageReference`
            The reference to this message.
        """

        return MessageReference.from_message(self, fail_if_not_exists=fail_if_not_exists, type=type)

    async def forward(
        self,
        destination: MessageableChannel,
        *,
        fail_if_not_exists: bool = True,
    ) -> Message:
        """|coro|

        Forwards this message to a channel.

        .. versionadded:: 2.5

        Parameters
        ----------
        destination: :class:`~discord.abc.Messageable`
            The channel to forward this message to.
        fail_if_not_exists: :class:`bool`
            Whether replying using the message reference should raise :class:`HTTPException`
            if the message no longer exists or Discord could not fetch the message.

        Raises
        ------
        ~discord.HTTPException
            Forwarding the message failed.

        Returns
        -------
        :class:`.Message`
            The message sent to the channel.
        """
        reference = self.to_reference(
            fail_if_not_exists=fail_if_not_exists,
            type=MessageReferenceType.forward,
        )
        ret = await destination.send(reference=reference)
        return ret

    def to_message_reference_dict(self) -> MessageReferencePayload:
        data: MessageReferencePayload = {
            'message_id': self.id,
            'channel_id': self.channel.id,
        }

        if self.guild is not None:
            data['guild_id'] = self.guild.id

        return data


@flatten_handlers
class Message(PartialMessage, Hashable):
    r"""Represents a message from Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: hash(x)

            Returns the message's hash.

    Attributes
    -----------
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: Union[:class:`Member`, :class:`abc.User`]
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has the left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
        If :attr:`Intents.message_content` is not enabled this will always be an empty string
        unless the bot is mentioned or the message is a direct message.
    nonce: Optional[Union[:class:`str`, :class:`int`]]
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is not stored long term within Discord's servers and is only used ephemerally.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
        If :attr:`Intents.message_content` is not enabled this will always be an empty list
        unless the bot is mentioned or the message is a direct message.
    channel: Union[:class:`TextChannel`, :class:`StageChannel`, :class:`VoiceChannel`, :class:`Thread`, :class:`DMChannel`, :class:`GroupChannel`, :class:`PartialMessageable`]
        The :class:`TextChannel` or :class:`Thread` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    reference: Optional[:class:`~discord.MessageReference`]
        The message that this message references. This is only applicable to messages of
        type :attr:`MessageType.pins_add`, crossposted messages created by a
        followed channel integration, or message replies.

        .. versionadded:: 1.5

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
            not rely on it. This is a Discord limitation, not one with the library.
    channel_mentions: List[Union[:class:`abc.GuildChannel`, :class:`Thread`]]
        A list of :class:`abc.GuildChannel` or :class:`Thread` that were mentioned. If the message is
        in a private message then the list is always empty.
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
        If :attr:`Intents.message_content` is not enabled this will always be an empty list
        unless the bot is mentioned or the message is a direct message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    flags: :class:`MessageFlags`
        Extra features of the message.

        .. versionadded:: 1.3

    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`~discord.MessageApplication`]
        The rich presence enabled application associated with this message.

        .. versionchanged:: 2.0
            Type is now :class:`MessageApplication` instead of :class:`dict`.

    stickers: List[:class:`StickerItem`]
        A list of sticker items given to the message.

        .. versionadded:: 1.6
    components: List[Union[:class:`ActionRow`, :class:`Button`, :class:`SelectMenu`]]
        A list of components in the message.
        If :attr:`Intents.message_content` is not enabled this will always be an empty list
        unless the bot is mentioned or the message is a direct message.

        .. versionadded:: 2.0
    role_subscription: Optional[:class:`RoleSubscriptionInfo`]
        The data of the role subscription purchase or renewal that prompted this
        :attr:`MessageType.role_subscription_purchase` message.

        .. versionadded:: 2.2
    application_id: Optional[:class:`int`]
        The application ID of the application that created this message if this
        message was sent by an application-owned webhook or an interaction.

        .. versionadded:: 2.2
    position: Optional[:class:`int`]
        A generally increasing integer with potentially gaps or duplicates that represents
        the approximate position of the message in a thread.

        .. versionadded:: 2.2
    guild: Optional[:class:`Guild`]
        The guild that the message belongs to, if applicable.
    interaction_metadata: Optional[:class:`.MessageInteractionMetadata`]
        The metadata of the interaction that this message is a response to.

        .. versionadded:: 2.4
    poll: Optional[:class:`Poll`]
        The poll attached to this message.

        .. versionadded:: 2.4
    call: Optional[:class:`CallMessage`]
        The call associated with this message.

        .. versionadded:: 2.5
    purchase_notification: Optional[:class:`PurchaseNotification`]
        The data of the purchase notification that prompted this :attr:`MessageType.purchase_notification` message.

        .. versionadded:: 2.5
    message_snapshots: List[:class:`MessageSnapshot`]
        The message snapshots attached to this message.

        .. versionadded:: 2.5
    """

    __slots__ = (
        '_edited_timestamp',
        '_cs_channel_mentions',
        '_cs_raw_mentions',
        '_cs_clean_content',
        '_cs_raw_channel_mentions',
        '_cs_raw_role_mentions',
        '_cs_system_content',
        '_thread',
        'tts',
        'content',
        'webhook_id',
        'mention_everyone',
        'embeds',
        'mentions',
        'author',
        'attachments',
        'nonce',
        'pinned',
        'role_mentions',
        'type',
        'flags',
        'reactions',
        'reference',
        'application',
        'activity',
        'stickers',
        'components',
        '_interaction',
        'role_subscription',
        'application_id',
        'position',
        'interaction_metadata',
        'poll',
        'call',
        'purchase_notification',
        'message_snapshots',
    )

    if TYPE_CHECKING:
        _HANDLERS: ClassVar[List[Tuple[str, Callable[..., None]]]]
        _CACHED_SLOTS: ClassVar[List[str]]
        # guild: Optional[Guild]
        reference: Optional[MessageReference]
        mentions: List[Union[User, Member]]
        author: Union[User, Member]
        role_mentions: List[Role]
        components: List[MessageComponentType]

    def __init__(
        self,
        *,
        state: ConnectionState,
        channel: MessageableChannel,
        data: MessagePayload,
    ) -> None:
        self.channel: MessageableChannel = channel
        self.id: int = int(data['id'])
        self._state: ConnectionState = state
        self.webhook_id: Optional[int] = utils._get_as_snowflake(data, 'webhook_id')
        self.reactions: List[Reaction] = [Reaction(message=self, data=d) for d in data.get('reactions', [])]
        self.attachments: List[Attachment] = [Attachment(data=a, state=self._state) for a in data['attachments']]
        self.embeds: List[Embed] = [Embed.from_dict(a) for a in data['embeds']]
        self.activity: Optional[MessageActivityPayload] = data.get('activity')
        self._edited_timestamp: Optional[datetime.datetime] = utils.parse_time(data['edited_timestamp'])
        self.type: MessageType = try_enum(MessageType, data['type'])
        self.pinned: bool = data['pinned']
        self.flags: MessageFlags = MessageFlags._from_value(data.get('flags', 0))
        self.mention_everyone: bool = data['mention_everyone']
        self.tts: bool = data['tts']
        self.content: str = data['content']
        self.nonce: Optional[Union[int, str]] = data.get('nonce')
        self.position: Optional[int] = data.get('position')
        self.application_id: Optional[int] = utils._get_as_snowflake(data, 'application_id')
        self.stickers: List[StickerItem] = [StickerItem(data=d, state=state) for d in data.get('sticker_items', [])]
        self.message_snapshots: List[MessageSnapshot] = MessageSnapshot._from_value(state, data.get('message_snapshots'))

        self.poll: Optional[Poll] = None
        try:
            self.poll = Poll._from_data(data=data['poll'], message=self, state=state)
        except KeyError:
            pass

        try:
            # if the channel doesn't have a guild attribute, we handle that
            self.guild = channel.guild
        except AttributeError:
            self.guild = state._get_guild(utils._get_as_snowflake(data, 'guild_id'))

        self._thread: Optional[Thread] = None

        if self.guild is not None:
            try:
                thread = data['thread']
            except KeyError:
                pass
            else:
                self._thread = self.guild.get_thread(int(thread['id']))

                if self._thread is not None:
                    self._thread._update(thread)
                else:
                    self._thread = Thread(guild=self.guild, state=state, data=thread)

        self._interaction: Optional[MessageInteraction] = None

        # deprecated
        try:
            interaction = data['interaction']
        except KeyError:
            pass
        else:
            self._interaction = MessageInteraction(state=state, guild=self.guild, data=interaction)

        self.interaction_metadata: Optional[MessageInteractionMetadata] = None
        try:
            interaction_metadata = data['interaction_metadata']
        except KeyError:
            pass
        else:
            self.interaction_metadata = MessageInteractionMetadata(state=state, guild=self.guild, data=interaction_metadata)

        try:
            ref = data['message_reference']
        except KeyError:
            self.reference = None
        else:
            self.reference = ref = MessageReference.with_state(state, ref)
            try:
                resolved = data['referenced_message']
            except KeyError:
                pass
            else:
                if resolved is None:
                    ref.resolved = DeletedReferencedMessage(ref)
                else:
                    # Right now the channel IDs match but maybe in the future they won't.
                    if ref.channel_id == channel.id:
                        chan = channel
                    elif isinstance(channel, Thread) and channel.parent_id == ref.channel_id:
                        chan = channel
                    else:
                        chan, _ = state._get_guild_channel(resolved, ref.guild_id)

                    # the channel will be the correct type here
                    ref.resolved = self.__class__(channel=chan, data=resolved, state=state)  # type: ignore

        self.application: Optional[MessageApplication] = None
        try:
            application = data['application']
        except KeyError:
            pass
        else:
            self.application = MessageApplication(state=self._state, data=application)

        self.role_subscription: Optional[RoleSubscriptionInfo] = None
        try:
            role_subscription = data['role_subscription_data']
        except KeyError:
            pass
        else:
            self.role_subscription = RoleSubscriptionInfo(role_subscription)

        self.purchase_notification: Optional[PurchaseNotification] = None
        try:
            purchase_notification = data['purchase_notification']
        except KeyError:
            pass
        else:
            self.purchase_notification = PurchaseNotification(purchase_notification)

        for handler in ('author', 'member', 'mentions', 'mention_roles', 'components', 'call'):
            try:
                getattr(self, f'_handle_{handler}')(data[handler])
            except KeyError:
                continue

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return (
            f'<{name} id={self.id} channel={self.channel!r} type={self.type!r} author={self.author!r} flags={self.flags!r}>'
        )

    def _try_patch(self, data, key, transform=None) -> None:
        try:
            value = data[key]
        except KeyError:
            pass
        else:
            if transform is None:
                setattr(self, key, value)
            else:
                setattr(self, key, transform(value))

    def _add_reaction(self, data, emoji, user_id) -> Reaction:
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

    def _remove_reaction(self, data: MessageReactionRemoveEvent, emoji: EmojiInputType, user_id: int) -> Reaction:
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

    def _clear_emoji(self, emoji: PartialEmoji) -> Optional[Reaction]:
        to_check = str(emoji)
        for index, reaction in enumerate(self.reactions):
            if str(reaction.emoji) == to_check:
                break
        else:
            # didn't find anything so just return
            return

        del self.reactions[index]
        return reaction

    def _update(self, data: MessageUpdateEvent) -> None:
        # In an update scheme, 'author' key has to be handled before 'member'
        # otherwise they overwrite each other which is undesirable.
        # Since there's no good way to do this we have to iterate over every
        # handler rather than iterating over the keys which is a little slower
        for key, handler in self._HANDLERS:
            try:
                value = data[key]
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

    def _handle_edited_timestamp(self, value: str) -> None:
        self._edited_timestamp = utils.parse_time(value)

    def _handle_pinned(self, value: bool) -> None:
        self.pinned = value

    def _handle_flags(self, value: int) -> None:
        self.flags = MessageFlags._from_value(value)

    def _handle_application(self, value: MessageApplicationPayload) -> None:
        application = MessageApplication(state=self._state, data=value)
        self.application = application

    def _handle_activity(self, value: MessageActivityPayload) -> None:
        self.activity = value

    def _handle_mention_everyone(self, value: bool) -> None:
        self.mention_everyone = value

    def _handle_tts(self, value: bool) -> None:
        self.tts = value

    def _handle_type(self, value: int) -> None:
        self.type = try_enum(MessageType, value)

    def _handle_content(self, value: str) -> None:
        self.content = value

    def _handle_attachments(self, value: List[AttachmentPayload]) -> None:
        self.attachments = [Attachment(data=a, state=self._state) for a in value]

    def _handle_embeds(self, value: List[EmbedPayload]) -> None:
        self.embeds = [Embed.from_dict(data) for data in value]

    def _handle_nonce(self, value: Union[str, int]) -> None:
        self.nonce = value

    def _handle_author(self, author: UserPayload) -> None:
        self.author = self._state.store_user(author, cache=self.webhook_id is None)
        if isinstance(self.guild, Guild):
            found = self.guild.get_member(self.author.id)
            if found is not None:
                self.author = found

    def _handle_member(self, member: MemberPayload) -> None:
        # The gateway now gives us full Member objects sometimes with the following keys
        # deaf, mute, joined_at, roles
        # For the sake of performance I'm going to assume that the only
        # field that needs *updating* would be the joined_at field.
        # If there is no Member object (for some strange reason), then we can upgrade
        # ourselves to a more "partial" member object.
        author = self.author
        try:
            # Update member reference
            author._update_from_message(member)  # type: ignore
        except AttributeError:
            # It's a user here
            self.author = Member._from_message(message=self, data=member)

    def _handle_mentions(self, mentions: List[UserWithMemberPayload]) -> None:
        self.mentions = r = []
        guild = self.guild
        state = self._state
        if not isinstance(guild, Guild):
            self.mentions = [state.store_user(m) for m in mentions]
            return

        for mention in filter(None, mentions):
            id_search = int(mention['id'])
            member = guild.get_member(id_search)
            if member is not None:
                r.append(member)
            else:
                r.append(Member._try_upgrade(data=mention, guild=guild, state=state))

    def _handle_mention_roles(self, role_mentions: List[int]) -> None:
        self.role_mentions = []
        if isinstance(self.guild, Guild):
            for role_id in map(int, role_mentions):
                role = self.guild.get_role(role_id)
                if role is not None:
                    self.role_mentions.append(role)

    def _handle_components(self, data: List[ComponentPayload]) -> None:
        self.components = []

        for component_data in data:
            component = _component_factory(component_data)

            if component is not None:
                self.components.append(component)

    def _handle_interaction(self, data: MessageInteractionPayload):
        self._interaction = MessageInteraction(state=self._state, guild=self.guild, data=data)

    def _handle_interaction_metadata(self, data: MessageInteractionMetadataPayload):
        self.interaction_metadata = MessageInteractionMetadata(state=self._state, guild=self.guild, data=data)

    def _handle_call(self, data: CallMessagePayload):
        self.call: Optional[CallMessage]
        if data is not None:
            self.call = CallMessage(state=self._state, message=self, data=data)
        else:
            self.call = None

    def _rebind_cached_references(
        self,
        new_guild: Guild,
        new_channel: Union[GuildChannel, Thread, PartialMessageable],
    ) -> None:
        self.guild = new_guild
        self.channel = new_channel  # type: ignore # Not all "GuildChannel" are messageable at the moment

    @utils.cached_slot_property('_cs_raw_mentions')
    def raw_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of user IDs matched with
        the syntax of ``<@user_id>`` in the message content.

        This allows you to receive the user IDs of mentioned users
        even in a private message context.
        """
        return [int(x) for x in re.findall(r'<@!?([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_raw_channel_mentions')
    def raw_channel_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of channel IDs matched with
        the syntax of ``<#channel_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<#([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_raw_role_mentions')
    def raw_role_mentions(self) -> List[int]:
        """List[:class:`int`]: A property that returns an array of role IDs matched with
        the syntax of ``<@&role_id>`` in the message content.
        """
        return [int(x) for x in re.findall(r'<@&([0-9]{15,20})>', self.content)]

    @utils.cached_slot_property('_cs_channel_mentions')
    def channel_mentions(self) -> List[Union[GuildChannel, Thread]]:
        if self.guild is None:
            return []
        it = filter(None, map(self.guild._resolve_channel, self.raw_channel_mentions))
        return utils._unique(it)

    @utils.cached_slot_property('_cs_clean_content')
    def clean_content(self) -> str:
        """:class:`str`: A property that returns the content in a "cleaned up"
        manner. This basically means that mentions are transformed
        into the way the client shows it. e.g. ``<#id>`` will transform
        into ``#name``.

        This will also transform @everyone and @here mentions into
        non-mentions.

        .. note::

            This *does not* affect markdown. If you want to escape
            or remove markdown then use :func:`utils.escape_markdown` or :func:`utils.remove_markdown`
            respectively, along with this function.
        """

        if self.guild:

            def resolve_member(id: int) -> str:
                m = self.guild.get_member(id) or utils.get(self.mentions, id=id)  # type: ignore
                return f'@{m.display_name}' if m else '@deleted-user'

            def resolve_role(id: int) -> str:
                r = self.guild.get_role(id) or utils.get(self.role_mentions, id=id)  # type: ignore
                return f'@{r.name}' if r else '@deleted-role'

            def resolve_channel(id: int) -> str:
                c = self.guild._resolve_channel(id)  # type: ignore
                return f'#{c.name}' if c else '#deleted-channel'

        else:

            def resolve_member(id: int) -> str:
                m = utils.get(self.mentions, id=id)
                return f'@{m.display_name}' if m else '@deleted-user'

            def resolve_role(id: int) -> str:
                return '@deleted-role'

            def resolve_channel(id: int) -> str:
                return '#deleted-channel'

        transforms = {
            '@': resolve_member,
            '@!': resolve_member,
            '#': resolve_channel,
            '@&': resolve_role,
        }

        def repl(match: re.Match) -> str:
            type = match[1]
            id = int(match[2])
            transformed = transforms[type](id)
            return transformed

        result = re.sub(r'<(@[!&]?|#)([0-9]{15,20})>', repl, self.content)

        return escape_mentions(result)

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: The message's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def edited_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: An aware UTC datetime object containing the edited time of the message."""
        return self._edited_timestamp

    @property
    def thread(self) -> Optional[Thread]:
        """Optional[:class:`Thread`]: The public thread created from this message, if it exists.

        .. note::

            For messages received via the gateway this does not retrieve archived threads, as they
            are not retained in the internal cache. Use :meth:`fetch_thread` instead.

        .. versionadded:: 2.4
        """
        if self.guild is not None:
            # Fall back to guild threads in case one was created after the message
            return self._thread or self.guild.get_thread(self.id)

    @property
    @deprecated('interaction_metadata')
    def interaction(self) -> Optional[MessageInteraction]:
        """Optional[:class:`~discord.MessageInteraction`]: The interaction that this message is a response to.

        .. versionadded:: 2.0
        .. deprecated:: 2.4
            This attribute is deprecated and will be removed in a future version. Use :attr:`.interaction_metadata` instead.
        """
        return self._interaction

    def is_system(self) -> bool:
        """:class:`bool`: Whether the message is a system message.

        A system message is a message that is constructed entirely by the Discord API
        in response to something.

        .. versionadded:: 1.3
        """
        return self.type not in (
            MessageType.default,
            MessageType.reply,
            MessageType.chat_input_command,
            MessageType.context_menu_command,
            MessageType.thread_starter_message,
        )

    @utils.cached_slot_property('_cs_system_content')
    def system_content(self) -> str:
        r""":class:`str`: A property that returns the content that is rendered
        regardless of the :attr:`Message.type`.

        In the case of :attr:`MessageType.default` and :attr:`MessageType.reply`\,
        this just returns the regular :attr:`Message.content`. Otherwise this
        returns an English message denoting the contents of the system message.
        """

        if self.type is MessageType.default:
            return self.content

        if self.type is MessageType.recipient_add:
            if self.channel.type is ChannelType.group:
                return f'{self.author.name} added {self.mentions[0].name} to the group.'
            else:
                return f'{self.author.name} added {self.mentions[0].name} to the thread.'

        if self.type is MessageType.recipient_remove:
            if self.channel.type is ChannelType.group:
                return f'{self.author.name} removed {self.mentions[0].name} from the group.'
            else:
                return f'{self.author.name} removed {self.mentions[0].name} from the thread.'

        if self.type is MessageType.channel_name_change:
            if getattr(self.channel, 'parent', self.channel).type is ChannelType.forum:
                return f'{self.author.name} changed the post title: **{self.content}**'
            else:
                return f'{self.author.name} changed the channel name: **{self.content}**'

        if self.type is MessageType.channel_icon_change:
            return f'{self.author.name} changed the group icon.'

        if self.type is MessageType.pins_add:
            return f'{self.author.name} pinned a message to this channel.'

        if self.type is MessageType.new_member:
            formats = [
                "{0} joined the party.",
                "{0} is here.",
                "Welcome, {0}. We hope you brought pizza.",
                "A wild {0} appeared.",
                "{0} just landed.",
                "{0} just slid into the server.",
                "{0} just showed up!",
                "Welcome {0}. Say hi!",
                "{0} hopped into the server.",
                "Everyone welcome {0}!",
                "Glad you're here, {0}.",
                "Good to see you, {0}.",
                "Yay you made it, {0}!",
            ]

            created_at_ms = int(self.created_at.timestamp() * 1000)
            return formats[created_at_ms % len(formats)].format(self.author.name)

        if self.type is MessageType.premium_guild_subscription:
            if not self.content:
                return f'{self.author.name} just boosted the server!'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times!'

        if self.type is MessageType.premium_guild_tier_1:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 1!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 1!**'

        if self.type is MessageType.premium_guild_tier_2:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 2!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 2!**'

        if self.type is MessageType.premium_guild_tier_3:
            if not self.content:
                return f'{self.author.name} just boosted the server! {self.guild} has achieved **Level 3!**'
            else:
                return f'{self.author.name} just boosted the server **{self.content}** times! {self.guild} has achieved **Level 3!**'

        if self.type is MessageType.channel_follow_add:
            return (
                f'{self.author.name} has added {self.content} to this channel. Its most important updates will show up here.'
            )

        if self.type is MessageType.guild_stream:
            # the author will be a Member
            return f'{self.author.name} is live! Now streaming {self.author.activity.name}'  # type: ignore

        if self.type is MessageType.guild_discovery_disqualified:
            return 'This server has been removed from Server Discovery because it no longer passes all the requirements. Check Server Settings for more details.'

        if self.type is MessageType.guild_discovery_requalified:
            return 'This server is eligible for Server Discovery again and has been automatically relisted!'

        if self.type is MessageType.guild_discovery_grace_period_initial_warning:
            return 'This server has failed Discovery activity requirements for 1 week. If this server fails for 4 weeks in a row, it will be automatically removed from Discovery.'

        if self.type is MessageType.guild_discovery_grace_period_final_warning:
            return 'This server has failed Discovery activity requirements for 3 weeks in a row. If this server fails for 1 more week, it will be removed from Discovery.'

        if self.type is MessageType.thread_created:
            return f'{self.author.name} started a thread: **{self.content}**. See all **threads**.'

        if self.type is MessageType.reply:
            return self.content

        if self.type is MessageType.thread_starter_message:
            if self.reference is None or self.reference.resolved is None:
                return 'Sorry, we couldn\'t load the first message in this thread'

            # the resolved message for the reference will be a Message
            return self.reference.resolved.content  # type: ignore

        if self.type is MessageType.guild_invite_reminder:
            return 'Wondering who to invite?\nStart by inviting anyone who can help you build the server!'

        if self.type is MessageType.role_subscription_purchase and self.role_subscription is not None:
            total_months = self.role_subscription.total_months_subscribed
            months = '1 month' if total_months == 1 else f'{total_months} months'
            action = 'renewed' if self.role_subscription.is_renewal else 'joined'
            return f'{self.author.name} {action} **{self.role_subscription.tier_name}** and has been a subscriber of {self.guild} for {months}!'

        if self.type is MessageType.stage_start:
            return f'{self.author.name} started **{self.content}**.'

        if self.type is MessageType.stage_end:
            return f'{self.author.name} ended **{self.content}**.'

        if self.type is MessageType.stage_speaker:
            return f'{self.author.name} is now a speaker.'

        if self.type is MessageType.stage_raise_hand:
            return f'{self.author.name} requested to speak.'

        if self.type is MessageType.stage_topic:
            return f'{self.author.name} changed Stage topic: **{self.content}**.'

        if self.type is MessageType.guild_incident_alert_mode_enabled:
            dt = utils.parse_time(self.content)
            dt_content = utils.format_dt(dt)
            return f'{self.author.name} enabled security actions until {dt_content}.'

        if self.type is MessageType.guild_incident_alert_mode_disabled:
            return f'{self.author.name} disabled security actions.'

        if self.type is MessageType.guild_incident_report_raid:
            return f'{self.author.name} reported a raid in {self.guild}.'

        if self.type is MessageType.guild_incident_report_false_alarm:
            return f'{self.author.name} reported a false alarm in {self.guild}.'

        if self.type is MessageType.call:
            call_ended = self.call.ended_timestamp is not None  # type: ignore # call can't be None here
            missed = self._state.user not in self.call.participants  # type: ignore # call can't be None here

            if call_ended:
                duration = utils._format_call_duration(self.call.duration)  # type: ignore # call can't be None here
                if missed:
                    return 'You missed a call from {0.author.name} that lasted {1}.'.format(self, duration)
                else:
                    return '{0.author.name} started a call that lasted {1}.'.format(self, duration)
            else:
                if missed:
                    return '{0.author.name} started a call. \N{EM DASH} Join the call'.format(self)
                else:
                    return '{0.author.name} started a call.'.format(self)

        if self.type is MessageType.purchase_notification and self.purchase_notification is not None:
            guild_product_purchase = self.purchase_notification.guild_product_purchase
            if guild_product_purchase is not None:
                return f'{self.author.name} has purchased {guild_product_purchase.product_name}!'

        # Fallback for unknown message types
        return ''

    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        embed: Optional[Embed] = ...,
        attachments: Sequence[Union[Attachment, File]] = ...,
        suppress: bool = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        view: Optional[View] = ...,
    ) -> Message:
        ...

    @overload
    async def edit(
        self,
        *,
        content: Optional[str] = ...,
        embeds: Sequence[Embed] = ...,
        attachments: Sequence[Union[Attachment, File]] = ...,
        suppress: bool = ...,
        delete_after: Optional[float] = ...,
        allowed_mentions: Optional[AllowedMentions] = ...,
        view: Optional[View] = ...,
    ) -> Message:
        ...

    async def edit(
        self,
        *,
        content: Optional[str] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: Sequence[Embed] = MISSING,
        attachments: Sequence[Union[Attachment, File]] = MISSING,
        suppress: bool = False,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = MISSING,
        view: Optional[View] = MISSING,
    ) -> Message:
        """|coro|

        Edits the message.

        The content must be able to be transformed into a string via ``str(content)``.

        .. versionchanged:: 1.3
            The ``suppress`` keyword-only parameter was added.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited message is returned instead.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with.
            Could be ``None`` to remove the content.
        embed: Optional[:class:`Embed`]
            The new embed to replace the original with.
            Could be ``None`` to remove the embed.
        embeds: List[:class:`Embed`]
            The new embeds to replace the original with. Must be a maximum of 10.
            To remove all embeds ``[]`` should be passed.

            .. versionadded:: 2.0
        attachments: List[Union[:class:`Attachment`, :class:`File`]]
            A list of attachments to keep in the message as well as new files to upload. If ``[]`` is passed
            then all attachments are removed.

            .. note::

                New files will always appear after current attachments.

            .. versionadded:: 2.0
        suppress: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Using this parameter requires :attr:`~.Permissions.manage_messages`.
        delete_after: Optional[:class:`float`]
            If provided, the number of seconds to wait in the background
            before deleting the message we just edited. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to suppress a message without permissions or
            edited a message's content or embed that isn't yours.
        NotFound
            This message does not exist.
        TypeError
            You specified both ``embed`` and ``embeds``

        Returns
        --------
        :class:`Message`
            The newly edited message.
        """

        if content is not MISSING:
            previous_allowed_mentions = self._state.allowed_mentions
        else:
            previous_allowed_mentions = None

        if suppress is not MISSING:
            flags = MessageFlags._from_value(self.flags.value)
            flags.suppress_embeds = suppress
        else:
            flags = MISSING

        if view is not MISSING:
            self._state.prevent_view_updates_for(self.id)

        with handle_message_parameters(
            content=content,
            flags=flags,
            embed=embed,
            embeds=embeds,
            attachments=attachments,
            view=view,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
        ) as params:
            data = await self._state.http.edit_message(self.channel.id, self.id, params=params)
            message = Message(state=self._state, channel=self.channel, data=data)

        if view and not view.is_finished():
            self._state.store_view(view, self.id)

        if delete_after is not None:
            await self.delete(delay=delete_after)

        return message

    async def add_files(self, *files: File) -> Message:
        r"""|coro|

        Adds new files to the end of the message attachments.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*files: :class:`File`
            New files to add to the message.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to edit a message that isn't yours.

        Returns
        --------
        :class:`Message`
            The newly edited message.
        """
        return await self.edit(attachments=[*self.attachments, *files])

    async def remove_attachments(self, *attachments: Attachment) -> Message:
        r"""|coro|

        Removes attachments from the message.

        .. versionadded:: 2.0

        Parameters
        -----------
        \*attachments: :class:`Attachment`
            Attachments to remove from the message.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Tried to edit a message that isn't yours.

        Returns
        --------
        :class:`Message`
            The newly edited message.
        """
        return await self.edit(attachments=[a for a in self.attachments if a not in attachments])
