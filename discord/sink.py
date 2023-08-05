import asyncio
import logging
import multiprocessing
import os
import queue
import struct
import subprocess
import threading
import wave
from collections import defaultdict
from concurrent.futures import Future
from dataclasses import dataclass
from time import monotonic
from typing import TYPE_CHECKING, Any, Awaitable, BinaryIO, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .enums import RTCPMessageType
from .errors import ClientException
from .object import Object
from .opus import Decoder as OpusDecoder
from .player import CREATE_NO_WINDOW

SILENT_FRAME = b"\xf8\xff\xfe"
has_nacl: bool

try:
    import nacl.secret  # type: ignore
    import nacl.utils  # type: ignore

    has_nacl = True
except ImportError:
    has_nacl = False

if TYPE_CHECKING:
    from .member import Member
    from .state import ConnectionState
    from .voice_client import VoiceClient


__all__ = (
    "AudioFrame",
    "AudioSink",
    "AudioHandlingSink",
    "AudioFileSink",
    "AudioFile",
    "WaveAudioFile",
    "MP3AudioFile",
    "RTCPPacket",
    "RTCPSenderReportPacket",
    "RTCPReceiverReportPacket",
    "RTCPSourceDescriptionPacket",
    "RTCPGoodbyePacket",
    "RTCPApplicationDefinedPacket",
    "RTCPReceiverReportBlock",
    "RTCPSourceDescriptionChunk",
    "RTCPSourceDescriptionItem",
)


_log = logging.getLogger(__name__)
_mp_ctx = multiprocessing.get_context("spawn")


@dataclass
class RTCPReceiverReportBlock:
    """Receiver report block from :class:`RTCPSenderReportPacket`
    or :class:`RTCPReceiverReportPacket`

    Conveys statistics on the reception of RTP packets from a single synchronization source.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

    Attributes
    ----------
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

    __slots__ = (
        "ssrc",
        "f",
        "c",
        "ehsn",
        "j",
        "lsr",
        "dlsr",
    )

    ssrc: int
    f: int
    c: int
    ehsn: int
    j: int
    lsr: int
    dlsr: int


@dataclass
class RTCPSourceDescriptionItem:
    """An item of a :class:`RTCPSourceDescriptionChunk` object

    Attributes
    ----------
    cname: :class:`int`
        Type of description.
    description: :class:`bytes`
        Description pertaining to the source of the chunk containing this item.
    """

    __slots__ = (
        "cname",
        "description",
    )

    cname: int
    description: bytes


@dataclass
class RTCPSourceDescriptionChunk:
    """A chunk of a :class:`RTCPSourceDescriptionPacket` object.

    Contains items that describe a source.

    Attributes
    ----------
    ssrc: :class:`int`
        The source which is being described.
    items: Sequence[:class:`RTCPSourceDescriptionItem`]
        A sequence of items which have a description.
    """

    __slots__ = (
        "ssrc",
        "items",
    )

    ssrc: int
    items: Sequence[RTCPSourceDescriptionItem]


class RTCPPacket:
    """Base class for all RTCP packet classes. Contains header attributes.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

    Attributes
    ----------
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

    __slots__ = (
        "v",
        "p",
        "rc",
        "pt",
        "l",
    )

    if TYPE_CHECKING:
        v: int
        p: bool
        rc: int
        pt: RTCPMessageType
        l: int

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int):
        self.v = version_flag >> 6
        self.p = bool((version_flag >> 5) & 0b1)
        self.rc = version_flag & 0b11111
        self.pt = rtcp_type
        self.l = length


class RTCPSenderReportPacket(RTCPPacket):
    """RTCP Sender Report packet which provides quality feedback

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/19.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    Attributes
    ----------
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
    soc: :class:`int`
        The total number of payload octets (i.e., not including header or padding)
        transmitted in RTP data packets by the sender since starting transmission
        up until the time this SR packet was generated. The count is reset if
        the sender changes its SSRC identifier.
    report_blocks: Sequence[:class:`RTCPReceiverReportPacket`]
        Sequence of :class:`RTCPReceiverReportPacket` objects that tell statistics.
        Receivers do not carry over statistics when a source changes its SSRC
        identifier due to a collision.
    extension: :class:`bytes`
        Profile-specific extension that may or may not contain a value.
    """

    __slots__ = (
        "ssrc",
        "nts",
        "rts",
        "spc",
        "soc",
        "report_blocks",
        "extension",
    )

    if TYPE_CHECKING:
        ssrc: int
        nts: int
        rts: int
        spc: int
        soc: int
        report_blocks: List
        extension: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        self.ssrc, self.nts, self.rts, self.spc, self.soc = struct.unpack_from("!IQ3I", buffer=data)
        self.report_blocks = []
        self.extension = data[24:]


