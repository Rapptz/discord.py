import struct
import wave
import os
import threading
import logging
import asyncio
from typing import TYPE_CHECKING, Optional, Callable, Any

from .opus import Decoder as OpusDecoder

if TYPE_CHECKING:
    from .member import Member
    from .voice_client import VoiceClient


__all__ = (
    "AudioFrame",
    "AudioSink",
    "AudioFileSink",
    "WaveAudioFileSink",
)


_log = logging.getLogger(__name__)


class RawAudioData:
    """Takes in raw data from discord and extracts its characteristics."""
    __slots__ = ("version_flag", "payload_type", "sequence", "timestamp", "ssrc", "audio")

    def __init__(self, data: bytes, decrypt_method):
        header = data[:12]
        data = data[12:]

        self.version_flag, self.payload_type, self.sequence, self.timestamp, self.ssrc = \
            struct.unpack(">BBHII", header)
        if 200 <= self.payload_type <= 204:
            # RTCP received.
            # RTCP provides information about the connection
            # as opposed to actual audio data, so it's not
            # important to implement at the moment.
            self.audio = None
            return
        self.audio = decrypt_method(header, data)


class AudioFrame:
    """Represents audio that has been fully decoded."""
    __slots__ = ("sequence", "timestamp", "ssrc", "audio", "user")

    def __init__(self, frame: bytes, raw_audio: RawAudioData, user: Optional['Member']):
        self.sequence = raw_audio.sequence
        self.timestamp = raw_audio.timestamp
        self.ssrc = raw_audio.ssrc
        self.audio = frame
        self.user = user


class AudioSink:
    def on_audio(self, frame):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()


class AudioFileSink(AudioSink):
    __slots__ = ("output_dir", "output_files", "done", "_timestamps", "_frame_buffer")

    FRAME_BUFFER_LIMIT = 10

    def __init__(self, output_dir="/"):
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid output directory")
        self.output_dir = output_dir
        self.output_files = {}
        self.done = False

        self._timestamps = {}
        # This gives leeway for frames sent out of order
        self._frame_buffer = []

    def on_audio(self, frame):
        self._frame_buffer.append(frame)
        if len(self._frame_buffer) >= self.FRAME_BUFFER_LIMIT:
            self._write_buffer()

    def _write_buffer(self):
        self._frame_buffer = sorted(self._frame_buffer, key=lambda frame: frame.timestamp)
        for frame in self._frame_buffer:
            self._write_frame(frame)
        self._frame_buffer = []

    def _write_frame(self, frame):
        if frame.ssrc not in self.output_files:
            filename = f"audio-{frame.user.name}#{frame.user.discriminator}.pcm" \
                if frame.user is not None else f"{frame.ssrc}.pcm"
            self.output_files[frame.ssrc] = open(os.path.join(self.output_dir, filename), "wb")
        else:
            # write silence
            silence = frame.timestamp - self._timestamps[frame.ssrc] - OpusDecoder.FRAME_SIZE
            if silence > 0: self.output_files[frame.ssrc].write(b"\x00"*silence*OpusDecoder.CHANNELS)
        self.output_files[frame.ssrc].write(frame.audio)
        self._timestamps[frame.ssrc] = frame.timestamp

    def cleanup(self):
        for file in self.output_files.values():
            file.close()
        self.done = True

    def convert_files(self):
        raise NotImplementedError()


class WaveAudioFileSink(AudioFileSink):
    def convert_files(self):
        if not self.done:
            self.cleanup()
        for ssrc, file in self.output_files.items():
            filepath = file.name
            with open(filepath, "rb") as f:
                audio = f.read()

                self.output_files[ssrc] = ".".join(filepath.split(".")[:-1]) + ".wav"
                with wave.open(self.output_files[ssrc], "wb") as wavf:
                    wavf.setnchannels(OpusDecoder.CHANNELS)
                    wavf.setsampwidth(OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS)
                    wavf.setframerate(OpusDecoder.SAMPLING_RATE)
                    wavf.writeframes(audio)

            os.remove(filepath)
        self.output_files = {}


class AudioReceiver(threading.Thread):
    def __init__(
        self,
        sink: AudioSink,
        client: 'VoiceClient',
        *,
        after: Optional[Callable[[AudioSink, Optional[Exception]], Any]] = None,
    ) -> None:
        threading.Thread.__init__(self)
        self.sink = sink
        self.client = client
        self.after: Optional[Callable[[AudioSink, Optional[Exception]], Any]] = after

        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()  # we are not paused
        self._current_error: Optional[Exception] = None
        self._connected: threading.Event = client._connected
        self._lock: threading.Lock = threading.Lock()

    def _do_run(self) -> None:
        _log.info("Began polling for audio packets from Channel ID %d (Guild ID %d).",
                  self.client.channel.id, self.client.guild.id)

        while not self._end.is_set():

            # are we disconnected from voice?
            if not self._connected.is_set():
                # wait until we are connected
                self._connected.wait()

            # dump audio while paused cuz discord sends you audio even
            # while you're deafened
            audio = self.client.recv_audio_packet(dump=not self._resumed.is_set())
            if audio is None: continue
            self.sink.on_audio(audio)

        _log.info("No longer polling for audio packets from Channel ID %d (Guild ID %d).",
                  self.client.channel.id, self.client.guild.id)

    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
            self.stop()
        finally:
            self._call_after()
            self.client.cleanup()

    def _call_after(self) -> None:
        error = self._current_error

        if self.after is not None:
            try:
                self.after(self.sink, error)
            except Exception as exc:
                exc.__context__ = error
                _log.exception('Calling the after function failed.', exc_info=exc)
        elif error:
            _log.exception('Exception in voice thread %s', self.name, exc_info=error)

    def stop(self) -> None:
        self._end.set()
        self._resumed.set()

    def pause(self) -> None:
        self._resumed.clear()

    def resume(self) -> None:
        self._resumed.set()

    def is_listening(self) -> bool:
        return self._resumed.is_set() and not self._end.is_set()

    def is_paused(self) -> bool:
        return not self._end.is_set() and not self._resumed.is_set()
