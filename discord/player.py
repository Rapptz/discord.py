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

import threading
import subprocess
import audioop
import asyncio
import logging
import shlex
import time
import json
import sys
import re
import io

from typing import Any, Callable, Generic, IO, Optional, TYPE_CHECKING, Tuple, TypeVar, Union

from .enums import SpeakingState
from .errors import ClientException
from .opus import Encoder as OpusEncoder
from .oggparse import OggStream
from .utils import MISSING

if TYPE_CHECKING:
    from typing_extensions import Self

    from .voice_client import VoiceClient


AT = TypeVar('AT', bound='AudioSource')

_log = logging.getLogger(__name__)

__all__ = (
    'AudioSource',
    'PCMAudio',
    'FFmpegAudio',
    'FFmpegPCMAudio',
    'FFmpegOpusAudio',
    'PCMVolumeTransformer',
)

CREATE_NO_WINDOW: int

if sys.platform != 'win32':
    CREATE_NO_WINDOW = 0
else:
    CREATE_NO_WINDOW = 0x08000000


class AudioSource:
    """Represents an audio stream.

    The audio stream can be Opus encoded or not, however if the audio stream
    is not Opus encoded then the audio format must be 16-bit 48KHz stereo PCM.

    .. warning::

        The audio source reads are done in a separate thread.
    """

    def read(self) -> bytes:
        """Reads 20ms worth of audio.

        Subclasses must implement this.

        If the audio is complete, then returning an empty
        :term:`py:bytes-like object` to signal this is the way to do so.

        If :meth:`~AudioSource.is_opus` method returns ``True``, then it must return
        20ms worth of Opus encoded audio. Otherwise, it must be 20ms
        worth of 16-bit 48KHz stereo PCM, which is about 3,840 bytes
        per frame (20ms worth of audio).

        Returns
        --------
        :class:`bytes`
            A bytes like object that represents the PCM or Opus data.
        """
        raise NotImplementedError

    def is_opus(self) -> bool:
        """Checks if the audio source is already encoded in Opus."""
        return False

    def cleanup(self) -> None:
        """Called when clean-up is needed to be done.

        Useful for clearing buffer data or processes after
        it is done playing audio.
        """
        pass

    def __del__(self) -> None:
        self.cleanup()


class PCMAudio(AudioSource):
    """Represents raw 16-bit 48KHz stereo PCM audio source.

    Attributes
    -----------
    stream: :term:`py:file object`
        A file-like object that reads byte data representing raw PCM.
    """

    def __init__(self, stream: io.BufferedIOBase) -> None:
        self.stream: io.BufferedIOBase = stream

    def read(self) -> bytes:
        ret = self.stream.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b''
        return ret


