from discord.ext import commands

import discord

class GoogleBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('$'))

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


# Define a simple View that gives us a google link button.
# We take in `query` as the query that the command author requests for
class Google(discord.ui.View):
    def __init__(self, query: str):
        super().__init__()
        # we need to replace spaces with plus signs to make a valid url. Discord will raise an error if it isn't valid.
        self.query = query.replace(' ', '+')

        # Link buttons cannot be made with the decorator
        # Therefore we have to manually create one.
        # We make a valid google search url with the query and add it to the url parameter.
        # Then we add it to the view
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label='Click Here', url='https://www.google.com/search?q=' + self.query)
        )


bot = GoogleBot()


@bot.command()
async def google(ctx: commands.Context, *, query: str):
    """Returns a google link for a query"""
    await ctx.send(f"Google Result for: `{query}`", view=Google(query))


bot.run('token')
