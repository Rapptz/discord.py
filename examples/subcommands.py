import discord
from discord.ext import commands

class ExampleCog(commands.Cog):
  def __init__(self, client):
    self.client = client
    
  @commands.group(invoke_without_command = True)
  async def wave(self, ctx):
    await ctx.send("wave goodbye or wave hello. Syntax: `prefix!wave hello @member` | `prefix!wave goodbye @member`")

  @wave.command(aliases = ["bye"]) #this would be @wave.command() because we named our command group "wave". If we named it "danny", it would be @danny.command()
  async def goodbye(self, ctx, *, member : discord.Member):
    await ctx.send(f"goodbye {member.mention}")
    
  @wave.command()
  async def hello(self, ctx, *, member : discord.Member):
    await ctx.send(f"hello {member.mention}")
    
    
    
    
 def setup(client):
  client.add_cog(ExampleCog(client))
