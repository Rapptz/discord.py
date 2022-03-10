import discord
from discord import app_commands
from typing import Literal

# the guild to register the command to, remove to make global
# (global commands can take up to an hour to register)
# you could also pass a `discord.Guild` and it would work.
guild = discord.Object(id=GUILD_ID_HERE)


class Farm(app_commands.Group):
    """Commands for managing farm plants"""

    # use a nested group
    view = app_commands.Group(name='view', description='View farm prices')
    items = app_commands.Group(name='items', description='Buy and sell farm plants')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the prices of the plants
        self.plants = {
            'apples': {'price': 1.0},
            'wheat': {'price': 3.0},
            'corn': {'price': 2.0},
        }

        # plant owners
        self.owners = {}

    @view.command()
    async def prices(self, interaction: discord.Interaction):
        """See the current farm prices"""

        # start with a base of 0
        base = 0

        for plant, details in self.plants.items():
            # raise the base value
            base += details['price']

        # send the price
        await interaction.response.send_message(f'The current normalized plant price is ${base}')

    @view.command()
    @app_commands.describe(plant='The plant to view the price of')  # describe the option
    async def price(self, interaction: discord.Interaction, plant: Literal['apples', 'wheat', 'corn']):
        """See the price of a plant"""

        # get the price of the plant
        price = self.plants[plant]['price']

        # send the price of the plant
        await interaction.response.send_message(f'{plant} currently sells for ${price}')

    @items.command()
    @app_commands.describe(plant='The plant to buy')  # describe the option
    async def buy(self, interaction: discord.Interaction, plant: Literal['apples', 'wheat', 'corn']):
        """Buy a plant"""

        # raise the price of the plant
        self.plants[plant]['price'] += 0.2

        try:
            self.owners[interaction.user.id][plant] += 1
        except KeyError:
            self.owners[interaction.user.id] = {plant: 1}

        await interaction.response.send_message(f'You have bought {plant}')

    @items.command()
    @app_commands.describe(plant='The plant to sell')  # describe the option
    async def sell(self, interaction: discord.Interaction, plant: Literal['apples', 'wheat', 'corn']):
        """Sell a plant"""

        # remove value from the plant
        self.plants[plant]['price'] - +0.1

        if self.owners[interaction.user.id][plant] == 0:
            return await interaction.response.send_message(f'You do not own this plant!')

        try:
            # remove the plant from the owner
            self.owners[interaction.user.id][plant] -= 1
        except KeyError:
            # make sure the owner actually owns this plant
            return await interaction.response.send_message(f'You do not own this plant!')

        await interaction.response.send_message(f'You have sold {plant}')


# initiate the default client with the default intents.
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# initiate our command tree
tree = app_commands.CommandTree(client)
# add the group to the tree
tree.add_command(Farm(name='farm'), guild=guild)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')  # type: ignore
    print('------')

    # Sync our local tree with Discord
    await tree.sync(guild=guild)


client.run('token')
