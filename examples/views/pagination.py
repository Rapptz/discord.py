from typing import List

import discord
from discord.ext import commands


class PaginationView(discord.ui.View):
    def __init__(self, embed_list: List[discord.Embed]):
        super().__init__(timeout=60.0)
        self.current = 0  # index of the embed in embed_list which is currently displayed.
        self.embed_list = embed_list
        if len(embed_list) == 1:
            self.next.disabled = True
            self.next.style = discord.ButtonStyle.red
        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

    async def on_timeout(self) -> None:
        self.clear_items()
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user == interaction.user:
            return True
        await interaction.response.send_message(f'Only {self.user.name} can react. Start new if you want to.',
                                                ephemeral=True)
        return False

    async def update_buttons(self, button: discord.ui.Button):
        if button == self.previous:
            self.current -= 1
            self.next.disabled = False
            self.next.style = discord.ButtonStyle.green
            if self.current == 0:  # disabling the previous button if it's the first page.
                self.previous.disabled = True
                self.previous.style = discord.ButtonStyle.red
        else:
            self.current += 1
            self.previous.disabled = False
            self.previous.style = discord.ButtonStyle.green
            if self.current == len(self.embed_list) - 1:  # disabling the next button if it's the last page.
                self.next.disabled = True
                self.next.style = discord.ButtonStyle.red
        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.red, disabled=True)  # you can add emojis too..
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.update_buttons(button)
        await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

    @discord.ui.button(disabled=True, style=discord.ButtonStyle.blurple)
    async def count(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass

    @discord.ui.button(label="Next", style=discord.ButtonStyle.green)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.update_buttons(button)
        await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

    # Starting the pagination view
    async def start(self, ctx):
        self.message = await ctx.reply(embed=self.embed_list[0], view=self)
        self.user = ctx.author
        return self.message


# Now the bot..
bot = commands.Bot(command_prefix="!")


@bot.command()
async def paginate(ctx, number: int):
    embed_list = [discord.Embed(title=f"Embed {i + 1}") for i in range(number)]
    message = await PaginationView(embed_list=embed_list).start(ctx=ctx)
    # do anything with the message object


bot.run("token")
