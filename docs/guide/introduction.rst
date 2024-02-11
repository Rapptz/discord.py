.. currentmodule:: discord

.. _guide_intro:

Introduction
============

This page shows how to make a basic bot using the commands extension "ext.commands".
Before you begin, make sure to install discord.py - see :ref:`guide_install` for more information.

Obtaining a Bot Token
----------------------

You need a bot application before being able to run a bot. Creating one is easy:

1. Go to the `Discord Developer Portal <https://discord.com/developers/applications/>`_.

2. Create a new application if you have not made one already:
    .. image:: /images/discord_create_app_button.png
        :scale: 90 %

3. Navigate over to the ``bot`` tab:
    .. image:: /images/discord_bot_tab.png
        :scale: 80%

4. Your bot token will only be accessible upon creation and looks like this:
    .. image:: /images/discord_bot_token.png

4a. Otherwise it will look like this:
    .. image:: /images/discord_bot_token_no_copy.png

.. danger::

    This token is **VERY IMPORTANT** and you should treat it like the password to your bot. Keep it as secure as possible and never give this to anyone.
    If you ever leak it, you can click the ``Regenerate`` button to forcibly invalidate all copies of the token. This will also terminate all running instances of your bot.
    You can find more information at :ref:`securing_token`.

.. _guide_quickstart_client_secret:

.. warning::

    If you accidentally use the ``Client Secret`` for your bot token, it's **NOT** what you are looking for - you need the bot **Token**, which has a different format.

    .. image:: /images/discord_client_secret_big_nono.png
        :scale: 90 %

Creating a simple bot
---------------------

This step-by-step walk-through will show you how to make a bot using the commands framework.

.. note::

    This walk-through does not cover application commands (slash commands). For a detailed walk-through of application commands, see :ref:`_guide_app_commands`.


1. Create a new Python file in the folder you want to work in.

    .. warning::

        Do not name the file ``discord.py``, as this will cause conflicts with the discord.py library. Likewise, do not create a sub-folder in your project named ``discord``, as that too will cause conflicts.

2. Open the new Python file in your preferred editor.

    If you do not have an editor installed, you can use a community recommended one, such as `Visual Studio Code <https://code.visualstudio.com/>`_,
    `PyCharm <https://www.jetbrains.com/pycharm/>`_ or `Sublime Text 4 <https://www.sublimetext.com/>`_.
    We don't recommend Python's built in IDLE, as the lack of features compared to other simple editors makes it difficult to use for projects with many files.

3. Now you can start creating your bot. The following steps will go over a simple bot line-by-line to help you understand what's happening.

First, you need to import the discord.py library:

.. code-block:: python3
    :emphasize-lines: 2

    import discord
    from discord.ext import commands

We import ``discord.ext.commands`` here as we will need it for our bot.
This manner of importing ``commands`` is important. ``discord.ext`` is a namespace package and this means you cannot directly import from it, and it must be accessed via name, like above.

.. code-block:: python3

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', description='This is my awesome bot!', intents=intents)

This is your bot instance. You can name the variable whatever you like but it is customary to name :class:`~ext.commands.Bot` instances ``bot``.
You will need to specify a ``command_prefix`` here, we use ``!``, but you can use any string, or a list of strings for multiple prefixes.
We also add the :attr:`Intents.message_content` intent, so that our bot can read regular text messages. You can read more in the `Intents guide <_guide_intents>`_.

.. note::
    This use of :class:`~ext.commands.Bot` is using the library provided implementation of Bot. For extending usage you may wish to consider subclassing it.


.. code-block:: python

    @bot.listen()
    async def on_ready():
        print(f'Ready! I am {bot.user} and my ID is {bot.user.id}')

This is the :func:`on_ready` event. It is called when the bot has finished loading and everything necessary is cached.
We use the :meth:`@bot.listen() <ext.commands.Bot.listen>` decorator as to not override the main event.
For a list of available events, see :ref:`discord-api-events`.

Since you will likely want to override other events, such as the one that exists for any new message the bot can read, you should consider this warning `here <ext_commands_on_message>`.

.. warning::

    :func:`on_ready` can and will be called multiple times throughout your bot's uptime. You should avoid doing any kind of state-management here, such as connecting and loading your database.

    Consider using :meth:`~ext.commands.Bot.setup_hook` for this purpose instead.

Moving on further, let's now create a basic command that can take further input from the person sending the message:-

.. code-block:: python

    @bot.command()
    async def apples(ctx: commands.Context, amount: int) -> None:
        await ctx.send(f"Hello, I would like {amount} apples please!")

Here's where our commands will be defined. We use the :meth:`@bot.command() <ext.commands.Bot.command>` decorator to flag this function as a command.
This creates a command ``!apples`` that we can type into a channel, and the bot will respond with the given amount of applies in a predefined sentence.. A few key features:

