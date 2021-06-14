import discord, asyncpg, asyncio
from discord.ext import commands
from datetime import datetime

class MyAdvancedBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="example ", *args, **kwargs)
        self.start_time = datetime.utcnow()
 
    async def on_ready(self):
        print(f"{'*' * 20}\nLogged in!\nBot User: {self.user}\n{'*' * 20}")

bot = MyAdvancedBot()

async def run():
    bot.db = await asyncpg.create_pool("db URL")
    await bot.db.execute("CREATE TABLE IF NOT EXISTS economy(user_id bigint, wallet bigint, bank bigint)")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
    bot.load_extension("cogs.example")
    bot.run("token")
