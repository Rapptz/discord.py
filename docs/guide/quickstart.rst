:orphan:

.. currentmodule:: discord

.. _guide_quickstart:

Quickstart
===========

This page will contain a simple explanation of how to make a basic bot using the commands extension "ext.commands".
Before you begin, make sure to install discord.py - see :ref:`guide_intro_installation` for more information.

Obtaining a Bot Token
----------------------

You will need a bot application before being able to run a bot. A step-by-step tutorial with screenshots follows:

1. Go to the `Discord Developer Portal <https://discord.com/developers/applications/>`_.
2. Create a new application if you have not made one already:
    .. image:: /images/discord_create_app_button.png
        :scale: 90 %
    
    Be sure to give it a good name!
3. Navigate over to the ``bot`` tab:
    .. image:: /images/discord_bot_tab.png
        :scale: 80 %
4. Create a new Bot user if you have not done so already:
    .. image:: /images/discord_create_bot_user.png
        :scale: 80 %
5. If you need these intents, scroll down and click on these check boxes:
    .. image:: /images/discord_privileged_intents.png
        :scale: 80%
6. Copy your bot token here:
    .. image:: /images/discord_bot_token.png
        :scale: 100%
    
.. danger::

    This token is **VERY IMPORTANT** and you should treat it like the password to your bot. Keep it as secure as possible and never give this to anyone.
    If you ever leak it, you can click the ``Regenerate`` button to forcibly invalidate all copies of the token. This will also terminate all running instances of this bot.

.. _guide_quickstart_client_secret:

.. warning::

    You may be thinking to use the ``Client Secret`` for your bot token. This is **NOT** what you are looking for, you need the bot **Token**, which is a completely different format.

    .. image:: /images/discord_client_secret_big_nono.png
        :scale: 90 %

A Simple Bot
-------------

This step-by-step walkthrough will show you how to make a bot using the commands framework.

.. note::

    This walkthrough does not cover application commands (slash commands). For a detailed walkthrough of application commands, see [insert guide here].

1. Create a new Python file in the folder you want to work in.

    .. warning::

        Do not name the file ``discord.py``, this will cause conflicts with the discord.py library. Also, do not create a sub-folder in your project named ``discord``, as that too will cause conflicts.
    
2. Open the new Python file in your preferred editor.

    If you do not have an editor installed, you can use a community recommended one, such as `Visual Studio Code <https://code.visualstudio.com/>`_,
    `PyCharm <https://www.jetbrains.com/pycharm/>`_ or `Sublime Text 4 <https://www.sublimetext.com/>`_.
    We don't recommend Python's built in IDLE, as the lack of features compared to other simple editors makes it very bothersome for projects with many files.

3. Now you can start creating your bot. The following steps will go over a simple bot line-by-line to help you understand what's happening.

First, you need to import the discord.py library:

.. code-block:: python

    import discord
    from discord.ext import commands

We import ``discord.ext.commands`` here as we will need it for our bot.

.. code-block:: python

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", description="This is my awesome bot!", intents=intents)

This is your bot instance. You can name the variable whatever you like but for simplicity's sake we will name it ``bot``.
You will need to specify a ``command_prefix`` here, we use ``!``, but you can use any string, or a list of strings for multiple prefixes.

.. note::

    ``Intents`` are the method to specify which gateway events you wish to receive. ``Intents.default()`` means you will receive all events that are not locked behind bot verification.
    For more information, see :ref:`intents_primer`.

.. code-block:: python

    @bot.listen()
    async def on_ready():
        print("Ready! I am", bot.user, "and my ID is", bot.user.id)

This is the ``ready`` event. It is called when the bot has finished loading and everything is cached.
We use the :meth:`@bot.listen() <ext.commands.Bot.listen>` decorator as to not override the main event.
For a list of available events, see :ref:`discord-api-events`.

.. _guide_quickstart_bot_event_warning:

.. warning::

    Using :meth:`@bot.event <ext.commands.Bot.event>` is also valid, but keep in mind that using :meth:`@bot.event <ext.commands.Bot.event>` with the ``on_message`` event can cause your commands to stop responding.
    To remedy this, either switch to :meth:`@bot.listen() <ext.commands.Bot.listen>`, or add :meth:`~ext.commands.Bot.process_commands` to your ``on_message`` event:

    .. code-block:: python

        @bot.event
        async def on_message(message: discord.Message):
            print(f'Received "{message.clean_content}" from {message.author}')
            # IMPORTANT:
            await bot.process_commands(message)

.. warning::

    ``on_ready`` can and will be called multiple times throughout your bots uptime. You should avoid doing any kind of state-management here, such as connecting and loading your database.

