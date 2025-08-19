from __future__ import annotations

from discord.ext import commands
import discord
import re

# Complicated use cases for persistent views can be difficult to achieve when dealing
# with state changes or dynamic items. In order to facilitate these complicated use cases,
# the library provides DynamicItem which allows you to define an item backed by a regular
# expression that can parse state out of the custom_id.

# The following example showcases a dynamic item that implements a counter.
# The `template` class parameter is used to give the library a regular expression to parse
# the custom_id. In this case we're parsing out custom_id in the form of e.g.
# `counter:5:user:80088516616269824` where the first number is the current count and the
# second number is the user ID who owns the button.


# Note that custom_ids can only be up to 100 characters long.
class DynamicCounter(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r'counter:(?P<count>[0-9]+):user:(?P<id>[0-9]+)',
):
    def __init__(self, user_id: int, count: int = 0) -> None:
        self.user_id: int = user_id
        self.count: int = count
        super().__init__(
            discord.ui.Button(
                label=f'Total: {count}',
                style=self.style,
                custom_id=f'counter:{count}:user:{user_id}',
                emoji='\N{THUMBS UP SIGN}',
            )
        )

    # We want the style of the button to be dynamic depending on the count.
    @property
    def style(self) -> discord.ButtonStyle:
        if self.count < 10:
            return discord.ButtonStyle.grey
        if self.count < 15:
            return discord.ButtonStyle.red
        if self.count < 20:
            return discord.ButtonStyle.blurple
        return discord.ButtonStyle.green

    # This method actually extracts the information from the custom ID and creates the item.
    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        count = int(match['count'])
        user_id = int(match['id'])
        return cls(user_id, count=count)

    # We want to ensure that our button is only called by the user who created it.
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        # When the button is invoked, we want to increase the count and update the button's
        # styling and label.
        # In order to actually persist these changes we need to also update the custom_id
        # to match the new information.
        # Note that the custom ID *must* match the template.
        self.count += 1
        self.item.label = f'Total: {self.count}'
        self.custom_id = f'counter:{self.count}:user:{self.user_id}'
        self.item.style = self.style
        # In here, self.view is the view given by the interaction's message.
        # It cannot be a custom subclass due to limitations.
        await interaction.response.edit_message(view=self.view)


class DynamicCounterBot(commands.Bot):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        # For dynamic items, we must register the classes instead of the views.
        self.add_dynamic_items(DynamicCounter)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = DynamicCounterBot()


@bot.command()
async def counter(ctx: commands.Context):
    """Starts a dynamic counter."""

    view = discord.ui.View(timeout=None)
    view.add_item(DynamicCounter(ctx.author.id))
    await ctx.send('Here is your very own button!', view=view)


bot.run('token')
