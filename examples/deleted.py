# This example requires the 'message_content' privileged intent to function.

import logging
import discord


class MyClient(discord.Client):
    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logging.info('------')

    async def on_message(self, message):
        if message.content.startswith('!deleteme'):
            msg = await message.channel.send('I will delete myself now...')
            await msg.delete()

            # this also works
            await message.channel.send('Goodbye in 3 seconds...', delete_after=3.0)

    async def on_message_delete(self, message):
        msg = f'{message.author} has deleted the message: {message.content}'
        await message.channel.send(msg)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('token', root_logger=True)
