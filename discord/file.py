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
from typing import Any, Dict, Optional, Tuple, Union

import os
import io
import base64
from .oggparse import OggStream
from .opus import Decoder
import struct

from .utils import MISSING

# fmt: off
__all__ = (
    'File',
)
# fmt: on


def _strip_spoiler(filename: str) -> Tuple[str, bool]:
    stripped = filename
    while stripped.startswith('SPOILER_'):
        stripped = stripped[8:]  # len('SPOILER_')
    spoiler = stripped != filename
    return stripped, spoiler


class File:
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

    voice: :class:`bool`
        Whether the file is a voice message. If left unspecified, the :attr:`~File.duration` is used
        to determine if the file is a voice message.

        .. note::

            Voice files must be an audio only format.

            A *non-exhaustive* list of supported formats are: `ogg`, `mp3`, `wav`, `aac`, and `flac`.

        .. versionadded:: 2.6

    duration: Optional[:class:`float`]
        The duration of the voice message in seconds

        .. versionadded:: 2.6
    """

    __slots__ = (
        'fp',
        '_filename',
        'spoiler',
        'description',
        '_original_pos',
        '_owner',
        '_closer',
        'duration',
        '_waveform',
        'voice',
    )

    def __init__(
        self,
        fp: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase],
        filename: Optional[str] = None,
        *,
        spoiler: bool = MISSING,
        description: Optional[str] = None,
        voice: bool = MISSING,
        duration: Optional[float] = None,
        waveform: Optional[list[int]] = None,
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

        # aiohttp only uses two methods from IOBase
        # read and close, since I want to control when the files
        # close, I need to stub it so it doesn't close unless
        # I tell it to
        self._closer = self.fp.close
        self.fp.close = lambda: None

        if filename is None:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                filename = getattr(fp, 'name', 'untitled')

        self._filename, filename_spoiler = _strip_spoiler(filename)  # type: ignore  # pyright doesn't understand the above getattr
        if spoiler is MISSING:
            spoiler = filename_spoiler

        self.spoiler: bool = spoiler
        self.description: Optional[str] = description
        self.duration = duration
        if waveform is not None:
            if len(waveform) > 256:
                raise ValueError("Waveforms have a maximum of 256 values")
            elif max(waveform) > 255:
                raise ValueError("Maximum value of ints is 255 for waveforms")
            elif min(waveform) < 0:
                raise ValueError("Minimum value of ints is 0 for waveforms")
        self._waveform = waveform

        if voice is MISSING:
            voice = duration is not None
        self.voice = voice

        if duration is None and voice:
            raise TypeError('Voice messages must have a duration')

    @property
    def filename(self) -> str:
        """:class:`str`: The filename to display when uploading to Discord.
        If this is not given then it defaults to ``fp.name`` or if ``fp`` is
        a string then the ``filename`` will default to the string given.
        """
        return 'SPOILER_' + self._filename if self.spoiler else self._filename

    @property
    def waveform(self) -> list[int]:
        """:class:`list[int]`: The waveform data for the voice message.

        .. note::
            If a waveform was not given, it will be generated

            Only supports generating the waveform for Opus format files, other files will be given a random waveform

        .. versionadded:: 2.6"""
        if self._waveform is None:
            try:
                self._waveform = self.generate_waveform()
            except Exception:
                self._waveform = list(os.urandom(256))
            self.reset()
        return self._waveform

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename, self.spoiler = _strip_spoiler(value)

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

    def to_dict(self, index: int) -> Dict[str, Any]:
        payload = {
            'id': index,
            'filename': self.filename,
        }

        if self.description is not None:
            payload['description'] = self.description

        if self.voice:
            payload['duration_secs'] = self.duration
            payload['waveform'] = base64.b64encode(bytes(self.waveform)).decode('utf-8')

        return payload

    def generate_waveform(self) -> list[int]:
        if not self.voice:
            raise ValueError("Cannot produce waveform for non voice file")
        self.reset()
        ogg = OggStream(self.fp)  # type: ignore
        decoder = Decoder()
        waveform: list[int] = []
        prefixes = [b'OpusHead', b'OpusTags']
        for packet in ogg.iter_packets():
            if packet[:8] in prefixes:
                continue

            if b'vorbis' in packet:
                raise ValueError("File format is 'vorbis'. Format of 'opus' is required for waveform generation")

            # these are PCM bytes in 16-bit signed little-endian form
            decoded = decoder.decode(packet, fec=False)

            # 16 bits -> 2 bytes per sample
            num_samples = len(decoded) // 2

            # https://docs.python.org/3/library/struct.html#byte-order-size-and-alignment
            format = '<' + 'h' * num_samples
            samples: tuple[int] = struct.unpack(format, decoded)

            waveform.extend(samples)

        # Make sure all values are positive
        for i in range(len(waveform)):
            if waveform[i] < 0:
                waveform[i] = -waveform[i]

        point_count: int = self.duration * 10  # type: ignore
        point_count = min(point_count, 255)
        points_per_sample: int = len(waveform) // point_count
        sample_waveform: list[int] = []

        total, count = 0, 0
        # Average out the amplitudes for each point within a sample
        for i in range(len(waveform)):
            total += waveform[i]
            count += 1
            if i % points_per_sample == 0:
                sample_waveform.append(total // count)
                total, count = 0, 0

        # Maximum value of a waveform is 0xff (255)
        highest = max(sample_waveform)
        mult = 255 / highest
        for i in range(len(sample_waveform)):
            sample_waveform[i] = int(sample_waveform[i] * mult)

        return sample_waveform