.. code-block:: python

    @bot.command()
    async def echo(ctx: commands.Context, *, sentence: commands.clean_content):
        await ctx.send(sentence)

Here's where our commands will be defined. We use the :meth:`@bot.command() <ext.commands.Bot.command>` decorator to flag this function as a command.
This creates a command ``!echo`` that we can type into a channel, and the bot will respond with the given sentence. A few key features:

- :class:`~ext.commands.Context` refers to the command invocation context - this includes the :attr:`~ext.commands.Context.channel`, command :attr:`~ext.commands.Context.author`, :attr:`~ext.commands.Context.message` and more.
- The ``*`` is a sign to tell discord.py that the following parameter should **consume all text afterward** and condense it into that parameter.
    .. note::
    
        As this consumes all text, parameters defined **after the next** will never be filled, so you should never have more than one parameter after the ``*``.

- :meth:`~ext.commands.clean_content` is a :ref:`Converter <ext_commands_api_converters>` used to clean user pings and ``@everyone`` mentions. This way people will not be able to ping everyone by using your bot. For more information, see :ref:`ext_commands_commands_converters`.

.. code-block:: python

    TOKEN = "your bot token here"
    bot.run(TOKEN)

This is the final step, you put your bot token here, save and run the file and the bot will start up.

.. note::

    :meth:`~ext.commands.Bot.run` is blocking, so any code after it will **not be run** until the bot has been stopped.

.. warning::

    As this is an example, token security is not applied here. However, you should be very careful with your bot token. Keep it in a secure place and only access it when you are starting the bot.


Running Your New Bot
---------------------

Now that you have your code ready, go to your terminal and ``cd`` into your project directory:

.. code-block:: shell

    $ cd my_bot_folder

Activate the virtual environment (if you made one):

.. code-block:: shell

    $ source .venv/bin/activate  # for Linux users
    $ .\.venv\Scripts\activate   # for Windows users

And run your bot!

.. code-block:: shell

    (.venv) $ python your_bot.py
    Ready! I am Documentation#7968 and my ID is 699701272739053589

.. image:: /images/discord_echo_example.png
    :scale: 100 %

Common Issues
--------------

Is your bot not starting, or is something going wrong? Here is a list of possible reasons:

Improper token has been passed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get a traceback similar to:

.. code-block:: python

    Traceback (most recent call last):
        File "G:\Programming\Python\discord.py-2.0\bot.py", line 17, in <module>
            bot.run(INVALID_TOKEN)
        File "G:\Programming\Python\discord.py-2.0\discord\client.py", line 704, in run
            return future.result()
        File "G:\Programming\Python\discord.py-2.0\discord\client.py", line 683, in runner
            await self.start(*args, **kwargs)
        File "G:\Programming\Python\discord.py-2.0\discord\client.py", line 646, in start
            await self.login(token)
        File "G:\Programming\Python\discord.py-2.0\discord\client.py", line 512, in login
            data = await self.http.static_login(token.strip())
        File "G:\Programming\Python\discord.py-2.0\discord\http.py", line 537, in static_login
            raise LoginFailure('Improper token has been passed.') from exc
    discord.errors.LoginFailure: Improper token has been passed.

This means you have passed an invalid token to :meth:`bot.run() <ext.commands.Bot.run>`:

- Perhaps you are reading from your secure file incorrectly?
- Did you copy the :ref:`Client Secret <guide_quickstart_client_secret>` instead of your bot token?
- Did you regenerate your token?

Be sure to copy the correct token from the bot tab on the Discord developer portal. A real token looks like: ::

    MjM4NDk0NzU2NTIxMzc3Nzky.CunGFQ.wUILz7z6HoJzVeq6pyHPmVgQgV4

My bot isn't responding to commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you ran a command, but the bot isn't responding, there can be a few reasons why.

- Are you using the correct prefix?
- - If you set ``command_prefix="!"``, you must invoke the command with that specific prefix, e.g. ``!echo Hello, world``
- Did you override ``on_message`` using :meth:`@bot.event <ext.commands.Bot.event>`?
- - There are two ways to fix this: either replace ``@bot.event`` with :meth:`@bot.listen() <ext.commands.Bot.listen>`, or add :meth:`~ext.commands.Bot.process_commands` to your ``on_message`` event. See :ref:`here <guide_quickstart_bot_event_warning>` for more information.

I can't find my issue here
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you've encountered a different issue, or need further support for other reasons, you can join our `public Discord server <https://discord.gg/dpy/>`_ and ask your question there - we'll be happy to help.