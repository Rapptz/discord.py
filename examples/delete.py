import discord

client = discord.Client()

@client.event
async def on_message(message):
    """Delete all messages found"""
    await None.send(message)

client.run("token")
