import discord
from discord.ext import commands


class PaginationView(discord.ui.View):
    current = 0 # It's not in the constructor because it'll be reset everytime the view is updated.
    def __init__(self, embed_list):
        super().__init__()
        self.embed_list = embed_list
        if len(embed_list) == 1:
            self.next.disabled = True
            self.next.style = discord.ButtonStyle.red
        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"


    # To make sure only ctx.author can interact.   
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user == interaction.user:
            return True
        await interaction.response.send_message(f'Only `{self.user.name}` can interact. Run the command if you want to.', ephemeral=True)
        return False
        
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.red, disabled=True) # you can add emojis too..
    async def previous(self, button, interaction):
        self.current -= 1
        self.next.disabled = False
        self.next.style = discord.ButtonStyle.green
        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"
        if self.current == 0:
            button.disabled = True
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)
        else:
            await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)
    
    
    @discord.ui.button(disabled=True, style=discord.ButtonStyle.blurple)
    async def count(self, btn, _):
        pass
    
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.green)
    async def next(self, button, interaction):
        self.current += 1
        self.previous.disabled = False
        self.previous.style = discord.ButtonStyle.green
        self.count.label = f"Page {self.current + 1}/{len(self.embed_list)}"
        if self.current == len(self.embed_list) -1 :
            button.disabled = True
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(embed=self.embed_list[self.current], view=self)
        else:
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
    embed_list = [discord.Embed(title=f"Embed {i+1}") for i in range(number)]
    message = await PaginationView(embed_list).start(ctx=ctx)
    # do anything with the message object
    
bot.run("token")
