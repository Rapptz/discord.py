import discord
import random

client = discord.Client()

@client.async_event
def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content.startswith('$guess'):
        yield from client.send_message(message.channel, 'Guess a number between 1 to 10')

        def guess_check(m):
            return m.content.isdigit()

        guess = yield from client.wait_for_message(timeout=5.0, author=message.author, check=guess_check)
        answer = random.randint(1, 10)
        if guess is None:
            fmt = 'Sorry, you took too long. It was {}.'
            yield from client.send_message(message.channel, fmt.format(answer))
            return
        if int(guess.content) == answer:
            yield from client.send_message(message.channel, 'You are right!')
        else:
            yield from client.send_message(message.channel, 'Sorry. It is actually {}.'.format(answer))


@client.async_event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run('email', 'password')
