
import traceback
from discord.ext import commands
from discord import Intents, app_commands

bot = commands.Bot(command_prefix='!!!', intents=Intents(messages=True, message_content=True, guilds=True))
Choice = commands.Choice
AChoice = app_commands.Choice

@bot.command()
async def normal(ctx):
    await ctx.send('test')
    
@bot.command()
@commands.choices(choice=[Choice(name="test", value=1,), Choice(name="test2", value=2)])
async def decorator(ctx: commands.Context, *, choice: Choice[int]):
    info = (
        f"choice: {choice=}\n"
        f"param: {ctx.current_parameter=}\n"
        
    )
    await ctx.send(info)

@bot.hybrid_command()
#@app_commands.choices(choice=[AChoice(name="test", value=1,), AChoice(name="test2", value=2)])
@commands.choices(choice=[Choice(name="test", value=1,), Choice(name="test2", value=2)])
async def hybrid_decorator(ctx: commands.Context, *, choice:Choice):
    info = (
        f"choice: {choice=}\n"
        f"param: {ctx.current_parameter=}\n"
        
    )
    await ctx.send(info)


@bot.event
async def setup_hook():
    await bot.load_extension("jishaku")

@bot.event
async def on_command_error(ctx, error):
    traceback.print_exception(type(error), error, error.__traceback__)

    await ctx.send(error)

@bot.tree.error
async def on_tree_error(interaction, error):
    traceback.print_exception(type(error), error, error.__traceback__)
    await interaction.response.send_message(error)

bot.run('NTczNTMxNjk0ODIxNTM5ODUw.XMsNAw._NNzDXww9EwYxlaQRgW4wBTcL44')
