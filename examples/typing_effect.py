import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        if message.content.startswith('!hi'):
          async with message.channel.typing():
            await channel.send(f'Hello {message.author.mention}')
          
intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('token')
