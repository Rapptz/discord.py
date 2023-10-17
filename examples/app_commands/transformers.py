# This example builds on the concepts of the app_commands/basic.py example
# It's suggested to look at that one to understand certain concepts first.

from typing import Literal, Union, NamedTuple
from enum import Enum

import discord
from discord import app_commands


MY_GUILD = discord.Object(id=0)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


client = MyClient()


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')


# A transformer is a class that specifies how a parameter in your code
# should behave both when used on Discord and when you receive it from Discord.
# There are a few built-in transformers, this example will show these along with
# creating your own for maximum flexibility.

# The first built-in transformer is app_commands.Range
# It works on `str`, `int`, and `float` options and tells you
# the maximum and minimum values (or length in the case of `str`) allowed


@client.tree.command()
@app_commands.describe(first='The first number to add', second='The second number to add')
async def add(
    interaction: discord.Interaction,
    # This makes it so the first parameter can only be between 0 to 100.
    first: app_commands.Range[int, 0, 100],
    # This makes it so the second parameter must be over 0, with no maximum limit.
    second: app_commands.Range[int, 0, None],
):
    """Adds two numbers together"""
    await interaction.response.send_message(f'{first} + {second} = {first + second}', ephemeral=True)


# Other transformers include regular type hints that are supported by Discord
# Examples of these include int, str, float, bool, User, Member, Role, and any channel type.
# Since there are a lot of these, for brevity only a channel example will be included.

# This command shows how to only show text and voice channels to a user using the Union type hint
# combined with the VoiceChannel and TextChannel types.
@client.tree.command(name='channel-info')
@app_commands.describe(channel='The channel to get info of')
async def channel_info(interaction: discord.Interaction, channel: Union[discord.VoiceChannel, discord.TextChannel]):
    """Shows basic channel info for a text or voice channel."""

    embed = discord.Embed(title='Channel Info')
    embed.add_field(name='Name', value=channel.name, inline=True)
    embed.add_field(name='ID', value=channel.id, inline=True)
    embed.add_field(
        name='Type',
        value='Voice' if isinstance(channel, discord.VoiceChannel) else 'Text',
        inline=True,
    )

    embed.set_footer(text='Created').timestamp = channel.created_at
    await interaction.response.send_message(embed=embed)


# In order to support choices, the library has a few ways of doing this.
# The first one is using a typing.Literal for basic choices.

# On Discord, this will show up as two choices, Buy and Sell.
# In the code, you will receive either 'Buy' or 'Sell' as a string.
@client.tree.command()
@app_commands.describe(action='The action to do in the shop', item='The target item')
async def shop(interaction: discord.Interaction, action: Literal['Buy', 'Sell'], item: str):
    """Interact with the shop"""
    await interaction.response.send_message(f'Action: {action}\nItem: {item}')


# The second way to do choices is via an Enum from the standard library
# On Discord, this will show up as four choices: apple, banana, cherry, and dragonfruit
# In the code, you will receive the appropriate enum value.


class Fruits(Enum):
    apple = 0
    banana = 1
    cherry = 2
    dragonfruit = 3


@client.tree.command()
@app_commands.describe(fruit='The fruit to choose')
async def fruit(interaction: discord.Interaction, fruit: Fruits):
    """Choose a fruit!"""
    await interaction.response.send_message(repr(fruit))


# You can also make your own transformer by inheriting from app_commands.Transformer


class Point(NamedTuple):
    x: int
    y: int


# The default transformer takes in a string option and you can transform
# it into any value you'd like.
#
# Transformers also support various other settings such as overriding
# properties like `choices`, `max_value`, `min_value`, `type`, or `channel_types`.
# However, this is outside of the scope of this example so check the documentation
# for more information.
class PointTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> Point:
        (x, _, y) = value.partition(',')
        return Point(x=int(x.strip()), y=int(y.strip()))


@client.tree.command()
async def graph(
    interaction: discord.Interaction,
    # In order to use the transformer, you should use Transform to tell the
    # library to use it.
    point: app_commands.Transform[Point, PointTransformer],
):
    await interaction.response.send_message(str(point))


# For more basic transformers for your own types without too much repetition,
# a concept known as "inline transformers" is supported. This allows you to use
# a classmethod to have a string based transformer. It's only useful
# if you only care about transforming a string to a class and nothing else.
class Point3D(NamedTuple):
    x: int
    y: int
    z: int

    # This is the same as the above transformer except inline
    @classmethod
    async def transform(cls, interaction: discord.Interaction, value: str):
        x, y, z = value.split(',')
        return cls(x=int(x.strip()), y=int(y.strip()), z=int(z.strip()))


@client.tree.command()
async def graph3d(interaction: discord.Interaction, point: Point3D):
    await interaction.response.send_message(str(point))


client.run('token')
