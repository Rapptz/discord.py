# We highly recommend using a database, but for this example, we will use a python dict.

import discord
from discord.ext import commands
from typing import Union

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
    
    @commands.command(name="balance")
    async def bal(self, ctx, user : Union[discord.Member, int]):
        user_id = user.id
        try:
            user_bal = self.users[str(user_id)]
        except KeyError:
            self.users[str(user_id)] = {"wallet": 0, "bank": 0}
        user_bal = self.users[str(user_id)]
        embed = discord.Embed(colour=discord.Colour.green(), title=f"{user.name}'s Balance", description=f"**Wallet**: {user_bal['wallet']} Coins\n**Bank**: {user_bal['bank']} Coins")
        await ctx.send(embed=embed)


    @commands.command(name="beg")
    async def beg(self, ctx):
        user_id = ctx.author.id
        try:
            user_bal = self.users[str(user_id)]
        except KeyError:
            self.users[str(user_id)] = {"wallet": 0, "bank": 0}
        user_bal = self.users[str(user_id)]
        earnings = random.randint(0, 200)
        await ctx.send(f"You got {earnings} coins!!")
        user_bal['wallet'] += earnings

def setup(bot):
    bot.add_cog(Economy(bot))
