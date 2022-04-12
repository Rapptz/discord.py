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

import asyncio
from typing import Awaitable, TYPE_CHECKING, TypeVar, Optional, Any, Callable, Union, List, Tuple, AsyncIterator, Dict

from .errors import InvalidData
from .utils import _generate_nonce
from .object import Object
from .commands import _command_factory
from .enums import AppCommandType

__all__ = (
    'CommandIterator',
    'FakeCommandIterator',
)

if TYPE_CHECKING:
    from .user import User
    from .message import Message
    from .abc import Snowflake, Messageable
    from .commands import ApplicationCommand
    from .channel import DMChannel

T = TypeVar('T')
OT = TypeVar('OT')
_Func = Callable[[T], Union[OT, Awaitable[OT]]]

OLDEST_OBJECT = Object(id=0)


def _is_fake(item: Union[Messageable, Message]) -> bool:  # I hate this too, but <circular imports> and performance exist
    try:
        item.guild  # type: ignore
    except AttributeError:
        return True
    try:
        item.channel.me  # type: ignore
    except AttributeError:
        return False
    return True


class CommandIterator:
    def __new__(cls, *args, **kwargs) -> Union[CommandIterator, FakeCommandIterator]:
        if _is_fake(args[0]):
            return FakeCommandIterator(*args)
        else:
            return super().__new__(cls)

    def __init__(
        self,
        item: Union[Messageable, Message],
        type: AppCommandType,
        query: Optional[str] = None,
        limit: Optional[int] = None,
        command_ids: Optional[List[int]] = None,
        **kwargs,
    ) -> None:
        if query and command_ids:
            raise TypeError('Cannot specify both query and command_ids')
        if limit is not None and limit <= 0:
            raise ValueError('limit must be > 0')

        self.item = item
        self.channel = None
        self.state = item._state
        self._tuple = None
        self.type = type
        _, self.cls = _command_factory(int(type))
        self.query = query
        self.limit = limit
        self.command_ids = command_ids
        self.applications: bool = kwargs.get('applications', True)
        self.application: Snowflake = kwargs.get('application', None)
        self.commands = asyncio.Queue()

    async def _process_args(self) -> Tuple[DMChannel, Optional[str], Optional[Union[User, Message]]]:
        item = self.item
        if self.type is AppCommandType.user:
            channel = await item._get_channel()  # type: ignore
            if getattr(item, 'bot', None):
                item = item
            else:
                item = None
            text = 'user'
        elif self.type is AppCommandType.message:
            message = self.item
            channel = message.channel  # type: ignore
            text = 'message'
        elif self.type is AppCommandType.chat_input:
            channel = await item._get_channel()  # type: ignore
            item = None
            text = None
        self._process_kwargs(channel)  # type: ignore
        return channel, text, item  # type: ignore

    def _process_kwargs(self, channel) -> None:
        kwargs = {
            'guild_id': channel.guild.id,
            'type': self.type.value,
            'offset': 0,
        }
        if self.applications:
            kwargs['applications'] = True  # Only sent if it's True...
        if app := self.application:
            kwargs['application'] = app.id
        if (query := self.query) is not None:
            kwargs['query'] = query
        if cmds := self.command_ids:
            kwargs['command_ids'] = cmds
        self.kwargs = kwargs

    async def iterate(self) -> AsyncIterator[ApplicationCommand]:
        while True:
            if self.commands.empty():
                await self.fill_commands()

            try:
                yield self.commands.get_nowait()
            except asyncio.QueueEmpty:
                break

    def _get_retrieve(self):
        l = self.limit
        if l is None or l > 100:
            r = 100
        else:
            r = l
        self.retrieve = r
        return r > 0

    async def fill_commands(self) -> None:
        if not self._tuple:  # Do the required setup
            self._tuple = await self._process_args()

        if not self._get_retrieve():
            return

        state = self.state
        kwargs = self.kwargs
        retrieve = self.retrieve
        nonce = _generate_nonce()

        def predicate(d):
            return d.get('nonce') == nonce

        data = None
        for _ in range(3):
            await state.ws.request_commands(**kwargs, limit=retrieve, nonce=nonce)
            try:
                data: Optional[Dict[str, Any]] = await asyncio.wait_for(
                    state.ws.wait_for('guild_application_commands_update', predicate), timeout=3
                )
            except asyncio.TimeoutError:
                pass

        if data is None:
            raise InvalidData('Didn\'t receive a response from Discord')

        cmds = data['application_commands']
        if len(cmds) < retrieve:
            self.limit = 0
        elif self.limit is not None:
            self.limit -= retrieve

        kwargs['offset'] += retrieve

        for cmd in cmds:
            self.commands.put_nowait(self.create_command(cmd))

        for app in data.get('applications', []):
            ...

    def create_command(self, data) -> ApplicationCommand:
        channel, item, value = self._tuple  # type: ignore
        if item is not None:
            kwargs = {item: value}
        else:
            kwargs = {}
        return self.cls(state=channel._state, data=data, channel=channel, **kwargs)


class FakeCommandIterator:
    def __init__(
        self,
        item: Union[User, Message, DMChannel],
        type: AppCommandType,
        query: Optional[str] = None,
        limit: Optional[int] = None,
        command_ids: Optional[List[int]] = None,
    ) -> None:
        if query and command_ids:
            raise TypeError('Cannot specify both query and command_ids')
        if limit is not None and limit <= 0:
            raise ValueError('limit must be > 0')

        self.item = item
        self.channel = None
        self._tuple = None
        self.type = type
        _, self.cls = _command_factory(int(type))
        self.query = query
        self.limit = limit
        self.command_ids = command_ids
        self.has_more = False
        self.commands = asyncio.Queue()

    async def _process_args(self) -> Tuple[DMChannel, Optional[str], Optional[Union[User, Message]]]:
        item = self.item
        if self.type is AppCommandType.user:
            channel = await item._get_channel()  # type: ignore
            if getattr(item, 'bot', None):
                item = item
            else:
                item = None
            text = 'user'
        elif self.type is AppCommandType.message:
            message = self.item
            channel = message.channel  # type: ignore
            text = 'message'
        elif self.type is AppCommandType.chat_input:
            channel = await item._get_channel()  # type: ignore
            item = None
            text = None
        if not channel.recipient.bot:  # type: ignore # Type checker cannot understand this
            raise TypeError('User is not a bot')
        return channel, text, item  # type: ignore

    async def iterate(self) -> AsyncIterator[ApplicationCommand]:
        while True:
            if self.commands.empty():
                await self.fill_commands()

            try:
                yield self.commands.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def fill_commands(self) -> None:
        if self.has_more:
            return

        if not (stuff := self._tuple):
            self._tuple = channel, _, _ = await self._process_args()
        else:
            channel = stuff[0]

        limit = self.limit or -1
        data = await channel._state.http.get_application_commands(channel.recipient.id)
        ids = self.command_ids
        query = self.query and self.query.lower()
        type = self.type.value

        for cmd in data:
            if cmd['type'] != type:
                continue

            if ids:
                if not int(cmd['id']) in ids:
                    continue

            if query:
                if not query in cmd['name'].lower():
                    continue

            self.commands.put_nowait(self.create_command(cmd))
            limit -= 1
            if limit == 0:
                break

        self.has_more = True

    def create_command(self, data) -> ApplicationCommand:
        channel, item, value = self._tuple  # type: ignore
        if item is not None:
            kwargs = {item: value}
        else:
            kwargs = {}
        return self.cls(state=channel._state, data=data, channel=channel, **kwargs)
