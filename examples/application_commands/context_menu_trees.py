import discord
from discord import app_commands


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.friends = {}
        self.bookmarked_messages = {}
        self.tree = app_commands.CommandTree(self)


    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')  # type: ignore
        print('------')

        # Sync our local tree with Discord
        await self.tree.sync(guild=guild)


intents = discord.Intents.default()
# the guild to register the command to, remove to make global
# (global commands can take up to an hour to register)
# you could also pass a `discord.Guild` and it would work.
guild = discord.Object(id=GUILD_ID_HERE)
client = MyClient(intents=intents)

@client.tree.context_menu(name='Add friend', guild=guild)
async def add_friend(interaction: discord.Interaction, member: discord.Member):
    try:
        # add the user as a friend
        client.friends[member.id].append(interaction.user.id)
    except KeyError:
        client.friends[member.id] = [interaction.user.id]

    await interaction.response.send_message(f'{interaction.user.mention} has added {member.mention} as a friend!')


@client.tree.context_menu(name='Remove friend', guild=guild)
async def remove_friend(interaction: discord.Interaction, member: discord.Member):
    try:
        # remove the user as a friend
        client.friends[member.id].remove(interaction.user.id)
    except (KeyError, ValueError):
        # handle them not being a friend
        return await interaction.response.send_message(f'You haven\'t added {member.name} as a friend yet!')

    await interaction.response.send_message(f'{interaction.user.mention} has removed {member.mention} as a friend')


@client.tree.context_menu(name='Add bookmark', guild=guild)
async def bookmark(interaction: discord.Interaction, message: discord.Message):
    try:
        client.bookmarked_messages[interaction.user.id].append(message)
    except KeyError:
        client.bookmarked_messages[interaction.user.id] = [message]

    await interaction.response.send_message('bookmarked that message!')


@client.tree.context_menu(name='Remove bookmark', guild=guild)
async def remove_bookmark(interaction: discord.Interaction, message: discord.Message):
    try:
        client.bookmarked_messages[interaction.user.id].remove(message)
    except (KeyError, ValueError):
        return await interaction.response.send_message('This message isn\'t bookmarked!')

    await interaction.response.send_message('Removed that message as bookmarked')


client.run('token')
