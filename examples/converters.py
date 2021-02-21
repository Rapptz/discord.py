# This example requires the 'members' privileged intent to use the Member converter.

import typing

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot('!', intents=intents)


@bot.command()
async def userinfo(ctx: commands.Context, user: discord.User):
    # In the command signature above, you can see that the `user`
    # parameter is typehinted to `discord.User`. This means that
    # during command invocation we will attempt to convert
    # the value passed as `user` to a `discord.User` instance.
    # The documentation notes what can be converted, in the case of `discord.User`
    # you pass an ID, mention or username (discrim optional)
    # E.g. 80088516616269824, @Danny or Danny#0007

    # NOTE: typehinting acts as a converter within the `commands` framework only.
    # In standard Python, it is use for documentation and IDE assistance purposes.

    # If the conversion is successful, we will have a `discord.User` instance
    # and can do the following:
    user_id = user.id
    username = user.name
    avatar = user.avatar_url
    await ctx.send('User found: {} -- {}\n{}'.format(user_id, username, avatar))

@userinfo.error
async def userinfo_error(ctx: commands.Context, error: commands.CommandError):
    # if the conversion above fails for any reason, it will raise `commands.BadArgument`
    # so we handle this in this error handler:
    if isinstance(error, commands.BadArgument):
        return await ctx.send('Couldn\'t find that user.')

# Custom Converter here
class ChannelOrMemberConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        # In this example we have made a custom converter.
        # Specifically - to check if an input is convertable to a
        # `discord.Member` or `discord.TextChannel` instance from a
        # single input.
        # E.g. we have an ID we want to add to a list of ignored IDs, or similar

        member_converter = commands.MemberConverter()
        try:
            # Try and convert to a Member instance.
            member = await member_converter.convert(ctx, argument)
        except commands.MemberNotFound:
            # Could not convert to a Member instance.
            pass
        else:
            # We have our `member` so lets return here.
            return member

        # Do the same for TextChannel...
        textchannel_converter = commands.TextChannelConverter()
        try:
            channel = await textchannel_converter.convert(ctx, argument)
        except commands.ChannelNotFound:
            pass
        else:
            return channel

        # In the case that it was not converted we should return None for expliciness' sake.
        return None



@bot.command()
async def lockdown(ctx: commands.Context, argument: ChannelOrMemberConverter):
    # So from the command signature, you can see that for `argument` we have typehinted
    # the custom converter we defined previously.
    # What will happen during command invocation is that the `argument` above will be passed to
    # `ChannelOrMemberConverter.convert` and the conversion will go through the process defined there.

    if argument is None:
        return await ctx.send('No channel or member found with this argument.')
    await ctx.send('Locking down {}!'.format(argument.mention))

@bot.command()
async def ignore(ctx: commands.Context, target: typing.Union[discord.Member, discord.TextChannel]):
    # This command signature utilises the `typing.Union` typehint.
    # The `commands` framework attempts a conversion of each type in this Union *in order*.
    # So, it will attempt to convert whatever is passed to `target` to a `discord.Member` instance.
    # If that fails, it will attempt to convert it to a `discord.TextChannel` instance.
    # See: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#typing-union
    # NOTE: If a Union typehint converter fails it will raise `commands.BadUnionArgument`
    # instead of `commands.BadArgument`.

    # This is a an example of a Union converter to native discord.py types. For more flexibility please see the
    # previous Custom Converter example.

    # Let's check the type we actually got...
    if isinstance(target, discord.Member):
        await ctx.send('Member found: {}, adding them to the ignore list.'.format(target.mention))
    elif isinstance(target, discord.TextChannel): # this could be an `else` but for completeness' sake.
        await ctx.send('Channel found: {}, adding it to the ignore list.'.format(target.mention))

# Built-in type converters.
@bot.command()
async def multiply(ctx: commands.Context, number: int, maybe: bool):
    # We want an `int` and a `bool` parameter here.
    # `bool` is a slightly special case, as shown here:
    # See: https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#bool

    if maybe is True:
        return await ctx.send(number * 2)
    await ctx.send(number * 5)

bot.run('token')
