import discord
from discord import app_commands
from discord.ext import commands

class FirstCog(commands.Cog):
    def __init__(self, bot):
        # Here, we create our cog, defining our bot instance.
        self.bot = bot
    
    @app_commands.command(name="cog", description="This command comes from a cog!")
    async def fromcog(self, interaction: discord.Interaction): # Create a application command (slash command) inside the cog
        await interaction.response.send_message("Hello, I'm sending from the cog!")
    
    @commands.command()
    async def cogcommand(self, ctx: commands.Context):
        await ctx.reply("Hey, replying from inside the cog!")

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        await self.add_cog(FirstCog(self)) # Add the cog to the bot
        await self.tree.sync() # Sync our application commands (this may take up to an hour)
        print(f"{self.user} is online and ready!")

bot = MyBot()
bot.run("token")
