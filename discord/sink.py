import struct
import wave
import os
from typing import TYPE_CHECKING, Optional

from .opus import _OpusStruct

if TYPE_CHECKING:
    from .member import Member


__all__ = (
    "AudioSink",
    "AudioFileSink",
)


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
        pass


class AudioFileSink(AudioSink):
    __slots__ = ("output_dir", "output_files", "_done")

    def __init__(self, output_dir="/"):
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid output directory")
        self.output_dir = output_dir
        self.output_files = {}
        self._done = False

    def on_audio(self, frame):
        if frame.ssrc not in self.output_files:
            filename = f"audio-{frame.user.name}#{frame.user.discriminator}.pcm" \
                if frame.user is not None else f"{frame.ssrc}.pcm"
            self.output_files[frame.ssrc] = open(os.path.join(self.output_dir, filename), "wb")
        self.output_files[frame.ssrc].write(frame.audio)

    def cleanup(self):
        for file in self.output_files.values():
            file.close()
        self._done = True

    def convert_files(self):
        if not self._done:
            self.cleanup()
        for ssrc, file in self.output_files.items():
            filepath = file.name
            with open(filepath, "rb") as f:
                audio = f.read()

                with wave.open(".".join(filepath.split(".")[:-1]) + ".wav", "wb") as wavf:
                    wavf.setnchannels(_OpusStruct.CHANNELS)
                    wavf.setsampwidth(_OpusStruct.SAMPLE_SIZE // _OpusStruct.CHANNELS)
                    wavf.setframerate(_OpusStruct.SAMPLING_RATE)
                    wavf.writeframes(audio)

            os.remove(filepath)
        self.output_files = {}

    @property
    def done(self):
        return self._done
