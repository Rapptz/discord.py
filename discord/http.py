# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

import aiohttp
import asyncio
import json
import sys
import logging
import inspect
import weakref
from random import randint as random_integer

log = logging.getLogger(__name__)

from .errors import HTTPException, Forbidden, NotFound, LoginFailure, GatewayNotFound
from . import utils, __version__

@asyncio.coroutine
def json_or_text(response):
    text = yield from response.text(encoding='utf-8')
    if response.headers['content-type'] == 'application/json':
        return json.loads(text)
    return text

def _func_():
    # emulate __func__ from C++
    return inspect.currentframe().f_back.f_code.co_name

class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Discord API."""

    BASE          = 'https://discordapp.com'
    API_BASE      = BASE     + '/api/v6'
    GATEWAY       = API_BASE + '/gateway'
    USERS         = API_BASE + '/users'
    ME            = USERS    + '/@me'
    REGISTER      = API_BASE + '/auth/register'
    LOGIN         = API_BASE + '/auth/login'
    LOGOUT        = API_BASE + '/auth/logout'
    GUILDS        = API_BASE + '/guilds'
    CHANNELS      = API_BASE + '/channels'
    APPLICATIONS  = API_BASE + '/oauth2/applications'

    SUCCESS_LOG = '{method} {url} has received {text}'
    REQUEST_LOG = '{method} {url} with {json} has returned {status}'

    def __init__(self, connector=None, *, loop=None):
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.connector = connector
        self.session = aiohttp.ClientSession(connector=connector, loop=self.loop)
        self._locks = weakref.WeakValueDictionary()
        self.token = None
        self.bot_token = False

        user_agent = 'DiscordBot (https://github.com/Rapptz/discord.py {0}) Python/{1[0]}.{1[1]} aiohttp/{2}'
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)

    @asyncio.coroutine
    def request(self, method, url, *, bucket=None, **kwargs):
        lock = self._locks.get(bucket)
        if lock is None:
            lock = asyncio.Lock(loop=self.loop)
            if bucket is not None:
                self._locks[bucket] = lock

        # header creation
        headers = {
            'User-Agent': self.user_agent,
        }

        if self.token is not None:
            headers['Authorization'] = 'Bot ' + self.token if self.bot_token else self.token

        # some checking if it's a JSON request
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = utils.to_json(kwargs.pop('json'))

        kwargs['headers'] = headers
        with (yield from lock):
            for tries in range(5):
                r = yield from self.session.request(method, url, **kwargs)
                log.debug(self.REQUEST_LOG.format(method=method, url=url, status=r.status, json=kwargs.get('data')))
                try:
                    # even errors have text involved in them so this is safe to call
                    data = yield from json_or_text(r)

                    # the request was successful so just return the text/json
                    if 300 > r.status >= 200:
                        log.debug(self.SUCCESS_LOG.format(method=method, url=url, text=data))
                        return data

                    # we are being rate limited
                    if r.status == 429:
                        fmt = 'We are being rate limited. Retrying in {:.2} seconds. Handled under the bucket "{}"'

                        # sleep a bit
                        retry_after = data['retry_after'] / 1000.0
                        log.info(fmt.format(retry_after, bucket))
                        yield from asyncio.sleep(retry_after)
                        continue

                    # we've received a 502, unconditional retry
                    if r.status == 502 and tries <= 5:
                        yield from asyncio.sleep(1 + tries * 2)
                        continue

                    # the usual error cases
                    if r.status == 403:
                        raise Forbidden(r, data)
                    elif r.status == 404:
                        raise NotFound(r, data)
                    else:
                        raise HTTPException(r, data)
                finally:
                    # clean-up just in case
                    yield from r.release()

    def get(self, *args, **kwargs):
        return self.request('GET', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('PUT', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('PATCH', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('DELETE', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('POST', *args, **kwargs)

    # state management

    @asyncio.coroutine
    def close(self):
        yield from self.session.close()

    def recreate(self):
        self.session = aiohttp.ClientSession(connector=self.connector, loop=self.loop)

    def _token(self, token, *, bot=True):
        self.token = token
        self.bot_token = bot

    # login management

    @asyncio.coroutine
    def email_login(self, email, password):
        payload = {
            'email': email,
            'password': password
        }

        try:
            data = yield from self.post(self.LOGIN, json=payload, bucket=_func_())
        except HTTPException as e:
            if e.response.status == 400:
                raise LoginFailure('Improper credentials have been passed.') from e
            raise

        self._token(data['token'], bot=False)
        return data

    @asyncio.coroutine
    def static_login(self, token, *, bot):
        old_token, old_bot = self.token, self.bot_token
        self._token(token, bot=bot)

        try:
            data = yield from self.get(self.ME)
        except HTTPException as e:
            self._token(old_token, bot=old_bot)
            if e.response.status == 401:
                raise LoginFailure('Improper token has been passed.') from e
            raise e

        return data

    def logout(self):
        return self.post(self.LOGOUT, bucket=_func_())

    # Message management

    def start_private_message(self, user_id):
        payload = {
            'recipient_id': user_id
        }

        return self.post(self.ME + '/channels', json=payload, bucket=_func_())

    def send_message(self, channel_id, content, *, guild_id=None, tts=False):
        url = '{0.CHANNELS}/{1}/messages'.format(self, channel_id)
        payload = {
            'content': str(content),
            'nonce': random_integer(-2**63, 2**63 - 1)
        }

        if tts:
            payload['tts'] = True

        return self.post(url, json=payload, bucket='messages:' + str(guild_id))

    def send_typing(self, channel_id):
        url = '{0.CHANNELS}/{1}/typing'.format(self, channel_id)
        return self.post(url, bucket=_func_())

    def send_file(self, channel_id, buffer, *, guild_id=None, filename=None, content=None, tts=False):
        url = '{0.CHANNELS}/{1}/messages'.format(self, channel_id)
        form = aiohttp.FormData()

        if content is not None:
            form.add_field('content', str(content))

        form.add_field('tts', 'true' if tts else 'false')
        form.add_field('file', buffer, filename=filename, content_type='application/octet-stream')

        return self.post(url, data=form, bucket='messages:' + str(guild_id))

    def delete_message(self, channel_id, message_id, guild_id=None):
        url = '{0.CHANNELS}/{1}/messages/{2}'.format(self, channel_id, message_id)
        bucket = '{}:{}'.format(_func_(), guild_id)
        return self.delete(url, bucket=bucket)

    def delete_messages(self, channel_id, message_ids, guild_id=None):
        url = '{0.CHANNELS}/{1}/messages/bulk_delete'.format(self, channel_id)
        payload = {
            'messages': message_ids
        }
        bucket = '{}:{}'.format(_func_(), guild_id)
        return self.post(url, json=payload, bucket=bucket)

    def edit_message(self, message_id, channel_id, content, *, guild_id=None):
        url = '{0.CHANNELS}/{1}/messages/{2}'.format(self, channel_id, message_id)
        payload = {
            'content': str(content)
        }
        return self.patch(url, json=payload, bucket='messages:' + str(guild_id))

    def get_message(self, channel_id, message_id):
        url = '{0.CHANNELS}/{1}/messages/{2}'.format(self, channel_id, message_id)
        return self.get(url, bucket=_func_())

    def logs_from(self, channel_id, limit, before=None, after=None):
        url = '{0.CHANNELS}/{1}/messages'.format(self, channel_id)
        params = {
            'limit': limit
        }

        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return self.get(url, params=params, bucket=_func_())

    def pin_message(self, channel_id, message_id):
        url = '{0.CHANNELS}/{1}/pins/{2}'.format(self, channel_id, message_id)
        return self.put(url, bucket=_func_())

    def unpin_message(self, channel_id, message_id):
        url = '{0.CHANNELS}/{1}/pins/{2}'.format(self, channel_id, message_id)
        return self.delete(url, bucket=_func_())

    def pins_from(self, channel_id):
        url = '{0.CHANNELS}/{1}/pins'.format(self, channel_id)
        return self.get(url, bucket=_func_())

    # Member management

    def kick(self, user_id, guild_id):
        url = '{0.GUILDS}/{1}/members/{2}'.format(self, guild_id, user_id)
        return self.delete(url, bucket=_func_())

    def ban(self, user_id, guild_id, delete_message_days=1):
        url = '{0.GUILDS}/{1}/bans/{2}'.format(self, guild_id, user_id)
        params = {
            'delete-message-days': delete_message_days
        }
        return self.put(url, params=params, bucket=_func_())

    def unban(self, user_id, guild_id):
        url = '{0.GUILDS}/{1}/bans/{2}'.format(self, guild_id, user_id)
        return self.delete(url, bucket=_func_())

    def server_voice_state(self, user_id, guild_id, *, mute=None, deafen=None):
        url = '{0.GUILDS}/{1}/members/{2}'.format(self, guild_id, user_id)
        payload = {}
        if mute is not None:
            payload['mute'] = mute

        if deafen is not None:
            payload['deaf'] = deafen

        return self.patch(url, json=payload, bucket='members:' + str(guild_id))

    def edit_profile(self, password, username, avatar, **fields):
        payload = {
            'password': password,
            'username': username,
            'avatar': avatar
        }

        if 'email' in fields:
            payload['email'] = fields['email']

        if 'new_password' in fields:
            payload['new_password'] = fields['new_password']

        return self.patch(self.ME, json=payload, bucket=_func_())

    def change_my_nickname(self, guild_id, nickname):
        url = '{0.GUILDS}/{1}/members/@me/nick'.format(self, guild_id)
        payload = {
            'nick': nickname
        }
        bucket = '{}:{}'.format(_func_(), guild_id)
        return self.patch(url, json=payload, bucket=bucket)

    def change_nickname(self, guild_id, user_id, nickname):
        url = '{0.GUILDS}/{1}/members/{2}'.format(self, guild_id, user_id)
        payload = {
            'nick': nickname
        }
        bucket = 'members:{}'.format(guild_id)
        return self.patch(url, json=payload, bucket=bucket)

    # Channel management

    def edit_channel(self, channel_id, **options):
        url = '{0.CHANNELS}/{1}'.format(self, channel_id)

        valid_keys = ('name', 'topic', 'bitrate', 'user_limit', 'position')
        payload = {
            k: v for k, v in options.items() if k in valid_keys
        }

        return self.patch(url, json=payload, bucket=_func_())

    def create_channel(self, guild_id, name, channe_type, permission_overwrites=None):
        url = '{0.GUILDS}/{1}/channels'.format(self, guild_id)
        payload = {
            'name': name,
            'type': channe_type
        }

        if permission_overwrites is not None:
            payload['permission_overwrites'] = permission_overwrites

        return self.post(url, json=payload, bucket=_func_())

    def delete_channel(self, channel_id):
        url = '{0.CHANNELS}/{1}'.format(self, channel_id)
        return self.delete(url, bucket=_func_())

    # Server management

    def leave_server(self, guild_id):
        url = '{0.USERS}/@me/guilds/{1}'.format(self, guild_id)
        return self.delete(url, bucket=_func_())

    def delete_server(self, guild_id):
        url = '{0.GUILDS}/{1}'.format(self, guild_id)
        return self.delete(url, bucket=_func_())

    def create_server(self, name, region, icon):
        payload = {
            'name': name,
            'icon': icon,
            'region': region
        }

        return self.post(self.GUILDS, json=payload, bucket=_func_())

    def edit_server(self, guild_id, **fields):
        valid_keys = ('name', 'region', 'icon', 'afk_timeout', 'owner_id',
                      'afk_channel_id', 'splash', 'verification_level')

        payload = {
            k: v for k, v in fields.items() if k in valid_keys
        }

        url = '{0.GUILDS}/{1}'.format(self, guild_id)
        return self.patch(url, json=payload, bucket=_func_())

    def get_bans(self, guild_id):
        url = '{0.GUILDS}/{1}/bans'.format(self, guild_id)
        return self.get(url, bucket=_func_())

    def prune_members(self, guild_id, days):
        url = '{0.GUILDS}/{1}/prune'.format(self, guild_id)
        params = {
            'days': days
        }
        return self.post(url, params=params, bucket=_func_())

    def estimate_pruned_members(self, guild_id, days):
        url = '{0.GUILDS}/{1}/prune'.format(self, guild_id)
        params = {
            'days': days
        }
        return self.get(url, params=params, bucket=_func_())

    # Invite management

    def create_invite(self, channel_id, **options):
        url = '{0.CHANNELS}/{1}/invites'.format(self, channel_id)
        payload = {
            'max_age': options.get('max_age', 0),
            'max_uses': options.get('max_uses', 0),
            'temporary': options.get('temporary', False),
            'xkcdpass': options.get('xkcd', False)
        }

        return self.post(url, json=payload, bucket=_func_())

    def get_invite(self, invite_id):
        url = '{0.API_BASE}/invite/{1}'.format(self, invite_id)
        return self.get(url, bucket=_func_())

    def invites_from(self, guild_id):
        url = '{0.GUILDS}/{1}/invites'.format(self, guild_id)
        return self.get(url, bucket=_func_())

    def accept_invite(self, invite_id):
        url = '{0.API_BASE}/invite/{1}'.format(self, invite_id)
        return self.post(url, bucket=_func_())

    def delete_invite(self, invite_id):
        url = '{0.API_BASE}/invite/{1}'.format(self, invite_id)
        return self.delete(url, bucket=_func_())

    # Role management

    def edit_role(self, guild_id, role_id, **fields):
        url = '{0.GUILDS}/{1}/roles/{2}'.format(self, guild_id, role_id)
        valid_keys = ('name', 'permissions', 'color', 'hoist', 'mentionable')
        payload = {
            k: v for k, v in fields.items() if k in valid_keys
        }
        return self.patch(url, json=payload, bucket='roles:' + str(guild_id))

    def delete_role(self, guild_id, role_id):
        url = '{0.GUILDS}/{1}/roles/{2}'.format(self, guild_id, role_id)
        return self.delete(url, bucket=_func_())

    def replace_roles(self, user_id, guild_id, role_ids):
        url = '{0.GUILDS}/{1}/members/{2}'.format(self, guild_id, user_id)
        payload = {
            'roles': role_ids
        }
        return self.patch(url, json=payload, bucket='members:' + str(guild_id))

    def create_role(self, guild_id):
        url = '{0.GUILDS}/{1}/roles'.format(self, guild_id)
        return self.post(url, bucket=_func_())

    def edit_channel_permissions(self, channel_id, target, allow, deny, type):
        url = '{0.CHANNELS}/{1}/permissions/{2}'.format(self, channel_id, target)
        payload = {
            'id': target,
            'allow': allow,
            'deny': deny,
            'type': type
        }
        return self.put(url, json=payload, bucket=_func_())

    def delete_channel_permissions(self, channel_id, target):
        url = '{0.CHANNELS}/{1}/permissions/{2}'.format(self, channel_id, target)
        return self.delete(url, bucket=_func_())

    # Voice management

    def move_member(self, user_id, guild_id, channel_id):
        url = '{0.GUILDS}/{1}/members/{2}'.format(self, guild_id, user_id)
        payload = {
            'channel_id': channel_id
        }
        return self.patch(url, json=payload, bucket='members:' + str(guild_id))

    # Misc

    def application_info(self):
        url = '{0.APPLICATIONS}/@me'.format(self)
        return self.get(url, bucket=_func_())

    @asyncio.coroutine
    def get_gateway(self):
        try:
            data = yield from self.get(self.GATEWAY, bucket=_func_())
        except HTTPException as e:
            raise GatewayNotFound() from e
        return data.get('url') + '?encoding=json&v=6'

    def get_user_info(self, user_id):
        return self.get('{0.USERS}/{1}'.format(self, user_id), bucket=_func_())
