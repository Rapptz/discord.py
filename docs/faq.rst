.. currentmodule:: discord
.. _faq:

Frequently Asked Questions
===========================

This is a list of Frequently Asked Questions regarding using ``discord.py`` and its extension modules. Feel free to suggest a
new question or submit one via pull requests.

.. contents:: Questions
    :local:

Coroutines
------------

Questions regarding coroutines and asyncio belong here.

I get a SyntaxError around the word ``async``\! What should I do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This :exc:`SyntaxError` happens because you're using a Python version lower than 3.5. Python 3.4 uses ``@asyncio.coroutine`` and
``yield from`` instead of ``async def`` and ``await``.

Thus you must do the following instead: ::

    async def foo():
        await bar()

    # into

    @asyncio.coroutine
    def foo():
        yield from bar()

Don't forget to ``import asyncio`` on the top of your files.

**It is heavily recommended that you update to Python 3.5 or higher as it simplifies asyncio massively.**

What is a coroutine?
~~~~~~~~~~~~~~~~~~~~~~

A coroutine is a function that must be invoked with ``await`` or ``yield from``. When Python encounters an ``await`` it stops
the function's execution at that point and works on other things until it comes back to that point and finishes off its work.
This allows for your program to be doing multiple things at the same time without using threads or complicated
multiprocessing.

**If you forget to await a coroutine then the coroutine will not run. Never forget to await a coroutine.**

Where can I use ``await``\?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can only use ``await`` inside ``async def`` functions and nowhere else.

What does "blocking" mean?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In asynchronous programming a blocking call is essentially all the parts of the function that are not ``await``. Do not
despair however, because not all forms of blocking are bad! Using blocking calls is inevitable, but you must work to make
sure that you don't excessively block functions. Remember, if you block for too long then your bot will freeze since it has
not stopped the function's execution at that point to do other things.

A common source of blocking for too long is something like :func:`time.sleep`. Don't do that. Use :func:`asyncio.sleep`
instead. Similar to this example: ::

    # bad
    time.sleep(10)

    # good
    await asyncio.sleep(10)

Another common source of blocking for too long is using HTTP requests with the famous module ``requests``. While ``requests``
is an amazing module for non-asynchronous programming, it is not a good choice for :mod:`asyncio` because certain requests can
block the event loop too long. Instead, use the ``aiohttp`` library which is installed on the side with this library.

Consider the following example: ::

    # bad
    r = requests.get('http://random.cat/meow')
    if r.status_code == 200:
        js = r.json()
        await channel.send(js['file'])

    # good
    async with aiohttp.ClientSession() as session:
        async with session.get('http://random.cat/meow') as r:
            if r.status == 200:
                js = await r.json()
                await channel.send(js['file'])

General
---------

General questions regarding library usage belong here.

How do I set the "Playing" status?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a method for this under :class:`Client` called :meth:`Client.change_presence`. The relevant aspect of this is its
``game`` keyword argument which takes in a :class:`Game` object. Putting both of these pieces of info together, you get the
following: ::

    await client.change_presence(game=discord.Game(name='my game'))

How do I send a message to a specific channel?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You must fetch the channel directly and then call the appropriate method. Example: ::

    channel = client.get_channel(12324234183172)
    await channel.send('hello')

How do I upload an image?
~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload something to Discord you have to use the :class:`File` object.

A :class:`File` accepts two parameters, the file-like object (or file path) and the filename
to pass to Discord when uploading.

If you want to upload an image it's as simple as: ::

    await channel.send(file=discord.File('my_file.png'))

If you have a file-like object you can do as follows: ::

    with open('my_file.png', 'rb') as fp:
        await channel.send(file=discord.File(fp, 'new_filename.png'))

To upload multiple files, you can use the ``files`` keyword argument instead of ``file``\: ::

    my_files = [
        discord.File('result.zip'),
        discord.File('teaser_graph.png'),
    ]
    await channel.send(files=my_files)

If you want to upload something from a URL, you will have to use an HTTP request using ``aiohttp``
and then pass an :class:`io.BytesIO` instance to :class:`File` like so:

.. code-block:: python3

    import io
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(my_url) as resp:
            if resp.status != 200:
                return await channel.send('Could not download file...')
            data = io.BytesIO(await resp.read())
            await channel.send(file=discord.File(data, 'cool_image.png'))


How can I add a reaction to a message?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You use the :meth:`Message.add_reaction` method.

If you want to use unicode emoji, you must pass a valid unicode code point in a string. In your code, you can write this in a few different ways:

- ``'👍'``
- ``'\U0001F44D'``
- ``'\N{THUMBS UP SIGN}'``

Quick example: ::

    await message.add_reaction('\N{THUMBS UP SIGN}')

In case you want to use emoji that come from a message, you already get their code points in the content without needing
to do anything special. You **cannot** send ``':thumbsup:'`` style shorthands.

