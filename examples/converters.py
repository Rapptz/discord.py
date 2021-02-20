import discord
from discord.ext import commands

# We will need the members intents at the minimum to use the Member converter.
intents = discord.Intents.all()

# Construct the Bot instance.
bot = commands.Bot("!", intents=intents)


@bot.command()
async def userinfo(ctx: commands.Context, user: discord.User):
    # In the command signature above, you can see that the `user`
    # parameter is typehinted to `discord.User`. This means that
    # during command invocation we will attempt to convert
    # the value passed as `user` to a `discord.User` instance.

    # If the conversion is successful we will have a User instance
    # and can do the following:
    await ctx.send(user.name)

@userinfo.error
async def userinfo_error(ctx: commands.Context, error: Exception):
    # if the conversion above fails for any reason, it will raise `commands.errors.BadArgument`
    # so we handle this in this error handler
    if isinstance(error, commands.BadArgument):
        return await ctx.send("Failed to convert the argument for `user` to `discord.User`.")
    else:
        return await ctx.send("Unhandled error: {}".format(error))

# Manual use of converters will follow
@bot.command()
async def channel_or_member(ctx: commands.Context, argument: str):
    # NOTE: command parameters are `str` type by default, the typehint above is just for completeness' sake.

    # If you are doing this kind of thing commonly, consider making a Custom Converter
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#advanced-converters

    # If for any reason you have an ID, but it may be of one of more
    # items, like a TextChannel or Member, you can manually call the converters
    # like the following:
    member_converter = commands.MemberConverter()
    try:
        # Try and convert to a Member instance.
        member = await member_converter.convert(ctx, argument)
    except commands.MemberNotFound:
        # Could not convert to a member instance
        pass
    else:
        # We have our `member` so lets return here.
        return await ctx.send("Member found: {}".format(member))

    # Do the same for TextChannel...
    textchannel_converter = commands.TextChannelConverter()
    try:
        channel = await textchannel_converter.convert(ctx, argument)
    except commands.ChannelNotFound:
        pass
    else:
        return await ctx.send("Channel found: {}".format(channel))

    await ctx.send("No member or channel matching this ID was found.")

# Builtin type converters
@bot.command()
async def trial_converter(ctx: commands.Context, number: int, maybe: bool):
    # We want and int and a bool parameter here.
    # Bool is a slightly special case, as shown here:
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#bool

    await ctx.send("Number: {} -- Bool: {}.".format(number, maybe))

token = "your token here"
bot.run(token)