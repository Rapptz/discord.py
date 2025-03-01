"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the 'Software'),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import io
from os import PathLike
from typing import TYPE_CHECKING, Any, Optional, Union

from .errors import ClientException
from .mixins import Hashable
from .file import File
from .flags import AttachmentFlags
from .enums import MediaLoadingState, try_enum
from . import utils

if TYPE_CHECKING:
    from .types.attachment import (
        AttachmentBase as AttachmentBasePayload,
        Attachment as AttachmentPayload,
        UnfurledAttachment as UnfurledAttachmentPayload,
    )

    from .http import HTTPClient
    from .state import ConnectionState

MISSING = utils.MISSING

__all__ = (
    'Attachment',
    'UnfurledAttachment',
)


class AttachmentBase:

    __slots__ = (
        'url',
        'proxy_url',
        'description',
        'filename',
        'spoiler',
        'height',
        'width',
        'content_type',
        '_flags',
        '_http',
        '_state',
    )

    def __init__(self, data: AttachmentBasePayload, state: Optional[ConnectionState]) -> None:
        self._state: Optional[ConnectionState] = state
        self._http: Optional[HTTPClient] = state.http if state else None
        self.url: str = data['url']
        self.proxy_url: str = data['proxy_url']
        self.description: Optional[str] = data.get('description')
        self.spoiler: bool = data.get('spoiler', False)
        self.height: Optional[int] = data.get('height')
        self.width: Optional[int] = data.get('width')
        self.content_type: Optional[str] = data.get('content_type')
        self._flags: int = data.get('flags', 0)

    @property
    def flags(self) -> AttachmentFlags:
        """:class:`AttachmentFlags`: The attachment's flag value."""
        return AttachmentFlags._from_value(self._flags)

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
        ----------
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
        ClientException
            Cannot read a stateless attachment.

        Returns
        -------
        :class:`bytes`
            The contents of the attachment.
        """
        if not self._http:
            raise ClientException(
                'Cannot read a stateless attachment'
            )

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
        file_description = (
            description if description is not MISSING else self.description
        )
        return File(
            io.BytesIO(data),
            filename=file_filename,
            description=file_description,
            spoiler=spoiler,
        )

    def to_dict(self) -> AttachmentBasePayload:
        base: AttachmentBasePayload = {
            'url': self.url,
            'proxy_url': self.proxy_url,
            'spoiler': self.spoiler,
        }

        if self.width:
            base['width'] = self.width
        if self.height:
            base['height'] = self.height
        if self.description:
            base['description'] = self.description

        return base


class Attachment(Hashable, AttachmentBase):
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
    spoiler: :class:`bool`
        Whether the attachment is a spoiler or not. Unlike :meth:`.is_spoiler`, this uses the API returned
        data.

        .. versionadded:: 2.6
    """

    __slots__ = (
        'id',
        'size',
        'ephemeral',
        'duration',
        'waveform',
        'title',
    )

    def __init__(self, *, data: AttachmentPayload, state: ConnectionState):
        self.id: int = int(data['id'])
        self.filename: str = data['filename']
        self.size: int = data['size']
        self.ephemeral: bool = data.get('ephemeral', False)
        self.duration: Optional[float] = data.get('duration_secs')
        self.title: Optional[str] = data.get('title')
        super().__init__(data, state)

    def is_spoiler(self) -> bool:
        """:class:`bool`: Whether this attachment contains a spoiler."""
        return self.spoiler or self.filename.startswith('SPOILER_')

    def is_voice_message(self) -> bool:
        """:class:`bool`: Whether this attachment is a voice message."""
        return self.duration is not None and 'voice-message' in self.url

    def __repr__(self) -> str:
        return f'<Attachment id={self.id} filename={self.filename!r} url={self.url!r}>'

    def to_dict(self) -> AttachmentPayload:
        result: AttachmentPayload = super().to_dict()  # pyright: ignore[reportAssignmentType]
        result['id'] = self.id
        result['filename'] = self.filename
        result['size'] = self.size
        return result


class UnfurledAttachment(AttachmentBase):
    """Represents an unfurled attachment item from a :class:`Component`.

    .. versionadded:: 2.6

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the attachment.

        .. describe:: x == y

            Checks if the unfurled attachment is equal to another unfurled attachment.

        .. describe:: x != y

            Checks if the unfurled attachment is not equal to another unfurled attachment.

    Attributes
    ----------
    height: Optional[:class:`int`]
        The attachment's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The attachment's width, in pixels. Only applicable to images and videos.
    url: :class:`str`
        The attachment URL. If the message this attachment was attached
        to is deleted, then this will 404.
    proxy_url: :class:`str`
        The proxy URL. This is a cached version of the :attr:`~Attachment.url` in the
        case of images. When the message is deleted, this URL might be valid for a few
        minutes or not valid at all.
    content_type: Optional[:class:`str`]
        The attachment's `media type <https://en.wikipedia.org/wiki/Media_type>`_
    description: Optional[:class:`str`]
        The attachment's description. Only applicable to images.
    spoiler: :class:`bool`
        Whether the attachment is a spoiler or not. Unlike :meth:`.is_spoiler`, this uses the API returned
        data.
    loading_state: :class:`MediaLoadingState`
        The cache state of this unfurled attachment.
    """

    __slots__ = (
        'loading_state',
    )

    def __init__(self, data: UnfurledAttachmentPayload, state: Optional[ConnectionState]) -> None:
        self.loading_state: MediaLoadingState = try_enum(MediaLoadingState, data.get('loading_state', 0))
        super().__init__(data, state)

    def __repr__(self) -> str:
        return f'<UnfurledAttachment url={self.url!r}>'

    def to_object_dict(self):
        return {'url': self.url}
