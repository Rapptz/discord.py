:orphan:

.. currentmodule:: discord

.. _guide_threads:

Threads
========

If you've been on a public Discord for a while, you've probably seen a :ddocs:`topics/threads` or two in your time.

They act as offshoots of regular text channels, allowing for a focused, but temporary, location to talk about a given topic.

This section will show you how to create and manage threads within your code.

You can view the API Reference at :class:`~Thread`.

Creating a thread
~~~~~~~~~~~~~~~~~~

There are two types of threads: **public** and **private** threads.

Public threads can be created in any channel where you have the :attr:`~Permissions.create_public_threads` permission.

Private threads, however, require the :attr:`~Permissions.create_private_threads` permission, and can only be used in a server with a boost level of 2 or higher.

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
    :scale: 90

Simple, right? Let's discuss some of the finer details.

Public threads
~~~~~~~~~~~~~~~

Public threads can be viewed by anyone who can see the channel they belong to.
People can browse and join these threads as they please.

All public threads are tied to a specific message. You can use a message that already exists, but you can also send a new message to attach the thread to.

Let's expand on our example from before by making it possible to name the thread. We can also switch to using the convenient :meth:`Message.create_thread` shortcut.

.. code-block:: python3

    @bot.command()
    async def create_thread(ctx: commands.Context, *, thread_name: str):
        thread = await ctx.message.create_thread(
            name=thread_name
        )

        await thread.send(f"Hello from the {thread_name} thread!")

and then we have our public thread:

.. image:: /images/guide/threads/create_public_thread_param.png
    :scale: 90

As discussed before, we can see it from the thread list, even if we're not a member:

.. image:: /images/guide/threads/not_a_member.png
    :scale: 90


Private threads
~~~~~~~~~~~~~~~~

Private threads exist as "invite only" threads.
By default, they only contain the person who created them, but other people can be invited to participate.

Private threads can optionally be 'invitable'.
If a thread is invitable, it means anyone in that thread can invite others to it.
Otherwise, only the owner and people with the :attr:`~Permissions.manage_threads` permission can add new people to the thread.

Users with :attr:`~Permissions.manage_threads` ("Moderators") can also see a list of private threads they're not in, similar to public threads.

Let's create a private, non-invitable thread with a command:

.. code-block:: python3

    @bot.command()
    async def secret_thread(ctx: commands.Context):
        thread = await ctx.channel.create_thread(
            name="Secret Birthday Planning!",
            invitable=False
        )
        await thread.send(ctx.author.mention)

We've chosen here to mention the author as soon as we make the thread.
If we didn't do this, then the thread would be created, but we wouldn't necessarily be able to see it!

Note that this mention is only guaranteed to work because we own the thread.
Mentions from regular users wouldn't work in this thread, because it is not ``invitable``.

You can also use the :meth:`~Thread.add_user` method to add someone, without sending a mention. This requires ``invitable`` to be ``False``.

Unlike a public thread, private threads are not tied to messages, so they won't appear in the channel they're attached to.
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

The API has methods of adding members that do not require pinging them, which is implemeted with :meth:`~Thread.add_user`.
You can add it as a command, like so:

.. code-block:: python3

    async def is_thread():
        def predicate(ctx: commands.Context) -> bool:
            return isinstance(ctx.channel, discord.Thread)
        return commands.check(predicate)

    @bot.command()
    @is_thread() # we use the defined check above so that this command can only be used in a thread.
    async def add_to_thread(ctx: commands.Context, *, member: discord.Member):
        await ctx.channel.add_user(member)
        await ctx.message.add_reaction("\U00002705")

Which performs the following:

.. image:: /images/guide/threads/add_member_to_thread.png

Another method in which to do so is to mention a role within the thread.

.. note::
    There is a limit of around 100 members per addition to a thread, so if your role contains more than 100 members they will not be added.


Setting the archive duration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Threads automatically archive after a set period of time of inactivity. You can choose this period when creating the thread.
The current accepted values are:

    - 1 hour
    - 24 hours
    - 3 days
    - 1 week


.. note::
    The options for both "3 days" and "1 week" are locked behind server boost level 1 and 2, respectively.


To pass an auto-archive duration during thread creation, you can use the ``auto_archive_duration`` keyword argument to the :meth:`~TextChannel.create_thread` call:

.. code-block:: python3

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

If you wish to force archive the thread you can use the :meth:`~Thread.edit` method and set the ``archived=True`` keyword argument.

To delete a thread you can use the :meth:`~Thread.delete` method.


Browsing threads in a channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can browse threads within :class:`~TextChannel` instances with the following methods:
    - :attr:`~TextChannel.threads`
    - :meth:`~TextChannel.archived_threads`

The former is a property of the channel instance that returns a list of all valid :class:`~Thread` instances

The latter returns an :term:`asynchronous iterator` that iterates over all of the archived threads in the guild,
in order of descending ID for threads you have joined, or descending :attr:`~Thread.archive_timestamp` otherwise.
