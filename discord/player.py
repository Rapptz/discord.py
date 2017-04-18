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

import threading
import subprocess
import shlex
import time

from .errors import ClientException
from .opus import Encoder as OpusEncoder

__all__ = [ 'AudioSource', 'PCMAudio', 'FFmpegPCMAudio' ]

class AudioSource:
    """Represents an audio stream.

    The audio stream can be Opus encoded or not, however if the audio stream
    is not Opus encoded then the audio format must be 16-bit 48KHz stereo PCM.

    .. warning::

        The audio source reads are done in a separate thread.
    """

    def read(self):
        """Reads 20ms worth of audio.

        Subclasses must implement this.

        If the audio is complete, then returning an empty *bytes-like* object
        to signal this is the way to do so.

        If :meth:`is_opus` method returns ``True``, then it must return
        20ms worth of Opus encoded audio. Otherwise, it must be 20ms
        worth of 16-bit 48KHz stereo PCM, which is about 3,840 bytes
        per frame (20ms worth of audio).

        Returns
        --------
        bytes
            A bytes like object that represents the PCM or Opus data.
        """
        raise NotImplementedError

    def is_opus(self):
        """Checks if the audio source is already encoded in Opus.

        Defaults to ``False``.
        """
        return False

    def cleanup(self):
        """Called when clean-up is needed to be done.

        Useful for clearing buffer data or processes after
        it is done playing audio.
        """
        pass

class PCMAudio(AudioSource):
    """Represents raw 16-bit 48KHz stereo PCM audio source.

    Attributes
    -----------
    stream: file-like object
        A file-like object that reads byte data representing raw PCM.
    """
    def __init__(self, stream):
        self.stream = stream

    def read(self):
        return self.stream.read(OpusEncoder.FRAME_SIZE)

class FFmpegPCMAudio(AudioSource):
    """An audio source from FFmpeg (or AVConv).

    This launches a sub-process to a specific input file given.

    .. warning::

        You must have the ffmpeg or avconv executable in your path environment
        variable in order for this to work.

    Parameters
    ------------
    source: Union[str, BinaryIO]
        The input that ffmpeg will take and convert to PCM bytes.
        If ``pipe`` is True then this is a file-like object that is
        passed to the stdin of ffmpeg.
    executable: str
        The executable name (and path) to use. Defaults to ``ffmpeg``.
    pipe: bool
        If true, denotes that ``source`` parameter will be passed
        to the stdin of ffmpeg. Defaults to ``False``.
    stderr: Optional[BinaryIO]
        A file-like object to pass to the Popen constructor.
        Could also be an instance of ``subprocess.PIPE``.
    options: Optional[str]
        Extra command line arguments to pass to ffmpeg after the ``-i`` flag.
    before_options: Optional[str]
        Extra command line arguments to pass to ffmpeg before the ``-i`` flag.

    Raises
    --------
    ClientException
        The subprocess failed to be created.
    """

    def __init__(self, source, *, executable='ffmpeg', pipe=False, stderr=None, before_options=None, options=None):
        stdin = None if not pipe else source

        args = [executable]

        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))

        args.append('-i')
        args.append('-' if pipe else source)
        args.extend(('-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning'))

        if isinstance(options, str):
            args.extend(shlex.split(options))

        args.append('pipe:1')

        try:
            self._process = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
            self._stdout = self._process.stdout
        except FileNotFoundError:
            raise ClientException(executable + ' was not found.') from None
        except subprocess.SubprocessError as e:
            raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(e)) from e

    def read(self):
        return self._stdout.read(OpusEncoder.FRAME_SIZE)

    def cleanup(self):
        proc = self._process
        proc.kill()
        if proc.poll() is None:
            proc.communicate()

class AudioPlayer(threading.Thread):
    DELAY = OpusEncoder.FRAME_LENGTH / 1000.0

    def __init__(self, source, client, *, after=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.source = source
        self.client = client
        self.after = after

        self._end = threading.Event()
        self._resumed = threading.Event()
        self._resumed.set() # we are not paused
        self._current_error = None
        self._connected = client._connected

        if after is not None and not callable(after):
            raise TypeError('Expected a callable for the "after" parameter.')

    def _do_run(self):
        self.loops = 0
        self._start = time.time()
        is_opus = self.source.is_opus()

        # getattr lookup speed ups
        play_audio = self.client.send_audio_packet

        while not self._end.is_set():
            # are we paused?
            if not self._resumed.is_set():
                # wait until we aren't
                self._resumed.wait()

            # are we disconnected from voice?
            if not self._connected.is_set():
                # wait until we are connected
                self._connected.wait()
                # reset our internal data
                self.loops = 0
                self._start = time.time()

            self.loops += 1
            data = self.source.read()

            if not data:
                self.stop()
                break

            play_audio(data, encode=not is_opus)
            next_time = self._start + self.DELAY * self.loops
            delay = max(0, self.DELAY + (next_time - time.time()))
            time.sleep(delay)

    def run(self):
        try:
            self._do_run()
        except Exception as e:
            self._current_error = e
            self.stop()
        finally:
            self._call_after()
            self.source.cleanup()

    def _call_after(self):
        if self.after is not None:
            try:
                self.after(self._current_error)
            except:
                pass

    def stop(self):
        self._end.set()

    def pause(self):
        self._resumed.clear()

    def resume(self):
        self.loops = 0
        self._start = time.time()
        self._resumed.set()

    def is_playing(self):
        return self._resumed.is_set() and not self._end.is_set()
