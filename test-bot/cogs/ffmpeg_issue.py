import discord
from discord.ext import commands

class FFmpegIssue(commands.Cog):
    """Commands to test FFmpeg exit behavior."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """Bot joins the author's voice channel."""
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send("Joined your voice channel!")
        else:
            await ctx.send("You are not in a voice channel.")

    @commands.command()
    async def play(self, ctx):
        """Plays a URL that is designed to fail to test FFmpeg error handling."""
        vc = ctx.voice_client
        if not vc:
            await ctx.send("I am not in a voice channel.")
            return

        url = "https://example.com/this_will_404.m3u8"

        def after(error):
            print("AFTER callback called")
            if error:
                print("FFmpeg error:", repr(error))
                # Send error to Discord
                try:
                    fut = asyncio.run_coroutine_threadsafe(
                        ctx.send(f"FFmpeg error: {error}"), self.bot.loop
                    )
                    fut.result()
                except Exception as e:
                    print("Failed to send error to Discord:", e)
            # optionally disconnect after test
            import asyncio
            asyncio.run_coroutine_threadsafe(vc.disconnect(), self.bot.loop)

        source = discord.FFmpegPCMAudio(url)
        vc.play(source, after=after)
        await ctx.send("Attempting to play (will fail)...")

async def setup(bot):
    await bot.add_cog(FFmpegIssue(bot))
