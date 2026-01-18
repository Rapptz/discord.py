import discord
from discord.ext import commands
import asyncio

TOKEN = ""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def main():
    # Load the cog
    await bot.load_extension("cogs.ffmpeg_issue")
    await bot.start(TOKEN)

asyncio.run(main())

