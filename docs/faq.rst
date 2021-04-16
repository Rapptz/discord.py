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

What is a coroutine?
~~~~~~~~~~~~~~~~~~~~~~

A |coroutine_link|_ is a function that must be invoked with ``await`` or ``yield from``. When Python encounters an ``await`` it stops
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

If logging is enabled, this library will attempt to warn you that blocking is occurring with the message:
``Heartbeat blocked for more than N seconds.``
See :ref:`logging_setup` for details on enabling logging.

A common source of blocking for too long is something like :func:`time.sleep`. Don't do that. Use :func:`asyncio.sleep`
instead. Similar to this example: ::

    # bad
    time.sleep(10)

    # good
    await asyncio.sleep(10)

Another common source of blocking for too long is using HTTP requests with the famous module :doc:`req:index`.
While :doc:`req:index` is an amazing module for non-asynchronous programming, it is not a good choice for
:mod:`asyncio` because certain requests can block the event loop too long. Instead, use the :doc:`aiohttp <aio:index>` library which
is installed on the side with this library.

Consider the following example: ::

    # bad
    r = requests.get('http://aws.random.cat/meow')
    if r.status_code == 200:
        js = r.json()
        await channel.send(js['file'])

    # good
    async with aiohttp.ClientSession() as session:
        async with session.get('http://aws.random.cat/meow') as r:
            if r.status == 200:
                js = await r.json()
                await channel.send(js['file'])

General
---------

General questions regarding library usage belong here.

Where can I find usage examples?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example code can be found in the `examples folder <https://github.com/Rapptz/discord.py/tree/master/examples>`_
in the repository.

How do I set the "Playing" status?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``activity`` keyword argument may be passed in the :class:`Client` constructor or :meth:`Client.change_presence`, given an :class:`Activity` object.

The constructor may be used for static activities, while :meth:`Client.change_presence` may be used to update the activity at runtime.

.. warning::

    It is highly discouraged to use :meth:`Client.change_presence` or API calls in :func:`on_ready` as this event may be called many times while running, not just once.

    There is a high chance of disconnecting if presences are changed right after connecting.

The status type (playing, listening, streaming, watching) can be set using the :class:`ActivityType` enum.
For memory optimisation purposes, some activities are offered in slimmed down versions:

- :class:`Game`
- :class:`Streaming`

Putting both of these pieces of info together, you get the following: ::

    client = discord.Client(activity=discord.Game(name='my game'))

    # or, for watching:
    activity = discord.Activity(name='my activity', type=discord.ActivityType.watching)
    client = discord.Client(activity=activity)

How do I send a message to a specific channel?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You must fetch the channel directly and then call the appropriate method. Example: ::

    channel = client.get_channel(12324234183172)
    await channel.send('hello')

How do I send a DM?
~~~~~~~~~~~~~~~~~~~

Get the :class:`User` or :class:`Member` object and call :meth:`abc.Messageable.send`. For example: ::

    user = client.get_user(381870129706958858)
    await user.send('👀')

If you are responding to an event, such as :func:`on_message`, you already have the :class:`User` object via :attr:`Message.author`: ::

    await message.author.send('👋')

How do I get the ID of a sent message?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`abc.Messageable.send` returns the :class:`Message` that was sent.
The ID of a message can be accessed via :attr:`Message.id`: ::

    message = await channel.send('hmm…')
    message_id = message.id

How do I upload an image?
~~~~~~~~~~~~~~~~~~~~~~~~~

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

If you want to upload something from a URL, you will have to use an HTTP request using :doc:`aiohttp <aio:index>`
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

    emoji = '\N{THUMBS UP SIGN}'
    # or '\U0001f44d' or '👍'
    await message.add_reaction(emoji)

In case you want to use emoji that come from a message, you already get their code points in the content without needing
to do anything special. You **cannot** send ``':thumbsup:'`` style shorthands.

