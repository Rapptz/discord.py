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

from asyncio import run, sleep
from inspect import iscoroutinefunction
from io import TextIOWrapper
import logging
import struct
from threading import Thread
import time
from typing import Any, List, Optional, Union

from discord.recorder.errors import RecorderError
from ..user import User

_log: logging.Logger = logging.getLogger(__name__)

__all__ = (
    "Options",
    "Recorder",
    "Data",
    "AudioData"
)

class Options:
    """The options that :class:`~.Recorder` has available.

    Attributes
    ----------
    store:

    """

    def __init__(self, *, users: List[User] = [], duration: int = 0, size: int = 0) -> None:
        self.users: List[User] = users or []
        self.duration: int = duration or 0
        self.size: int = size

        # Property variables
        self._finished: bool = False

    @property
    def is_finished(self) -> bool:
        return self._finished
    
    @is_finished.setter
    def is_finished(self, value) -> None:
        return

    @staticmethod
    def store(function):
        """Decorator that stores all options of the recorder.
        """

        if iscoroutinefunction(function):
            async def inner(self, user: User, payload): # type: ignore
                if user in self.users or not self.users:            # Ignored type error because function can
                    return await function(self, user, payload)      # Can be different if deco is used in a coro
                
        else:
            def inner(self, user: User, payload):
                if user in self.users or not self.users:
                    return function(self, user, payload)
                
        return inner
    
    def start(self, *, asynchronous: bool = True) -> None:
        if not self.duration == 0:
            record: Thread = Thread(target = self.wait_until_finished, kwargs = {"asyncrhonous": asynchronous})
            record.start()

    def wait_until_finished(self, *, asyncrhonous: bool = True) -> None:
        if asyncrhonous:
            run(sleep(self.duration))
        else:
            time.sleep(self.duration) # Please, do it asynchronusly, no need for bots to have global lock

        if self.is_finished:
            return
        
        self.voice.stop_recording()

class Data:
    """Manages the data incoming from Discord for it to be descrypted and decoded
    """

    def __init__(self, data, client) -> None: # hint: No type hinted because the variables may be different from the expected ig
        self.data: bytearray = bytearray(data)
        self.client = client

        # Data parts
        self.headers = data[:12]
        self.data = self.data[12:]

        unpacker = struct.Struct(">xxHII")
        self.seq, self.timestamp, self.ssrc = unpacker.unpack_from(self.headers)
        self.decrypted = getattr(self.client, f"_decrypt:{self.client.mode}")

        self.decoded = None

        self.user_id: Optional[int] = None

class AudioData:
    """Manages the data that has been decrypted and decoded.

    This data can be saved as a file.
    """

    def __init__(self, file: TextIOWrapper) -> None:
        self.file = file
        self.finished: bool = False

    def save(self, data):
        """Saves the audio data.

        Raises
        ------
        RecorderError
            The instance has already finished saving the data.
        """

        if self.finished:
            raise RecorderError("The instance has already finished saving the data")
        
        # Tries to save the data
        try:
            self.file.write(data)

        except ValueError:
            _log.exception('Ignoring exception in save')

    def clear_cache(self) -> None:
        """Ends and cleans the cache of the audio data.
        
        Raises
        ------
        RecorderError
            The instance has already finished saving the data.
        """

        if self.finished:
            raise RecorderError("The instance has already finished saving the data")

        self.file.seek(0)
        self.finished = True

    def on_format(self, encoding: Union[str, Any]) -> None:
        """Event called when data is formatted.
        
        Raises
        ------
        RecorderError
            The instance is still saving the data.
        """

        if not self.finished:
            raise RecorderError("The instance is still saving the data")
