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

A Command Bot
---------------

This is a bot style is geared towards command driven events instead of using if else statements 
to filter for commands. It adds robust features such as ease of command documentation, command
aliases, permission checks, and much more.

command_bot.py
"""""""""""""""
.. code-block:: python3

    import discord
    from discord.ext import commands

    PREFIX = '$'

    bot = commands.Bot(
        command_prefix=PREFIX,
        # For info about intents: https://discordpy.readthedocs.io/en/stable/intents.html
        intents=discord.Intents.default(),
        # This makes the commands `$hello` and `$Hello` act as the same command.
        case_insensitive=True)

    @bot.event
    async def on_ready():
        print('Bot logged in as: {0.user}'.format(bot))

    @bot.command(name='hello', aliases=['hi'])
    async def hello(ctx: commands.Context):
        """Replies to the user with a greeting."""
        await ctx.reply('Hello {0.author}!'.format(ctx))

    # Run the bot.
    bot.run('your token here')

Let's walk through the program step by step.

1. The first lines just import the library and commands extension.
2. Next, we give the program the prefix. This tells the bot what messages to consider as commands.
3. Then, we create an instance of a Bot using the commands extension. 
   This acts similar to :class:`Client`.
5. We use the ``@bot.event`` decorator to register an event and ``@bot.command`` for commands.
   This is what makes python functions act as commands. By default, if no name is specified, the command
   name will be the function name. 
6. The ``hello()`` command will simply reply to your command with a greeting.
7. The docstrings of each command give descriptions in the help command. This is extremely
   helpful in making your bot more user-friendly.
8. You will need to type your bot's token in the ``'your token here'`` field. The bot is now complete.
   If you need help getting your token or creating a bot, look in the :ref:`discord-intro` section.

This bot executes in the same manner the Minimal Bot does. If you need assistance in running, 
refer to its documentation on how to run the code.

Once your bot is running, type ``$hello`` in a channel you and your bot are in.
