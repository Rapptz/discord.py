import discord
import random

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('$guess'):
            await message.channel.send('Guess a number between 1 and 10.')
            check = lambda m: m.content.isdigit()
            guess = await self.wait_for_message(author=message.author, check=check, timeout=5.0)

            answer = random.randint(1, 10)
            if guess is not None:
                await message.channel.send('Sorry, you took too long it was {}.'.format(answer))
                return

            if int(guess.content) == answer:
                await message.channel.send('You are right!')
            else:
                await message.channel.send('Oops. It is actually {}.'.format(answer))

client = MyClient()
client.run('token')
