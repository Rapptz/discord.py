import discord

client = discord.Client()

@client.async_event
def on_member_join(member):
    server = member.server
    fmt = 'Welcome {0} to {1.name}!'
    yield from client.send_message(server, fmt.format(member.mention(), server))

@client.async_event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run('email', 'password')