class FFmpegAudio(AudioSource):
    """Represents an FFmpeg (or AVConv) based AudioSource.

    User created AudioSources using FFmpeg differently from how :class:`FFmpegPCMAudio` and
    :class:`FFmpegOpusAudio` work should subclass this.

    .. versionadded:: 1.3
    """

    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = 'ffmpeg',
        args: Any,
        **subprocess_kwargs: Any,
    ):
        piping = subprocess_kwargs.get('stdin') == subprocess.PIPE
        if piping and isinstance(source, str):
            raise TypeError("parameter conflict: 'source' parameter cannot be a string when piping to stdin")

        args = [executable, *args]
        kwargs = {'stdout': subprocess.PIPE}
        kwargs.update(subprocess_kwargs)

        # Ensure attribute is assigned even in the case of errors
        self._process: subprocess.Popen = MISSING
        self._process = self._spawn_process(args, **kwargs)
        self._stdout: IO[bytes] = self._process.stdout  # type: ignore # process stdout is explicitly set
        self._stdin: Optional[IO[bytes]] = None
        self._pipe_thread: Optional[threading.Thread] = None

        if piping:
            n = f'popen-stdin-writer:{id(self):#x}'
            self._stdin = self._process.stdin
            self._pipe_thread = threading.Thread(target=self._pipe_writer, args=(source,), daemon=True, name=n)
            self._pipe_thread.start()

    def _spawn_process(self, args: Any, **subprocess_kwargs: Any) -> subprocess.Popen:
        process = None
        try:
            process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW, **subprocess_kwargs)
        except FileNotFoundError:
            executable = args.partition(' ')[0] if isinstance(args, str) else args[0]
            raise ClientException(executable + ' was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException(f'Popen failed: {exc.__class__.__name__}: {exc}') from exc
        else:
            return process

    def _kill_process(self) -> None:
        proc = self._process
        if proc is MISSING:
            return

        _log.debug('Preparing to terminate ffmpeg process %s.', proc.pid)

        try:
            proc.kill()
        except Exception:
            _log.exception('Ignoring error attempting to kill ffmpeg process %s', proc.pid)

        if proc.poll() is None:
            _log.info('ffmpeg process %s has not terminated. Waiting to terminate...', proc.pid)
            proc.communicate()
            _log.info('ffmpeg process %s should have terminated with a return code of %s.', proc.pid, proc.returncode)
        else:
            _log.info('ffmpeg process %s successfully terminated with return code of %s.', proc.pid, proc.returncode)

    def _pipe_writer(self, source: io.BufferedIOBase) -> None:
        while self._process:
            # arbitrarily large read size
            data = source.read(8192)
            if not data:
                if self._stdin is not None:
                    self._stdin.close()
                return
            try:
                if self._stdin is not None:
                    self._stdin.write(data)
            except Exception:
                _log.debug('Write error for %s, this is probably not a problem', self, exc_info=True)
                # at this point the source data is either exhausted or the process is fubar
                self._process.terminate()
                return

    def cleanup(self) -> None:
        self._kill_process()
        self._process = self._stdout = self._stdin = MISSING


class FFmpegPCMAudio(FFmpegAudio):
    """An audio source from FFmpeg (or AVConv).

    This launches a sub-process to a specific input file given.

    .. warning::

        You must have the ffmpeg or avconv executable in your path environment
        variable in order for this to work.

    Parameters
    ------------
    source: Union[:class:`str`, :class:`io.BufferedIOBase`]
        The input that ffmpeg will take and convert to PCM bytes.
        If ``pipe`` is ``True`` then this is a file-like object that is
        passed to the stdin of ffmpeg.
    executable: :class:`str`
        The executable name (and path) to use. Defaults to ``ffmpeg``.
    pipe: :class:`bool`
        If ``True``, denotes that ``source`` parameter will be passed
        to the stdin of ffmpeg. Defaults to ``False``.
    stderr: Optional[:term:`py:file object`]
        A file-like object to pass to the Popen constructor.
        Could also be an instance of ``subprocess.PIPE``.
    before_options: Optional[:class:`str`]
        Extra command line arguments to pass to ffmpeg before the ``-i`` flag.
    options: Optional[:class:`str`]
        Extra command line arguments to pass to ffmpeg after the ``-i`` flag.

    Raises
    --------
    ClientException
        The subprocess failed to be created.
    """

    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        executable: str = 'ffmpeg',
        pipe: bool = False,
        stderr: Optional[IO[str]] = None,
        before_options: Optional[str] = None,
        options: Optional[str] = None,
    ) -> None:
        args = []
        subprocess_kwargs = {'stdin': subprocess.PIPE if pipe else subprocess.DEVNULL, 'stderr': stderr}

        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))

        args.append('-i')
        args.append('-' if pipe else source)
        args.extend(('-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning'))

        if isinstance(options, str):
            args.extend(shlex.split(options))

        args.append('pipe:1')

        super().__init__(source, executable=executable, args=args, **subprocess_kwargs)

    def read(self) -> bytes:
        ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b''
        return ret

    def is_opus(self) -> bool:
        return False


