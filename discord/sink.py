import struct
import wave
import os
import threading
import logging
import subprocess
from collections import namedtuple
from typing import TYPE_CHECKING, Optional, Callable, Any

from .opus import Decoder as OpusDecoder
from .errors import ClientException
from .enums import RTCPMessageType

if TYPE_CHECKING:
    from .member import Member
    from .voice_client import VoiceClient


__all__ = (
    "AudioFrame",
    "AudioSink",
    "AudioFileSink",
    "WaveAudioFileSink",
    "MP3AudioFileSink"
)


_log = logging.getLogger(__name__)


RTCPReceiverReportBlock = namedtuple("RTCPReceiverReportBlock", ("ssrc", "f", "c", "ehsn", "j", "lsr", "dlsr"))
RTCPReceiverReportBlock.__doc__ = """Receiver report block from :class:`RTCPSenderReportPacket` 
or :class:`RTCPReceiverReportPacket`

Conveys statistics on the reception of RTP packets from a single synchronization source. 

Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

ssrc: :class:`int`
    The SSRC identifier of the source to which the information in this 
    reception report block pertains.
f: :class:`int`
    The fraction of RTP data packets from source SSRC lost since the 
    previous SR or RR packet was sent.
c: :class:`int`
    The total number of RTP data packets from source SSRC that have 
    been lost since the beginning of reception.
ehsn: :class:`int`
    The low 16 bits contain the highest sequence number received in an RTP 
    data packet from source SSRC, and the most significant 16 bits extend 
    that sequence number with the corresponding count of sequence number cycles.
j: :class:`int`
    An estimate of the statistical variance of the RTP data packet interarrival 
    time, measured in timestamp units and expressed as an unsigned integer.
lsr: :class:`int`
    The middle 32 bits out of 64 in the NTP timestamp received as part of the most 
    recent RTCP sender report (SR) packet from source SSRC. If no SR has been 
    received yet, the field is set to zero.
dlsr: :class:`int`
    The delay, expressed in units of 1/65536 seconds, between receiving the last 
    SR packet from source SSRC and sending this reception report block. If no 
    SR packet has been received yet from SSRC, the DLSR field is set to zero.
"""

RTCPSourceDescriptionChunk = namedtuple("RTCPSourceDescriptionChunk", ("ssrc", "items"))
RTCPSourceDescriptionChunk.__doc__ = """A chunk of a :class:`RTCPSourceDescription` object.

Contains items that describe a source.

ssrc: :class:`int`
    The source which is being described.
items: Sequence[:class:`RTCPSourceDescriptionItem`]
    A sequence of items which have a description.
"""

RTCPSourceDescriptionItem = namedtuple("RTCPSourceDescriptionItem", ("cname", "description"))
RTCPSourceDescriptionItem.__doc__ = """An item of a :class:`RTCPSourceDescriptionChunk` object

cname: :class:`int`
    Type of description.
description: :class:`bytes`
    Description pertaining to the source of the chunk containing this item.
"""


class RTCPPacket:
    """Base class for all RTCP packet classes. Contains header attributes.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

    v: :class:`int`
        Identifies the version of RTP, which is the same in RTCP packets
        as in RTP data packets.
    p: :class:`bool`
        If the padding bit is set, this RTCP packet contains some additional
        padding octets at the end which are not part of the control information.
        The last octet of the padding is a count of how many padding octets
        should be ignored.
    rc: :class:`int`
        Indicates the number of "items" within a packet. For sender and receiver
        packets it indicates the number of Receiver Report Blocks.
    pt: :class:`RTCPMessageType`
        Indicates the RTCP packet type.
    l: :class:`int`
        The length of this RTCP packet in 32-bit words minus one, including
        the header and any padding.
    """
    __slots__ = ("v", "p", "rc", "pt", "l")

    def __init__(self, version_flag, rtcp_type, length):
        self.v = version_flag >> 6
        self.p = bool((version_flag >> 5) & 0b1)
        self.rc = version_flag & 0b11111
        self.pt = rtcp_type
        self.l = length

    def _parse_report_and_extension(self, data):
        # Tested this and it appears that discord does not send
        # the specified amount of report blocks
        # fmt = ">IB3s4I"
        # buf_size = struct.calcsize(fmt)
        # report_blocks = [struct.unpack_from(fmt, buffer=data, offset=buf_size * i)
        #                  for i in range(self.rc)]
        # self.report_blocks = list(map(lambda args: RTCPReceiverReportBlock(
        #     *args[:2], int.from_bytes(args[2], 'big'), *args[3:]
        # ), report_blocks))
        self.report_blocks = []

        self.extension = data  # data[len(self.report_blocks) * buf_size:]