For custom emoji, you should pass an instance of :class:`Emoji`. You can also pass a ``'<:name:id>'`` string, but if you
can use said emoji, you should be able to use :meth:`Client.get_emoji` to get an emoji via ID or use :func:`utils.find`/
:func:`utils.get` on :attr:`Client.emojis` or :attr:`Guild.emojis` collections.

The name and ID of a custom emoji can be found with the client by prefixing ``:custom_emoji:`` with a backslash.
For example, sending the message ``\:python3:`` with the client will result in ``<:python3:232720527448342530>``.

Quick example: ::


    # if you have the ID already
    emoji = client.get_emoji(310177266011340803)
    await message.add_reaction(emoji)

    # no ID, do a lookup
    emoji = discord.utils.get(guild.emojis, name='LUL')
    if emoji:
        await message.add_reaction(emoji)

    # if you have the name and ID of a custom emoji:
    emoji = '<:python3:232720527448342530>'
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

However, this function returns a :class:`~concurrent.futures.Future` and to actually call it we have to fetch its result. Putting all of
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

`Check the background_task.py example. <https://github.com/Rapptz/discord.py/blob/master/examples/background_task.py>`_

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
- :meth:`Guild.get_role`

The following use an HTTP request:

- :meth:`abc.Messageable.fetch_message`
- :meth:`Client.fetch_user`
- :meth:`Client.fetch_guilds`
- :meth:`Client.fetch_guild`
- :meth:`Guild.fetch_emoji`
- :meth:`Guild.fetch_emojis`
- :meth:`Guild.fetch_member`


If the functions above do not help you, then use of :func:`utils.find` or :func:`utils.get` would serve some use in finding
specific models.

Quick example: ::

    # find a guild by name
    guild = discord.utils.get(client.guilds, name='My Server')

    # make sure to check if it's found
    if guild is not None:
        # find a channel by name
        channel = discord.utils.get(guild.text_channels, name='cool-channel')

How do I make a web request?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make a request, you should use a non-blocking library.
This library already uses and requires a 3rd party library for making requests, :doc:`aiohttp <aio:index>`.

Quick example: ::

    async with aiohttp.ClientSession() as session:
        async with session.get('http://aws.random.cat/meow') as r:
            if r.status == 200:
                js = await r.json()

See `aiohttp's full documentation <http://aiohttp.readthedocs.io/en/stable/>`_ for more information.

How do I use a local image file for an embed image?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Discord special-cases uploading an image attachment and using it within an embed so that it will not
display separately, but instead in the embed's thumbnail, image, footer or author icon.

To do so, upload the image normally with :meth:`abc.Messageable.send`,
and set the embed's image URL to ``attachment://image.png``,
where ``image.png`` is the filename of the image you will send.


Quick example: ::

    file = discord.File("path/to/my/image.png", filename="image.png")
    embed = discord.Embed()
    embed.set_image(url="attachment://image.png")
    await channel.send(file=file, embed=embed)

.. note ::

    Due to a Discord limitation, filenames may not include underscores.

Is there an event for audit log entries being created?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since Discord does not dispatch this information in the gateway, the library cannot provide this information.
This is currently a Discord limitation.

Commands Extension
-------------------

Questions regarding ``discord.ext.commands`` belong here.

Why does ``on_message`` make my commands stop working?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overriding the default provided ``on_message`` forbids any extra commands from running. To fix this, add a
``bot.process_commands(message)`` line at the end of your ``on_message``. For example: ::

    @bot.event
    async def on_message(message):
        # do some extra stuff here

        await bot.process_commands(message)

Alternatively, you can place your ``on_message`` logic into a **listener**. In this setup, you should not
manually call ``bot.process_commands()``. This also allows you to do multiple things asynchronously in response
to a message. Example::

    @bot.listen('on_message')
    async def whatever_you_want_to_call_it(message):
        # do stuff here
        # do not process commands here

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
    async def length(ctx):
        await ctx.send('Your message is {} characters long.'.format(len(ctx.message.content)))

How do I make a subcommand?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the :func:`~ext.commands.group` decorator. This will transform the callback into a :class:`~ext.commands.Group` which will allow you to add commands into
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
