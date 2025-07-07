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

from typing import List, Tuple, TypedDict, Any, TYPE_CHECKING, Callable, TypeVar, Literal, Optional, overload

import array
import ctypes
import ctypes.util
import logging
import math
import os.path
import struct
import sys

from .errors import DiscordException

if TYPE_CHECKING:
    T = TypeVar('T')
    APPLICATION_CTL = Literal['audio', 'voip', 'lowdelay']
    BAND_CTL = Literal['narrow', 'medium', 'wide', 'superwide', 'full']
    SIGNAL_CTL = Literal['auto', 'voice', 'music']


class ApplicationCtl(TypedDict):
    audio: int
    voip: int
    lowdelay: int


class BandCtl(TypedDict):
    narrow: int
    medium: int
    wide: int
    superwide: int
    full: int


class SignalCtl(TypedDict):
    auto: int
    voice: int
    music: int


__all__ = (
    'Encoder',
    'OpusError',
    'OpusNotLoaded',
)

_log = logging.getLogger(__name__)

OPUS_SILENCE = b'\xF8\xFF\xFE'

c_int_ptr = ctypes.POINTER(ctypes.c_int)
c_int16_ptr = ctypes.POINTER(ctypes.c_int16)
c_float_ptr = ctypes.POINTER(ctypes.c_float)

_lib: Any = None


class EncoderStruct(ctypes.Structure):
    pass


class DecoderStruct(ctypes.Structure):
    pass


EncoderStructPtr = ctypes.POINTER(EncoderStruct)
DecoderStructPtr = ctypes.POINTER(DecoderStruct)

## Some constants from opus_defines.h
# Error codes
# fmt: off
OK      = 0
BAD_ARG = -1

# Encoder CTLs
APPLICATION_AUDIO    = 'audio'
APPLICATION_VOIP     = 'voip'
APPLICATION_LOWDELAY = 'lowdelay'
# These remain as strings for backwards compat

CTL_SET_BITRATE      = 4002
CTL_SET_BANDWIDTH    = 4008
CTL_SET_FEC          = 4012
CTL_SET_PLP          = 4014
CTL_SET_SIGNAL       = 4024

# Decoder CTLs
CTL_SET_GAIN             = 4034
CTL_LAST_PACKET_DURATION = 4039
# fmt: on

application_ctl: ApplicationCtl = {
    'audio': 2049,
    'voip': 2048,
    'lowdelay': 2051,
}

band_ctl: BandCtl = {
    'narrow': 1101,
    'medium': 1102,
    'wide': 1103,
    'superwide': 1104,
    'full': 1105,
}

signal_ctl: SignalCtl = {
    'auto': -1000,
    'voice': 3001,
    'music': 3002,
}


def _err_lt(result: int, func: Callable, args: List) -> int:
    if result < OK:
        _log.debug('error has happened in %s', func.__name__)
        raise OpusError(result)
    return result


def _err_ne(result: T, func: Callable, args: List) -> T:
    ret = args[-1]._obj
    if ret.value != OK:
        _log.debug('error has happened in %s', func.__name__)
        raise OpusError(ret.value)
    return result


