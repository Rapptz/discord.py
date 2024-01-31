.. currentmodule:: discord

.. _guide_threads:

Threads
========

If you've been on a public Discord for a while, you've probably seen a :ddocs:`topics/threads` or two in your time.

They act as offshoots of regular text channels, allowing for a focused, but temporary, location to talk about a given topic.

This section will show you how to create and manage threads within your code.

You can view the API Reference at :class:`Thread`.

Creating a thread
~~~~~~~~~~~~~~~~~~

There are two types of threads: **public** and **private** threads.

Public threads can be created in any channel where you have the :attr:`~Permissions.create_public_threads` permission.

Private threads, however, require the :attr:`~Permissions.create_private_threads` permission.

Users with the :attr:`~Permissions.manage_threads` permission can see all threads, including private ones they are not explicitly invited to.

You can view the API reference for creating threads here: :meth:`TextChannel.create_thread` / :meth:`Message.create_thread`.

For a quick primer, let's try making a command that creates a thread and then sends a message in it:

.. code-block:: python3

    @bot.command()
    async def create_thread(ctx: commands.Context):
        thread = await ctx.channel.create_thread(name="My cool thread", message=ctx.message)

        await thread.send("Created!")

which will create a thread like so:

.. image:: /images/guide/threads/create_public_thread.png

Simple, right? Let's discuss some of the finer details.

Public threads
~~~~~~~~~~~~~~~

Public threads can be viewed by anyone who can see the channel they belong to.
People can browse and join these threads as they please.

Public threads can be tied to a specific message. You can use a message that already exists, but you can also send a new message to attach the thread to.

Let's expand on our example from before by making it possible to name the thread. We can also switch to using the convenient :meth:`Message.create_thread` shortcut.

.. code-block:: python3
    :emphasize-lines: 3

    @bot.command()
    async def create_thread(ctx: commands.Context, *, thread_name: str):
        thread = await ctx.message.create_thread(name=thread_name)

        await thread.send(f"Hello from the {thread_name} thread!")

and then we have our public thread:-

.. image:: /images/guide/threads/create_public_thread_param.png

As discussed before, we can see it from the thread list, even if we're not a member:-

.. image:: /images/guide/threads/not_a_member.png
    :scale: 90

Public threads can also be standalone, with no message tied to the creation. The example code above would be similar to do this:-

.. code-block:: python3
    :emphasize-lines: 3

    @bot.command()
    async def create_thread(ctx: commands.Context, *, thread_name: str):
        thread = await ctx.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)

        await thread.send(f"Hello from the {thread_name} thread!")

You can see here we now utilise ``ctx.channel`` over ``ctx.message`` to create the thread, but we also pass :attr:`ChannelType.public_thread` to the ``type=`` keyword argument to denote that it will be a public thread.


Private threads
~~~~~~~~~~~~~~~~

Private threads exist as "invite only" threads.
By default, they only contain the person who created them, but other people can be invited to participate.

Private threads can optionally be 'invitable'.
If a thread is invitable, it means anyone in that thread can invite others to it.
Otherwise, only the owner and people with the :attr:`~Permissions.manage_threads` permission can add new people to the thread.

Users with :attr:`~Permissions.manage_threads` can also see a list of private threads they're not in, similar to public threads.

Let's create a private, non-invitable thread with a command:

.. code-block:: python3
    :emphasize-lines: 5

    @bot.command()
    async def secret_thread(ctx: commands.Context):
        thread = await ctx.channel.create_thread(
            name="Secret Birthday Planning!",
            invitable=False
        )
        await thread.send(ctx.author.mention)

We've chosen here to mention the author as soon as we make the thread.
If this wasn't done, then the thread would be created, but the command author wouldn't necessarily be able to see it!

Note that this mention is only guaranteed to work because we own the thread.
Mentions from regular users wouldn't work in this thread, because it is not ``invitable``.

You can also use the :meth:`Thread.add_user` method to add someone. This will mention the user to add them but the content will look like a system message similar to "<Bot> added <User> to the thread.". This also requires ``invitable`` to be ``False``.

Private threads are not tied to messages (unlike public threads, which *can* be), so they won't appear in the channel they're attached to.
The member list will look like this inside in the thread:

.. image:: /images/guide/threads/create_private_thread.png
    :scale: 90


.. warning::
    Thread creation shows up in the audit logs, even if the thread is private.
    Be wary of this if you don't intend for others to know about the thread.


Adding members to threads
~~~~~~~~~~~~~~~~~~~~~~~~~~

