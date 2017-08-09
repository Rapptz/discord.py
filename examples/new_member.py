import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_member_join(self, member):
        await member.send('Welcome {0.mention} to {1.name}!'.format(member, guild))

client = MyClient()
client.run('token')