# A list of exported functions.
# The first argument is obviously the name.
# The second one are the types of arguments it takes.
# The third is the result type.
# The fourth is the error handler.
exported_functions: List[Tuple[Any, ...]] = [
    # Generic
    ('opus_get_version_string', [], ctypes.c_char_p, None),
    ('opus_strerror', [ctypes.c_int], ctypes.c_char_p, None),
    # Encoder functions
    ('opus_encoder_get_size', [ctypes.c_int], ctypes.c_int, None),
    ('opus_encoder_create', [ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_ptr], EncoderStructPtr, _err_ne),
    ('opus_encode', [EncoderStructPtr, c_int16_ptr, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int32, _err_lt),
    (
        'opus_encode_float',
        [EncoderStructPtr, c_float_ptr, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32],
        ctypes.c_int32,
        _err_lt,
    ),
    ('opus_encoder_ctl', [EncoderStructPtr, ctypes.c_int], ctypes.c_int32, _err_lt),
    ('opus_encoder_destroy', [EncoderStructPtr], None, None),
    # Decoder functions
    ('opus_decoder_get_size', [ctypes.c_int], ctypes.c_int, None),
    ('opus_decoder_create', [ctypes.c_int, ctypes.c_int, c_int_ptr], DecoderStructPtr, _err_ne),
    (
        'opus_decode',
        [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_int16_ptr, ctypes.c_int, ctypes.c_int],
        ctypes.c_int,
        _err_lt,
    ),
    (
        'opus_decode_float',
        [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_float_ptr, ctypes.c_int, ctypes.c_int],
        ctypes.c_int,
        _err_lt,
    ),
    ('opus_decoder_ctl', [DecoderStructPtr, ctypes.c_int], ctypes.c_int32, _err_lt),
    ('opus_decoder_destroy', [DecoderStructPtr], None, None),
    ('opus_decoder_get_nb_samples', [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int, _err_lt),
    # Packet functions
    ('opus_packet_get_bandwidth', [ctypes.c_char_p], ctypes.c_int, _err_lt),
    ('opus_packet_get_nb_channels', [ctypes.c_char_p], ctypes.c_int, _err_lt),
    ('opus_packet_get_nb_frames', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int, _err_lt),
    ('opus_packet_get_samples_per_frame', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int, _err_lt),
]


def libopus_loader(name: str) -> Any:
    # create the library...
    lib = ctypes.cdll.LoadLibrary(name)

    # register the functions...
    for item in exported_functions:
        func = getattr(lib, item[0])

        try:
            if item[1]:
                func.argtypes = item[1]

            func.restype = item[2]
        except KeyError:
            pass

        try:
            if item[3]:
                func.errcheck = item[3]
        except KeyError:
            _log.exception("Error assigning check function to %s", func)

    return lib


def _load_default() -> bool:
    global _lib
    try:
        if sys.platform == 'win32':
            _basedir = os.path.dirname(os.path.abspath(__file__))
            _bitness = struct.calcsize('P') * 8
            _target = 'x64' if _bitness > 32 else 'x86'
            _filename = os.path.join(_basedir, 'bin', f'libopus-0.{_target}.dll')
            _lib = libopus_loader(_filename)
        else:
            # This is handled in the exception case
            _lib = libopus_loader(ctypes.util.find_library('opus'))  # type: ignore
    except Exception:
        _lib = None

    return _lib is not None


def load_opus(name: str) -> None:
    """Loads the libopus shared library for use with voice.

    If this function is not called then the library uses the function
    :func:`ctypes.util.find_library` and then loads that one if available.

    Not loading a library and attempting to use PCM based AudioSources will
    lead to voice not working.

    This function propagates the exceptions thrown.

    .. warning::

        The bitness of the library must match the bitness of your python
        interpreter. If the library is 64-bit then your python interpreter
        must be 64-bit as well. Usually if there's a mismatch in bitness then
        the load will throw an exception.

    .. note::

        On Windows, this function should not need to be called as the binaries
        are automatically loaded.

    .. note::

        On Windows, the .dll extension is not necessary. However, on Linux
        the full extension is required to load the library, e.g. ``libopus.so.1``.
        On Linux however, :func:`ctypes.util.find_library` will usually find the library automatically
        without you having to call this.

    Parameters
    ----------
    name: :class:`str`
        The filename of the shared library.
    """
    global _lib
    _lib = libopus_loader(name)


def is_loaded() -> bool:
    """Function to check if opus lib is successfully loaded either
    via the :func:`ctypes.util.find_library` call of :func:`load_opus`.

    This must return ``True`` for voice to work.

    Returns
    -------
    :class:`bool`
        Indicates if the opus library has been loaded.
    """
    global _lib
    return _lib is not None


class OpusError(DiscordException):
    """An exception that is thrown for libopus related errors.

    Attributes
    ----------
    code: :class:`int`
        The error code returned.
    """

    def __init__(self, code: int):
        self.code: int = code
        msg = _lib.opus_strerror(self.code).decode('utf-8')
        _log.debug('"%s" has happened', msg)
        super().__init__(msg)


class OpusNotLoaded(DiscordException):
    """An exception that is thrown for when libopus is not loaded."""

    pass


class _OpusStruct:
    SAMPLING_RATE = 48000
    CHANNELS = 2
    FRAME_LENGTH = 20  # in milliseconds
    SAMPLE_SIZE = struct.calcsize('h') * CHANNELS
    SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

    FRAME_SIZE = SAMPLES_PER_FRAME * SAMPLE_SIZE

    @staticmethod
    def get_opus_version() -> str:
        if not is_loaded() and not _load_default():
            raise OpusNotLoaded()

        return _lib.opus_get_version_string().decode('utf-8')


class Encoder(_OpusStruct):
    def __init__(
        self,
        *,
        application: APPLICATION_CTL = 'audio',
        bitrate: int = 128,
        fec: bool = True,
        expected_packet_loss: float = 0.15,
        bandwidth: BAND_CTL = 'full',
        signal_type: SIGNAL_CTL = 'auto',
    ):
        if application not in application_ctl:
            raise ValueError(f'{application} is not a valid application setting. Try one of: {"".join(application_ctl)}')

        if not 16 <= bitrate <= 512:
            raise ValueError(f'bitrate must be between 16 and 512, not {bitrate}')

        if not 0 < expected_packet_loss <= 1.0:
            raise ValueError(
                f'expected_packet_loss must be a positive number less than or equal to 1, not {expected_packet_loss}'
            )

        _OpusStruct.get_opus_version()  # lazy loads the opus library

        self.application: int = application_ctl[application]
        self._state: EncoderStruct = self._create_state()

        self.set_bitrate(bitrate)
        self.set_fec(fec)
        if fec:
            self.set_expected_packet_loss_percent(expected_packet_loss)
        self.set_bandwidth(bandwidth)
        self.set_signal_type(signal_type)

    def __del__(self) -> None:
        if hasattr(self, '_state'):
            _lib.opus_encoder_destroy(self._state)
            # This is a destructor, so it's okay to assign None
            self._state = None  # type: ignore

    def _create_state(self) -> EncoderStruct:
        ret = ctypes.c_int()
        return _lib.opus_encoder_create(self.SAMPLING_RATE, self.CHANNELS, self.application, ctypes.byref(ret))

    def set_bitrate(self, kbps: int) -> int:
        kbps = min(512, max(16, int(kbps)))

        _lib.opus_encoder_ctl(self._state, CTL_SET_BITRATE, kbps * 1024)
        return kbps

    def set_bandwidth(self, req: BAND_CTL) -> None:
        if req not in band_ctl:
            raise KeyError(f'{req!r} is not a valid bandwidth setting. Try one of: {",".join(band_ctl)}')

        k = band_ctl[req]
        _lib.opus_encoder_ctl(self._state, CTL_SET_BANDWIDTH, k)

    def set_signal_type(self, req: SIGNAL_CTL) -> None:
        if req not in signal_ctl:
            raise KeyError(f'{req!r} is not a valid signal type setting. Try one of: {",".join(signal_ctl)}')

        k = signal_ctl[req]
        _lib.opus_encoder_ctl(self._state, CTL_SET_SIGNAL, k)

    def set_fec(self, enabled: bool = True) -> None:
        _lib.opus_encoder_ctl(self._state, CTL_SET_FEC, 1 if enabled else 0)

    def set_expected_packet_loss_percent(self, percentage: float) -> None:
        _lib.opus_encoder_ctl(self._state, CTL_SET_PLP, min(100, max(0, int(percentage * 100))))

    def encode(self, pcm: bytes, frame_size: int) -> bytes:
        max_data_bytes = len(pcm)
        # bytes can be used to reference pointer
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)  # type: ignore
        data = (ctypes.c_char * max_data_bytes)()

        ret = _lib.opus_encode(self._state, pcm_ptr, frame_size, data, max_data_bytes)

        return array.array('b', data[:ret]).tobytes()


class Decoder(_OpusStruct):
    def __init__(self):
        _OpusStruct.get_opus_version()

        self._state: DecoderStruct = self._create_state()

    def __del__(self) -> None:
        if hasattr(self, '_state'):
            _lib.opus_decoder_destroy(self._state)
            # This is a destructor, so it's okay to assign None
            self._state = None  # type: ignore

    def _create_state(self) -> DecoderStruct:
        ret = ctypes.c_int()
        return _lib.opus_decoder_create(self.SAMPLING_RATE, self.CHANNELS, ctypes.byref(ret))

    @staticmethod
    def packet_get_nb_frames(data: bytes) -> int:
        """Gets the number of frames in an Opus packet"""
        return _lib.opus_packet_get_nb_frames(data, len(data))

    @staticmethod
    def packet_get_nb_channels(data: bytes) -> int:
        """Gets the number of channels in an Opus packet"""
        return _lib.opus_packet_get_nb_channels(data)

    @classmethod
    def packet_get_samples_per_frame(cls, data: bytes) -> int:
        """Gets the number of samples per frame from an Opus packet"""
        return _lib.opus_packet_get_samples_per_frame(data, cls.SAMPLING_RATE)

    def _set_gain(self, adjustment: int) -> int:
        """Configures decoder gain adjustment.

        Scales the decoded output by a factor specified in Q8 dB units.
        This has a maximum range of -32768 to 32767 inclusive, and returns
        OPUS_BAD_ARG (-1) otherwise. The default is zero indicating no adjustment.
        This setting survives decoder reset (irrelevant for now).
        gain = 10**x/(20.0*256)
        (from opus_defines.h)
        """
        return _lib.opus_decoder_ctl(self._state, CTL_SET_GAIN, adjustment)

    def set_gain(self, dB: float) -> int:
        """Sets the decoder gain in dB, from -128 to 128."""

        dB_Q8 = max(-32768, min(32767, round(dB * 256)))  # dB * 2^n where n is 8 (Q8)
        return self._set_gain(dB_Q8)

    def set_volume(self, mult: float) -> int:
        """Sets the output volume as a float percent, i.e. 0.5 for 50%, 1.75 for 175%, etc."""
        return self.set_gain(20 * math.log10(mult))  # amplitude ratio

    def _get_last_packet_duration(self) -> int:
        """Gets the duration (in samples) of the last packet successfully decoded or concealed."""

        ret = ctypes.c_int32()
        _lib.opus_decoder_ctl(self._state, CTL_LAST_PACKET_DURATION, ctypes.byref(ret))
        return ret.value

    @overload
    def decode(self, data: bytes, *, fec: bool) -> bytes:
        ...

    @overload
    def decode(self, data: Literal[None], *, fec: Literal[False]) -> bytes:
        ...

    def decode(self, data: Optional[bytes], *, fec: bool = False) -> bytes:
        if data is None and fec:
            raise TypeError("Invalid arguments: FEC cannot be used with null data")

        if data is None:
            frame_size = self._get_last_packet_duration() or self.SAMPLES_PER_FRAME
            channel_count = self.CHANNELS
        else:
            frames = self.packet_get_nb_frames(data)
            # Discord silent frames erroneously present themselves as 1 channel instead of 2
            # Therefore we need to hardcode the number instead of using packet_get_nb_channels
            channel_count = self.CHANNELS
            samples_per_frame = self.packet_get_samples_per_frame(data)
            frame_size = frames * samples_per_frame

        pcm = (ctypes.c_int16 * (frame_size * channel_count))()
        pcm_ptr = ctypes.cast(pcm, c_int16_ptr)

        ret = _lib.opus_decode(self._state, data, len(data) if data else 0, pcm_ptr, frame_size, fec)

        return array.array('h', pcm[: ret * channel_count]).tobytes()