class RTCPReceiverReportPacket(RTCPPacket):
    """RTCP Receiver Report packet which provides quality feedback.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/20.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    Attributes
    ----------
    ssrc: :class:`int`
        The synchronization source identifier for the originator of this SR packet.
    report_blocks: Sequence[:class:`RTCPReceiverReportPacket`]
        Sequence of :class:`RTCPReceiverReportPacket` objects that tell statistics.
        Receivers do not carry over statistics when a source changes its SSRC
        identifier due to a collision.
    extension: :class:`bytes`
        Profile-specific extension that may or may not contain a value.
    """

    __slots__ = (
        "ssrc",
        "report_blocks",
        "extension",
    )

    if TYPE_CHECKING:
        ssrc: int
        report_blocks: List
        extension: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        self.ssrc = struct.unpack_from("!I", buffer=data)[0]
        self.report_blocks = []
        self.extension = data[4:]


class RTCPSourceDescriptionPacket(RTCPPacket):
    """Source Description packet which describes sources.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/23.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    Attributes
    ----------
    chunks: Sequence[:class:`RTCPSourceDescriptionChunk`]
        Sequence of chunks that contain items.
    """

    __slots__ = ("chunks",)

    if TYPE_CHECKING:
        chunks: List[RTCPSourceDescriptionChunk]

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        self.chunks = []
        for _ in range(self.rc):
            chunk, offset = self._parse_chunk(data)
            data = data[offset:]
            self.chunks.append(chunk)

    def _parse_chunk(self, data: bytes) -> Tuple[RTCPSourceDescriptionChunk, int]:
        ssrc = struct.unpack("!I", data)[0]
        items = []
        i = 4
        while True:
            cname = struct.unpack_from("!B", buffer=data, offset=i)[0]
            i += 1
            if cname == 0:
                break

            length = struct.unpack_from("!B", buffer=data, offset=i)[0]
            i += 1
            description = struct.unpack_from(f"!{length}s", buffer=data, offset=i)[0]
            i += length

            items.append(RTCPSourceDescriptionItem(cname, description))

        # Chunks are padded by 32-bit boundaries
        if i % 4 != 0:
            i += 4 - (i % 4)
        return RTCPSourceDescriptionChunk(ssrc, items), i


class RTCPGoodbyePacket(RTCPPacket):
    """A Goodbye packet indicating a number of SSRCs that are disconnected
    and possibly providing a reason for the disconnect

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/32.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    Attributes
    ----------
    ssrc_byes: Tuple[:class:`int`]
        List of SSRCs that are disconnecting. Not guaranteed to contain any values.
    reason: :class:`bytes`
        Reason for disconnect.
    """

    __slots__ = (
        "ssrc_byes",
        "reason",
    )

    if TYPE_CHECKING:
        ssrc_byes: Union[Tuple[int], Tuple]
        reason: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        buf_size = self.rc * 4
        self.ssrc_byes = struct.unpack_from(f"!{self.rc}I", buffer=data)
        reason_length = struct.unpack_from("!B", buffer=data, offset=buf_size)[0]
        self.reason = (
            b"" if reason_length == 0 else struct.unpack_from(f"!{reason_length}s", buffer=data, offset=buf_size + 1)[0]
        )


