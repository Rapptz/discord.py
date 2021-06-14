import discord
from discord.ext import commands
from typing import Union

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
    
    async def create_bal(self, user_id):
        user_id = user.id
        try:
            self.user_bal = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", user_id)
        except Exception:
            await self.bot.db.execute("INSERT INTO economy(user_id, wallet, bank) VALUES ($1, 0, 0)", user_id)
            self.user_bal = await self.bot.db.fetchrow("SELECT * FROM economy WHERE user_id = $1", user_id)
    
    @commands.command(name="balance")
    async def bal(self, ctx, user : Union[discord.Member, int]):     
        embed = discord.Embed(colour=discord.Colour.green(), title=f"{user.name}'s Balance", description=f"**Wallet**: {self.user_bal['wallet']} Coins\n**Bank**: {self.user_bal['bank']} Coins")
        await ctx.send(embed=embed)


    @commands.command(name="beg")
    async def beg(self, ctx):
        await self.make_bal(user.id)
        earnings = random.randint(0, 200)
        await ctx.send(f"You got {earnings} coins!!")
        await self.bot.db.execute("UPDATE economy SET wallet = $1 WHERE user_id = $2", self.user_bal['wallet']+earnings, ctx.author.id)

def setup(bot):
    bot.add_cog(Economy(bot))