We touched on it earlier a bit, but now we'll go into how to add people to threads.

The go-to practice for doing this is pinging the member, like so:

.. image:: /images/guide/threads/mention_member_to_thread.png

The API has methods of adding members without sending a message directly, which is implemented with :meth:`Thread.add_user`.
You can add it as a command, like so:

.. code-block:: python3
    :emphasize-lines: 10

    async def is_thread():
        def predicate(ctx: commands.Context) -> bool:
            return isinstance(ctx.channel, discord.Thread)
        return commands.check(predicate)

    @bot.command()
    @is_thread() # we use the defined check above so that this command can only be used in a thread.
    async def add_to_thread(ctx: commands.Context, *, member: discord.Member) -> None:
        assert isinstance(ctx.channel, discord.Thread) # guarded by decorated check!
        await ctx.channel.add_user(member)
        await ctx.message.add_reaction("\U00002705")

Which performs the following:

.. image:: /images/guide/threads/add_member_to_thread.png

Another method in which to do so is to mention a role within the thread.

.. note::
    There is a limit of around 100 members per addition to a thread, so if your role contains more than 100 members they will not be added.


Setting the archive duration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Threads automatically "hide" after a set period of time of inactivity. Meaning they will move to the lower end of the thread view list. You can choose this period when creating the thread.
The current accepted values are:

    - 1 hour (represented as ``60`` in code)
    - 24 hours (represented as ``1440`` in code)
    - 3 days (represented as ``4320`` in code)
    - 1 week (represented as ``10080`` in code)


To pass an auto-archive duration during thread creation, you can use the ``auto_archive_duration`` keyword argument to the :meth:`TextChannel.create_thread` call:

.. code-block:: python3
    :emphasize-lines: 5

    async def create_daily_thread(ctx: commands.Context):
        duration = 1440 # 24 hours represented as minutes
        await ctx.channel.create_thread(
            name="Daily thread!",
            auto_archive_duration=duration,
            message=ctx.message
        )

Deleting or archiving a thread
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can delete or force archive threads if you have the :attr:`~Permissions.manage_threads` permission.

If you wish to force archive the thread you can use the :meth:`Thread.edit` method and set the ``archived=True`` keyword argument.

Alternatively there is also the capability to *lock* threads. This means that general users can no longer message in them, only thread moderators (one who had :attr:`~Permissions.manage_threads`) can effectively re-open the thread.
To do this you can call :meth:`Thread.edit` and set the ``locked=`` keyword argument to ``True``.

To delete a thread you can use the :meth:`Thread.delete` method.


Browsing threads in a channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can browse threads within :class:`TextChannel` instances with the following methods:
    - :attr:`TextChannel.threads`
    - :meth:`TextChannel.archived_threads`

The former is a property of the channel instance that returns a list of all non-archived :class:`Thread` instances.

The latter returns an :term:`asynchronous iterator` that iterates over all of the archived threads in the guild,
in order of descending ID for threads you have joined, or descending :attr:`Thread.archive_timestamp` otherwise.

Notes for receiving messages from a thread
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To identify messages that your client receives from a thread, you can check the type of :attr:`Message.channel`:-

.. code-block:: python3

    if isinstance(message.channel, discord.Thread):
        # Hey, we're in a thread!

Replying to this message or interacting with it in any discernible way will add your client to the thread.

It should be noted that you cannot receive gateway events for private threads you are not a member of.

Forum Channels
===============

Forum Channels are an addition to the Discord channel repertoire which are special cased as container type channels which allow the creation of threads (and only threads) within them.

They are presented in the form of a small browser style window which shows the thread title, an excerpt of the thread text, related image previews as well as any applied 'tags' to the post.

As such we now have :class:`ForumChannel` and :class:`ForumTag` within the library for interacting with these types of channels and tags, respectively.

To create a new thread within this forum channel, we utilise the :meth:`ForumChannel.create_thread` method as normal, the only notable difference is we can add multiple :class:`ForumTag` to the message.
A small example of this would be:-

.. code-block:: python3
    :emphasize-lines: 4,6

    tags = your_forum_channel.available_tags

    # let's get the baking tag for our post, this is one of the simpler ways of doing so:-
    baking_tag = discord.utils.get(tags, name="Baking")

    thread, message = await your_forum_channel.create_thread(name="My brownie recipe!", content="1 tbsp sugar...", applied_tags=[baking_tag])

    # we can send more messages using the new `thread` variable here
    # the `message` variable is the starter message that was sent.