class RTCPApplicationDefinedPacket(RTCPPacket):
    """An application-defined packet  intended for experimental use.

    Read in detail here: https://www.freesoft.org/CIE/RFC/1889/33.htm

    Extends :class:`RTCPPacket` and inherits its attributes.

    Attributes
    ----------
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

    __slots__ = (
        "ssrc",
        "name",
        "app_data",
    )

    if TYPE_CHECKING:
        ssrc: int
        name: str
        app_data: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        self.ssrc, name = struct.unpack_from("!I4s", buffer=data)
        self.name = name.decode("ascii")
        self.app_data = data[8:]


class RawAudioData:
    """Takes in a raw audio frame from discord and extracts its characteristics.

    Attributes
    ----------
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
    """

    __slots__ = (
        "version",
        "extended",
        "marker",
        "payload_type",
        "sequence",
        "timestamp",
        "ssrc",
        "csrc_list",
        "audio",
    )

    if TYPE_CHECKING:
        sequence: int
        timestamp: int
        ssrc: int
        version: int
        extended: bool
        marker: bool
        payload_type: int
        csrc_list: Tuple
        audio: bytes

    def __init__(self, data: bytes, decrypt_method: Callable[[bytes, bytes], bytes]):
        version_flag, payload_flag, self.sequence, self.timestamp, self.ssrc = struct.unpack_from(">BBHII", buffer=data)
        i = 12
        self.version = version_flag >> 6
        padding = (version_flag >> 5) & 0b1
        self.extended = bool((version_flag >> 4) & 0b1)
        self.marker = bool(payload_flag >> 7)
        self.payload_type = payload_flag & 0b1111111
        csrc_count = version_flag & 0b1111
        self.csrc_list = struct.unpack_from(f">{csrc_count}I", buffer=data, offset=i)
        i += csrc_count * 4

        # Extension parsing would go here, but discord's packets seem to have some problems
        # related to that, so no attempt will be made to parse extensions.

        if padding and data[-1] != 0:
            data = data[: -data[-1]]

        self.audio = decrypt_method(data[:i], data[i:])


_PACKET_TYPE = Union[
    RTCPSenderReportPacket,
    RTCPReceiverReportPacket,
    RTCPSourceDescriptionPacket,
    RTCPGoodbyePacket,
    RTCPApplicationDefinedPacket,
    RawAudioData,
]
_RTCP_MAP = {
    RTCPMessageType.sender_report: RTCPSenderReportPacket,
    RTCPMessageType.receiver_report: RTCPReceiverReportPacket,
    RTCPMessageType.source_description: RTCPSourceDescriptionPacket,
    RTCPMessageType.goodbye: RTCPGoodbyePacket,
    RTCPMessageType.application_defined: RTCPApplicationDefinedPacket,
}


def get_audio_packet(data: bytes, decrypt_method: Callable[[bytes, bytes], bytes]) -> _PACKET_TYPE:
    version_flag, payload_type, length = struct.unpack_from(">BBH", buffer=data)
    if 200 <= payload_type <= 204:
        rtcp_type = RTCPMessageType(payload_type)
        return _RTCP_MAP[rtcp_type](version_flag, rtcp_type, length, data[4:])
    return RawAudioData(data, decrypt_method)


class AudioFrame:
    """Represents audio that has been fully decoded.

    Attributes
    ----------
    sequence: :class:`int`
        The sequence of this frame in accordance with other frames
        that precede or follow it
    timestamp: :class:`int`
        Timestamp of the audio in accordance with its frame size
    ssrc: :class:`int`
        The source of the audio
    audio: :class:`bytes`
        Raw audio data
    user: Optional[Union[:class:`Member`, :class:`int`]]
        If the ssrc can be resolved to a user then this attribute
        contains the Member object for that user.
    """

    __slots__ = (
        "sequence",
        "timestamp",
        "ssrc",
        "audio",
        "user",
    )

    def __init__(self, frame: bytes, raw_audio: RawAudioData, user: Optional[Union['Member', 'Object']]):
        self.sequence: int = raw_audio.sequence
        self.timestamp: int = raw_audio.timestamp
        self.ssrc: int = raw_audio.ssrc
        self.audio: bytes = frame
        self.user: Optional[Union[Member, Object]] = user


class AudioSink:
    """An object that handles fully decoded and decrypted audio frames

    This class defines three major functions that an audio sink object must outline
    """

    def on_audio(self, frame: AudioFrame) -> Any:
        """This function receives :class:`AudioFrame` objects.

        Abstract method

        IMPORTANT: This method must not run stalling code for a substantial amount of time.

        Parameters
        ----------
        frame: :class:`AudioFrame`
            A frame of audio received from discord
        """
        raise NotImplementedError()

    def on_rtcp(self, packet: RTCPPacket) -> Any:
        """This function receives :class:`RTCPPacket` objects.

        Abstract method

        IMPORTANT: This method must not run stalling code for a substantial amount of time.

        Parameters
        ----------
        packet: Union[:class:`RTCPSenderReportPacket`, :class:`RTCPReceiverReportPacket`,
        :class:`RTCPSourceDescriptionPacket`, :class:`RTCPGoodbyePacket`, :class:`RTCPApplicationDefinedPacket`]
            A RTCP Packet received from discord.
        """
        raise NotImplementedError()

    def cleanup(self) -> Any:
        """This function is called when the bot is done receiving
        audio and before the after callback is called.

        Abstract method
        """
        raise NotImplementedError()


class AudioHandlingSink(AudioSink):
    """An object extending :class:`AudioSink` which implements methods for
    dealing with out-of-order packets and delays.
    """

    __slots__ = (
        "_last_sequence",
        "_buffer",
        "_buffer_wait",
        "_frame_queue",
        "_is_validating",
        "_buffer_till",
        "_lock",
        "_done_validating",
    )
    # how long to wait for missing a packet
    PACKET_WAIT_TIME = 2
    # how long to wait for a new packet before closing the _validation_loop thread
    VALIDATION_LOOP_TIMEOUT = 3
    # how long to wait for _validation_loop thread to start in _start_validation_loop
    VALIDATION_LOOP_START_TIMEOUT = 1

    def __init__(self):
        self._last_sequence: Dict[int, int] = defaultdict(lambda: -1)
        # _buffer is not shared across threads
        self._buffers: Dict[int, List[AudioFrame]] = defaultdict(list)
        self._frame_queue = queue.Queue()
        self._is_validating: threading.Event = threading.Event()
        self._buffer_till: Dict[int, Optional[float]] = defaultdict(lambda: None)
        self._lock: threading.Lock = threading.Lock()
        self._done_validating: threading.Event = threading.Event()

    def on_audio(self, frame: AudioFrame) -> None:
        """Puts frame in a queue and lets a processing loop thread deal with it."""
        # lock is also used by _empty_buffer
        self._lock.acquire()
        self._frame_queue.put_nowait(frame)
        self._start_validation_loop()
        self._lock.release()

    def _start_validation_loop(self) -> None:
        if not self._is_validating.is_set():
            threading.Thread(target=self._validation_loop).start()
            # prevent multiple threads spawning and make sure it spawns, otherwise giving a warning
            if not self._is_validating.wait(timeout=self.VALIDATION_LOOP_START_TIMEOUT):
                _log.warning("Timeout reached waiting for _validation_loop thread to start")

    def _validation_loop(self) -> None:
        self._is_validating.set()
        self._done_validating.clear()
        while True:
            try:
                frame = self._frame_queue.get(timeout=self.VALIDATION_LOOP_TIMEOUT)
            except queue.Empty:
                break

            self._validate_audio_frame(frame)
        self._is_validating.clear()
        if not self._empty_entire_buffer():
            self._done_validating.set()

    def _validate_audio_frame(self, frame: AudioFrame) -> None:
        # 1. If audio is a silent frame, empty buffer and reset last sequence
        # 2. If packet sequence is less than last_sequence, drop it
        # 3a. If packet has a valid sequence, send to on_valid_audio
        # If buffer is not empty, empty it into the queue to be validated
        # 3b. Else, put in a buffer
        # Buffer should be forcefully emptied (same as in 3a) when a missing frame is not received
        # after a specific amount of time

        last_sequence = self._last_sequence[frame.ssrc]
        if frame.sequence <= last_sequence:
            return

        if last_sequence == -1 or frame.sequence == last_sequence + 1:
            self._last_sequence[frame.ssrc] = frame.sequence
            self.on_valid_audio(frame)
            self._empty_buffer(frame.ssrc)
        else:
            self._append_to_buffer(frame)

    def _append_to_buffer(self, frame) -> None:
        self._buffers[frame.ssrc].append(frame)
        buffer_till = self._buffer_till[frame.ssrc]
        if buffer_till is None:
            self._buffer_till[frame.ssrc] = monotonic() + self.PACKET_WAIT_TIME
        elif monotonic() >= buffer_till:
            self._buffer_till[frame.ssrc] = None
            self._empty_buffer(frame.ssrc)

    def _empty_entire_buffer(self) -> bool:
        result = False
        for ssrc in self._buffers.keys():
            result = result or self._empty_buffer(ssrc)
        return result

    def _empty_buffer(self, ssrc) -> bool:
        buffer = self._buffers[ssrc]
        if len(buffer) == 0:
            return False

        sorted_buffer = sorted(buffer, key=lambda f: f.sequence)
        self._last_sequence[ssrc] = sorted_buffer[0].sequence - 1
        # prevent on_audio from putting frames in queue before these frames
        # and no conflicts on starting validation loop
        self._lock.acquire()
        for frame in sorted_buffer:
            self._frame_queue.put_nowait(frame)
        self._start_validation_loop()
        self._lock.release()
        self._buffers[ssrc] = []
        return True

    def on_valid_audio(self, frame: AudioFrame) -> Any:
        """When an audio packet is declared valid, it'll be passed to this function.

        Abstract method

        IMPORTANT: Stalling code will stall

        Parameters
        ----------
        frame: :class:`AudioFrame`
            A frame of audio received from discord that has been validated by
            :class:`AudioHandlingSink.on_audio`.
        """
        raise NotImplementedError()


class AudioFileSink(AudioHandlingSink):
    """This implements :class:`AudioHandlingSink` with functionality for saving
    the audio to file.

    Parameters
    ----------
    file_type: Callable[[str, int], :class:`AudioFile`]
        A callable (such as a class or function) that returns an :class:`AudioFile` type.
        Is used to create AudioFile objects. Its two arguments are the default audio file path and
        audio ssrc respectfully.
    output_dir: :class:`str`
        The directory to save files to.

    Attributes
    ----------
    file_type: Callable[[str, int], :class:`AudioFile`]
        The file_type passed as an argument.
    output_dir: :class:`str`
        The directory where files are being saved.
    output_files: Dict[int, :class:`AudioFile`]
        Dictionary that maps an ssrc to file object or file path. It's a file object unless
        convert_files has been called.
    done: :class:`bool`
        Indicates whether cleanup has been called.
    """

    __slots__ = ("file_type", "output_dir", "output_files", "done", "_clean_lock")

    def __init__(self, file_type: Callable[[str, int], 'AudioFile'], output_dir: str = "."):
        super().__init__()
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid output directory")
        self.file_type: Callable[[str, int], 'AudioFile'] = file_type
        self.output_dir: str = output_dir
        self.output_files: Dict[int, AudioFile] = {}
        self.done: bool = False
        self._clean_lock: threading.Lock = threading.Lock()

    def on_valid_audio(self, frame: AudioFrame) -> None:
        """Takes an audio frame and passes it to a :class:`AudioFile` object. If
        the AudioFile object does not already exist then it is created.

        Parameters
        ----------
        frame: :class:`AudioFrame`
            The frame which will be added to the buffer.
        """
        self._clean_lock.acquire()
        if self.done:
            return

        if frame.ssrc not in self.output_files:
            self.output_files[frame.ssrc] = self.file_type(
                os.path.join(self.output_dir, f"audio-{frame.ssrc}.pcm"), frame.ssrc
            )

        self.output_files[frame.ssrc].on_audio(frame)
        self._clean_lock.release()

    def on_rtcp(self, packet: RTCPPacket) -> None:
        """This function receives RTCP Packets, but does nothing with them since
        there is no use for them in this sink.

        Parameters
        ----------
        packet: :class:`RTCPPacket`
            A RTCP Packet received from discord. Can be any of the following:
            :class:`RTCPSenderReportPacket`, :class:`RTCPReceiverReportPacket`,
            :class:`RTCPSourceDescriptionPacket`, :class:`RTCPGoodbyePacket`,
            :class:`RTCPApplicationDefinedPacket`
        """
        return

    def cleanup(self) -> None:
        """Calls cleanup on all :class:`AudioFile` objects."""
        self._clean_lock.acquire()
        if self.done:
            return
        self._done_validating.wait()
        self.done = True
        for file in self.output_files.values():
            file.cleanup()
        self._clean_lock.release()

    def convert_files(self) -> None:
        """Calls cleanup if it hasn't already been called and then calls convert on all :class:`AudioFile` objects."""
        if not self.done:
            self.cleanup()
        for file in self.output_files.values():
            file.convert(self._create_name(file))

    def _create_name(self, file: 'AudioFile') -> str:
        if file.user is None:
            return f"audio-{file.ssrc}"
        elif isinstance(file.user, Object):
            return f"audio-{file.user.id}-{file.ssrc}"
        else:
            return f"audio-{file.user.name}#{file.user.discriminator}-{file.ssrc}"