class RTCPSenderReportPacket(RTCPPacket):
    """RTCP Sender Report packet which provides quality feedback

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    ssrc: :class:`int`
        The synchronization source identifier for the originator of this SR packet.
    nts: :class:`int`
        NTP timestamp. Indicates the wallclock time when this report was sent
        so that it may be used in combination with timestamps returned in
        reception reports from other receivers to measure round-trip
        propagation to those receivers.
    rts: :class:`int`
        RTP timestamp. Corresponds to the same time as the NTP timestamp (above),
        but in the same units and with the same random offset as the RTP
        timestamps in data packets.
    spc: :class:`int`
        The total number of RTP data packets transmitted by the sender since
        starting transmission up until the time this SR packet was generated.
        The count is reset if the sender changes its SSRC identifier.
    soc:
        The total number of payload octets (i.e., not including header or padding)
        transmitted in RTP data packets by the sender since starting transmission
        up until the time this SR packet was generated. The count is reset if
        the sender changes its SSRC identifier.
    report_blocks: Sequence[:class:`RTCPReceiverReport`]
        Sequence of :class:`RTCPReceiverReport` objects that tell statistics.
        Receivers do not carry over statistics when a source changes its SSRC
        identifier due to a collision.
    extension: :class:`bytes`
        Profile-specific extension that may or may not contain a value.
    """
    __slots__ = RTCPPacket.__slots__ + (
        "ssrc", "nts", "rts", "spc", "soc", "report_blocks",
        "extension"
    )

    def __init__(self, version_flag, rtcp_type, remaining_header, data):
        super().__init__(version_flag, rtcp_type, remaining_header)

        fmt = ">IQ3I"
        buf_size = struct.calcsize(fmt)
        self.ssrc, self.nts, self.rts, self.spc, self.soc = \
            struct.unpack(fmt, data[:buf_size])

        self._parse_report_and_extension(data[buf_size:])


class RTCPReceiverReportPacket(RTCPPacket):
    """RTCP Receiver Report packet which provides quality feedback.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/20.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    ssrc: :class:`int`
        The synchronization source identifier for the originator of this SR packet.
    report_blocks: Sequence[:class:`RTCPReceiverReport`]
        Sequence of :class:`RTCPReceiverReport` objects that tell statistics.
        Receivers do not carry over statistics when a source changes its SSRC
        identifier due to a collision.
    extension: :class:`bytes`
        Profile-specific extension that may or may not contain a value.
    """
    __slots__ = RTCPPacket.__slots__ + (
        "ssrc", "report_blocks", "extension"
    )

    def __init__(self, version_flag, rtcp_type, length, data):
        super().__init__(version_flag, rtcp_type, length)

        fmt = ">I"
        buf_size = struct.calcsize(fmt)
        self.ssrc = struct.unpack(fmt, data[:buf_size])[0]
        self._parse_report_and_extension(data[buf_size:])


class RTCPSourceDescriptionPacket(RTCPPacket):
    """Source Description packet which describes sources.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/23.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    chunks: Sequence[:class:`RTCPSourceDescriptionChunk`]
        Sequence of chunks that contain items.
    """
    __slots__ = RTCPPacket.__slots__ + ("chunks",)

    def __init__(self, version_flag, rtcp_type, length, data):
        super().__init__(version_flag, rtcp_type, length)

        self.chunks = []
        for _ in range(self.rc):
            chunk, offset = self._parse_chunk(data)
            data = data[offset:]
            self.chunks.append(chunk)

    def _parse_chunk(self, data):
        chunk = RTCPSourceDescriptionChunk(struct.unpack(">I", data), [])
        i = 4
        while True:
            cname = struct.unpack_from(">B", buffer=data, offset=i)[0]
            i += 1
            if cname == 0:
                break

            length = struct.unpack_from(">B", buffer=data, offset=i)[0]
            i += 1
            description = ""
            if length > 0:
                description = struct.unpack_from(f">{length}s", buffer=data, offset=i)
                i += length

            chunk.items.append(RTCPSourceDescriptionItem(cname, description))

        # Chunks are padded by 32-bit boundaries
        if i % 4 != 0:
            i += 4 - (i % 4)
        return chunk, i


