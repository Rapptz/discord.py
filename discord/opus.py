# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015 Rapptz

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

import ctypes
import ctypes.util
import array
from .errors import DiscordException
import logging

log = logging.getLogger(__name__)
c_int_ptr = ctypes.POINTER(ctypes.c_int)
c_int16_ptr = ctypes.POINTER(ctypes.c_int16)
c_float_ptr = ctypes.POINTER(ctypes.c_float)

class EncoderStruct(ctypes.Structure):
    pass

EncoderStructPtr = ctypes.POINTER(EncoderStruct)

class DecoderStruct(ctypes.Structure):
    pass

DecoderStructPtr = ctypes.POINTER(DecoderStruct)

# A list of exported functions.
# The first argument is obviously the name.
# The second one are the types of arguments it takes.
# The third is the result type.
exported_functions = [
    ('opus_strerror', [ctypes.c_int], ctypes.c_char_p),

    # Encoder functions
    ('opus_encoder_get_size', [ctypes.c_int], ctypes.c_int),
    ('opus_encoder_create', [ctypes.c_int, ctypes.c_int, ctypes.c_int, c_int_ptr], EncoderStructPtr),
    ('opus_encode', [EncoderStructPtr, c_int16_ptr, ctypes.c_int, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int32),
    ('opus_encoder_destroy', [EncoderStructPtr], None),

    # Decoder functions
    ('opus_decoder_get_size', [ctypes.c_int], ctypes.c_int),
    ('opus_decoder_create', [ctypes.c_int, ctypes.c_int, c_int_ptr], DecoderStructPtr),
    ('opus_packet_get_bandwidth', [ctypes.c_char_p], ctypes.c_int),
    ('opus_packet_get_nb_channels', [ctypes.c_char_p], ctypes.c_int),
    ('opus_packet_get_nb_frames', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int),
    ('opus_packet_get_samples_per_frame', [ctypes.c_char_p, ctypes.c_int], ctypes.c_int),
    ('opus_decoder_get_nb_samples', [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32], ctypes.c_int),
    ('opus_decode', [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_int16_ptr, ctypes.c_int, ctypes.c_int], ctypes.c_int),
    ('opus_decode_float', [DecoderStructPtr, ctypes.c_char_p, ctypes.c_int32, c_float_ptr, ctypes.c_int, ctypes.c_int], ctypes.c_int),
    ('opus_decoder_destroy', [DecoderStructPtr], None)
]

def libopus_loader(name):
    # create the library...
    lib = ctypes.cdll.LoadLibrary(name)

    # register the functions...
    for item in exported_functions:
        try:
            func = getattr(lib, item[0])
        except Exception as e:
            raise e

        try:
            func.argtypes = item[1]
            func.restype = item[2]
        except KeyError:
            pass

    return lib

try:
    _lib = libopus_loader(ctypes.util.find_library('opus'))
except:
    _lib = None

def load_opus(name):
    """Loads the libopus shared library for use with voice.

    If this function is not called then the library uses the function
    `ctypes.util.find_library`__ and then loads that one
    if available.

    .. _find library: https://docs.python.org/3.5/library/ctypes.html#finding-shared-libraries
    __ `find library`_

    Not loading a library leads to voice not working.

    This function propagates the exceptions thrown.

    Warning
    --------
    The bitness of the library must match the bitness of your python
    interpreter. If the library is 64-bit then your python interpreter
    must be 64-bit as well. Usually if there's a mismatch in bitness then
    the load will throw an exception.

    Note
    ----
    On Windows, the .dll extension is not necessary. However, on Linux
    the full extension is required to load the library, e.g. ``libopus.so.1``.
    On Linux however, `find library`_ will usually find the library automatically
    without you having to call this.

    Parameters
    ----------
    name: str
        The filename of the shared library.
    """
    global _lib
    _lib = libopus_loader(name)

def is_loaded():
    """Function to check if opus lib is successfully loaded either
    via the ``ctypes.util.find_library`` call of :func:`load_opus`.

    This must return ``True`` for voice to work.

    Returns
    -------
    bool
        Indicates if the opus library has been loaded.
    """
    global _lib
    return _lib is not None

class OpusError(DiscordException):
    """An exception that is thrown for libopus related errors.

    Attributes
    ----------
    code : int
        The error code returned.
    """
    def __init__(self, code):
        self.code = code
        msg = _lib.opus_strerror(self.code).decode('utf-8')
        log.info('"{}" has happened'.format(msg))
        super().__init__(msg)

class OpusNotLoaded(DiscordException):
    """An exception that is thrown for when libopus is not loaded."""
    pass


# Some constants...
OK = 0
APPLICATION_AUDIO    = 2049
APPLICATION_VOIP     = 2048
APPLICATION_LOWDELAY = 2051

class Encoder:
    def __init__(self, sampling, channels, application=APPLICATION_AUDIO):
        self.sampling_rate = sampling
        self.channels = channels
        self.application = application

        self.frame_length = 20
        self.sample_size = 2 * self.channels # (bit_rate / 8) but bit_rate == 16
        self.samples_per_frame = int(self.sampling_rate / 1000 * self.frame_length)
        self.frame_size = self.samples_per_frame * self.sample_size

        if not is_loaded():
            raise OpusNotLoaded()

        self._state = self._create_state()

    def __del__(self):
        if hasattr(self, '_state'):
            _lib.opus_encoder_destroy(self._state)
            self._state = None

    def _create_state(self):
        ret = ctypes.c_int()
        result = _lib.opus_encoder_create(self.sampling_rate, self.channels, self.application, ctypes.byref(ret))

        if ret.value != 0:
            log.info('error has happened in encoder state creation')
            raise OpusError(ret.value)

        return result

    def encode(self, pcm, frame_size):
        max_data_bytes = len(pcm)
        pcm = ctypes.cast(pcm, c_int16_ptr)
        data = (ctypes.c_char * max_data_bytes)()

        ret = _lib.opus_encode(self._state, pcm, frame_size, data, max_data_bytes)
        if ret < 0:
            log.info('error has happened in encode')
            raise OpusError(ret)

        return array.array('b', data[:ret]).tobytes()

class Decoder:
    def __init__(self, sampling=48000, channels=2):
        self.sampling_rate = sampling
        self.channels = channels

        self._state = self._create_state()

    def __del__(self):
        if hasattr(self, '_state'):
            _lib.opus_decoder_destroy(self._state)
            self._state = None

    def _create_state(self):
        ret = ctypes.c_int()
        result = _lib.opus_decoder_create(self.sampling_rate, self.channels, ctypes.byref(ret))

        if ret.value != 0:
            log.info('error has happened in decoder state creation')
            raise OpusError(ret.value)

        return result

    @classmethod
    def _packet_get_nb_frames(cls, data):
        """Gets the number of frames in an Opus packet"""
        result = _lib.opus_packet_get_nb_frames(data, len(data))
        if result < 0:
            log.info('error has happened in packet_get_nb_frames')
            raise OpusError(result)

        return result

    @classmethod
    def _packet_get_nb_channels(cls, data):
        """Gets the number of channels in an Opus packet"""
        result = _lib.opus_packet_get_nb_channels(data)
        if result < 0:
            log.info('error has happened in packet_get_nb_channels')
            raise OpusError(result)

        return result

    def _packet_get_samples_per_frame(self, data):
        """Gets the number of samples per frame from an Opus packet"""
        result = _lib.opus_packet_get_samples_per_frame(data, self.sampling_rate)
        if result < 0:
            log.info('error has happened in packet_get_samples_per_frame')
            raise OpusError(result)

        return result

    def _decode(self, data, frame_size, decode_fec, decode_func, decode_ctype, arr_type):
        if frame_size is None:
            frames = self._packet_get_nb_frames(data)
            samples_per_frame = self._packet_get_samples_per_frame(data)
            # note: channels could be different from self.channels
            # this doesn't actually get used in frame_size, but we get
            # the value for debugging
            channels = self._packet_get_nb_channels(data)
            frame_size = frames * samples_per_frame
            log.debug('detected frame_size {} ({} frames, {} samples per frame, {} channels)'.format(frame_size, frames, samples_per_frame, channels))

        # note: python-opus also multiplies this value by
        # ctypes.sizeof(decode_ctype) but that appears to be wrong
        pcm_size = frame_size * self.channels
        pcm = (decode_ctype * pcm_size)()
        pcm_ptr = ctypes.cast(pcm, ctypes.POINTER(decode_ctype))

        decode_fec = int(bool(decode_fec))

        result = decode_func(self._state, data, len(data), pcm_ptr, frame_size, decode_fec)
        if result < 0:
            log.info('error happened in decode')
            raise OpusError(result)

        # note: I'm not sure exactly how to interpret result. It appears to be
        # the number of samples decoded, but if the packet was only 1 channel
        # and the decoder was created with 2 channels, the actual output
        # appears to be 2 * result samples (same audio on each channel).
        # Regardless, the way we've created the pcm buffer, it should be
        # completely filled.
        log.debug('opus decode result: {} (total buf size: {})'.format(result, len(pcm)))
        return array.array(arr_type, pcm).tobytes()

    def decode(self, data, frame_size=None, decode_fec=False):
        return self._decode(data, frame_size, decode_fec, _lib.opus_decode, ctypes.c_int16, 'h')

    def decode_float(self, data, frame_size=None, decode_fec=False):
        return self._decode(data, frame_size, decode_fec, _lib.opus_decode_float, ctypes.c_float, 'f')
