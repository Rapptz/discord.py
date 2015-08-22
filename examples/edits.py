import discord

client = discord.Client()
client.login('email', 'password')

@client.event
def on_ready():
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)

@client.event
def on_message_edit(before, after):
    client.send_message(after.channel, '**{}** edited their message:\n{}'.format(after.author.name, before.content))

client.run()
