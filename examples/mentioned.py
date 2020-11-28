import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged in as {0.user}".format(self))

    async def on_message(self, message):
        if self.user.mentioned_in(message): 
            await message.channel.send("That's me!")
            # or do other stuff here

client = MyClient()
client.run('token')