- :class:`~ext.commands.Context` refers to the command invocation context - this includes the :attr:`~ext.commands.Context.channel`, command :attr:`~ext.commands.Context.author`, :attr:`~ext.commands.Context.message` and more.
- Using ``int`` as a parameter type annotation here will instruct the library to attempt the given argument to an :class:`int` type. This means you'll have an integer in the command body and not a string.

For more information on the commands extension and other converters, please reference :ref:`ext_commands_commands`.

.. code-block:: python

    TOKEN = "your bot token here"

This is the final step, you put your bot token here, save and run the file and the bot will start up.

.. note::

    :meth:`~ext.commands.Bot.run` is :ref:`blocking <faq_blocking>`, so any code after it will **not be run** until the bot has been stopped.

.. warning::

    As this is an example, token security is not applied here. However, you should be very careful with your bot token. Keep it in a secure place and only access it when you are starting the bot.
    See :ref:`securing_token` for more information.

.. _quickstart_newbot_newcog:

Convenience methods
~~~~~~~~~~~~~~~~~~~

discord.py provides a pair of useful cli tools for getting a fresh workspace up and ready to go. These utilities are:-

- ``newbot``
- ``newcog``

They can be used like so:-

.. code-block:: shell
    :emphasize-lines: 1

    $ python -m discord newbot CoolBot
    > successfully made bot at /your/path/CoolBot

    $ ls CoolBot/
    > bot.py cogs/ config.py .gitignore

Using these utilities will create a basic bot project with an assortment of essentials for getting started. This includes:-

- A basic ``bot.py`` which is prefilled with a basic :class:`~ext.commands.Bot` subclass and functionality for extending it.
- A ``cogs/`` directory for creating extension files in with Cog functionality (which is optional).
- A ``config.py`` which acts as your token or general configuration storage.
- A ``.gitignore`` file so you don't accidentally push the ``config.py`` file to a version control system like GitHub.

There is also ``newcog`` which does the following:-

.. code-block:: shell
    :emphasize-lines: 1

    $ python -m discord newcog CoolCog CoolBot/cogs
    > successfully made cog at CoolBot/cogs/CoolCog.py

This tool creates a new file within the passed directory with the provided name, and again this is a blanket implementation of an :ref:`extension <ext_commands_extensions>` file for use with the :meth:`~ext.commands.Bot.load_extension` method.

The file imports the necessary items and defines a Cog class that you can extend, and adds the necessary ``setup`` method for the extension to function correctly.


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

.. _securing_token:

Securing your bot's token
--------------------------

Your bot's token is **very important**. If a malicious user obtains it, they can delete your private guilds or get you and your bot banned.
This short sub-guide shows a few basic ways to secure your token, so it's not publicly obtainable.

.. note::

    This will not go over securing your bot's host system (i.e. VPS). Make sure your system is private and only you and authorized users can access it.

1. Create a config file.

    There are a few options for this, and you can choose whichever you prefer:

    - JSON, YAML, TOML
    - Python (you can import the config!)
    - Environment Variable (either on your system, or with a ``.env`` file)

    For this example, we will use a Python file.

2. Store your token and other secrets here.

    .. code-block:: python

        token = "123"
        database_password = "hello_world"

3. Import your config module into your main bot file

    .. code-block:: python

        import config


        bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
        bot.run(config.my_token)

4. If you store your bot's code on a public repository (e.g. GitHub), you can create a ``.gitignore`` file to prevent pushing the config file:

    .. code-block:: shell

        # file: .gitignore
        config.py

And here we commit and add it to the git repository for tracking:

    .. code-block:: shell

        $ git add .gitignore
        $ git commit -m "Add .gitignore"
        $ git status
        # notice how there is no more ``config.py``!
        On branch master
        no changes to commit, working tree clean

By doing this, the config file will not exist on the repository. If you wish to ever move your bot, you should copy the config file from your old system to your new one, or create a new config file.

Common Issues
--------------

Is your bot not starting, or is something going wrong? Here is a list of possible reasons:

Improper token has been passed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get an :exc:`LoginFailure` exception with a message ``"Improper token has been passed"`` this means you have passed an invalid token to :meth:`bot.run() <ext.commands.Bot.run>`:

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
- - There are two ways to fix this: either replace ``@bot.event`` with :meth:`@bot.listen() <ext.commands.Bot.listen>`, or add :meth:`~ext.commands.Bot.process_commands` to your ``on_message`` event. See :ref:`here <ext_commands_on_message>` for more information.
- You may be missing the :attr:`Intents.message_content` intents. Further information can be found in the `Intents guide <_guide_intents>`_.

I can't find my issue here
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you've encountered a different issue, or need further support for other reasons, you can join our `public Discord server <https://discord.gg/dpy/>`_ and ask your question there - we'll be happy to help.
