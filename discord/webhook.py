from .embeds import Embed
from .errors import HTTPException
from .utils import _bytes_to_base64_data
import aiohttp
import io
import json
WEBHOOK_BASE = 'https://discordapp.com/api/webhooks/'
class Webhook():
    def __init__(self,**kwargs):
        self.avatar = kwargs.get('avatar','')
        self.name = kwargs.get('name','')
        self.id = kwargs.get('id',0)
        self.token = kwargs.get('token','')
        self.url = WEBHOOK_BASE + '{0.id}/{0.token}'.format(self)
        self.webhook = kwargs # Anything we didnt get will be in here
    def from_data(self,data):
        self.avatar = data.get('avatar','')
        self.name = data.get('name','')
        self.id = data.get('id',0)
        self.token = data.get('token','')
        self.url = WEBHOOK_BASE + '{0.id}/{0.token}'.format(self)
        self.webhook = data # Anything we didnt get will be in here
        return self

    async def edit(self,*,update=False,**kwargs):
        """
        Set the webhooks information

        Returns
        ------
            Updated discord.Webhook
        """
        if kwargs.get('name'): self.name = kwargs.get('name')
        if kwargs.get('avatar'): self.avatar = kwargs.get('avatar')
        if update: await self.update() # Updates the webhook
        return self
    async def update(self,**kwargs):
        """|coro|
        Updates the webhook
        """
        avatar = self.avatar
        if self.avatar:
            async with aiohttp.request('GET',self.avatar) as ret:
                if ret.status not in [200,204]:
                    raise HTTPException(await ret.text())
                img = io.BytesIO(await ret.read())
                img.seek(0)
            avatar = _bytes_to_base64_data(img.read())

        payload = {'name':self.name if not kwargs.get('name') else kwargs.get('name'),
                   'avatar':avatar}
        
        url = WEBHOOK_BASE + '{webhook_id}/{webhook_token}'.format(webhook_id = self.id, webhook_token = self.token)
        async with aiohttp.request('PATCH',url,data=json.dumps(payload),headers = {'content-type': 'application/json'}) as ret:
            if ret.status not in [200,204]:
                raise HTTPException(ret,message=await ret.text())
            return self.from_data(await ret.json()) # Update the webhook with the new data

    async def make_request(self,method,data):
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
        async with aiohttp.request(method,self.url,data=json.dumps(data),headers = {'content-type': 'application/json'}) as ret:
            if ret.status not in [200,204]:
                raise HTTPException(await ret.text())
            return await ret.json()
    async def send(self,message,*,embeds=None,tts=False):
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

        return await self.make_request('POST',{'content':message,'embeds':embeds,
                                                'tts':tts})