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
from base64 import b64encode
import json
import logging
from random import choice
from typing import (
    Any,
    ClassVar,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import quote as _uriquote
import weakref

import aiohttp

from .enums import RelationshipAction, InviteType
from .errors import HTTPException, Forbidden, NotFound, LoginFailure, DiscordServerError, InvalidArgument
from . import utils
from .tracking import ContextProperties
from .utils import MISSING

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .file import File
    from .enums import AuditLogAction, ChannelType
    from .message import Message
    from .types import (
        appinfo,
        audit_log,
        channel,
        emoji,
        guild,
        integration,
        invite,
        member,
        message,
        template,
        role,
        user,
        webhook,
        widget,
        team,
        threads,
        sticker,
        welcome_screen,
    )
    from .types.snowflake import Snowflake, SnowflakeList

    from types import TracebackType

    T = TypeVar('T')
    BE = TypeVar('BE', bound=BaseException)
    MU = TypeVar('MU', bound='MaybeUnlock')
    Response = Coroutine[Any, Any, T]


async def json_or_text(response: aiohttp.ClientResponse) -> Union[Dict[str, Any], str]:
    text = await response.text(encoding='utf-8')
    try:
        if response.headers['content-type'] == 'application/json':
            return utils._from_json(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


def _gen_accept_encoding_header():
    return 'gzip, deflate, br' if aiohttp.http_parser.HAS_BROTLI else 'gzip, deflate'  # type: ignore


class Route:
    BASE: ClassVar[str] = 'https://discord.com/api/v9'

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.path: str = path
        self.method: str = method
        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url

        # Major parameters
        self.channel_id: Optional[Snowflake] = parameters.get('channel_id')
        self.guild_id: Optional[Snowflake] = parameters.get('guild_id')
        self.webhook_id: Optional[Snowflake] = parameters.get('webhook_id')
        self.webhook_token: Optional[str] = parameters.get('webhook_token')

    @property
    def bucket(self) -> str:
        # TODO: Implement buckets :(
        return f'{self.channel_id}:{self.guild_id}:{self.path}'


class MaybeUnlock:
    def __init__(self, lock: asyncio.Lock) -> None:
        self.lock: asyncio.Lock = lock
        self._unlock: bool = True

    def __enter__(self: MU) -> MU:
        return self

    def defer(self) -> None:
        self._unlock = False

    def __exit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self._unlock:
            self.lock.release()


# For some reason, the Discord voice websocket expects this header to be
# completely lowercase while aiohttp respects spec and does it as case-insensitive
aiohttp.hdrs.WEBSOCKET = 'websocket'  # type: ignore
# Support brotli if installed
aiohttp.client_reqrep.ClientRequest.DEFAULT_HEADERS[aiohttp.hdrs.ACCEPT_ENCODING] = _gen_accept_encoding_header()  # type: ignore


class _FakeResponse:
    def __init__(self, reason: str, status: int) -> None:
        self.reason = reason
        self.status = status


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Discord API."""

    def __init__(
        self,
        connector: Optional[aiohttp.BaseConnector] = None,
        *,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        unsync_clock: bool = True,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self.connector = connector
        self.__session: aiohttp.ClientSession = MISSING
        self._locks: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._global_over: asyncio.Event = asyncio.Event()
        self._global_over.set()
        self.token: Optional[str] = None
        self.ack_token: Optional[str] = None
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[aiohttp.BasicAuth] = proxy_auth
        self.use_clock: bool = not unsync_clock

        self.user_agent: str = MISSING
        self.super_properties: Dict[str, Any] = {}
        self.encoded_super_properties: str = MISSING
        self._started: bool = False

    def __del__(self) -> None:
        session = self.__session
        if session:
            try:
                session.connector._close()
            except AttributeError:
                pass

    async def startup(self) -> None:
        if self._started:
            return
        self.__session = session = aiohttp.ClientSession(connector=self.connector)
        self.user_agent, self.browser_version, self.client_build_number = ua, bv, bn = await utils._get_info(session)
        _log.info('Found user agent %s (%s), build number %s.', ua, bv, bn)
        self.super_properties = sp = {
            'os': 'Windows',
            'browser': 'Chrome',
            'device': '',
            'browser_user_agent': ua,
            'browser_version': bv,
            'os_version': '10',
            'referrer': '',
            'referring_domain': '',
            'referrer_current': '',
            'referring_domain_current': '',
            'release_channel': 'stable',
            'system_locale': 'en-US',
            'client_build_number': bn,
            'client_event_source': None
        }
        self.encoded_super_properties = b64encode(json.dumps(sp).encode()).decode('utf-8')
        self._started = True

    async def ws_connect(self, url: str, *, compress: int = 0, host: Optional[str] = None) -> Any:
        if not host:
            host = url[6:].split('?')[0].rstrip('/')  # Removes 'wss://' and the query params

        kwargs: Dict[str, Any] = {
            'proxy_auth': self.proxy_auth,
            'proxy': self.proxy,
            'max_msg_size': 0,
            'timeout': 30.0,
            'autoclose': False,
            'headers': {
                'Accept-Language': 'en-US',
                'Cache-Control': 'no-cache',
                'Connection': 'Upgrade',
                'Host': host,
                'Origin': 'https://discord.com',
                'Pragma': 'no-cache',
                'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
                'User-Agent': self.user_agent,
            },
            'compress': compress,
        }

        return await self.__session.ws_connect(url, **kwargs)

    async def request(
        self,
        route: Route,
        *,
        files: Optional[Sequence[File]] = None,
        form: Optional[Iterable[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Any:
        bucket = route.bucket
        method = route.method
        url = route.url

        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock()
            if bucket is not None:
                self._locks[bucket] = lock

        # Header creation
        headers = {
            'Accept-Language': 'en-US',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://discord.com',
            'Pragma': 'no-cache',
            'Referer': 'https://discord.com/channels/@me',
            'Sec-CH-UA': '"Google Chrome";v="{0}", "Chromium";v="{0}", ";Not A Brand";v="99"'.format(self.browser_version.split('.')[0]),
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': self.user_agent,
            'X-Discord-Locale': 'en-US',
            'X-Debug-Options': 'bugReporterEnabled',
            'X-Super-Properties': self.encoded_super_properties
        }

        # Header modification
        if self.token is not None and kwargs.get('auth', True):
            headers['Authorization'] = self.token

        reason = kwargs.pop('reason', None)
        if reason:
            headers['X-Audit-Log-Reason'] = _uriquote(reason)

        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = utils._to_json(kwargs.pop('json'))

        if 'context_properties' in kwargs:
            props = kwargs.pop('context_properties')
            if isinstance(props, ContextProperties):
                headers['X-Context-Properties'] = props.value

        if kwargs.pop('super_properties_to_track', False):
            headers['X-Track'] = headers.pop('X-Super-Properties')

        kwargs['headers'] = headers

        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth

        if not self._global_over.is_set():
            await self._global_over.wait()

        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        await lock.acquire()
        with MaybeUnlock(lock) as maybe_lock:
            for tries in range(5):
                if files:
                    for f in files:
                        f.reset(seek=tries)

                if form:
                    form_data = aiohttp.FormData(quote_fields=False)
                    for params in form:
                        form_data.add_field(**params)
                    kwargs['data'] = form_data

                try:
                    async with self.__session.request(method, url, **kwargs) as response:
                        _log.debug('%s %s with %s has returned %s.', method, url, kwargs.get('data'), response.status)
                        data = await json_or_text(response)

                        # Check if we have rate limit information
                        remaining = response.headers.get('X-Ratelimit-Remaining')
                        if remaining == '0' and response.status != 429:
                            # We've depleted our current bucket
                            delta = utils._parse_ratelimit_header(response, use_clock=self.use_clock)
                            _log.debug('A rate limit bucket has been exhausted (bucket: %s, retry: %s).', bucket, delta)
                            maybe_lock.defer()
                            self.loop.call_later(delta, lock.release)

                        # Request was successful so just return the text/json
                        if 300 > response.status >= 200:
                            _log.debug('%s %s has received %s', method, url, data)
                            return data

                        # Rate limited
                        if response.status == 429:
                            if not response.headers.get('Via') or isinstance(data, str):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(response, data)

                            fmt = 'We are being rate limited. Retrying in %.2f seconds. Handled under the bucket "%s".'

                            # Sleep a bit
                            retry_after: float = data['retry_after']
                            _log.warning(fmt, retry_after, bucket)

                            # Check if it's a global rate limit
                            is_global = data.get('global', False)
                            if is_global:
                                _log.warning('Global rate limit has been hit. Retrying in %.2f seconds.', retry_after)
                                self._global_over.clear()

                            await asyncio.sleep(retry_after)
                            _log.debug('Done sleeping for the rate limit. Retrying...')

                            # Release the global lock now that the rate limit passed
                            if is_global:
                                self._global_over.set()
                                _log.debug('Global rate limit is now over.')

                            continue

                        # Unconditional retry
                        if response.status in {500, 502, 504}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        # Usual error cases
                        if response.status == 403:
                            raise Forbidden(response, data)
                        elif response.status == 404:
                            raise NotFound(response, data)
                        elif response.status >= 500:
                            raise DiscordServerError(response, data)
                        else:
                            raise HTTPException(response, data)

                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        await asyncio.sleep(1 + tries * 2)
                        continue
                    raise

            if response is not None:
                # We've run out of retries, raise
                if response.status >= 500:
                    raise DiscordServerError(response, data)

                raise HTTPException(response, data)

            raise RuntimeError('Unreachable code in HTTP handling')

    async def get_from_cdn(self, url: str) -> bytes:
        async with self.__session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            elif resp.status == 404:
                raise NotFound(resp, 'asset not found')
            elif resp.status == 403:
                raise Forbidden(resp, 'cannot retrieve asset')
            else:
                raise HTTPException(resp, 'failed to get asset')

    # State management

    def recreate(self) -> None:
        if self.__session and self.__session.closed:
            self.__session = aiohttp.ClientSession(connector=self.connector)

    async def close(self) -> None:
        if self.__session:
            await self.__session.close()

    # Login management

    def _token(self, token: str) -> None:
        self.token = token
        self.ack_token = None

    def get_me(self, with_analytics_token=True) -> Response[user.User]:
        params = {
            'with_analytics_token': str(with_analytics_token).lower()
        }
        return self.request(Route('GET', '/users/@me'), params=params)

    async def static_login(self, token: str) -> user.User:
        old_token, self.token = self.token, token

        await self.startup()

        try:
            data = await self.get_me()
        except HTTPException as exc:
            self.token = old_token
            if exc.status == 401:
                raise LoginFailure('Improper token has been passed') from exc
            raise

        return data

    # PM functionality

    def start_group(self, recipients: SnowflakeList) -> Response[channel.GroupDMChannel]:
        payload = {
            'recipients': recipients,
        }
        props = ContextProperties._from_new_group_dm()  # New Group DM button

        return self.request(Route('POST', '/users/@me/channels'), json=payload, context_properties=props)

    def add_group_recipient(self, channel_id: Snowflake, user_id: Snowflake):  # TODO: return typings
        r = Route('PUT', '/channels/{channel_id}/recipients/{user_id}', channel_id=channel_id, user_id=user_id)
        return self.request(r)

    def remove_group_recipient(self, channel_id: Snowflake, user_id: Snowflake):  # TODO: return typings
        r = Route('DELETE', '/channels/{channel_id}/recipients/{user_id}', channel_id=channel_id, user_id=user_id)
        return self.request(r)

    def edit_group(
        self, channel_id: Snowflake, name: Optional[str] = MISSING, icon: Optional[bytes] = MISSING
    ) -> Response[channel.GroupDMChannel]:
        payload = {}
        if name is not MISSING:
            payload['name'] = name
        if icon is not MISSING:
            payload['icon'] = icon

        return self.request(Route('PATCH', '/channels/{channel_id}', channel_id=channel_id), json=payload)

    def get_private_channels(self) -> Response[List[Union[channel.DMChannel, channel.GroupDMChannel]]]:
        return self.request(Route('GET', '/users/@me/channels'))

    def start_private_message(self, user_id: Snowflake) -> Response[channel.DMChannel]:
        payload = {
            'recipients': [user_id],
        }
        props = ContextProperties._empty()  # {}

        return self.request(Route('POST', '/users/@me/channels'), json=payload, context_properties=props)

    # Message management

    def send_message(
        self,
        channel_id: Snowflake,
        content: Optional[str],
        *,
        tts: bool = False,
        nonce: Optional[Snowflake] = None,
        allowed_mentions: Optional[message.AllowedMentions] = None,
        message_reference: Optional[message.MessageReference] = None,
        stickers: Optional[List[sticker.StickerItem]] = None,
    ) -> Response[message.Message]:
        r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
        payload: Dict[str, Any] = {'tts': tts}
        if content:
            payload['content'] = content
        if nonce:
            payload['nonce'] = nonce
        if allowed_mentions:
            payload['allowed_mentions'] = allowed_mentions
        if message_reference:
            payload['message_reference'] = message_reference
        if stickers:
            payload['sticker_ids'] = stickers

        return self.request(r, json=payload)

    def send_typing(self, channel_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/channels/{channel_id}/typing', channel_id=channel_id))

    def send_multipart_helper(
        self,
        route: Route,
        *,
        files: Sequence[File],
        content: Optional[str] = None,
        tts: bool = False,
        nonce: Optional[Snowflake] = None,
        allowed_mentions: Optional[message.AllowedMentions] = None,
        message_reference: Optional[message.MessageReference] = None,
        stickers: Optional[List[sticker.StickerItem]] = None,
    ) -> Response[message.Message]:
        form = []
        payload: Dict[str, Any] = {'tts': tts}

        if content:
            payload['content'] = content
        if nonce:
            payload['nonce'] = nonce
        if allowed_mentions:
            payload['allowed_mentions'] = allowed_mentions
        if message_reference:
            payload['message_reference'] = message_reference
        if stickers:
            payload['sticker_ids'] = stickers

        attachments = []
        for index, file in enumerate(files):
            attachment = {'id': str(index), 'filename': file.filename}
            if file.description is not None:
                attachment['description'] = file.description
            attachments.append(attachment)
            form.append(
                {
                    'name': f'files[{index}]',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': 'application/octet-stream',
                }
            )

        payload['attachments'] = attachments
        form.append({'name': 'payload_json', 'value': utils._to_json(payload)})

        return self.request(route, form=form, files=files)

    def send_files(
        self,
        channel_id: Snowflake,
        *,
        files: Sequence[File],
        content: Optional[str] = None,
        tts: bool = False,
        nonce: Optional[Snowflake] = None,
        allowed_mentions: Optional[message.AllowedMentions] = None,
        message_reference: Optional[message.MessageReference] = None,
        stickers: Optional[List[sticker.StickerItem]] = None,
    ) -> Response[message.Message]:
        return self.send_multipart_helper(
            Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id),
            files=files,
            content=content,
            tts=tts,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=message_reference,
            stickers=stickers,
        )

    async def ack_message(
        self, channel_id: Snowflake, message_id: Snowflake
    ):  # TODO: response type (simple)
        r = Route('POST', '/channels/{channel_id}/messages/{message_id}/ack', channel_id=channel_id, message_id=message_id)
        payload = {
            'token': self.ack_token
        }

        data = await self.request(r, json=payload)
        self.ack_token = data['token']

    def unack_message(
        self, channel_id: Snowflake, message_id: Snowflake, *, mention_count: int = 0
    ) -> Response[None]:
        r = Route('POST', '/channels/{channel_id}/messages/{message_id}/ack', channel_id=channel_id, message_id=message_id)
        payload = {
            'manual': True,
            'mention_count': mention_count
        }

        return self.request(r, json=payload)

    def ack_messages(self, read_states) -> Response[None]:  # TODO: type and implement
        payload = {
            'read_states': read_states
        }

        return self.request(Route('POST', '/read-states/ack-bulk'), json=payload)

    def ack_guild(self, guild_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/guilds/{guild_id}/ack', guild_id=guild_id))

    def unack_something(self, channel_id: Snowflake) -> Response[None]:  # TODO: research
        return self.request(Route('DELETE', '/channels/{channel_id}/messages/ack', channel_id=channel_id))

    def delete_message(
        self, channel_id: Snowflake, message_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        r = Route('DELETE', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        return self.request(r, reason=reason)

    def edit_message(self, channel_id: Snowflake, message_id: Snowflake, **fields: Any) -> Response[message.Message]:
        r = Route('PATCH', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        return self.request(r, json=fields)

    def add_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str) -> Response[None]:
        r = Route(
            'PUT',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )
        return self.request(r)

    def remove_reaction(
        self, channel_id: Snowflake, message_id: Snowflake, emoji: str, member_id: Snowflake
    ) -> Response[None]:
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{member_id}',
            channel_id=channel_id,
            message_id=message_id,
            member_id=member_id,
            emoji=emoji,
        )
        return self.request(r)

    def remove_own_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str) -> Response[None]:
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )
        return self.request(r)

    def get_reaction_users(
        self,
        channel_id: Snowflake,
        message_id: Snowflake,
        emoji: str,
        limit: int,
        after: Optional[Snowflake] = None,
    ) -> Response[List[user.User]]:
        r = Route(
            'GET',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )
        params: Dict[str, Any] = {
            'limit': limit,
        }
        if after:
            params['after'] = after

        return self.request(r, params=params)

    def clear_reactions(self, channel_id: Snowflake, message_id: Snowflake) -> Response[None]:
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions',
            channel_id=channel_id,
            message_id=message_id,
        )
        return self.request(r)

    def clear_single_reaction(self, channel_id: Snowflake, message_id: Snowflake, emoji: str) -> Response[None]:
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}/reactions/{emoji}',
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )
        return self.request(r)

    async def get_message(self, channel_id: Snowflake, message_id: Snowflake) -> message.Message:
        data = await self.logs_from(channel_id, 1, around=message_id)

        try:
            msg = data[0]
        except IndexError:
            raise NotFound(_FakeResponse('Not Found', 404), 'message not found')
        if int(msg.get('id')) != message_id:
            raise NotFound(_FakeResponse('Not Found', 404), 'message not found')

        return msg

    def get_channel(self, channel_id: Snowflake) -> Response[channel.Channel]:
        return self.request(Route('GET', '/channels/{channel_id}', channel_id=channel_id))

    def logs_from(
        self,
        channel_id: Snowflake,
        limit: int,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        around: Optional[Snowflake] = None,
    ) -> Response[List[message.Message]]:
        params: Dict[str, Any] = {
            'limit': limit,
        }
        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after
        if around is not None:
            params['around'] = around

        return self.request(Route('GET', '/channels/{channel_id}/messages', channel_id=channel_id), params=params)

    def publish_message(self, channel_id: Snowflake, message_id: Snowflake) -> Response[message.Message]:
        r = Route(
            'POST',
            '/channels/{channel_id}/messages/{message_id}/crosspost',
            channel_id=channel_id,
            message_id=message_id,
        )
        return self.request(r)

    def pin_message(self, channel_id: Snowflake, message_id: Snowflake, reason: Optional[str] = None) -> Response[None]:
        r = Route(
            'PUT',
            '/channels/{channel_id}/pins/{message_id}',
            channel_id=channel_id,
            message_id=message_id,
        )
        return self.request(r, reason=reason)

    def unpin_message(self, channel_id: Snowflake, message_id: Snowflake, reason: Optional[str] = None) -> Response[None]:
        r = Route(
            'DELETE',
            '/channels/{channel_id}/pins/{message_id}',
            channel_id=channel_id,
            message_id=message_id,
        )
        return self.request(r, reason=reason)

    def pins_from(self, channel_id: Snowflake) -> Response[List[message.Message]]:
        return self.request(Route('GET', '/channels/{channel_id}/pins', channel_id=channel_id))

    def ack_pins(self, channel_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/channels/{channel_id}/pins/ack', channel_id=channel_id))

    # Member management

    def kick(self, user_id: Snowflake, guild_id: Snowflake, reason: Optional[str] = None) -> Response[None]:
        r = Route('DELETE', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, reason=reason)

    def ban(
        self,
        user_id: Snowflake,
        guild_id: Snowflake,
        delete_message_days: int = 1,
        reason: Optional[str] = None,
    ) -> Response[None]:
        r = Route('PUT', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id)
        payload = {
            'delete_message_days': str(delete_message_days),
        }

        return self.request(r, json=payload, reason=reason)

    def unban(self, user_id: Snowflake, guild_id: Snowflake, *, reason: Optional[str] = None) -> Response[None]:
        r = Route('DELETE', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, reason=reason)

    def guild_voice_state(
        self,
        user_id: Snowflake,
        guild_id: Snowflake,
        *,
        mute: Optional[bool] = None,
        deafen: Optional[bool] = None,
        reason: Optional[str] = None,
    ) -> Response[member.Member]:
        r = Route('PATCH', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        payload = {}
        if mute is not None:
            payload['mute'] = mute

        if deafen is not None:
            payload['deaf'] = deafen

        return self.request(r, json=payload, reason=reason)

    def edit_profile(self, payload: Dict[str, Any]) -> Response[user.User]:
        return self.request(Route('PATCH', '/users/@me'), json=payload)

    def edit_my_voice_state(self, guild_id: Snowflake, payload: Dict[str, Any]) -> Response[None]:  # TODO: remove payload
        r = Route('PATCH', '/guilds/{guild_id}/voice-states/@me', guild_id=guild_id)
        return self.request(r, json=payload)

    def edit_voice_state(self, guild_id: Snowflake, user_id: Snowflake, payload: Dict[str, Any]) -> Response[None]:  # TODO: remove payload
        r = Route('PATCH', '/guilds/{guild_id}/voice-states/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, json=payload)

    def edit_me(
        self,
        guild_id: Snowflake,
        *,
        nick: Optional[str] = MISSING,
        avatar: Optional[bytes] = MISSING,
        reason: Optional[str] = None,
    ) -> Response[member.MemberWithUser]:
        payload = {}
        if nick is not MISSING:
            payload['nick'] = nick
        if avatar is not MISSING:
            r = Route('PATCH', '/guilds/{guild_id}/members/@me', guild_id=guild_id)
            payload['avatar'] = avatar
        else:
            r = choice((
                Route('PATCH', '/guilds/{guild_id}/members/@me/nick', guild_id=guild_id),
                Route('PATCH', '/guilds/{guild_id}/members/@me', guild_id=guild_id)
            ))

        return self.request(r, json=payload, reason=reason)

    def edit_member(
        self,
        guild_id: Snowflake,
        user_id: Snowflake,
        *,
        reason: Optional[str] = None,
        **fields: Any,  # TODO: Is this cheating
    ) -> Response[member.MemberWithUser]:
        r = Route('PATCH', '/guilds/{guild_id}/members/{user_id}', guild_id=guild_id, user_id=user_id)
        return self.request(r, json=fields, reason=reason)

    # Channel management

    def edit_channel(
        self,
        channel_id: Snowflake,
        *,
        reason: Optional[str] = None,
        **options: Any,  # TODO: Is this cheating
    ) -> Response[channel.Channel]:
        r = Route('PATCH', '/channels/{channel_id}', channel_id=channel_id)
        valid_keys = (  # TODO: Why is this being validated?
            'name',
            'parent_id',
            'topic',
            'bitrate',
            'nsfw',
            'user_limit',
            'position',
            'permission_overwrites',
            'rate_limit_per_user',
            'type',
            'rtc_region',
            'video_quality_mode',
            'archived',
            'auto_archive_duration',
            'locked',
            'invitable',
            'default_auto_archive_duration',
        )
        payload = {k: v for k, v in options.items() if k in valid_keys}
        return self.request(r, reason=reason, json=payload)

    def bulk_channel_update(
        self,
        guild_id: Snowflake,
        data: List[guild.ChannelPositionUpdate],
        *,
        reason: Optional[str] = None,
    ) -> Response[None]:
        r = Route('PATCH', '/guilds/{guild_id}/channels', guild_id=guild_id)
        return self.request(r, json=data, reason=reason)

    def create_channel(
        self,
        guild_id: Snowflake,
        channel_type: channel.ChannelType,
        *,
        reason: Optional[str] = None,
        **options: Any,  # TODO: Is this cheating
    ) -> Response[channel.GuildChannel]:
        payload = {  # TODO: WTF is happening here??
            'type': channel_type,
        }
        valid_keys = (
            'name',
            'parent_id',
            'topic',
            'bitrate',
            'nsfw',
            'user_limit',
            'position',
            'permission_overwrites',
            'rate_limit_per_user',
            'rtc_region',
            'video_quality_mode',
            'auto_archive_duration',
        )
        payload.update({k: v for k, v in options.items() if k in valid_keys and v is not None})

        return self.request(Route('POST', '/guilds/{guild_id}/channels', guild_id=guild_id), json=payload, reason=reason)

    def delete_channel(
        self, channel_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        return self.request(Route('DELETE', '/channels/{channel_id}', channel_id=channel_id), reason=reason)

    # Thread management

    def start_thread_with_message(
        self,
        channel_id: Snowflake,
        message_id: Snowflake,
        *,
        name: str,
        auto_archive_duration: threads.ThreadArchiveDuration,
        location: str = MISSING,
        reason: Optional[str] = None,
    ) -> Response[threads.Thread]:
        route = Route(
            'POST', '/channels/{channel_id}/messages/{message_id}/threads', channel_id=channel_id, message_id=message_id
        )
        payload = {
            'auto_archive_duration': auto_archive_duration,
            'name': name,
            'type': 11,
        }
        if location is MISSING:
            payload['location'] = choice(('Message', 'Reply Chain Nudge'))
        else:
            payload['location'] = location

        return self.request(route, json=payload, reason=reason)

    def start_thread_without_message(
        self,
        channel_id: Snowflake,
        *,
        name: str,
        auto_archive_duration: threads.ThreadArchiveDuration,
        type: threads.ThreadType,
        invitable: bool = MISSING,
        reason: Optional[str] = None,
    ) -> Response[threads.Thread]:
        r = Route('POST', '/channels/{channel_id}/threads', channel_id=channel_id)
        payload = {
            'auto_archive_duration': auto_archive_duration,
            'location': None,
            'name': name,
            'type': type,
        }
        if invitable is not MISSING:
            payload['invitable'] = invitable

        return self.request(r, json=payload, reason=reason)

    def join_thread(self, channel_id: Snowflake) -> Response[None]:
        r = Route('POST', '/channels/{channel_id}/thread-members/@me', channel_id=channel_id)
        params = {
            'location': choice(('Banner', 'Toolbar Overflow', 'Context Menu'))
        }

        return self.request(r, params=params)

    def add_user_to_thread(self, channel_id: Snowflake, user_id: Snowflake) -> Response[None]:  # TODO: Find a way to test private thread stuff
        r = Route('PUT', '/channels/{channel_id}/thread-members/{user_id}', channel_id=channel_id, user_id=user_id)
        return self.request(r)

    def leave_thread(self, channel_id: Snowflake) -> Response[None]:
        r = Route('DELETE', '/channels/{channel_id}/thread-members/@me', channel_id=channel_id)
        params = {
            'location': choice(('Toolbar Overflow', 'Context Menu'))
        }

        return self.request(r, params=params)

    def remove_user_from_thread(self, channel_id: Snowflake, user_id: Snowflake) -> Response[None]:
        r = Route('DELETE', '/channels/{channel_id}/thread-members/{user_id}', channel_id=channel_id, user_id=user_id)
        params = {
            'location': 'Context Menu'
        }

        return self.request(r, params=params)

    def get_public_archived_threads(
        self, channel_id: Snowflake, before: Optional[Snowflake] = None, limit: int = 50
    ) -> Response[threads.ThreadPaginationPayload]:
        route = Route('GET', '/channels/{channel_id}/threads/archived/public', channel_id=channel_id)

        params = {}
        if before:
            params['before'] = before
        if limit and limit != 50:
            params['limit'] = limit
        return self.request(route, params=params)

    def get_private_archived_threads(
        self, channel_id: Snowflake, before: Optional[Snowflake] = None, limit: int = 50
    ) -> Response[threads.ThreadPaginationPayload]:
        route = Route('GET', '/channels/{channel_id}/threads/archived/private', channel_id=channel_id)

        params = {}
        if before:
            params['before'] = before
        if limit and limit != 50:
            params['limit'] = limit
        return self.request(route, params=params)

    def get_joined_private_archived_threads(
        self, channel_id: Snowflake, before: Optional[Snowflake] = None, limit: int = 50
    ) -> Response[threads.ThreadPaginationPayload]:
        route = Route('GET', '/channels/{channel_id}/users/@me/threads/archived/private', channel_id=channel_id)
        params = {}
        if before:
            params['before'] = before
        if limit and limit != 50:
            params['limit'] = limit
        return self.request(route, params=params)

    # Webhook management

    def create_webhook(
        self,
        channel_id: Snowflake,
        *,
        name: str,
        avatar: Optional[bytes] = None,
        reason: Optional[str] = None,
    ) -> Response[webhook.Webhook]:
        payload: Dict[str, Any] = {
            'name': name,
        }
        if avatar is not None:
            payload['avatar'] = avatar

        r = Route('POST', '/channels/{channel_id}/webhooks', channel_id=channel_id)
        return self.request(r, json=payload, reason=reason)

    def channel_webhooks(self, channel_id: Snowflake) -> Response[List[webhook.Webhook]]:
        return self.request(Route('GET', '/channels/{channel_id}/webhooks', channel_id=channel_id))

    def guild_webhooks(self, guild_id: Snowflake) -> Response[List[webhook.Webhook]]:
        return self.request(Route('GET', '/guilds/{guild_id}/webhooks', guild_id=guild_id))

    def get_webhook(self, webhook_id: Snowflake) -> Response[webhook.Webhook]:
        return self.request(Route('GET', '/webhooks/{webhook_id}', webhook_id=webhook_id))

    def follow_webhook(
        self,
        channel_id: Snowflake,
        webhook_channel_id: Snowflake,
        reason: Optional[str] = None,
    ) -> Response[None]:
        r = Route('POST', '/channels/{channel_id}/followers', channel_id=channel_id)
        payload = {
            'webhook_channel_id': str(webhook_channel_id),
        }

        return self.request(r, json=payload, reason=reason)

    # Guild management

    def get_guilds(self, with_counts: bool = True) -> Response[List[guild.Guild]]:
        params = {
            'with_counts': str(with_counts).lower()
        }

        return self.request(Route('GET', '/users/@me/guilds'), params=params, super_properties_to_track=True)

    def leave_guild(self, guild_id: Snowflake, lurking: bool = False) -> Response[None]:
        r = Route('DELETE', '/users/@me/guilds/{guild_id}', guild_id=guild_id)
        payload = {
            'lurking': lurking
        }

        return self.request(r, json=payload)

    def get_guild(self, guild_id: Snowflake, with_counts: bool = True) -> Response[guild.Guild]:
        params = {
            'with_counts': str(with_counts).lower()
        }

        return self.request(Route('GET', '/guilds/{guild_id}', guild_id=guild_id), params=params)

    def delete_guild(self, guild_id: Snowflake) -> Response[None]:
        return self.request(Route('DELETE', '/guilds/{guild_id}', guild_id=guild_id))

    def create_guild(
        self, name: str, icon: Optional[str] = None, *, template: str = '2TffvPucqHkN'
    ) -> Response[guild.Guild]:
        payload = {
            'name': name,
            'icon': icon,
            'system_channel_id': None,
            'channels': [],
            'guild_template_code': template  # API go brrr
        }

        return self.request(Route('POST', '/guilds'), json=payload)

    def edit_guild(self, guild_id: Snowflake, *, reason: Optional[str] = None, **fields: Any) -> Response[guild.Guild]:
        valid_keys = (  # TODO: is this necessary?
            'name',
            'icon',
            'afk_timeout',
            'owner_id',
            'afk_channel_id',
            'splash',
            'discovery_splash',
            'features',
            'verification_level',
            'system_channel_id',
            'default_message_notifications',
            'description',
            'explicit_content_filter',
            'banner',
            'system_channel_flags',
            'rules_channel_id',
            'public_updates_channel_id',
            'preferred_locale',
            'premium_progress_bar_enabled',
        )
        payload = {k: v for k, v in fields.items() if k in valid_keys}

        return self.request(Route('PATCH', '/guilds/{guild_id}', guild_id=guild_id), json=payload, reason=reason)

    def edit_guild_settings(self, guild_id: Snowflake, fields):  # TODO: type
        return self.request(Route('PATCH', '/users/@me/guilds/{guild_id}/settings', guild_id=guild_id), json=fields)

    def get_template(self, code: str) -> Response[template.Template]:
        return self.request(Route('GET', '/guilds/templates/{code}', code=code))

    def guild_templates(self, guild_id: Snowflake) -> Response[List[template.Template]]:
        return self.request(Route('GET', '/guilds/{guild_id}/templates', guild_id=guild_id))

    def create_template(self, guild_id: Snowflake, payload: template.CreateTemplate) -> Response[template.Template]:
        return self.request(Route('POST', '/guilds/{guild_id}/templates', guild_id=guild_id), json=payload)

    def sync_template(self, guild_id: Snowflake, code: str) -> Response[template.Template]:
        return self.request(Route('PUT', '/guilds/{guild_id}/templates/{code}', guild_id=guild_id, code=code))

    def edit_template(self, guild_id: Snowflake, code: str, payload) -> Response[template.Template]:
        r = Route('PATCH', '/guilds/{guild_id}/templates/{code}', guild_id=guild_id, code=code)
        valid_keys = (
            'name',
            'description',
        )
        payload = {k: v for k, v in payload.items() if k in valid_keys}

        return self.request(r, json=payload)

    def delete_template(self, guild_id: Snowflake, code: str) -> Response[None]:
        return self.request(Route('DELETE', '/guilds/{guild_id}/templates/{code}', guild_id=guild_id, code=code))

    def create_from_template(self, code: str, name: str, icon: Optional[str]) -> Response[guild.Guild]:
        payload = {
            'name': name,
            'icon': icon,
        }

        return self.request(Route('POST', '/guilds/templates/{code}', code=code), json=payload)

    def get_bans(self, guild_id: Snowflake) -> Response[List[guild.Ban]]:
        return self.request(Route('GET', '/guilds/{guild_id}/bans', guild_id=guild_id))

    def get_ban(self, user_id: Snowflake, guild_id: Snowflake) -> Response[guild.Ban]:
        return self.request(Route('GET', '/guilds/{guild_id}/bans/{user_id}', guild_id=guild_id, user_id=user_id))

    def get_vanity_code(self, guild_id: Snowflake) -> Response[invite.VanityInvite]:
        return self.request(Route('GET', '/guilds/{guild_id}/vanity-url', guild_id=guild_id))

    def change_vanity_code(self, guild_id: Snowflake, code: str, *, reason: Optional[str] = None) -> Response[None]:
        payload = {
            'code': code
        }

        return self.request(Route('PATCH', '/guilds/{guild_id}/vanity-url', guild_id=guild_id), json=payload, reason=reason)

    def get_all_guild_channels(self, guild_id: Snowflake) -> Response[List[guild.GuildChannel]]:
        return self.request(Route('GET', '/guilds/{guild_id}/channels', guild_id=guild_id))

    def get_member(self, guild_id: Snowflake, member_id: Snowflake) -> Response[member.MemberWithUser]:
        return self.request(Route('GET', '/guilds/{guild_id}/members/{member_id}', guild_id=guild_id, member_id=member_id))

    def prune_members(
        self,
        guild_id: Snowflake,
        days: int,
        compute_prune_count: bool,
        roles: List[str],
        *,
        reason: Optional[str] = None,
    ) -> Response[guild.GuildPrune]:
        payload: Dict[str, Any] = {
            'days': days,
            'compute_prune_count': str(compute_prune_count).lower(),
        }
        if roles:
            payload['include_roles'] = ', '.join(roles)

        return self.request(Route('POST', '/guilds/{guild_id}/prune', guild_id=guild_id), json=payload, reason=reason)

    def estimate_pruned_members(
        self,
        guild_id: Snowflake,
        days: int,
        roles: List[str],
    ) -> Response[guild.GuildPrune]:
        params: Dict[str, Any] = {
            'days': days,
        }
        if roles:
            params['include_roles'] = ', '.join(roles)

        return self.request(Route('GET', '/guilds/{guild_id}/prune', guild_id=guild_id), params=params)

    def get_sticker(self, sticker_id: Snowflake) -> Response[sticker.Sticker]:
        return self.request(Route('GET', '/stickers/{sticker_id}', sticker_id=sticker_id))

    def list_premium_sticker_packs(
        self, country: str = 'US', locale: str = 'en-US', payment_source_id: Snowflake = MISSING
    ) -> Response[sticker.ListPremiumStickerPacks]:
        params: Dict[str, Snowflake] = {
            'country_code': country,
            'locale': locale,
        }
        if payment_source_id is not MISSING:
            params['payment_source_id'] = payment_source_id

        return self.request(Route('GET', '/sticker-packs'), params=params)

    def get_sticker_pack(self, pack_id: Snowflake):
        return self.request(Route('GET', '/sticker-packs/{pack_id}', pack_id=pack_id), auth=False)

    def get_all_guild_stickers(self, guild_id: Snowflake) -> Response[List[sticker.GuildSticker]]:
        return self.request(Route('GET', '/guilds/{guild_id}/stickers', guild_id=guild_id))

    def get_guild_sticker(self, guild_id: Snowflake, sticker_id: Snowflake) -> Response[sticker.GuildSticker]:
        r = Route('GET', '/guilds/{guild_id}/stickers/{sticker_id}', guild_id=guild_id, sticker_id=sticker_id)
        return self.request(r)

    def create_guild_sticker(
        self, guild_id: Snowflake, payload: sticker.CreateGuildSticker, file: File, reason: str
    ) -> Response[sticker.GuildSticker]:
        initial_bytes = file.fp.read(16)

        try:
            mime_type = utils._get_mime_type_for_image(initial_bytes)
        except InvalidArgument:
            if initial_bytes.startswith(b'{'):
                mime_type = 'application/json'
            else:
                mime_type = 'application/octet-stream'
        finally:
            file.reset()

        form: List[Dict[str, Any]] = [
            {
                'name': 'file',
                'value': file.fp,
                'filename': file.filename,
                'content_type': mime_type,
            }
        ]

        for k, v in payload.items():
            form.append(
                {
                    'name': k,
                    'value': v,
                }
            )

        return self.request(
            Route('POST', '/guilds/{guild_id}/stickers', guild_id=guild_id), form=form, files=[file], reason=reason
        )

    def modify_guild_sticker(
        self, guild_id: Snowflake, sticker_id: Snowflake, payload: sticker.EditGuildSticker, reason: Optional[str],
    ) -> Response[sticker.GuildSticker]:
        return self.request(
            Route('PATCH', '/guilds/{guild_id}/stickers/{sticker_id}', guild_id=guild_id, sticker_id=sticker_id),
            json=payload,
            reason=reason,
        )

    def delete_guild_sticker(self, guild_id: Snowflake, sticker_id: Snowflake, reason: Optional[str]) -> Response[None]:
        return self.request(
            Route('DELETE', '/guilds/{guild_id}/stickers/{sticker_id}', guild_id=guild_id, sticker_id=sticker_id),
            reason=reason,
        )

    def get_all_custom_emojis(self, guild_id: Snowflake) -> Response[List[emoji.Emoji]]:
        return self.request(Route('GET', '/guilds/{guild_id}/emojis', guild_id=guild_id))

    def get_custom_emoji(self, guild_id: Snowflake, emoji_id: Snowflake) -> Response[emoji.Emoji]:
        return self.request(Route('GET', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id))

    def create_custom_emoji(
        self,
        guild_id: Snowflake,
        name: str,
        image: bytes,
        *,
        roles: Optional[SnowflakeList] = None,
        reason: Optional[str] = None,
    ) -> Response[emoji.Emoji]:
        payload = {
            'name': name,
            'image': image,
        }
        if roles:
            payload['roles'] = roles

        r = Route('POST', '/guilds/{guild_id}/emojis', guild_id=guild_id)
        return self.request(r, json=payload, reason=reason)

    def delete_custom_emoji(
        self,
        guild_id: Snowflake,
        emoji_id: Snowflake,
        *,
        reason: Optional[str] = None,
    ) -> Response[None]:
        r = Route('DELETE', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id)
        return self.request(r, reason=reason)

    def edit_custom_emoji(
        self,
        guild_id: Snowflake,
        emoji_id: Snowflake,
        *,
        payload: Dict[str, Any],  # TODO: Is this cheating?
        reason: Optional[str] = None,
    ) -> Response[emoji.Emoji]:
        r = Route('PATCH', '/guilds/{guild_id}/emojis/{emoji_id}', guild_id=guild_id, emoji_id=emoji_id)
        return self.request(r, json=payload, reason=reason)

    def get_member_verification(
        self, guild_id: Snowflake, *, with_guild: bool = False, invite: str = MISSING
    ):  # TODO: return type
        params = {
            'with_guild': str(with_guild).lower(),
        }
        if invite is not MISSING:
            params['invite_code'] = invite

        return self.request(Route('GET', '/guilds/{guild_id}/member-verification', guild_id=guild_id), params=params)

    def accept_member_verification(self, guild_id: Snowflake, **payload) -> Response[None]:  # payload is the same as the above return type
        return self.request(Route('PUT', '/guilds/{guild_id}/requests/@me', guild_id=guild_id), json=payload)

    def get_all_integrations(
        self, guild_id: Snowflake, include_applications: bool = True
    ) -> Response[List[integration.Integration]]:
        r = Route('GET', '/guilds/{guild_id}/integrations', guild_id=guild_id)
        params = {
            'include_applications': str(include_applications).lower(),
        }

        return self.request(r, params=params)

    def create_integration(self, guild_id: Snowflake, type: integration.IntegrationType, id: int) -> Response[None]:
        r = Route('POST', '/guilds/{guild_id}/integrations', guild_id=guild_id)
        payload = {
            'type': type,
            'id': id,
        }

        return self.request(r, json=payload)

    def edit_integration(self, guild_id: Snowflake, integration_id: Snowflake, **payload: Any) -> Response[None]:
        r = Route(
            'PATCH', '/guilds/{guild_id}/integrations/{integration_id}', guild_id=guild_id, integration_id=integration_id
        )
        return self.request(r, json=payload)

    def sync_integration(self, guild_id: Snowflake, integration_id: Snowflake) -> Response[None]:
        r = Route(
            'POST', '/guilds/{guild_id}/integrations/{integration_id}/sync', guild_id=guild_id, integration_id=integration_id
        )
        return self.request(r)

    def delete_integration(
        self, guild_id: Snowflake, integration_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        r = Route(
            'DELETE', '/guilds/{guild_id}/integrations/{integration_id}', guild_id=guild_id, integration_id=integration_id
        )
        return self.request(r, reason=reason)

    def get_audit_logs(
        self,
        guild_id: Snowflake,
        limit: int = 100,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        user_id: Optional[Snowflake] = None,
        action_type: Optional[AuditLogAction] = None,
    ) -> Response[audit_log.AuditLog]:
        r = Route('GET', '/guilds/{guild_id}/audit-logs', guild_id=guild_id)
        params: Dict[str, Any] = {
            'limit': limit
        }
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        if user_id:
            params['user_id'] = user_id
        if action_type:
            params['action_type'] = action_type

        return self.request(r, params=params)

    def get_widget(self, guild_id: Snowflake) -> Response[widget.Widget]:
        return self.request(Route('GET', '/guilds/{guild_id}/widget.json', guild_id=guild_id))

    def edit_widget(self, guild_id: Snowflake, payload) -> Response[widget.WidgetSettings]:
        return self.request(Route('PATCH', '/guilds/{guild_id}/widget', guild_id=guild_id), json=payload)

    def get_welcome_screen(self, guild_id: Snowflake) -> Response[welcome_screen.WelcomeScreen]:
        return self.request(Route('GET', '/guilds/{guild_id}/welcome-screen', guild_id=guild_id))

    def edit_welcome_screen(self, guild_id: Snowflake, payload) -> Response[welcome_screen.WelcomeScreen]:
        return self.request(Route('PATCH', '/guilds/{guild_id}/welcome-screen', guild_id=guild_id), json=payload)

    # Invite management

    def accept_invite(
        self,
        invite_id: str,
        type: InviteType,
        *,
        guild_id: Snowflake = MISSING,
        channel_id: Snowflake = MISSING,
        channel_type: ChannelType = MISSING,
        message: Message = MISSING,
    ):  # TODO: response type
        if message is not MISSING:  # Invite Button Embed
            props = ContextProperties._from_invite_embed(
                guild_id=getattr(message.guild, 'id', None),
                channel_id=message.channel.id,
                channel_type=getattr(message.channel, 'type', None),
                message_id=message.id
            )
        elif type is InviteType.guild or type is InviteType.group_dm:  # Join Guild, Accept Invite Page
            props = choice((
                ContextProperties._from_accept_invite_page(guild_id=guild_id, channel_id=channel_id, channel_type=channel_type),
                ContextProperties._from_join_guild_popup(guild_id=guild_id, channel_id=channel_id, channel_type=channel_type)
            ))
        else:  # Accept Invite Page
            props = ContextProperties._from_accept_invite_page(guild_id=guild_id, channel_id=channel_id, channel_type=channel_type)
        return self.request(Route('POST', '/invites/{invite_id}', invite_id=invite_id), context_properties=props, json={})

    def create_invite(
        self,
        channel_id: Snowflake,
        *,
        reason: Optional[str] = None,
        max_age: int = 0,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        target_type: Optional[invite.InviteTargetType] = None,
        target_user_id: Optional[Snowflake] = None,
        target_application_id: Optional[Snowflake] = None,
    ) -> Response[invite.Invite]:
        r = Route('POST', '/channels/{channel_id}/invites', channel_id=channel_id)
        payload = {
            'max_age': max_age,
            'max_uses': max_uses,
            'temporary': temporary,
            'unique': unique,
        }
        if target_type:
            payload['target_type'] = target_type
        if target_user_id:
            payload['target_user_id'] = target_user_id
        if target_application_id:
            payload['target_application_id'] = str(target_application_id)

        return self.request(r, reason=reason, json=payload)

    def create_group_invite(self, channel_id: Snowflake, *, max_age: int = 86400) -> Response[invite.Invite]:
        payload = {
            'max_age': max_age,
        }

        return self.request(Route('POST', '/channels/{channel_id}/invites', channel_id=channel_id), json=payload)

    def get_invite(
        self, invite_id: str, *, with_counts: bool = True, with_expiration: bool = True
    ) -> Response[invite.Invite]:
        params = {
            'inputValue': invite_id,
            'with_counts': str(with_counts),
            'with_expiration': str(with_expiration),
        }

        return self.request(Route('GET', '/invites/{invite_id}', invite_id=invite_id), params=params)

    def invites_from(self, guild_id: Snowflake) -> Response[List[invite.Invite]]:
        return self.request(Route('GET', '/guilds/{guild_id}/invites', guild_id=guild_id))

    def invites_from_channel(self, channel_id: Snowflake) -> Response[List[invite.Invite]]:
        return self.request(Route('GET', '/channels/{channel_id}/invites', channel_id=channel_id))

    def delete_invite(self, invite_id: str, *, reason: Optional[str] = None) -> Response[None]:
        return self.request(Route('DELETE', '/invites/{invite_id}', invite_id=invite_id), reason=reason)

    # Role management

    def get_roles(self, guild_id: Snowflake) -> Response[List[role.Role]]:
        return self.request(Route('GET', '/guilds/{guild_id}/roles', guild_id=guild_id))

    def edit_role(
        self, guild_id: Snowflake, role_id: Snowflake, *, reason: Optional[str] = None, **fields: Any
    ) -> Response[role.Role]:
        r = Route('PATCH', '/guilds/{guild_id}/roles/{role_id}', guild_id=guild_id, role_id=role_id)
        valid_keys = ('name', 'permissions', 'color', 'hoist', 'mentionable', 'icon', 'unicode_emoji')
        payload = {k: v for k, v in fields.items() if k in valid_keys}
        return self.request(r, json=payload, reason=reason)

    def delete_role(self, guild_id: Snowflake, role_id: Snowflake, *, reason: Optional[str] = None) -> Response[None]:
        r = Route('DELETE', '/guilds/{guild_id}/roles/{role_id}', guild_id=guild_id, role_id=role_id)
        return self.request(r, reason=reason)

    def replace_roles(
        self,
        user_id: Snowflake,
        guild_id: Snowflake,
        role_ids: List[int],
        *,
        reason: Optional[str] = None,
    ) -> Response[member.MemberWithUser]:
        return self.edit_member(guild_id=guild_id, user_id=user_id, roles=role_ids, reason=reason)

    def create_role(self, guild_id: Snowflake, *, reason: Optional[str] = None, **fields: Any) -> Response[role.Role]:
        r = Route('POST', '/guilds/{guild_id}/roles', guild_id=guild_id)
        return self.request(r, json=fields, reason=reason)

    def move_role_position(
        self,
        guild_id: Snowflake,
        positions: List[guild.RolePositionUpdate],
        *,
        reason: Optional[str] = None,
    ) -> Response[List[role.Role]]:
        r = Route('PATCH', '/guilds/{guild_id}/roles', guild_id=guild_id)
        return self.request(r, json=positions, reason=reason)

    def add_role(
        self, guild_id: Snowflake, user_id: Snowflake, role_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        r = Route(
            'PUT',
            '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
        )
        return self.request(r, reason=reason)

    def remove_role(
        self, guild_id: Snowflake, user_id: Snowflake, role_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        r = Route(
            'DELETE',
            '/guilds/{guild_id}/members/{user_id}/roles/{role_id}',
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
        )
        return self.request(r, reason=reason)

    def edit_channel_permissions(
        self,
        channel_id: Snowflake,
        target: Snowflake,
        allow: str,
        deny: str,
        type: channel.OverwriteType,
        *,
        reason: Optional[str] = None,
    ) -> Response[None]:
        payload = {'id': target, 'allow': allow, 'deny': deny, 'type': type}
        r = Route('PUT', '/channels/{channel_id}/permissions/{target}', channel_id=channel_id, target=target)
        return self.request(r, json=payload, reason=reason)

    def delete_channel_permissions(
        self, channel_id: Snowflake, target: channel.OverwriteType, *, reason: Optional[str] = None
    ) -> Response[None]:
        r = Route('DELETE', '/channels/{channel_id}/permissions/{target}', channel_id=channel_id, target=target)
        return self.request(r, reason=reason)

    # Voice management

    def move_member(
        self,
        user_id: Snowflake,
        guild_id: Snowflake,
        channel_id: Snowflake,
        *,
        reason: Optional[str] = None,
    ) -> Response[member.MemberWithUser]:
        return self.edit_member(guild_id=guild_id, user_id=user_id, channel_id=channel_id, reason=reason)

    def ring(self, channel_id: Snowflake, *recipients: Snowflake) -> Response[None]:
        payload = {
            'recipients': recipients or None
        }

        return self.request(Route('POST', '/channels/{channel_id}/call/ring', channel_id=channel_id), json=payload)

    def stop_ringing(self, channel_id: Snowflake, *recipients: Snowflake) -> Response[None]:
        r = Route('POST', '/channels/{channel_id}/call/stop-ringing', channel_id=channel_id)
        payload = {
            'recipients': recipients
        }

        return self.request(r, json=payload)

    def change_call_voice_region(self, channel_id: int, voice_region: str):  # TODO: return type
        payload = {
            'region': voice_region
        }

        return self.request(Route('PATCH', '/channels/{channel_id}/call', channel_id=channel_id), json=payload)

    # Stage instance management
    # TODO: Check all :(

    def get_stage_instance(self, channel_id: Snowflake) -> Response[channel.StageInstance]:
        return self.request(Route('GET', '/stage-instances/{channel_id}', channel_id=channel_id))

    def create_stage_instance(self, *, reason: Optional[str], **payload: Any) -> Response[channel.StageInstance]:
        valid_keys = (
            'channel_id',
            'topic',
            'privacy_level',
        )
        payload = {k: v for k, v in payload.items() if k in valid_keys}

        return self.request(Route('POST', '/stage-instances'), json=payload, reason=reason)

    def edit_stage_instance(self, channel_id: Snowflake, *, reason: Optional[str] = None, **payload: Any) -> Response[None]:
        r = Route('PATCH', '/stage-instances/{channel_id}', channel_id=channel_id)
        valid_keys = (
            'topic',
            'privacy_level',
        )
        payload = {k: v for k, v in payload.items() if k in valid_keys}

        return self.request(r, json=payload, reason=reason)

    def delete_stage_instance(self, channel_id: Snowflake, *, reason: Optional[str] = None) -> Response[None]:
        return self.request(Route('DELETE', '/stage-instances/{channel_id}', channel_id=channel_id), reason=reason)

    # Relationships

    def get_relationships(self):  # TODO: return type
        return self.request(Route('GET', '/users/@me/relationships'))

    def remove_relationship(self, user_id: Snowflake, *, action: RelationshipAction) -> Response[None]:
        r = Route('DELETE', '/users/@me/relationships/{user_id}', user_id=user_id)
        if action is RelationshipAction.deny_request:  # User Profile, Friends, DM Channel
            props = choice((
                ContextProperties._from_friends_page(), ContextProperties._from_user_profile(),
                ContextProperties._from_dm_channel()
            ))
        elif action is RelationshipAction.unfriend:  # Friends, ContextMenu, User Profile, DM Channel
            props = choice((
                ContextProperties._from_context_menu(), ContextProperties._from_user_profile(),
                ContextProperties._from_friends_page(), ContextProperties._from_dm_channel()
            ))
        elif action == RelationshipAction.unblock:  # Friends, ContextMenu, User Profile, DM Channel, NONE
            props = choice((
                ContextProperties._from_context_menu(), ContextProperties._from_user_profile(),
                ContextProperties._from_friends_page(), ContextProperties._from_dm_channel(), None
            ))
        elif action == RelationshipAction.remove_pending_request: # Friends
            props = ContextProperties._from_friends_page()

        return self.request(r, context_properties=props)  # type: ignore

    def add_relationship(
        self, user_id: Snowflake, type: int = MISSING, *, action: RelationshipAction
    ):  # TODO: return type
        r = Route('PUT', '/users/@me/relationships/{user_id}', user_id=user_id)
        if action is RelationshipAction.accept_request:  # User Profile, Friends, DM Channel
            props = choice((
                ContextProperties._from_friends_page(),
                ContextProperties._from_user_profile(),
                ContextProperties._from_dm_channel()
            ))
        elif action is RelationshipAction.block:  # Friends, ContextMenu, User Profile, DM Channel.
            props = choice((
                ContextProperties._from_context_menu(),
                ContextProperties._from_user_profile(),
                ContextProperties._from_friends_page(),
                ContextProperties._from_dm_channel()
            ))
        elif action is RelationshipAction.send_friend_request:  # ContextMenu, User Profile, DM Channel
            props = choice((
                ContextProperties._from_context_menu(),
                ContextProperties._from_user_profile(),
                ContextProperties._from_dm_channel()
            ))
        kwargs = {
            'context_properties': props  # type: ignore
        }
        if type:
            kwargs['json'] = {'type': type}

        return self.request(r, **kwargs)

    def send_friend_request(self, username, discriminator):  # TODO: return type
        r = Route('POST', '/users/@me/relationships')
        props = choice((  # Friends, Group DM
            ContextProperties._from_add_friend_page,
            ContextProperties._from_group_dm
        ))
        payload = {
            'username': username,
            'discriminator': int(discriminator)
        }

        return self.request(r, json=payload, context_properties=props)

    def change_friend_nickname(self, user_id, nickname):
        payload = {
            'nickname': nickname
        }

        return self.request(Route('PATCH', '/users/@me/relationships/{user_id}', user_id=user_id), json=payload)

    # Misc

    async def get_gateway(self, *, encoding: str = 'json', zlib: bool = True) -> str:
        # The gateway URL hasn't changed for over 5 years
        # And, the official clients aren't GETting it anymore, sooooo...
        self.zlib = zlib
        if zlib:
            value = 'wss://gateway.discord.gg?encoding={0}&v=9&compress=zlib-stream'
        else:
            value = 'wss://gateway.discord.gg?encoding={0}&v=9'

        return value.format(encoding)

    def get_user(self, user_id: Snowflake) -> Response[user.User]:
        return self.request(Route('GET', '/users/{user_id}', user_id=user_id))

    def get_user_profile(self, user_id: Snowflake, guild_id: Snowflake = MISSING, *, with_mutual_guilds: bool = True):  # TODO: return type
        params: Dict[str, Any] = {
            'with_mutual_guilds': str(with_mutual_guilds).lower()
        }
        if guild_id is not MISSING:
            params['guild_id'] = guild_id

        return self.request(Route('GET', '/users/{user_id}/profile', user_id=user_id), params=params)

    def get_mutual_friends(self, user_id: Snowflake):  # TODO: return type
        return self.request(Route('GET', '/users/{user_id}/relationships', user_id=user_id))

    def get_notes(self):  # TODO: return type
        return self.request(Route('GET', '/users/@me/notes'))

    def get_note(self, user_id: Snowflake):  # TODO: return type
        return self.request(Route('GET', '/users/@me/notes/{user_id}', user_id=user_id))

    def set_note(self, user_id: Snowflake, *, note: Optional[str] = None) -> Response[None]:
        payload = {
            'note': note or ''
        }

        return self.request(Route('PUT', '/users/@me/notes/{user_id}', user_id=user_id), json=payload)

    def change_hypesquad_house(self, house_id: int) -> Response[None]:
        payload = {
            'house_id': house_id
        }

        return self.request(Route('POST', '/hypesquad/online'), json=payload)

    def leave_hypesquad_house(self) -> Response[None]:
        return self.request(Route('DELETE', '/hypesquad/online'))

    def get_settings(self):  # TODO: return type
        return self.request(Route('GET', '/users/@me/settings'))

    def edit_settings(self, **payload):  # TODO: return type, is this cheating?
        return self.request(Route('PATCH', '/users/@me/settings'), json=payload)

    def get_tracking(self): # TODO: return type
        return self.request(Route('GET', '/users/@me/consent'))

    def edit_tracking(self, payload):
        return self.request(Route('POST', '/users/@me/consent'), json=payload)

    def get_connections(self):
        return self.request(Route('GET', '/users/@me/connections'))

    def edit_connection(self, type, id, **payload):
        return self.request(Route('PATCH', '/users/@me/connections/{type}/{id}', type=type, id=id), json=payload)

    def delete_connection(self, type, id):
        return self.request(Route('DELETE', '/users/@me/connections/{type}/{id}', type=type, id=id))

    def get_my_applications(self, *, with_team_applications: bool = True) -> Response[List[appinfo.AppInfo]]:
        params = {
            'with_team_applications': str(with_team_applications).lower()
        }

        return self.request(Route('GET', '/applications'), params=params, super_properties_to_track=True)

    def get_my_application(self, app_id: Snowflake) -> Response[appinfo.AppInfo]:
        return self.request(Route('GET', '/applications/{app_id}', app_id=app_id), super_properties_to_track=True)

    def edit_application(self, app_id: Snowflake, payload) -> Response[appinfo.AppInfo]:
        return self.request(Route('PATCH', '/applications/{app_id}', app_id=app_id), super_properties_to_track=True, json=payload)

    def delete_application(self, app_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/applications/{app_id}/delete', app_id=app_id), super_properties_to_track=True)

    def transfer_application(self, app_id: Snowflake, team_id: Snowflake) -> Response[appinfo.AppInfo]:
        payload = {
            'team_id': team_id
        }

        return self.request(Route('POST', '/applications/{app_id}/transfer', app_id=app_id), json=payload, super_properties_to_track=True)

    def get_partial_application(self, app_id: Snowflake) -> Response[appinfo.PartialAppInfo]:
        return self.request(Route('GET', '/applications/{app_id}/rpc', app_id=app_id), auth=False)

    def create_app(self, name: str):
        payload = {
            'name': name
        }

        return self.request(Route('POST', '/applications'), json=payload, super_properties_to_track=True)

    def get_app_entitlements(self, app_id: Snowflake):  # TODO: return type
        r = Route('GET', '/users/@me/applications/{app_id}/entitlements', app_id=app_id)
        return self.request(r, super_properties_to_track=True)

    def get_app_skus(
        self, app_id: Snowflake, *, localize: bool = False, with_bundled_skus: bool = True
    ):  # TODO: return type
        r = Route('GET', '/applications/{app_id}/skus', app_id=app_id)
        params = {
            'localize': str(localize).lower(),
            'with_bundled_skus': str(with_bundled_skus).lower()
        }

        return self.request(r, params=params, super_properties_to_track=True)

    def get_app_whitelist(self, app_id):
        return self.request(Route('GET', '/oauth2/applications/{app_id}/allowlist', app_id=app_id), super_properties_to_track=True)

    def create_team(self, name: str):
        payload = {
            'name': name
        }

        return self.request(Route('POST', '/teams'), json=payload, super_properties_to_track=True)

    def get_teams(self) -> Response[List[team.Team]]:
        return self.request(Route('GET', '/teams'), super_properties_to_track=True)

    def get_team(self, team_id: Snowflake) -> Response[team.Team]:
        return self.request(Route('GET', '/teams/{team_id}', team_id=team_id), super_properties_to_track=True)

    def edit_team(self, team_id: Snowflake, payload) -> Response[team.Team]:
        return self.request(Route('PATCH', '/teams/{team_id}', team_id=team_id), json=payload, super_properties_to_track=True)

    def delete_application(self, team_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/teams/{app_id}/delete', team_id=team_id), super_properties_to_track=True)

    def get_team_applications(self, team_id: Snowflake) -> Response[List[appinfo.AppInfo]]:
        return self.request(Route('GET', '/teams/{team_id}/applications', team_id=team_id), super_properties_to_track=True)

    def get_team_members(self, team_id: Snowflake) -> Response[List[team.TeamMember]]:
        return self.request(Route('GET', '/teams/{team_id}/members', team_id=team_id), super_properties_to_track=True)

    def invite_team_member(self, team_id: Snowflake, username: str, discriminator: Snowflake):
        payload = {
            'username': username,
            'discriminator': str(discriminator)
        }

        return self.request(Route('POST', '/teams/{team_id}/members', team_id=team_id), json=payload, super_properties_to_track=True)

    def remove_team_member(self, team_id: Snowflake, user_id: Snowflake):
        return self.request(Route('DELETE', '/teams/{team_id}/members/{user_id}', team_id=team_id, user_id=user_id), super_properties_to_track=True)

    def botify_app(self, app_id: Snowflake):
        return self.request(Route('POST', '/applications/{app_id}/bot', app_id=app_id), super_properties_to_track=True)

    def reset_secret(self, app_id: Snowflake) -> Response[appinfo.AppInfo]:
        return self.request(Route('POST', '/applications/{app_id}/reset', app_id=app_id), super_properties_to_track=True)

    def reset_token(self, app_id: Snowflake):
        return self.request(Route('POST', '/applications/{app_id}/bot/reset', app_id=app_id), super_properties_to_track=True)

    def mobile_report(  # Report v1
        self, guild_id: Snowflake, channel_id: Snowflake, message_id: Snowflake, reason: str
    ):  # TODO: return type
        payload = {
            'guild_id': guild_id,
            'channel_id': channel_id,
            'message_id': message_id,
            'reason': reason
        }

        return self.request(Route('POST', '/report'), json=payload)

    def get_application_commands(self, id):
        return self.request(Route('GET', '/applications/{user_id}/commands', user_id=id))

    def interact(self, payload, *, form_data=False) -> Response[None]:
        if form_data:
            form = [{'name': 'payload_json', 'value': utils._to_json(payload)}]
            return self.request(Route('POST', '/interactions'), form=form)
        else:
            return self.request(Route('POST', '/interactions'), json=payload)