class RTCPGoodbyePacket(RTCPPacket):
    """A Goodbye packet indicating a number of SSRCs that are disconnected
    and possibly providing a reason for the disconnect

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/32.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    ssrc_byes: Sequence[:class:`int`]
        List of SSRCs that are disconnecting.
    reason: :class:`bytes`
        Reason for disconnect.
    """
    __slots__ = RTCPPacket.__slots__ + ("ssrc_byes", "reason")

    def __init__(self, version_flag, rtcp_type, length, data):
        super().__init__(version_flag, rtcp_type, length)

        if self.rc == 0:
            buf_size = 0
            self.ssrc_byes = []
        else:
            buf_size = self.rc*struct.calcsize("I")
            self.ssrc_byes = struct.unpack(f">{self.rc}I", data[:buf_size])
        reason_length = struct.unpack(">B", data[buf_size:buf_size+1])
        self.reason = b"" if reason_length == 0 else struct.unpack(f">{reason_length}s", data[buf_size+1:])


class RTCPApplicationDefinedPacket(RTCPPacket):
    """An application-defined packet  intended for experimental use.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/33.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    rc: :class:`int`
        rc in this packet represents a subtype
    ssrc: :class:`int`
        The synchronization source identifier for the originator of this SR packet.
    name: :class:`str`
        A name chosen by the person defining the set of APP packets to be unique
        with respect to other APP packets this application might receive.
    app_data: :class:`bytes`
        Application-dependent data may or may not appear in an APP packet.
    """
    __slots__ = RTCPPacket.__slots__ + ("ssrc", "name", "app_data")

    def __init__(self, version_flag, rtcp_type, length, data):
        super().__init__(version_flag, rtcp_type, length)

        fmt = ">I4s"
        buf_size = struct.calcsize(fmt)
        self.ssrc, self.name = struct.unpack(fmt, data[:buf_size])
        self.name = self.name.decode("ascii")
        self.app_data = data[buf_size:]


class RawAudioData:
    """Takes in a raw audio frame from discord and extracts its characteristics.

    version: :class:`int`
        RTP version
    extended :class:`bool`
        Whether a header extension is present.
    marker: :class:`int`
        The interpretation of the marker is defined by a profile.
    payload_type: :class:`int`
        Type of payload, audio in this case
    sequence: :class:`int`
        The sequence number increments by one for each RTP data packet sent.
    timestamp: :class:`int`
        The timestamp reflects the sampling instant of the first octet in the audio data
    ssrc: :class:`int`
        Identifies the synchronization source.
    csrc_list: Sequence[:class:`int`]
        The CSRC list identifies the contributing sources for the payload
        contained in this packet.
    extension_id: :class:`int`
        Profile-specific identifier
    extension_header: :class:`int`
        The header of the extension
    extension_data: Sequence[:class:`int`]
        Extension header data
    """
    __slots__ = (
        "version", "extended", "marker", "payload_type", "sequence", "timestamp", "ssrc",
        "csrc_list", "extension_id", "extension_header", "extension_data", "audio"
    )

    def __init__(self, data: bytes, decrypt_method):
        fmt = ">BBHII"
        version_flag, payload_flag, self.sequence, self.timestamp, self.ssrc = \
            struct.unpack_from(fmt, buffer=data)
        i = struct.calcsize(fmt)
        self.version = version_flag >> 6
        padding = (version_flag >> 5) & 0b1
        self.extended = bool((version_flag >> 4) & 0b1)
        self.marker = payload_flag >> 7
        self.payload_type = payload_flag & 0b1111111
        csrc_count = version_flag & 0b1111
        self.csrc_list = []
        if csrc_count > 0:
            fmt = f">{csrc_count}I"
            self.csrc_list = struct.unpack_from(fmt, buffer=data, offset=i)
            i += struct.calcsize(fmt)
        # While testing, I received a packet marked as extended that did not
        # contain an extension, so I've commented this out.
        # if self.extended:
        #     fmt = ">HHI"
        #     self.extension_id, num, self.extension_header = \
        #         struct.unpack_from(fmt, buffer=data, offset=i)
        #     i += struct.calcsize(fmt)
        #     fmt = f">{num}I"
        #     self.extension_data = struct.unpack_from(fmt, buffer=data, offset=i)
        #     i += struct.calcsize(fmt)
        if padding:
            data = data[:-data[-1]]

        self.audio = decrypt_method(data[:i], data[i:])


