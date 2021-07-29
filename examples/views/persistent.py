from discord.ext import commands
import discord


class PersistentViewBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('$'))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


# Define a simple View that persists between bot restarts
# In order a view to persist between restarts it needs to meet the following conditions:
# 1) The timeout of the View has to be set to None
# 2) Every item in the View has to have a custom_id set
# It is recommended that the custom_id be sufficiently unique to
# prevent conflicts with other buttons the bot sends.
# For this example the custom_id is prefixed with the name of the bot.
# Note that custom_ids can only be up to 100 characters long.
class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Green', style=discord.ButtonStyle.green, custom_id='persistent_view:green')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is green.', ephemeral=True)

    @discord.ui.button(label='Red', style=discord.ButtonStyle.red, custom_id='persistent_view:red')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is red.', ephemeral=True)

    @discord.ui.button(label='Grey', style=discord.ButtonStyle.grey, custom_id='persistent_view:grey')
    async def grey(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is grey.', ephemeral=True)


bot = PersistentViewBot()

async def add_persistent_view():
    # Register the persistent view for listening
    # Note that this does not send the view to any message.
    # In order to do this you need to first send a message with the View, which is shown below.
    # If you have the message_id you can also pass it as a keyword argument, but for this example
    # we don't have one.
    # Add the view in a startup task to prevent loop issues.
    bot.add_view(PersistentView())

bot.loop.create_task(add_persistent_view())

@bot.command()
@commands.is_owner()
async def prepare(ctx: commands.Context):
    """Starts a persistent view."""
    # In order for a persistent view to be listened to, it needs to be sent to an actual message.
    # Call this method once just to store it somewhere.
    # In a more complicated program you might fetch the message_id from a database for use later.
    # However this is outside of the scope of this simple example.
    await ctx.send("What's your favourite colour?", view=PersistentView())


bot.run('token')
