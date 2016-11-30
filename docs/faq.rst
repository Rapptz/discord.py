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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This ``SyntaxError`` happens because you're using a Python version lower than 3.5. Python 3.4 uses ``@asyncio.coroutine`` and
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
~~~~~~~~~~~~~~~~~~~~~~~~~~

In asynchronous programming a blocking call is essentially all the parts of the function that are not ``await``. Do not
despair however, because not all forms of blocking are bad! Using blocking calls is inevitable, but you must work to make
sure that you don't excessively block functions. Remember, if you block for too long then your bot will freeze since it has
not stopped the function's execution at that point to do other things.

A common source of blocking for too long is something like ``time.sleep(n)``. Don't do that. Use ``asyncio.sleep(n)``
instead. Similar to this example: ::

    # bad
    time.sleep(10)

    # good
    await asyncio.sleep(10)

Another common source of blocking for too long is using HTTP requests with the famous module ``requests``. While ``requests``
is an amazing module for non-asynchronous programming, it is not a good choice for ``asyncio`` because certain requests can
block the event loop too long. Instead, use the ``aiohttp`` library which is installed on the side with this library.

Consider the following example: ::

    # bad
    r = requests.get('http://random.cat/meow')
    if r.status_code == 200:
        js = r.json()
        await client.send_message(channel, js['file'])

    # good
    async with aiohttp.get('http://random.cat/meow') as r:
        if r.status == 200:
            js = await r.json()
            await client.send_message(channel, js['file'])

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

If you have its ID then you can do this in two ways, first is by using :class:`Object`\: ::

    await client.send_message(discord.Object(id='12324234183172'), 'hello')

The second way is by calling :meth:`Client.get_channel` directly: ::

    await client.send_message(client.get_channel('12324234183172'), 'hello')

I'm passing IDs as integers and things are not working!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the library IDs must be of type ``str`` not of type ``int``. Wrap it in quotes.

How do I upload an image?
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways of doing it. Both of which involve using :meth:`Client.send_file`.

The first is by opening the file and passing it directly: ::

    with open('my_image.png', 'rb') as f:
        await client.send_file(channel, f)

The second is by passing the file name directly: ::

    await client.send_file(channel, 'my_image.png')

How can I add a reaction to a message?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You use the :meth:`Client.add_reaction` method.

If you want to use unicode emoji, you must pass a valid unicode code point in a string. In your code, you can write this in a few different ways:

- ``'👍'``
- ``'\U0001F44D'``
- ``'\N{THUMBS UP SIGN}'``

In case you want to use emoji that come from a message, you already get their code points in the content without needing to do anything special.
You **cannot** send ``':thumbsup:'`` style shorthands.

For custom emoji, you should pass an instance of :class:`discord.Emoji`. You can also pass a ``'name:id'`` string, but if you can use said emoji,
you should be able to use :meth:`Client.get_all_emojis`/:attr:`Server.emojis` to find the one you're looking for.

How do I pass a coroutine to the player's "after" function?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A StreamPlayer is just a ``threading.Thread`` object that plays music. As a result it does not execute inside a coroutine.
This does not mean that it is not possible to call a coroutine in the ``after`` parameter. To do so you must pass a callable
that wraps up a couple of aspects.

The first gotcha that you must be aware of is that calling a coroutine is not a thread-safe operation. Since we are
technically in another thread, we must take caution in calling thread-safe operations so things do not bug out. Luckily for
us, ``asyncio`` comes with a ``asyncio.run_coroutine_threadsafe``
`function <https://docs.python.org/3.5/library/asyncio-task.html#asyncio.run_coroutine_threadsafe>`_ that allows us to call
a coroutine from another thread.

.. warning::

    This function is only part of 3.5.1+ and 3.4.4+. If you are not using these Python versions then use
    ``discord.compat.run_coroutine_threadsafe``.

However, this function returns a ``concurrent.Future`` and to actually call it we have to fetch its result. Putting all of
this together we can do the following: ::

    def my_after():
        coro = client.send_message(some_channel, 'Song is done!')
        fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
        try:
            fut.result()
        except:
            # an error happened sending the message
            pass

    player = await voice.create_ytdl_player(url, after=my_after)
    player.start()

Why is my "after" function being called right away?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``after`` keyword argument expects a *function object* to be passed in. Similar to how ``threading.Thread`` expects a
callable in its ``target`` keyword argument. This means that the following are invalid:

.. code-block:: python

    player = await voice.create_ytdl_player(url, after=self.foo())
    other  = await voice.create_ytdl_player(url, after=self.bar(10))

However the following are correct:

.. code-block:: python

    player = await voice.create_ytdl_player(url, after=self.foo)
    other  = await voice.create_ytdl_player(url, after=lambda: self.bar(10))

Basically, these functions should not be called.


How do I run something in the background?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Check the background_task.py example. <https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py>`_

How do I get a specific User/Role/Channel/Server?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are multiple ways of doing this. If you have a specific entity's ID then you can use
one of the following functions:

- :meth:`Client.get_channel`
- :meth:`Client.get_server`
- :meth:`Server.get_member`
- :meth:`Server.get_channel`

If the functions above do not help you, then use of :func:`utils.find` or :func:`utils.get` would serve some use in finding
specific entities. The documentation for those functions provide specific examples.

Commands Extension
-------------------

Questions regarding ``discord.ext.commands`` belong here.

Is there any documentation for this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not at the moment. Writing documentation for stuff takes time. A lot of people get by reading the docstrings in the source
code. Others get by via asking questions in the `Discord server <https://discord.gg/0SBTUU1wZTXZNJPa>`_. Others look at the
source code of `other existing bots <https://github.com/Rapptz/RoboDanny>`_.

There is a `basic example <https://github.com/Rapptz/discord.py/blob/master/examples/basic_bot.py>`_ showcasing some
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

Can I use ``bot.say`` in other places aside from commands?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No. They only work inside commands due to the way the magic involved works.

Why do my arguments require quotes?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a simple command defined as: ::

    @bot.command()
    async def echo(message: str):
        await bot.say(message)

Calling it via ``?echo a b c`` will only fetch the first argument and disregard the rest. To fix this you should either call
it via ``?echo "a b c"`` or change the signature to have "consume rest" behaviour. Example: ::

    @bot.command()
    async def echo(*, message: str):
        await bot.say(message)

This will allow you to use ``?echo a b c`` without needing the quotes.

How do I get the original ``message``\?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ask the command to pass you the invocation context via ``pass_context``. This context will be passed as the first parameter.

Example: ::

    @bot.command(pass_context=True)
    async def joined_at(ctx, member: discord.Member = None):
        if member is None:
            member = ctx.message.author

        await bot.say('{0} joined at {0.joined_at}'.format(member))

How do I make a subcommand?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``group`` decorator. This will transform the callback into a ``Group`` which will allow you to add commands into
the group operating as "subcommands". These groups can be arbitrarily nested as well.

Example: ::

    @bot.group(pass_context=True)
    async def git(ctx):
        if ctx.invoked_subcommand is None:
            await bot.say('Invalid git command passed...')

    @git.command()
    async def push(remote: str, branch: str):
        await bot.say('Pushing to {} {}'.format(remote, branch))


This could then be used as ``?git push origin master``.

