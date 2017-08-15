from .embeds import Embed
from .mixins import Hashable
from .errors import HTTPException
from .utils import _bytes_to_base64_data
import io
import json
import asyncio

# Webhook code made by Cerulean#7014 

WEBHOOK_BASE = 'https://discordapp.com/api/webhooks/'
AVATAR_BASE = 'https://cdn.discordapp.com/avatars/{id}/{avatar}.png'


class Webhook(Hashable):
    __slots__ = ('name', 'id', 'avatar', 'url', '_state',
                 'webhook', 'token')

    def __init__(self, state, **kwargs):
        self._state = state
        
        self.name = kwargs.get('name',None)
        self.id = kwargs.get('id',0)
        self.token = kwargs.get('token','')
        self.url = WEBHOOK_BASE + '{0.id}/{0.token}'.format(self)
        self.avatar = AVATAR_BASE.format(id=self.id,
                                         avatar=kwargs.get('avatar', ''))
        self.webhook = kwargs  # Anything we didn't get will be in here

    @classmethod
    def _from_data(cls,state,data):
        return cls(state,**data)

    @asyncio.coroutine
    def edit(self,*,update=False,**kwargs):
        """
        Set the webhooks information

        Returns
        ------
            Updated discord.Webhook
        """
        if kwargs.get('name'):
            self.name = kwargs.get('name')
        if kwargs.get('avatar'):
            self.avatar = kwargs.get('avatar')
        if update:
            yield from self.update()  # Updates the webhook
        return self

    @asyncio.coroutine
    def update(self, **kwargs):
        """|coro|
        Updates the webhook
        """
        avatar = self.avatar
        if self.avatar:
            ret = yield from self._state.http._session.request('GET', self.avatar)
            if ret.status not in [200, 204]:
                t = yield from ret.text()
                raise HTTPException(t)
            d = yield from ret.read()
            img = io.BytesIO(d)
            img.seek(0)
            avatar = _bytes_to_base64_data(img.read())

        payload = {
            'name': kwargs.get('name', self.name),
            'avatar': avatar
        }
        
        url = WEBHOOK_BASE + '{webhook_id}/{webhook_token}'.format(webhook_id=self.id, webhook_token=self.token)
        ret = yield from self._state.http._session.request(
                                                           'PATCH',
                                                           url,
                                                           data=json.dumps(payload),
                                                           headers={'Content-Type': 'application/json'}
                                                           )
        yield from ret.json()
        if ret.status not in [200, 204]:
            m = yield from ret.text()
            raise HTTPException(ret, message=m)

        new = self.webhook.copy()
        new.update(kwargs)
        Webhook.__init__(self, self._state, **new)
        return self

    @asyncio.coroutine
    def make_request(self, method, data):
        """|coro|
        Send data to discord

        Has to use a different system than discord.py because of how different webhooks
        are to the main client.

        Danny, if you don't like how I did this, feel free to change it. I feel like I could
        Have done better TBH
        """
        data['username'] = self.name
        data['avatar_url'] = self.avatar
        data['embeds_cache'] = []
        if data.get('embeds') and isinstance(data.get('embeds'),list):
            for em in data['embeds']:
                if isinstance(em,Embed):
                    data['embeds_cache'].append(em.to_dict())
        elif isinstance(data.get('embeds'), Embed):
            data['embeds_cache'] = [data['embeds'].to_dict()]
        data['embeds'] = data['embeds_cache']
        del data['embeds_cache']
        ret = yield from self._state.http._session.request(method,
                                                           self.url,
                                                           data=json.dumps(data),
                                                           headers={'content-type': 'application/json'})
        if ret.status not in [200,204]:
            m = yield from ret.text()
            raise HTTPException(ret,message=m)
        t = yield from ret.text()
        if t:
            # We got a response, load into json and return it.
            j = yield from ret.json()
            return j

    @asyncio.coroutine
    def send(self, message, *, embeds=None, tts=False):
        """|coro|

        Sends a message to the webhook

        Parameters:

            message: str
                The message you want to send
            embeds: list [discord.Embed] or discord.Embed
                The embed(s) you want to send
            (Everything else is the same as the standard send_message)

        Returns:
            Raw data from Discord
        """

        yield from self.make_request('POST',
                                     {'content': message,
                                      'embeds': embeds,
                                      'tts': tts}
                                     )