For custom emoji, you should pass an instance of :class:`Emoji`. You can also pass a ``'name:id'`` string, but if you
can use said emoji, you should be able to use :meth:`Client.get_emoji` to get an emoji via ID or use :func:`utils.find`/
:func:`utils.get` on :attr:`Client.emojis` or :attr:`Guild.emojis` collections.

Quick example: ::

    # if you have the ID already
    emoji = client.get_emoji(310177266011340803)
    await message.add_reaction(emoji)

    # no ID, do a lookup
    emoji = discord.utils.get(guild.emojis, name='LUL')
    if emoji:
        await message.add_reaction(emoji)

How do I pass a coroutine to the player's "after" function?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The library's music player launches on a separate thread, ergo it does not execute inside a coroutine.
This does not mean that it is not possible to call a coroutine in the ``after`` parameter. To do so you must pass a callable
that wraps up a couple of aspects.

The first gotcha that you must be aware of is that calling a coroutine is not a thread-safe operation. Since we are
technically in another thread, we must take caution in calling thread-safe operations so things do not bug out. Luckily for
us, :mod:`asyncio` comes with a :func:`asyncio.run_coroutine_threadsafe` function that allows us to call
a coroutine from another thread.

.. warning::

    This function is only part of 3.5.1+ and 3.4.4+. If you are not using these Python versions then use
    ``discord.compat.run_coroutine_threadsafe``.

However, this function returns a :class:`concurrent.Future` and to actually call it we have to fetch its result. Putting all of
this together we can do the following: ::

    def my_after(error):
        coro = some_channel.send('Song is done!')
        fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
        try:
            fut.result()
        except:
            # an error happened sending the message
            pass

    voice.play(discord.FFmpegPCMAudio(url), after=my_after)

How do I run something in the background?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Check the background_task.py example. <https://github.com/Rapptz/discord.py/blob/rewrite/examples/background_task.py>`_

How do I get a specific model?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are multiple ways of doing this. If you have a specific model's ID then you can use
one of the following functions:

- :meth:`Client.get_channel`
- :meth:`Client.get_guild`
- :meth:`Client.get_user`
- :meth:`Client.get_emoji`
- :meth:`Guild.get_member`
- :meth:`Guild.get_channel`

The following use an HTTP request:

- :meth:`abc.Messageable.get_message`
- :meth:`Client.get_user_info`


If the functions above do not help you, then use of :func:`utils.find` or :func:`utils.get` would serve some use in finding
specific models.

Quick example: ::

    # find a guild by name
    guild = discord.utils.get(client.guilds, name='My Server')

    # make sure to check if it's found
    if guild is not None:
        # find a channel by name
        channel = discord.utils.get(guild.text_channels, name='cool-channel')

Commands Extension
-------------------

Questions regarding ``discord.ext.commands`` belong here.

Is there any documentation for this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not at the moment. Writing documentation for stuff takes time. A lot of people get by reading the docstrings in the source
code. Others get by via asking questions in the `Discord server <https://discord.gg/discord-api>`_. Others look at the
source code of `other existing bots <https://github.com/Rapptz/RoboDanny>`_.

There is a `basic example <https://github.com/Rapptz/discord.py/blob/rewrite/examples/basic_bot.py>`_ showcasing some
functionality.

**Documentation is being worked on, it will just take some time to polish it**.

Why does ``on_message`` make my commands stop working?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overriding the default provided ``on_message`` forbids any extra commands from running. To fix this, add a
``bot.process_commands(message)`` line at the end of your ``on_message``. For example: ::

    @bot.event
    async def on_message(message):
        # do some extra stuff here

        await bot.process_commands(message)

Why do my arguments require quotes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a simple command defined as: ::

    @bot.command()
    async def echo(ctx, message: str):
        await ctx.send(message)

Calling it via ``?echo a b c`` will only fetch the first argument and disregard the rest. To fix this you should either call
it via ``?echo "a b c"`` or change the signature to have "consume rest" behaviour. Example: ::

    @bot.command()
    async def echo(ctx, *, message: str):
        await ctx.send(message)

This will allow you to use ``?echo a b c`` without needing the quotes.

How do I get the original ``message``\?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~ext.commands.Context` contains an attribute, :attr:`~.Context.message` to get the original
message.

Example: ::

    @bot.command()
    async def joined_at(ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send('{0} joined at {0.joined_at}'.format(member))

How do I make a subcommand?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``group`` decorator. This will transform the callback into a ``Group`` which will allow you to add commands into
the group operating as "subcommands". These groups can be arbitrarily nested as well.

Example: ::

    @bot.group()
    async def git(ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid git command passed...')

    @git.command()
    async def push(ctx, remote: str, branch: str):
        await ctx.send('Pushing to {} {}'.format(remote, branch))

This could then be used as ``?git push origin master``.

