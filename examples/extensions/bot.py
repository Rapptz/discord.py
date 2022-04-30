import discord
from discord.ext import commands

intents = discord.Intents.default()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    
    async def on_ready(self):
        extensions_to_load = ["contextmenu", "groups", "slashcommand"] # A list with the names of the files containing the extensions we want to load. 
        for extension in extensions_to_load:
            await self.load_extension("cogs." + extension)
            # Load the extension
            print(f"Loaded {extension}")

        await self.tree.sync() 
        # Sync our commands
        print("Successfully synced commands")
        print(f"Logged onto {self.user}")

bot = MyBot()
bot.run("token")