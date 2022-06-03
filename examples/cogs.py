#Required Imports
import asyncio
import discord
from discord.ext import commands

#A basic Cog
class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None: 
        self.bot = bot
    
    @commands.command(name="ping")
    async def _ping(self, ctx: commands.Context) -> None:
        await ctx.send(f"Pong!")

#Initialising the bot and loading the cog 
class Bot(commands.Bot):
    def __init__(self, intents: discord.Intents) -> commands.Bot:
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self) -> None:
        await self.add_cog(ExampleCog(self))

    async def on_ready(self) -> None:
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

intents = discord.Intents.default()
intents.message_content = True #Enabling the required message content intent
bot = Bot(intents=intents)

async def main():
    async with bot:
        await bot.start("token")
    
asyncio.run(main())