import discord
from discord.ext import commands
from datetime import datetime

class MyAdvancedBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="example ", *args, **kwargs)
        self.start_time = datetime.utcnow()
    
    async def on_ready(self):
        print(f"{'*' * 20}\nLogged in!\nBot User: {self.user.name}#{self.user.discriminator}\n{'*' * 20}")

bot = MyAdvancedBot()

if __name__ == "__main__":
    bot.load_extension("cogs.example")
    bot.run("token")
