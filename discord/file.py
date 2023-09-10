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

import io
import os
from base64 import b64encode
from hashlib import md5
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

import yarl

from .utils import MISSING, cached_slot_property

if TYPE_CHECKING:
    from typing_extensions import Self

    from .state import ConnectionState
    from .types.message import (
        CloudAttachment as CloudAttachmentPayload,
        PartialAttachment as PartialAttachmentPayload,
        UploadedAttachment as UploadedAttachmentPayload,
    )

__all__ = (
    'File',
    'CloudFile',
)


def _strip_spoiler(filename: str) -> Tuple[str, bool]:
    stripped = filename
    while stripped.startswith('SPOILER_'):
        stripped = stripped[8:]  # len('SPOILER_')
    spoiler = stripped != filename
    return stripped, spoiler


class _FileBase:
    __slots__ = ('_filename', 'spoiler', 'description')

    def __init__(self, filename: str, *, spoiler: bool = False, description: Optional[str] = None):
        self._filename, filename_spoiler = _strip_spoiler(filename)
        if spoiler is MISSING:
            spoiler = filename_spoiler

        self.spoiler: bool = spoiler
        self.description: Optional[str] = description

    @property
    def filename(self) -> str:
        """:class:`str`: The filename to display when uploading to Discord.
        If this is not given then it defaults to ``fp.name`` or if ``fp`` is
        a string then the ``filename`` will default to the string given.
        """
        return 'SPOILER_' + self._filename if self.spoiler else self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename, self.spoiler = _strip_spoiler(value)

    def to_dict(self, index: int) -> PartialAttachmentPayload:
        payload: PartialAttachmentPayload = {
            'id': str(index),
            'filename': self.filename,
        }

        if self.description is not None:
            payload['description'] = self.description

        return payload

    def reset(self, *, seek: Union[int, bool] = True) -> None:
        return

    def close(self) -> None:
        return


class File(_FileBase):
    r"""A parameter object used for :meth:`abc.Messageable.send`
    for sending file objects.

    .. note::

        File objects are single use and are not meant to be reused in
        multiple :meth:`abc.Messageable.send`\s.

    Attributes
    -----------
    fp: Union[:class:`os.PathLike`, :class:`io.BufferedIOBase`]
        A file-like object opened in binary mode and read mode
        or a filename representing a file in the hard drive to
        open.

        .. note::

            If the file-like object passed is opened via ``open`` then the
            modes 'rb' should be used.

            To pass binary data, consider usage of ``io.BytesIO``.

    spoiler: :class:`bool`
        Whether the attachment is a spoiler. If left unspecified, the :attr:`~File.filename` is used
        to determine if the file is a spoiler.
    description: Optional[:class:`str`]
        The file description to display, currently only supported for images.

        .. versionadded:: 2.0
    """

    __slots__ = ('fp', '_original_pos', '_owner', '_closer', '_cs_md5', '_cs_size')

    def __init__(
        self,
        fp: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        spoiler: bool = MISSING,
        description: Optional[str] = None,
    ):
        if isinstance(fp, io.IOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(f'File buffer {fp!r} must be seekable and readable')
            self.fp: io.BufferedIOBase = fp
            self._original_pos = fp.tell()
            self._owner = False
        else:
            self.fp = open(fp, 'rb')
            self._original_pos = 0
            self._owner = True

        # aiohttp only uses two methods from IOBase (read and close)
        # Since I want to control when the files close,
        # I need to stub it so it doesn't close unless I tell it to
        self._closer = self.fp.close
        self.fp.close = lambda: None

        if filename is None:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                filename = getattr(fp, 'name', 'untitled')

        super().__init__(filename, spoiler=spoiler, description=description)

    @cached_slot_property('_cs_md5')
    def md5(self):
        try:
            return md5(self.fp.read())
        finally:
            self.reset()

    @property
    def b64_md5(self) -> str:
        return b64encode(self.md5.digest()).decode('ascii')

    @cached_slot_property('_cs_size')
    def size(self) -> int:
        self.fp.seek(0, os.SEEK_END)
        try:
            return self.fp.tell()
        finally:
            self.reset()

    def to_upload_dict(self, index: int) -> UploadedAttachmentPayload:
        return {
            'id': str(index),
            'filename': self.filename,
            'file_size': self.size,
        }

    def reset(self, *, seek: Union[int, bool] = True) -> None:
        # The `seek` parameter is needed because
        # the retry-loop is iterated over multiple times
        # starting from 0, as an implementation quirk
        # the resetting must be done at the beginning
        # before a request is done, since the first index
        # is 0, and thus false, then this prevents an
        # unnecessary seek since it's the first request
        # done.
        if seek:
            self.fp.seek(self._original_pos)

    def close(self) -> None:
        self.fp.close = self._closer
        if self._owner:
            self._closer()


class CloudFile(_FileBase):
    """A parameter object used for :meth:`abc.Messageable.send`
    for sending file objects that have been pre-uploaded to Discord's GCP bucket.

    .. note::

        Unlike :class:`File`, this class is not directly user-constructable, however
        it can be reused multiple times in :meth:`abc.Messageable.send`.

        To construct it, see :meth:`abc.Messageable.upload_files`.

    .. versionadded:: 2.1

    Attributes
    -----------
    url: :class:`str`
        The upload URL of the file.

        .. note::

            This URL cannot be used to download the file,
            it is merely used to send the file to Discord.
    upload_filename: :class:`str`
        The filename that Discord has assigned to the file.
    spoiler: :class:`bool`
        Whether the attachment is a spoiler. If left unspecified, the :attr:`~CloudFile.filename` is used
        to determine if the file is a spoiler.
    description: Optional[:class:`str`]
        The file description to display, currently only supported for images.
    """

    __slots__ = ('url', 'upload_filename', '_state')

    def __init__(
        self,
        url: str,
        filename: str,
        upload_filename: str,
        *,
        spoiler: bool = MISSING,
        description: Optional[str] = None,
        state: ConnectionState,
    ):
        super().__init__(filename, spoiler=spoiler, description=description)
        self.url = url
        self.upload_filename = upload_filename
        self._state = state

    @classmethod
    async def from_file(cls, *, file: File, state: ConnectionState, data: CloudAttachmentPayload) -> Self:
        await state.http.upload_to_cloud(data['upload_url'], file)
        return cls(data['upload_url'], file._filename, data['upload_filename'], description=file.description, state=state)

    @property
    def upload_id(self) -> str:
        """:class:`str`: The upload ID of the file."""
        url = yarl.URL(self.url)
        return url.query['upload_id']

    def to_dict(self, index: int) -> PartialAttachmentPayload:
        payload = super().to_dict(index)
        payload['uploaded_filename'] = self.upload_filename
        return payload

    async def delete(self) -> None:
        """|coro|

        Deletes the uploaded file from Discord's GCP bucket.

        Raises
        -------
        HTTPException
            Deleting the file failed.
        """
        await self._state.http.delete_attachment(self.upload_filename)
