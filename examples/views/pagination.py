import discord

from discord.ext import commands

class PaginationView(discord.ui.View):

    current = 0

    def __init__(self, embed_list: list):

        super().__init__()

        self.embed_list = embed_list

    async def on_timeout(self) -> None:

        self.clear_items()
        self.message.edit(view=self)
        

    @discord.ui.button(label="Prev.", style=discord.ButtonStyle.red, disabled=True)

    async def prev(self, button, interaction):

        if (self.current - 1) <= 0:

            button.style = discord.ButtonStyle.red

            button.disabled = True

            self.current -= 1

            self.next.disabled = False

            self.next.style = discord.ButtonStyle.green

            self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

            await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

            return

        if len(self.embed_list) > 2:

            self.next.disabled = False

            self.next.style = discord.ButtonStyle.green

        self.current -= 1

        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

        await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

    @discord.ui.button(label=f"Page 1", style=discord.ButtonStyle.gray, disabled=True)

    async def count(self, _, interaction):

        pass

    @discord.ui.button(label="Next", style=discord.ButtonStyle.green)

    async def next(self, button, interaction):

        if self.current + 1 == len(self.embed_list) - 1:

            button.style = discord.ButtonStyle.red

            button.disabled = True

            self.current += 1

            self.prev.disabled = False

            self.prev.style = discord.ButtonStyle.green

            self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

            await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

            return

        self.current += 1

        self.prev.disabled = False

        self.prev.style = discord.ButtonStyle.green

        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"

        await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)

    async def start(self, ctx):

        self.message = await ctx.send(embed=self.embed_list[self.current], view=self)

        return self.message

bot = commands.Bot(command_prefix="!")

@bot.command()

async def paginate(ctx):

    embed_list = [discord.Embed(title=f"Embed {i + 1}") for i in range(3)]

    message = await PaginationView(embed_list).start(ctx=ctx)
    # do anything with message 🤞

    

bot.run("token")

