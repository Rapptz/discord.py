import discord

client = discord.Client()

@client.event
async def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
async def on_message(message):
    if message.content.startswith('!deleteme'):
        msg = await client.send_message(message.channel, 'I will delete myself now...')
        await client.delete_message(msg)

@client.event
async def on_message_delete(message):
    fmt = '{0.author.name} has deleted the message:\n{0.content}'
    await client.send_message(message.channel, fmt.format(message))

client.run('token')