class AudioFile:
    """Manages an audio file and its attributes.

    Parameters
    ----------
    path: :class:`str`
        Path to the audio file.
    ssrc: :class:`int`
        ssrc of the user this file belongs to

    Attributes
    ----------
    file: :term:`py:file object`
        File object of the audio file this object refers to.
    ssrc: :class:`int`
        ssrc of the user associated with this audio file
    done: :class:`bool`
        Indicates whether cleanup has been called and file is closed. Does not
        indicate that the convert has been called.
    converted: :class:`bool`
        Indicates whether convert has been called already.
    user: Optional[Union[:class:`Member`, :class:`Object`]]
        User of this audio file
    path: :class:`str`
        Path to the file object.
    """

    __slots__ = (
        "file",
        "ssrc",
        "done",
        "converted",
        "path",
        "_last_timestamp",
        "_last_sequence",
        "_packet_count",
        "user",
        "_clean_lock",
    )

    FRAME_BUFFER_LIMIT = 10

    def __init__(self, path: str, ssrc: int):
        self.file: BinaryIO = open(path, "wb")
        self.ssrc: int = ssrc
        self.done: bool = False
        self.converted: bool = False
        self.user: Optional[Union[Member, Object]] = None
        self.path: str = self.file.name
        self._clean_lock: threading.Lock = threading.Lock()

        self._last_timestamp: Optional[int] = None
        self._last_sequence: Optional[int] = None
        self._packet_count = 0

    def on_audio(self, frame: AudioFrame) -> None:
        """Takes an audio frame and adds it to a buffer. Once the buffer
        reaches a certain size, all audio frames in the buffer are
        written to file. The buffer allows leeway for packets that
        arrive out of order to be reorganized.

        Parameters
        ----------
        frame: :class:`AudioFrame`
            The frame which will be added to the buffer.
        """
        self._clean_lock.acquire()
        if self.done:
            return
        if self._packet_count < 7:
            self._packet_count += 1
        self._write_frame(frame)
        self._clean_lock.release()

    def _write_frame(self, frame: AudioFrame) -> None:
        # When the bot joins a vc and starts listening and a user speaks for the first time,
        # the timestamp encompasses all that silence, including silence before the bot even
        # joined the vc. It goes in a pattern that the 6th packet has a 11 sequence skip, so
        # this last part of the if statement gets rid of that silence.
        if self._last_timestamp is not None and not (self._packet_count == 6 and frame.sequence - self._last_sequence == 11):
            silence = frame.timestamp - self._last_timestamp - OpusDecoder.SAMPLES_PER_FRAME
            if silence > 0:
                self.file.write(b"\x00" * silence * OpusDecoder.SAMPLE_SIZE)
        if frame.audio != SILENT_FRAME:
            self.file.write(frame.audio)
        self._last_timestamp = frame.timestamp
        self._last_sequence = frame.sequence
        self._cache_user(frame.user)

    def _cache_user(self, user: Optional[Union['Member', 'Object']]) -> None:
        if user is None:
            return
        if self.user is None:
            self.user = user
        elif type(self.user) == int and isinstance(user, Object):
            self.user = user

    def _get_new_path(self, path: str, ext: str, new_name: Optional[str] = None) -> str:
        ext = "." + ext
        directory, name = os.path.split(path)
        name = new_name + ext if new_name is not None else ".".join(name.split(".")[:-1]) + ext
        return os.path.join(directory, name)

    def cleanup(self) -> None:
        """Writes remaining frames in buffer to file and then closes it."""
        self._clean_lock.acquire()
        if self.done:
            return
        self.file.close()
        self.done = True
        self._clean_lock.release()

    def convert(self, new_name: Optional[str] = None) -> None:
        """Converts the file to its formatted file type.

        This function is abstract. Any implementation of this function should
        call AudioFile._convert_cleanup with the path of the formatted file
        after it finishes. It will delete the raw audio file and update
        some attributes.

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            A new name for the file excluding the extension.
        """
        raise NotImplementedError()

    def _convert_cleanup(self, new_path: str) -> None:
        os.remove(self.path)
        self.path = new_path
        # this can be ignored because this function is meant to be used by subclasses.
        # where file is an optional type
        self.file = None  # type: ignore
        self.converted = True


