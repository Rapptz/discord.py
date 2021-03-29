.. _quickstart:

.. currentmodule:: discord

Quickstart
============

This page gives a brief introduction to the library. It assumes you have the library installed,
if you don't check the :ref:`installing` portion.

A Minimal Bot
---------------

Let's make a bot that responds to a specific message and walk you through it.

It looks something like this:

.. code-block:: python3

    import discord

    client = discord.Client()

    @client.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(client))

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

    client.run('your token here')

Let's name this file ``example_bot.py``. Make sure not to name it ``discord.py`` as that'll conflict
with the library.

There's a lot going on here, so let's walk you through it step by step.

1. The first line just imports the library, if this raises a `ModuleNotFoundError` or `ImportError`
   then head on over to :ref:`installing` section to properly install.
2. Next, we create an instance of a :class:`Client`. This client is our connection to Discord.
3. We then use the :meth:`Client.event` decorator to register an event. This library has many events.
   Since this library is asynchronous, we do things in a "callback" style manner.

   A callback is essentially a function that is called when something happens. In our case,
   the :func:`on_ready` event is called when the bot has finished logging in and setting things
   up and the :func:`on_message` event is called when the bot has received a message.
4. Since the :func:`on_message` event triggers for *every* message received, we have to make
   sure that we ignore messages from ourselves. We do this by checking if the :attr:`Message.author`
   is the same as the :attr:`Client.user`.
5. Afterwards, we check if the :class:`Message.content` starts with ``'$hello'``. If it is,
   then we send a message in the channel it was used in with ``'Hello!'``.
6. Finally, we run the bot with our login token. If you need help getting your token or creating a bot,
   look in the :ref:`discord-intro` section.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 example_bot.py

On other systems:

.. code-block:: shell

    $ python3 example_bot.py

Now you can try playing around with your basic bot.

An Advanced Bot
---------------

Let's make a bot that supports a dynamic style of adding commands. This is for more advanced 
discord.py users or expirenced python programmers.

Pros
 * Easier to configure command driven commands.
 * Easier to debug for issues.
 * Modular code for ease of adding and removing commands.
Cons
 * Bulky for light bot applications.
 * Requires higher level of python knowledge.

Note: This example was written with discord.py v1.6.0 in mind.

File Structure
^^^^^^^^^^^^^^^

A good file structure comes in many shapes and sizes, but this is the one we will be 
following for this example:

::

    my_bot_folder/
    ├── cogs/
    │   ├── commands/
    │   │   ├── basic.py
    │   │   └── reload.py
    │   ├── listeners/
    │   │   └── message_updates.py
    │   └── tasks/
    ├── advanced_bot.py
    └── config.py


Main Bot File
^^^^^^^^^^^^^^^

Lets start with the main bot file and name it ``advanced_bot.py``:

advanced_bot.py
"""""""""""""""
.. code-block:: python3

    import glob

    import discord
    from discord.ext.commands import Bot
    import config

    BOT = Bot(
        # This is the symbol(s) you use to tell the bot it's a command
        command_prefix=config.prefix,
        # Used to designate what the bot needs as input to function. 
        # For more info: https://discordpy.readthedocs.io/en/latest/api.html#intents
        intents=discord.Intents.default(),
        # This makes the command `$hello` and `$Hello` act as the same command.
        case_insensitive=True
        )

    @BOT.event
    async def on_ready():
        """ Called when the client is done preparing the data received from Discord.

        For more information:
        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_ready
        """
        # Showing on console that the bot is ready.
        print(f"Logged in as: {BOT.user.name}")
        print(f"discord.py version: {discord.__version__}")

        # Adding in a activity message when the bot begins.
        await BOT.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{config.prefix}help"
            )
        )

    @BOT.event
    async def on_message(message: discord.Message):
        """ This event listener has been moved to cogs/listeners/message_updates.py

        Unfortuneatley, this listener has to remain and do nothing, otherwise,
        any message will be ran twice and cause issues.
        """
        pass # Do nothing

    if __name__ == '__main__':
        # Recursively loads in all the files in the folder named cogs.
        # Skips over any files that start with '__' or do not end with .py.
        for cog in glob.iglob("cogs/**/[!^_]*.py", recursive=True):
            if "\\" in cog:  # Fix pathing on Windows.
                BOT.load_extension(cog.replace("\\", ".")[:-3])
            else:  # Fix pathing on Linux.
                BOT.load_extension(cog.replace("/", ".")[:-3])

        # Finally, run the bot.
        BOT.run(config.token)

Let's name this file ``advanced_bot.py``. Make sure not to name it ``discord.py`` as that'll conflict
with the library.

There is too much going on to explain step by step, and this example will assume you know your way 
around python already, so let's walk through some key points.

1. The first lines just imports the library, if this raises a `ModuleNotFoundError` or `ImportError`
    then head on over to :ref:`installing` section to properly install.
2. This bot structure uses the bot extension of discord.py. We create an instance of a :class:`Bot` 
   with `discord.ext.commands.Bot()` but that is a mouthful, we shorten it with a specific import 
   of `Bot`.
3. We use the :meth:`Bot.event` decorator to register an event. This library has many events.
   Since this library is asynchronous, we do things in a "callback" style manner. Do note though, 
   `@bot.event` syntax is unique to the first starting file for this example.
4. The :func:`on_ready` event triggers when all the guilds and other info is loaded into memory.
   This event isn't guaranteed to be the first event triggered nor trigger only once.
5. Because of the nature of on_ready, it's a good location to give an activity presence to the bot.
   This looks just like when your friends have the text of "Now playing" or "Listening to x song"
   but is instead on the bot.
6. The way discord.py is built, it will assume an on_message function if none is present, this gives
   us problems when we wish to consolidate all the listeners into one cog file. Therefore, we will 
   give it a function to "eat" the second command.
7. Lastly, the cog loader is the bread and butter of the whole operation. This for loop will load all
   files  under the cogs folder even if its nested under a lot of folders. We have to be disciplined 
   to not put non-cog python files in the cogs folder or else things might break.


Configuration
^^^^^^^^^^^^^^^

Lets name this file ``config.py``.

config.py
"""""""""""""""
.. code-block:: python3

    # Discord Bot token
    token = 'your token here'
    # Symbol(s) that designate that a message is a command.
    prefix = '$'

This config is very basic but will most likely become increasingly complex as the bot grows. Some devs
use a yaml file, json, or even a database to store their configurations. For this example, we will just use a
simple config.py file.

After these two files, the bot should be in a running state, but a bot is useless without commands to
follow. Lets show how you can add features to your bot.

Listeners
^^^^^^^^^^^^^^^
Lets setup a listener cog named ``message_updates.py``. This will be used for message events.

message_updates.py
""""""""""""""""""
.. code-block:: python3

    from discord import Message
    from discord.ext.commands import Cog, Bot


    class MessageUpdates(Cog):
        """ Message event handler cog. """

        def __init__(self, bot: Bot):
            self.bot = bot

        @Cog.listener()
        async def on_message_edit(self, before: Message, after: Message):
            """ Event Listener which is called when a message is edited.

            Note:
                This requires Intents.messages to be enabled.

            Parameters:
                before (Message): The previous version of the message.
                after (Message): The current version of the message.

            For more information:
                https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message_edit
            """
            # Ignore bots
            if after.author.bot:
                return
            # Links that have embeds, such as picture URL's are considered edits and need to be ignored.
            if before.clean_content == after.clean_content:
                return
            # This makes it where users may fix their typo in a command without making a new messaage.
            await self.bot.process_commands(after)

        @Cog.listener()
        async def on_message(self, message: Message):
            """ Event Listener which is called when a Message is created and sent.

            Parameters:
                message (Message): A Message of the current message.

            Warning:
                Your bot’s own messages and private messages are sent through this event.

            Note:
                This requires Intents.messages to be enabled.

            For more information:
                https://discordpy.readthedocs.io/en/latest/api.html#discord.on_message
            """
            # Ignore messages from all bots (this includes itself).
            if message.author.bot:
                return
            # Run command if it is one
            await self.bot.process_commands(message)

    # The setup function below is necessary for cog files.
    def setup(bot: Bot) -> None:
        """ Load the message_updates cog. """
        bot.add_cog(MessageUpdates(bot))
        print("Cog loaded: message_updates")

Commands
^^^^^^^^^^^^^^^
Lets add some commands.