class AudioPacket:
    RTCP_MAP = {
        RTCPMessageType.sender_report: RTCPSenderReportPacket,
        RTCPMessageType.receiver_report: RTCPReceiverReportPacket,
        RTCPMessageType.source_description: RTCPSourceDescriptionPacket,
        RTCPMessageType.goodbye: RTCPGoodbyePacket,
        RTCPMessageType.application_defined: RTCPApplicationDefinedPacket,
    }

    def __new__(cls, data: bytes, decrypt_method):
        fmt = ">BBH"
        buf_size = struct.calcsize(fmt)
        version_flag, payload_type, length = struct.unpack_from(fmt, buffer=data)
        if 200 <= payload_type <= 204:
            rtcp_type = RTCPMessageType(payload_type)
            return cls.RTCP_MAP[rtcp_type](version_flag, rtcp_type, length, data[buf_size:])
        return RawAudioData(data, decrypt_method)


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

    def on_rtcp(self, packet):
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

    def on_rtcp(self, packet):
        pass

    def _write_buffer(self):
        self._frame_buffer = sorted(self._frame_buffer, key=lambda frame: frame.sequence)
        for frame in self._frame_buffer:
            self._write_frame(frame)
        self._frame_buffer = []

    def _write_frame(self, frame):
        if frame.ssrc not in self.output_files:
            filename = f"audio-{frame.user.name}#{frame.user.discriminator}-{frame.ssrc}.pcm" \
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
        if not self.done:
            self.cleanup()
        for ssrc, file in self.output_files.items():
            filepath = file.name
            with open(filepath, "rb") as f:
                self.output_files[ssrc] = self.convert_file(f)

            os.remove(filepath)
        self.output_files = {}

    def convert_file(self, file):
        raise NotImplementedError()


class WaveAudioFileSink(AudioFileSink):
    CHUNK_WRITE_SIZE = 64

    def convert_file(self, file):
        wavfilepath = ".".join(file.name.split(".")[:-1]) + ".wav"
        with wave.open(wavfilepath, "wb") as wavf:
            wavf.setnchannels(OpusDecoder.CHANNELS)
            wavf.setsampwidth(OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS)
            wavf.setframerate(OpusDecoder.SAMPLING_RATE)
            while frames := file.read(OpusDecoder.FRAME_SIZE*self.CHUNK_WRITE_SIZE):
                wavf.writeframes(frames)
        return wavfilepath


class MP3AudioFileSink(AudioFileSink):
    def convert_file(self, file):
        mp3_file = ".".join(file.name.split(".")[:-1]) + ".mp3"
        args = ['ffmpeg', '-f', 's16le', '-ar', str(OpusDecoder.SAMPLING_RATE),
                '-ac', str(OpusDecoder.CHANNELS), '-i', file.name, mp3_file]
        # process will get stuck asking whether or not to overwrite, if file already exists.
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        try:
            process = subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW)
        except FileNotFoundError:
            raise ClientException('ffmpeg was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
        process.wait()


class AudioReceiver(threading.Thread):
    def __init__(
        self,
        sink: AudioSink,
        client: 'VoiceClient',
        *,
        after: Optional[Callable[[AudioSink, Optional[Exception]], Any]] = None,
    ) -> None:
        threading.Thread.__init__(self)
        self.daemon = False
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
            packet = self.client.recv_audio_packet(dump=not self._resumed.is_set())
            if packet is None: continue
            if not isinstance(packet, AudioFrame):
                self.sink.on_rtcp(packet)
                continue
            if packet.audio is None: continue
            self.sink.on_audio(packet)

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
