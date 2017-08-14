from .embeds import Embed
import aiohttp
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
    # Some coloured printing stuffs - Move to Logging asap
    def error(self,err):
        print(err)
    def info(self,msg):
        print(Colors.OKBLUE + msg + Colors.ENDC)
    def set(self,**kwargs):
        """
        Set the webhooks information

        Returns
        ------
        Updated discord.Webhook
        """
        if kwargs.get('name'): self.name = kwargs.get('name')
        if kwargs.get('avatar'): self.avatar = kwargs.get('avatar')
        return self
    async def make_request(self,method,data):
        """
        Send data to discord

        Has to use a different system than discord.py because of how different webhooks
        are to the main client.
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
                self.error('[ERROR] '+str(ret.status)+' '+await ret.text())
        self.info('[SEND] Sent message')
    async def send(self,message,*,embeds=None,tts=False):
        await self.make_request('POST',{'content':message,'embeds':embeds,
                                        'tts':tts})