basic.py
"""""""""
.. code-block:: python3

    import discord
    from discord.ext import commands
    from discord.ext.commands import Bot, Cog, Context


    class Basic(Cog):
        """Basic cog"""

        def __init__(self, bot):
            self.bot = bot

        @commands.bot_has_permissions(read_message_history=True, send_messages=True)
        @commands.command(name="ping", aliases=["latency"])
        async def ping(self, ctx: Context):
            """Returns the Discord WebSocket latency."""
            await ctx.reply(f"Bot latency is: {round(self.bot.latency * 1000)}ms.")

        @commands.bot_has_permissions(send_messages=True)
        @commands.command(name="count")
        async def count(self, ctx: Context):
            """Returns the current guild member count."""
            await ctx.send(ctx.guild.member_count)

        @commands.bot_has_permissions(send_messages=True, embed_links=True)
        @commands.command(name='profile_picture', aliases=["pfp", "avatar", "profilepicture"])
        async def pfp(self, ctx: Context, user: discord.User = None):
            """Returns the profile picture of the invoker or the mentioned user."""
            # If no user is given, then use the author.
            user = user or ctx.author

            # Making an embed with the user's name as the title and profile picure.
            embed = discord.Embed(colour=0xe91e63, description=f"{user.mention}'s Profile Picture")
            embed.set_image(url=user.avatar_url)

            # Set the author of the embed as the command user and timestamp it.
            embed.set_author(
                icon_url=ctx.author.avatar_url,
                name=str(ctx.author))
            embed.timestamp = ctx.message.created_at
            await ctx.send(embed=embed)


    # The setup function below is necessary for cog files.
    def setup(bot: Bot) -> None:
        """Load the Basic cog."""
        bot.add_cog(Basic(bot))
        print("Cog loaded: basic")

Lets go over what this cog does.

1. First every cog has to have a function ``setup(bot)`` that add's the cog or else it will 
   not be considered a cog. You can find said function at the bottom of this code.
2. Although not required, it is most of the time easier to put all your functions in classes.
   Programmers love classy bots 😉.
3. Adding checks to commands makes the robust for debugging and ease of making error messages.
   This cog has checks on each function called ``bot_has_permissions`` this will give properl
   errors if the required permissions for the command to operate are not given.
4. The doc strings of each function give them descriptions in the help command. This is extreamly
   helpful in documenting your bot for the discord users trying to use your bot!

TODO - Check to see if there is more details to give.

reload.py
"""""""""
.. code-block:: python3

    import glob
    import re

    import discord
    from discord.ext import commands
    from discord.ext.commands import Bot, Cog, Context


    class Reload(Cog):
        """Reload Cog"""

        def __init__(self, bot: Bot):
            self.bot = bot

        @commands.is_owner() # Only allow you to run this command.
        @commands.bot_has_permissions(add_reactions=True, send_messages=True)
        @commands.command(name="reload")
        async def reload_cog(self, ctx: Context):
            """Reloads cogs."""
            
            # Reload all the cogs in the folder named cogs.
            # Skips over any files that start with '__' or do not end with .py.
            try:
                for cog in glob.iglob("cogs/**/[!^_]*.py", recursive=True):
                    if "\\" in cog:  # Pathing on Windows.
                        self.bot.reload_extension(cog.replace("\\", ".")[:-3])
                    else:  # Pathing on Linux.
                        self.bot.reload_extension(cog.replace("/", ".")[:-3])
            except commands.ExtensionError as error:
                await ctx.message.add_reaction("❌")
                await ctx.send(f'{error.__class__.__name__}: {error}')

            else:
                await ctx.message.add_reaction("✔")
                await ctx.send("Reloaded all modules!")


    # The setup function below is necessary for cog files.
    def setup(bot: Bot) -> None:
        """Load the Reload cog."""
        bot.add_cog(Reload(bot))
        print("Cog loaded: reload")

TODO - explain this cog.


Tasks
^^^^^^^^^^^^^^^

TODO - make a simple task and explain it.

Starting Up
^^^^^^^^^^^^^^^

TODO - explain how to run the program.


Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a
Python script, we can run it directly.

On Windows:

.. code-block:: shell

    $ py -3 advanced_bot.py

On other systems:

.. code-block:: shell

    $ python3 advanced_bot.py

Now you can try playing around with your advanced bot.

TODO - Check for grammer and spelling.
TODO - Fix and make more refrence links.
