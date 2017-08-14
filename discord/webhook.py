from .embeds import Embed
from .errors import HTTPException
from .utils import _bytes_to_base64_data
import aiohttp
import io
import json
import asyncio
WEBHOOK_BASE = 'https://discordapp.com/api/webhooks/'
class Webhook():
    def __init__(self,**kwargs):
        self.avatar = kwargs.get('avatar','')
        self.name = kwargs.get('name','')
        self.id = kwargs.get('id',0)
        self.token = kwargs.get('token','')
        self.url = WEBHOOK_BASE + '{0.id}/{0.token}'.format(self)
        self.webhook = kwargs # Anything we didnt get will be in here
    def from_data(self,data,state):
        self._state = data.get('state')
        self.avatar = data.get('avatar','')
        self.name = data.get('name','')
        self.id = data.get('id',0)
        self.token = data.get('token','')
        self.url = WEBHOOK_BASE + '{0.id}/{0.token}'.format(self)
        self.webhook = data # Anything we didnt get will be in here
        return self
    @asyncio.coroutine
    def edit(self,*,update=False,**kwargs):
        """
        Set the webhooks information

        Returns
        ------
            Updated discord.Webhook
        """
        if kwargs.get('name'): self.name = kwargs.get('name')
        if kwargs.get('avatar'): self.avatar = kwargs.get('avatar')
        if update: yield from self.update() # Updates the webhook
        return self
    @asyncio.coroutine
    def update(self,**kwargs):
        """|coro|
        Updates the webhook
        """
        avatar = self.avatar
        if self.avatar:
            ret = yield from self._state.http._session.request('GET',self.avatar)
            if ret.status not in [200,204]:
                t = yield from ret.text()
                raise HTTPException(t)
            d = yield from ret.read()
            img = io.BytesIO(d)
            img.seek(0)
            avatar = _bytes_to_base64_data(img.read())

        payload = {'name':self.name if not kwargs.get('name') else kwargs.get('name'),
                   'avatar':avatar}
        
        url = WEBHOOK_BASE + '{webhook_id}/{webhook_token}'.format(webhook_id = self.id, webhook_token = self.token)
        ret = yield from self._state.http._session.request('PATCH',url,data=json.dumps(payload),headers = {'content-type': 'application/json'})
        d = yield from ret.json()
        if ret.status not in [200,204]:
            m = yield from ret.text()
            raise HTTPException(ret,message=m)
        return self.from_data() # Update the webhook with the new data
    @asyncio.coroutine
    def make_request(self,method,data):
        """|coro|
        Send data to discord

        Has to use a different system than discord.py because of how different webhooks
        are to the main client.

        Danny, if you dont like how I did this, feel free to change it. I feel like I could
        Have done better TBH
        """
        data['username'] = self.name
        data['avatar_url'] = self.avatar
        data['embeds_cache'] = []
        if data.get('embeds') and isinstance(data.get('embeds'),list):
            for em in data['embeds']:
                if isinstance(em,Embed):
                    data['embeds_cache'].append(em.to_dict())
        elif isinstance(data.get('embeds'),Embed):
            data['embeds_cache'] = [data['embeds'].to_dict()]
        data['embeds'] = data['embeds_cache']
        del data['embeds_cache']
        ret = yield from self._state.http._session.request(method,self.url,data=json.dumps(data),headers = {'content-type': 'application/json'})
        if ret.status not in [200,204]:
            m = yield from ret.text()
            raise HTTPException(ret,message=m)
        toreturn = yield from ret.json()
        return toreturn
    @asyncio.coroutine
    def send(self,message,*,embeds=None,tts=False):
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

        yield from self.make_request('POST',{'content':message,'embeds':embeds,
                                                'tts':tts})