class FFmpegOpusAudio(FFmpegAudio):
    """An audio source from FFmpeg (or AVConv).

    This launches a sub-process to a specific input file given.  However, rather than
    producing PCM packets like :class:`FFmpegPCMAudio` does that need to be encoded to
    Opus, this class produces Opus packets, skipping the encoding step done by the library.

    Alternatively, instead of instantiating this class directly, you can use
    :meth:`FFmpegOpusAudio.from_probe` to probe for bitrate and codec information.  This
    can be used to opportunistically skip pointless re-encoding of existing Opus audio data
    for a boost in performance at the cost of a short initial delay to gather the information.
    The same can be achieved by passing ``copy`` to the ``codec`` parameter, but only if you
    know that the input source is Opus encoded beforehand.

    .. versionadded:: 1.3

    .. warning::

        You must have the ffmpeg or avconv executable in your path environment
        variable in order for this to work.

    Parameters
    ------------
    source: Union[:class:`str`, :class:`io.BufferedIOBase`]
        The input that ffmpeg will take and convert to Opus bytes.
        If ``pipe`` is ``True`` then this is a file-like object that is
        passed to the stdin of ffmpeg.
    bitrate: :class:`int`
        The bitrate in kbps to encode the output to.  Defaults to ``128``.
    codec: Optional[:class:`str`]
        The codec to use to encode the audio data.  Normally this would be
        just ``libopus``, but is used by :meth:`FFmpegOpusAudio.from_probe` to
        opportunistically skip pointlessly re-encoding Opus audio data by passing
        ``copy`` as the codec value.  Any values other than ``copy``, ``opus``, or
        ``libopus`` will be considered ``libopus``.  Defaults to ``libopus``.

        .. warning::

            Do not provide this parameter unless you are certain that the audio input is
            already Opus encoded.  For typical use :meth:`FFmpegOpusAudio.from_probe`
            should be used to determine the proper value for this parameter.

    executable: :class:`str`
        The executable name (and path) to use. Defaults to ``ffmpeg``.
    pipe: :class:`bool`
        If ``True``, denotes that ``source`` parameter will be passed
        to the stdin of ffmpeg. Defaults to ``False``.
    stderr: Optional[:term:`py:file object`]
        A file-like object to pass to the Popen constructor.
        Could also be an instance of ``subprocess.PIPE``.
    before_options: Optional[:class:`str`]
        Extra command line arguments to pass to ffmpeg before the ``-i`` flag.
    options: Optional[:class:`str`]
        Extra command line arguments to pass to ffmpeg after the ``-i`` flag.

    Raises
    --------
    ClientException
        The subprocess failed to be created.
    """

    def __init__(
        self,
        source: Union[str, io.BufferedIOBase],
        *,
        bitrate: Optional[int] = None,
        codec: Optional[str] = None,
        executable: str = 'ffmpeg',
        pipe: bool = False,
        stderr: Optional[IO[bytes]] = None,
        before_options: Optional[str] = None,
        options: Optional[str] = None,
    ) -> None:
        args = []
        subprocess_kwargs = {'stdin': subprocess.PIPE if pipe else subprocess.DEVNULL, 'stderr': stderr}

        if isinstance(before_options, str):
            args.extend(shlex.split(before_options))

        args.append('-i')
        args.append('-' if pipe else source)

        codec = 'copy' if codec in ('opus', 'libopus') else 'libopus'
        bitrate = bitrate if bitrate is not None else 128

        # fmt: off
        args.extend(('-map_metadata', '-1',
                     '-f', 'opus',
                     '-c:a', codec,
                     '-ar', '48000',
                     '-ac', '2',
                     '-b:a', f'{bitrate}k',
                     '-loglevel', 'warning'))
        # fmt: on

        if isinstance(options, str):
            args.extend(shlex.split(options))

        args.append('pipe:1')

        super().__init__(source, executable=executable, args=args, **subprocess_kwargs)
        self._packet_iter = OggStream(self._stdout).iter_packets()

    @classmethod
    async def from_probe(
        cls,
        source: str,
        *,
        method: Optional[Union[str, Callable[[str, str], Tuple[Optional[str], Optional[int]]]]] = None,
        **kwargs: Any,
    ) -> Self:
        """|coro|

        A factory method that creates a :class:`FFmpegOpusAudio` after probing
        the input source for audio codec and bitrate information.

        Examples
        ----------

        Use this function to create an :class:`FFmpegOpusAudio` instance instead of the constructor: ::

            source = await discord.FFmpegOpusAudio.from_probe("song.webm")
            voice_client.play(source)

        If you are on Windows and don't have ffprobe installed, use the ``fallback`` method
        to probe using ffmpeg instead: ::

            source = await discord.FFmpegOpusAudio.from_probe("song.webm", method='fallback')
            voice_client.play(source)

        Using a custom method of determining codec and bitrate: ::

            def custom_probe(source, executable):
                # some analysis code here
                return codec, bitrate

            source = await discord.FFmpegOpusAudio.from_probe("song.webm", method=custom_probe)
            voice_client.play(source)

        Parameters
        ------------
        source
            Identical to the ``source`` parameter for the constructor.
        method: Optional[Union[:class:`str`, Callable[:class:`str`, :class:`str`]]]
            The probing method used to determine bitrate and codec information. As a string, valid
            values are ``native`` to use ffprobe (or avprobe) and ``fallback`` to use ffmpeg
            (or avconv).  As a callable, it must take two string arguments, ``source`` and
            ``executable``.  Both parameters are the same values passed to this factory function.
            ``executable`` will default to ``ffmpeg`` if not provided as a keyword argument.
        kwargs
            The remaining parameters to be passed to the :class:`FFmpegOpusAudio` constructor,
            excluding ``bitrate`` and ``codec``.

        Raises
        --------
        AttributeError
            Invalid probe method, must be ``'native'`` or ``'fallback'``.
        TypeError
            Invalid value for ``probe`` parameter, must be :class:`str` or a callable.

        Returns
        --------
        :class:`FFmpegOpusAudio`
            An instance of this class.
        """

        executable = kwargs.get('executable')
        codec, bitrate = await cls.probe(source, method=method, executable=executable)
        return cls(source, bitrate=bitrate, codec=codec, **kwargs)

    @classmethod
    async def probe(
        cls,
        source: str,
        *,
        method: Optional[Union[str, Callable[[str, str], Tuple[Optional[str], Optional[int]]]]] = None,
        executable: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[int]]:
        """|coro|

        Probes the input source for bitrate and codec information.

        Parameters
        ------------
        source
            Identical to the ``source`` parameter for :class:`FFmpegOpusAudio`.
        method
            Identical to the ``method`` parameter for :meth:`FFmpegOpusAudio.from_probe`.
        executable: :class:`str`
            Identical to the ``executable`` parameter for :class:`FFmpegOpusAudio`.

        Raises
        --------
        AttributeError
            Invalid probe method, must be ``'native'`` or ``'fallback'``.
        TypeError
            Invalid value for ``probe`` parameter, must be :class:`str` or a callable.

        Returns
        ---------
        Optional[Tuple[Optional[:class:`str`], :class:`int`]]
            A 2-tuple with the codec and bitrate of the input source.
        """

        method = method or 'native'
        executable = executable or 'ffmpeg'
        probefunc = fallback = None

        if isinstance(method, str):
            probefunc = getattr(cls, '_probe_codec_' + method, None)
            if probefunc is None:
                raise AttributeError(f"Invalid probe method {method!r}")

            if probefunc is cls._probe_codec_native:
                fallback = cls._probe_codec_fallback

        elif callable(method):
            probefunc = method
            fallback = cls._probe_codec_fallback
        else:
            raise TypeError(f"Expected str or callable for parameter 'probe', not '{method.__class__.__name__}'")

        codec = bitrate = None
        loop = asyncio.get_running_loop()
        try:
            codec, bitrate = await loop.run_in_executor(None, lambda: probefunc(source, executable))
        except Exception:
            if not fallback:
                _log.exception("Probe '%s' using '%s' failed", method, executable)
                return  # type: ignore

            _log.exception("Probe '%s' using '%s' failed, trying fallback", method, executable)
            try:
                codec, bitrate = await loop.run_in_executor(None, lambda: fallback(source, executable))
            except Exception:
                _log.exception("Fallback probe using '%s' failed", executable)
            else:
                _log.debug("Fallback probe found codec=%s, bitrate=%s", codec, bitrate)
        else:
            _log.debug("Probe found codec=%s, bitrate=%s", codec, bitrate)
        finally:
            return codec, bitrate

    @staticmethod
    def _probe_codec_native(source, executable: str = 'ffmpeg') -> Tuple[Optional[str], Optional[int]]:
        exe = executable[:2] + 'probe' if executable in ('ffmpeg', 'avconv') else executable
        args = [exe, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a:0', source]
        output = subprocess.check_output(args, timeout=20)
        codec = bitrate = None

        if output:
            data = json.loads(output)
            streamdata = data['streams'][0]

            codec = streamdata.get('codec_name')
            bitrate = int(streamdata.get('bit_rate', 0))
            bitrate = max(round(bitrate / 1000), 512)

        return codec, bitrate

    @staticmethod
    def _probe_codec_fallback(source, executable: str = 'ffmpeg') -> Tuple[Optional[str], Optional[int]]:
        args = [executable, '-hide_banner', '-i', source]
        proc = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate(timeout=20)
        output = out.decode('utf8')
        codec = bitrate = None

        codec_match = re.search(r"Stream #0.*?Audio: (\w+)", output)
        if codec_match:
            codec = codec_match.group(1)

        br_match = re.search(r"(\d+) [kK]b/s", output)
        if br_match:
            bitrate = max(int(br_match.group(1)), 512)

        return codec, bitrate

    def read(self) -> bytes:
        return next(self._packet_iter, b'')

    def is_opus(self) -> bool:
        return True


class PCMVolumeTransformer(AudioSource, Generic[AT]):
    """Transforms a previous :class:`AudioSource` to have volume controls.

    This does not work on audio sources that have :meth:`AudioSource.is_opus`
    set to ``True``.

    Parameters
    ------------
    original: :class:`AudioSource`
        The original AudioSource to transform.
    volume: :class:`float`
        The initial volume to set it to.
        See :attr:`volume` for more info.

    Raises
    -------
    TypeError
        Not an audio source.
    ClientException
        The audio source is opus encoded.
    """

    def __init__(self, original: AT, volume: float = 1.0):
        if not isinstance(original, AudioSource):
            raise TypeError(f'expected AudioSource not {original.__class__.__name__}.')

        if original.is_opus():
            raise ClientException('AudioSource must not be Opus encoded.')

        self.original: AT = original
        self.volume = volume

    @property
    def volume(self) -> float:
        """Retrieves or sets the volume as a floating point percentage (e.g. ``1.0`` for 100%)."""
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(value, 0.0)

    def cleanup(self) -> None:
        self.original.cleanup()

    def read(self) -> bytes:
        ret = self.original.read()
        return audioop.mul(ret, 2, min(self._volume, 2.0))


class AudioPlayer(threading.Thread):
    DELAY: float = OpusEncoder.FRAME_LENGTH / 1000.0

    def __init__(
        self,
        source: AudioSource,
        client: VoiceClient,
        *,
        after: Optional[Callable[[Optional[Exception]], Any]] = None,
    ) -> None:
        threading.Thread.__init__(self)
        self.daemon: bool = True
        self.source: AudioSource = source
        self.client: VoiceClient = client
        self.after: Optional[Callable[[Optional[Exception]], Any]] = after

        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()  # we are not paused
        self._current_error: Optional[Exception] = None
        self._connected: threading.Event = client._connected
        self._lock: threading.Lock = threading.Lock()

        if after is not None and not callable(after):
            raise TypeError('Expected a callable for the "after" parameter.')

    def _do_run(self) -> None:
        self.loops = 0
        self._start = time.perf_counter()

        # getattr lookup speed ups
        play_audio = self.client.send_audio_packet
        self._speak(SpeakingState.voice)

        while not self._end.is_set():
            # are we paused?
            if not self._resumed.is_set():
                # wait until we aren't
                self._resumed.wait()
                continue

            # are we disconnected from voice?
            if not self._connected.is_set():
                # wait until we are connected
                self._connected.wait()
                # reset our internal data
                self.loops = 0
                self._start = time.perf_counter()

            self.loops += 1
            data = self.source.read()

            if not data:
                self.stop()
                break

            play_audio(data, encode=not self.source.is_opus())
            next_time = self._start + self.DELAY * self.loops
            delay = max(0, self.DELAY + (next_time - time.perf_counter()))
            time.sleep(delay)

    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
            self.stop()
        finally:
            self._call_after()
            self.source.cleanup()

    def _call_after(self) -> None:
        error = self._current_error

        if self.after is not None:
            try:
                self.after(error)
            except Exception as exc:
                exc.__context__ = error
                _log.exception('Calling the after function failed.', exc_info=exc)
        elif error:
            _log.exception('Exception in voice thread %s', self.name, exc_info=error)

    def stop(self) -> None:
        self._end.set()
        self._resumed.set()
        self._speak(SpeakingState.none)

    def pause(self, *, update_speaking: bool = True) -> None:
        self._resumed.clear()
        if update_speaking:
            self._speak(SpeakingState.none)

    def resume(self, *, update_speaking: bool = True) -> None:
        self.loops: int = 0
        self._start: float = time.perf_counter()
        self._resumed.set()
        if update_speaking:
            self._speak(SpeakingState.voice)

    def is_playing(self) -> bool:
        return self._resumed.is_set() and not self._end.is_set()

    def is_paused(self) -> bool:
        return not self._end.is_set() and not self._resumed.is_set()

    def _set_source(self, source: AudioSource) -> None:
        with self._lock:
            self.pause(update_speaking=False)
            self.source = source
            self.resume(update_speaking=False)

    def _speak(self, speaking: SpeakingState) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self.client.ws.speak(speaking), self.client.client.loop)
        except Exception:
            _log.exception("Speaking call in player failed")
