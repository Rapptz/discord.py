import asyncio
from dataclasses import dataclass
import logging
import os
import struct
import subprocess
import threading
import wave
from typing import TYPE_CHECKING, Any, Awaitable, BinaryIO, Callable, Dict, List, Optional, Sequence, Tuple, Union

from .enums import RTCPMessageType
from .errors import ClientException
from .opus import Decoder as OpusDecoder
from .player import CREATE_NO_WINDOW

if TYPE_CHECKING:
    from .member import Member
    from .voice_client import VoiceClient


__all__ = (
    "AudioFrame",
    "AudioSink",
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

    # This function parses the report blocks and extension attributes, but it's
    # not being used because discord was sending invalid RTCP packets while testing
    # and it caused invalid values to be parsed.
    # def _parse_report_and_extension(self, data):
    #     fmt = "!IB3s4I"
    #     buf_size = struct.calcsize(fmt)
    #     report_blocks = [struct.unpack_from(fmt, buffer=data, offset=buf_size * i)
    #                      for i in range(self.rc)]
    #     self.report_blocks = list(map(lambda args: RTCPReceiverReportBlock(
    #         *args[:2], int.from_bytes(args[2], 'big'), *args[3:]
    #     ), report_blocks))
    #
    #     self.extension = data[len(self.report_blocks) * buf_size:]


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

    chunks: List

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
            description = b""
            if length > 0:
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
    ssrc_byes: Sequence[:class:`int`]
        List of SSRCs that are disconnecting.
    reason: :class:`bytes`
        Reason for disconnect.
    """

    __slots__ = (
        "ssrc_byes",
        "reason",
    )

    ssrc_byes: Tuple
    reason: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        if self.rc == 0:
            buf_size = 0
            self.ssrc_byes = ()
        else:
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

    ssrc: int
    name: str
    app_data: bytes

    def __init__(self, version_flag: int, rtcp_type: RTCPMessageType, length: int, data: bytes):
        super().__init__(version_flag, rtcp_type, length)

        self.ssrc, self.name = struct.unpack_from("!I4s", buffer=data)
        self.name = self.name.decode("ascii")
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

    # extension_id: :class:`int`
    #     Profile-specific identifier
    # extension_header: :class:`int`
    #     The header of the extension
    # extension_data: Sequence[:class:`int`]
    #     Extension header data

    __slots__ = (
        "version",
        "extended",
        "marker",
        "payload_type",
        "sequence",
        "timestamp",
        "ssrc",
        "csrc_list",
        # "extension_id",
        # "extension_header",
        # "extension_data",
        "audio",
    )

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
        self.csrc_list = ()
        if csrc_count > 0:
            self.csrc_list = struct.unpack_from(f">{csrc_count}I", buffer=data, offset=i)
            i += csrc_count * 4
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
            data = data[: -data[-1]]

        self.audio = decrypt_method(data[:i], data[i:])


class AudioPacket:
    RTCP_MAP = {
        RTCPMessageType.sender_report: RTCPSenderReportPacket,
        RTCPMessageType.receiver_report: RTCPReceiverReportPacket,
        RTCPMessageType.source_description: RTCPSourceDescriptionPacket,
        RTCPMessageType.goodbye: RTCPGoodbyePacket,
        RTCPMessageType.application_defined: RTCPApplicationDefinedPacket,
    }

    def __new__(
        cls, data: bytes, decrypt_method: Callable[[bytes, bytes], bytes]
    ) -> Union[
        RTCPSenderReportPacket,
        RTCPReceiverReportPacket,
        RTCPSourceDescriptionPacket,
        RTCPGoodbyePacket,
        RTCPApplicationDefinedPacket,
        RawAudioData,
    ]:
        fmt = ">BBH"
        buf_size = struct.calcsize(fmt)
        version_flag, payload_type, length = struct.unpack_from(fmt, buffer=data)
        if 200 <= payload_type <= 204:
            rtcp_type = RTCPMessageType(payload_type)
            return cls.RTCP_MAP[rtcp_type](version_flag, rtcp_type, length, data[buf_size:])
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

    def __init__(self, frame: bytes, raw_audio: RawAudioData, user: Optional[Union['Member', int]]):
        self.sequence: int = raw_audio.sequence
        self.timestamp: int = raw_audio.timestamp
        self.ssrc: int = raw_audio.ssrc
        self.audio: bytes = frame
        self.user: Optional[Union[Member, int]] = user


class AudioSink:
    """An object that handles fully decoded and decrypted audio frames

    This class defines three major functions that an audio sink object must outline
    """

    def on_audio(self, frame: AudioFrame) -> Any:
        """This function receives :class:`AudioFrame` objects.

        Abstract method

        Parameters
        ----------
        frame: :class:`AudioFrame`
            A frame of audio received from discord
        """
        raise NotImplementedError()

    def on_rtcp(self, packet: RTCPPacket) -> Any:
        """This function receives RTCP Packets

        Abstract method

        Parameters
        ----------
        packet: :class:`RTCPPacket`
            A RTCP Packet received from discord. Can be any of the following:
            :class:`RTCPSenderReportPacket`, :class:`RTCPReceiverReportPacket`,
            :class:`RTCPSourceDescriptionPacket`, :class:`RTCPGoodbyePacket`,
            :class:`RTCPApplicationDefinedPacket`
        """
        raise NotImplementedError()

    def cleanup(self) -> Any:
        """This function is called when the bot is done receiving
        audio and before the after callback is called.

        Abstract method
        """
        raise NotImplementedError()


class AudioFileSink(AudioSink):
    """This implements :class:`AudioSink` with functionality for saving
    the audio to file.

    Parameters
    ----------
    file_type: Callable[[str, int], :class:`AudioFile`]
        A callable (such as a class or function) that returns an :class:`AudioFile` type.
        Is used to create AudioFile objects.
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

    __slots__ = (
        "file_type",
        "output_dir",
        "output_files",
    )

    def __init__(self, file_type: Callable[[str, int], 'AudioFile'], output_dir: str = "."):
        if not os.path.isdir(output_dir):
            raise ValueError("Invalid output directory")
        self.file_type: Callable[[str, int], 'AudioFile'] = file_type
        self.output_dir: str = output_dir
        self.output_files: Dict[int, AudioFile] = {}
        self.done: bool = False

    def __del__(self):
        if hasattr(self, "done") and not self.done:
            self.cleanup()

    def on_audio(self, frame: AudioFrame) -> None:
        """Takes an audio frame and passes it to a :class:`AudioFile` object. If
        the AudioFile object does not already exist then it is created.

        Parameters
        ----------
        frame: :class:`AudioFrame`
            The frame which will be added to the buffer.
        """
        if frame.ssrc not in self.output_files:
            self.output_files[frame.ssrc] = self.file_type(
                os.path.join(self.output_dir, f"audio-{frame.ssrc}.pcm"), frame.ssrc
            )
        self.output_files[frame.ssrc].on_audio(frame)

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
        pass

    def cleanup(self) -> None:
        """Calls cleanup on all :class:`AudioFile` objects."""
        if self.done:
            return
        for file in self.output_files.values():
            file.cleanup()
        self.done = True

    def convert_files(self) -> None:
        """Calls cleanup if it hasn't already been called and then calls cleanup on all :class:`AudioFile` objects."""
        if not self.done:
            self.cleanup()
        for file in self.output_files.values():
            file.convert(self._create_name(file))

    def _create_name(self, file: 'AudioFile'):
        if file.user is None:
            return f"audio-{file.ssrc}"
        elif isinstance(file.user, int):
            return f"audio-{file.user}-{file.ssrc}"
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
    user: Optional[Union[:class:`Member`, :class:`int`]]
        User of this audio file
    path: :class:`str`
        Path to the file object.
    """

    __slots__ = (
        "file",
        "ssrc",
        "done",
        "_last_timestamp",
        "_frame_buffer",
        "user",
    )

    FRAME_BUFFER_LIMIT = 10

    def __init__(self, path: str, ssrc: int):
        self.file: BinaryIO = open(path, "wb")
        self.ssrc: int = ssrc
        self.done: bool = False

        self._last_timestamp: Optional[int] = None
        # This gives leeway for frames sent out of order
        self._frame_buffer: List[AudioFrame] = []
        self.user: Optional[Union[Member, int]] = None

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
        self._frame_buffer.append(frame)
        if len(self._frame_buffer) >= self.FRAME_BUFFER_LIMIT:
            self._write_buffer()

    def _write_buffer(self, empty: bool = False) -> None:
        self._frame_buffer = sorted(self._frame_buffer, key=lambda frame: frame.sequence)
        index = self.FRAME_BUFFER_LIMIT // 2 if not empty else self.FRAME_BUFFER_LIMIT
        for frame in self._frame_buffer[:index]:
            self._write_frame(frame)
        self._frame_buffer = self._frame_buffer[index:]

    def _write_frame(self, frame: AudioFrame) -> None:
        if self._last_timestamp is not None:
            # write silence
            silence = frame.timestamp - self._last_timestamp - OpusDecoder.SAMPLES_PER_FRAME
            if silence > 0:
                self.file.write(b"\x00" * silence * OpusDecoder.SAMPLE_SIZE)
        self.file.write(frame.audio)
        self._last_timestamp = frame.timestamp
        self._cache_user(frame.user)

    def _cache_user(self, user: Optional[Union['Member', int]]) -> None:
        if user is None:
            return
        if self.user is None:
            self.user = user
        elif self.user is None or isinstance(self.user, int):
            self.user = user

    def _get_new_path(self, path: str, ext: str, new_name: Optional[str] = None) -> str:
        ext = "." + ext
        directory, name = os.path.split(path)
        name = new_name + ext if new_name is not None else ".".join(name.split(".")[:-1]) + ext
        return os.path.join(directory, name)

    def cleanup(self) -> None:
        """Writes remaining frames in buffer to file and then closes it."""
        if self.done:
            return
        if len(self._frame_buffer) > 0:
            self._write_buffer(empty=True)
        self.file.close()
        self.done = True

    def convert(self, new_name: Optional[str] = None) -> None:
        """Converts the file to its formatted file type.

        This function is abstract.

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            A new name for the file excluding the extension.
        """
        raise NotImplementedError()

    @property
    def path(self) -> str:
        return self.file.name


class WaveAudioFile(AudioFile):
    CHUNK_WRITE_SIZE = 64

    def convert(self, new_name: Optional[str] = None) -> None:
        """Write the raw audio data to a wave file.

        Extends :class:`AudioFile`

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            Name for the wave file excluding ".wav". Defaults to current name if None.
        """
        path = self._get_new_path(self.path, "wav", new_name)
        with wave.open(path, "wb") as wavf:
            wavf.setnchannels(OpusDecoder.CHANNELS)
            wavf.setsampwidth(OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS)
            wavf.setframerate(OpusDecoder.SAMPLING_RATE)
            while frames := self.file.read(OpusDecoder.FRAME_SIZE * self.CHUNK_WRITE_SIZE):
                wavf.writeframes(frames)

        os.remove(self.path)
        file = open(path, "rb")
        file.close()
        self.file = file


class MP3AudioFile(AudioFile):
    def convert(self, new_name: Optional[str] = None) -> None:
        """Write the raw audio data to an mp3 file.

        Extends :class:`AudioFile`

        Parameters
        ----------
        new_name: Optional[:class:`str`]
            Name for the wave file excluding ".mp3". Defaults to current name if None.
        """
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

        os.remove(self.path)
        file = open(path, "rb")
        file.close()
        self.file = file


class AudioReceiver(threading.Thread):
    def __init__(
        self,
        sink: AudioSink,
        client: 'VoiceClient',
        *,
        decode: bool = True,
        after: Optional[Callable[..., Awaitable[Any]]] = None,
        after_kwargs: Optional[dict] = None,
    ) -> None:
        super().__init__()
        self.daemon: bool = False
        self.sink: AudioSink = sink
        self.client: VoiceClient = client
        self.decode: bool = decode
        self.after: Optional[Callable[..., Awaitable[Any]]] = after
        self.after_kwargs: Optional[dict] = after_kwargs

        self._end: threading.Event = threading.Event()
        self._resumed: threading.Event = threading.Event()
        self._resumed.set()  # we are not paused
        self._current_error: Optional[Exception] = None
        self._connected: threading.Event = client._connected
        self._lock: threading.Lock = threading.Lock()

    def _do_run(self) -> None:
        while not self._end.is_set():
            # are we disconnected from voice?
            if not self._connected.is_set():
                # wait until we are connected
                self._connected.wait()

            # dump audio while paused cuz we aren't using the audio
            packet = self.client.recv_audio_packet(dump=not self._resumed.is_set())
            if packet is None:
                continue
            if not isinstance(packet, AudioFrame):
                self.sink.on_rtcp(packet)
                continue
            if packet.audio is None:
                continue
            self.sink.on_audio(packet)

    def run(self) -> None:
        try:
            self._do_run()
        except Exception as exc:
            self._current_error = exc
            self.stop()
        finally:
            self.sink.cleanup()
            self._call_after()

    def _call_after(self) -> None:
        error = self._current_error

        if self.after is not None:
            try:
                kwargs = self.after_kwargs if self.after_kwargs is not None else {}
                asyncio.run_coroutine_threadsafe(self.after(self.sink, error, **kwargs), self.client.client.loop)
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
