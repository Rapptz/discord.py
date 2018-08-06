from .errors import DiscordException

from typing import ClassVar, Union
from mypy_extensions import TypedDict

def load_opus(name: str) -> None: ...


def is_loaded() -> bool: ...


class OpusError(DiscordException):
    code: int


class OpusNotLoaded(DiscordException):
    ...


OK: int
APPLICATION_AUDIO: int
APPLICATION_VOIP: int
APPLICATION_LOWDELAY: int
CTL_SET_BITRATE: int
CTL_SET_BANDWIDTH: int
CTL_SET_FEC: int
CTL_SET_PLP: int
CTL_SET_SIGNAL: int


class _BandCtl(TypedDict):
    narrow: int
    medium: int
    wide: int
    superwide: int
    full: int


class _SignalCtl(TypedDict):
    auto: int
    voice: int
    music: int


band_ctl: _BandCtl
signal_ctl: _SignalCtl


class Encoder:
    SAMPLING_RATE: ClassVar[int]
    CHANNELS: ClassVar[int]
    SAMPLE_SIZE: ClassVar[int]
    SAMPLES_PER_FRAME: ClassVar[int]
    FRAME_SIZE: ClassVar[int]

    def __init__(self, application: int = ...) -> None: ...

    def __del__(self) -> None: ...

    def set_bitrate(self, kbps: int) -> int: ...

    def set_bandwidth(self, req: str) -> None: ...

    def set_signal_type(self, req: str) -> None: ...

    def set_fec(self, enabled: bool = ...) -> None: ...

    def set_expected_packet_loss_percent(self, percentage: Union[int, float]) -> None: ...

    def encode(self, pcm: bytes, frame_size: int) -> bytes: ...
