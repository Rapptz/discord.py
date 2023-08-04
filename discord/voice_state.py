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

from typing import TYPE_CHECKING, Optional
from typing_extensions import Self

from .utils import MISSING

if TYPE_CHECKING:
    from . import abc
    from .voice_client import VoiceProtocol
    from .gateway import DiscordVoiceWebSocket

    from .types.voice import (
        GuildVoiceState as GuildVoiceStatePayload,
        VoiceServerUpdate as VoiceServerUpdatePayload,
        # SupportedModes,
    )


class VoiceConnectionState:
    """Represents the internal state of a voice connection."""

    def __init__(self, voice_client: VoiceProtocol):
        self.voice_client = voice_client
        self.token: str = MISSING
        self.socket = MISSING
        self.ws: DiscordVoiceWebSocket = MISSING

    async def voice_state_update(self, data: GuildVoiceStatePayload) -> None:
        ...

    async def voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        ...

    async def connect(
        self,
        *,
        reconnect: bool,
        timeout: float,
        self_deaf: bool,
        self_mute: bool,
        resume: bool
    ) -> Self:
        ...

    async def disconnect(self, *, force: bool=False) -> None:
        ...

    async def move_to(self, channel: Optional[abc.Snowflake]) -> None:
        ...

    def wait(self, timeout: float=0) -> bool:
        ...

    async def wait_async(self, timeout: float=0) -> bool:
        ...

    def is_connected(self) -> bool:
        ...

    def send_packet(self, data: bytes) -> None:
        ...