class WaveAudioFile(AudioFile):
    """Extends :class:`AudioFile` with a method for converting the raw audio file
    to a wave file.

    Attributes
    ----------
    file: Optional[:term:`py:file object`]
        Same as in :class:`AudioFile`, but this attribute becomes None after convert is called.
    """

    CHUNK_WRITE_SIZE = 64
    if TYPE_CHECKING:
        file: Optional[BinaryIO]

    def convert(self, new_name: Optional[str] = None) -> None:
        """Write the raw audio data to a wave file.

        Extends :class:`AudioFile`

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            Name for the wave file excluding ".wav". Defaults to current name if None.
        """
        if self.converted:
            return

        path = self._get_new_path(self.path, "wav", new_name)
        with wave.open(path, "wb") as wavf:
            wavf.setnchannels(OpusDecoder.CHANNELS)
            wavf.setsampwidth(OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS)
            wavf.setframerate(OpusDecoder.SAMPLING_RATE)
            with open(self.path, "rb") as file:
                while frames := file.read(OpusDecoder.FRAME_SIZE * self.CHUNK_WRITE_SIZE):
                    wavf.writeframes(frames)

        self._convert_cleanup(path)


class MP3AudioFile(AudioFile):
    """Extends :class:`AudioFile` with a method for converting the raw audio file
    to a mp3 file.

    Attributes
    ----------
    file: Optional[:term:`py:file object`]
        Same as in :class:`AudioFile`, but this attribute becomes None after convert is called.
    """

    if TYPE_CHECKING:
        file: Optional[BinaryIO]

    def convert(self, new_name: Optional[str] = None) -> None:
        """Write the raw audio data to an mp3 file.

        Extends :class:`AudioFile`

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            Name for the wave file excluding ".mp3". Defaults to current name if None.
        """
        if self.converted:
            return

        path = self._get_new_path(self.path, "mp3", new_name)
        args = [
            'ffmpeg',
            '-f',
            's16le',
            '-ar',
            str(OpusDecoder.SAMPLING_RATE),
            '-ac',
            str(OpusDecoder.CHANNELS),
            '-y',
            '-i',
            self.path,
            path,
        ]
        try:
            process = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        except FileNotFoundError:
            raise ClientException('ffmpeg was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
        process.wait()

        self._convert_cleanup(path)


class AsyncEventWrapper:
    def __init__(self, event: Optional[threading.Event] = None):
        self.event: threading.Event = event or threading.Event()
        self._waiters: queue.Queue = queue.Queue()

    def __getattr__(self, item):
        return getattr(self.event, item)

    def set(self) -> None:
        self.event.set()
        # Queue.empty() is not reliable, so instead we just catch when the queue throws an Empty error
        try:
            while True:
                future = self._waiters.get_nowait()
                future._loop.call_soon_threadsafe(future.set_result, True)
        except queue.Empty:
            pass

    async def async_wait(self, loop) -> None:
        if self.is_set():
            return
        future = loop.create_future()
        self._waiters.put(future)
        await future


class AudioReceiver(threading.Thread):
    def __init__(
        self,
        client: 'VoiceClient',
    ) -> None:
        if not has_nacl:
            raise RuntimeError("PyNaCl library is required to use audio receiving")

        super().__init__()
        self.sink: Optional[AudioSink] = None
        self.client: VoiceClient = client
        self._state: ConnectionState = self.client._state
        self.loop = self.client.client.loop

        self.decode: bool = True
        self.after: Optional[Callable[..., Awaitable[Any]]] = None
        self.after_kwargs: Optional[dict] = None

        self._end: AsyncEventWrapper = AsyncEventWrapper()
        self._on_standby: AsyncEventWrapper = AsyncEventWrapper()
        self._on_standby.set()
        self._resumed: AsyncEventWrapper = AsyncEventWrapper()
        self._clean: AsyncEventWrapper = AsyncEventWrapper()
        self._clean.set()
        self._connected: threading.Event = client._connected

    def _do_run(self) -> None:
        while not self._end.is_set():
            if not self._connected.is_set():
                self._connected.wait()

            data = self.client.recv_audio(dump=not self._resumed.is_set())
            if data is None:
                continue

            future = self._state.process_audio(
                data, self.decode, self.client.mode, self.client.secret_key, self.client.guild.id
            )
            future.add_done_callback(self._audio_processing_callback)

    def _audio_processing_callback(self, future: Future) -> None:
        try:
            packet = future.result()
        except BaseException as exc:
            _log.exception("Exception occurred in audio process", exc_info=exc)
            return
        if isinstance(packet, AudioFrame):
            sink_callback = self.sink.on_audio
            packet.user = self.client.ws.get_member_from_ssrc(packet.ssrc)
        else:
            sink_callback = self.sink.on_rtcp
            packet.pt = RTCPMessageType(packet.pt)
        sink_callback(packet)

    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self.stop()
            _log.exception("Exception occurred in voice receiver", exc_info=exc)

    def _call_after(self) -> None:
        if self.after is not None:
            try:
                kwargs = self.after_kwargs if self.after_kwargs is not None else {}
                asyncio.run_coroutine_threadsafe(self.after(self.sink, **kwargs), self.loop)
            except Exception as exc:
                _log.exception('Calling the after function failed.', exc_info=exc)

    def _cleanup_listen(self) -> None:
        self.sink.cleanup()
        self._call_after()
        self.sink = None
        self._clean.set()

    def start_listening(
        self,
        sink: AudioSink,
        *,
        decode: bool = True,
        after: Optional[Callable[..., Awaitable[Any]]] = None,
        after_kwargs: Optional[dict] = None,
    ) -> None:
        self.sink = sink
        self.decode = decode
        self.after = after
        self.after_kwargs = after_kwargs
        self._on_standby.clear()
        self._clean.clear()
        self._resumed.set()

    def stop(self) -> None:
        self._end.set()

    def stop_listening(self) -> None:
        self._resumed.clear()
        self._on_standby.set()
        self._cleanup_listen()

    def pause(self) -> None:
        self._resumed.clear()

    def resume(self) -> None:
        self._resumed.set()

    def is_done(self) -> bool:
        return self._end.is_set()

    def is_listening(self) -> bool:
        return self._resumed.is_set() and not self._on_standby.is_set()

    def is_paused(self) -> bool:
        return not self._resumed.is_set() and not self._on_standby.is_set()

    def is_on_standby(self) -> bool:
        return self._on_standby.is_set()

    def is_cleaning(self) -> bool:
        return self._on_standby.is_set() and not self._clean.is_set()

    async def wait_for_resumed(self, *, loop=None) -> None:
        await self._resumed.async_wait(self.loop if loop is None else loop)

    async def wait_for_standby(self, *, loop=None) -> None:
        await self._on_standby.async_wait(self.loop if loop is None else loop)

    async def wait_for_clean(self, *, loop=None) -> None:
        await self._clean.async_wait(self.loop if loop is None else loop)


class AudioProcessPool:
    def __init__(self, max_processes: int, *, wait_timeout: Optional[float] = 3):
        if max_processes < 1:
            raise ValueError("max_processes must be greater than 0")
        if wait_timeout < 1:
            raise ValueError("wait_timeout must be greater than 0")
        self.max_processes: int = max_processes
        self.wait_timeout: Optional[int] = wait_timeout
        self._processes: Dict[int, Tuple] = {}
        self._wait_queue: queue.Queue = queue.Queue()
        self._wait_loop_running: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()

    def submit(self, data: bytes, n_p: int, decode: bool, mode: str, secret_key: List[int]) -> Future:
        self._lock.acquire()

        if n_p >= self.max_processes:
            raise ValueError(f"n_p must be less than the maximum processes ({self.max_processes})")

        if n_p not in self._processes:
            self._spawn_process(n_p)

        future = Future()
        self._processes[n_p][0].send((data, decode, mode, secret_key))
        self._wait_queue.put((n_p, future))
        self._start_recv_loop()

        self._lock.release()
        return future

    def _spawn_process(self, n_p) -> None:
        conn1, conn2 = _mp_ctx.Pipe(duplex=True)
        process = AudioUnpacker(args=(conn2,))
        process.start()
        self._processes[n_p] = (conn1, process)

    def _start_recv_loop(self) -> None:
        if not self._wait_loop_running.is_set():
            threading.Thread(target=self._recv_loop).start()

    def _recv_loop(self) -> None:
        self._wait_loop_running.set()
        while True:
            try:
                n_p, future = self._wait_queue.get(timeout=self.wait_timeout)
            except queue.Empty:
                break
            try:
                ret = self._processes[n_p][0].recv()
            except EOFError:
                self._lock.acquire()
                self._processes.pop(n_p)
                self._lock.release()
                continue
            (future.set_exception if isinstance(ret, BaseException) else future.set_result)(ret)

        self._wait_loop_running.clear()


class AudioUnpacker(_mp_ctx.Process):
    def __init__(self, **kwargs):
        super().__init__(daemon=True, **kwargs)

        self.secret_key: Optional[List[int]] = None
        self.decoders: Dict[int, OpusDecoder] = {}

    def run(self) -> None:
        pipe = self._args[0]
        while True:
            try:
                data, decode, mode, secret_key = pipe.recv()
                if secret_key is not None:
                    self.secret_key = secret_key

                packet = self.unpack_audio_packet(data, mode, decode)
                if isinstance(packet, RTCPPacket):
                    # enum not picklable
                    packet.pt = packet.pt.value

                pipe.send(packet)
            except BaseException as exc:
                pipe.send(exc)
                return

    def _decrypt_xsalsa20_poly1305(self, header, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))

        nonce = bytearray(24)
        nonce[:12] = header

        return self.strip_header_ext(box.decrypt(bytes(data), bytes(nonce)))

    def _decrypt_xsalsa20_poly1305_suffix(self, header, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))

        nonce_size = nacl.secret.SecretBox.NONCE_SIZE
        nonce = data[-nonce_size:]

        return self.strip_header_ext(box.decrypt(bytes(data[:-nonce_size]), nonce))

    def _decrypt_xsalsa20_poly1305_lite(self, header, data) -> bytes:
        box = nacl.secret.SecretBox(bytes(self.secret_key))

        nonce = bytearray(24)
        nonce[:4] = data[-4:]
        data = data[:-4]

        return self.strip_header_ext(box.decrypt(bytes(data), bytes(nonce)))

    @staticmethod
    def strip_header_ext(data: bytes) -> bytes:
        if data[0] == 0xBE and data[1] == 0xDE and len(data) > 4:
            _, length = struct.unpack_from('>HH', data)
            offset = 4 + length * 4
            data = data[offset:]
        return data

    def unpack_audio_packet(self, data: bytes, mode: str, decode: bool) -> Union[RTCPPacket, AudioFrame]:
        packet = get_audio_packet(data, getattr(self, '_decrypt_' + mode))

        if not isinstance(packet, RawAudioData):  # is RTCP packet
            return packet

        if decode and packet.audio != SILENT_FRAME:
            if packet.ssrc not in self.decoders:
                self.decoders[packet.ssrc] = OpusDecoder()
            return AudioFrame(self.decoders[packet.ssrc].decode(packet.audio), packet, None)  # type: ignore

        return AudioFrame(packet.audio, packet, None)
