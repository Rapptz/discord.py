.. currentmodule:: discord

.. _guide_threads:

Threads
========

Threads are a feature from Discord designed as messaging spaces within text channels, designed for subtopics of a chat to assist with multiple conversations happening at once.

This section will show you how to create and manage threads within your code.

You can view our API Reference at :class:`~Thread`.

Creating a thread
~~~~~~~~~~~~~~~~~~

Threads are creatable in any channel you have the :attr:`~Permissions.create_public_threads` or :attr:`~Permissions.create_private_threads` permissions in.
Private threads are currently locked to level 2 server boosting or higher.

Moderators with the :attr:`~Permissions.manage_threads` permission can see all threads, including private ones they are not explicitly invited to.

You can view our documentation on how to create threads here: :meth:`~TextChannel.create_thread` / :meth:`~Message.create_thread`.

Let's create a command like so:

.. code-block:: python3

    @bot.command()
    async def create_thread(ctx: commands.Context) -> None:
        thread = await ctx.create_thread(name="My cool thread", message=ctx.message)

        await thread.send("Created!")

which will create a thread like so:

.. image:: /images/guide/threads/create_public_thread.png
    :scale: 90

Now let's show more things you can do with threads:

Public threads
~~~~~~~~~~~~~~~

Public threads can be viewed by anyone and joined by anyone. They are browsable in the channel and they can be messaged by anyone or members can be brought in with a mention.

To create one, you must have the :attr:`~Permissions.create_public_threads` permission.

Let's create a public thread now:

.. code-block:: python3

    @bot.command()
    async def create_thread(ctx: commands.Context, *, thread_name: str) -> None:
        thread = await ctx.message.create_thread( # Creating a thread from a Message will make it public only.
            name=thread_name
        )

        await thread.send(f"Hello from the {thread_name} thread!")

and then we have our public thread:

.. image:: /images/guide/threads/create_public_thread_param.png
    :scale: 90

You can view it from the channel list, even if you are not a member:

.. image:: /images/guide/threads/not_a_member.png
    :scale: 90


Private threads
~~~~~~~~~~~~~~~~

Private threads exist as "invite only" threads. There is a toggle option so that only moderators can add more people.
Perfect for planning birthday or guild events!

To create one, you must have the :attr:`~Permissions.create_private_threads` permission.

You can create one using the following example command:

.. code-block:: python3

    @bot.command()
    async def secret_thread(ctx: commands.Context) -> None:
        thread = await ctx.channel.create_thread(name="Secret Birthday Planning!")
        await thread.send(ctx.author.mention)

The mention being sent at the end will add you (the author of the command) to the thread that was created, otherwise only moderators with the :attr:`~Permissions.manage_threads` permission can see it.
You may also use the :meth:`~Thread.add_user` method to add someone, without sending a mention. This requires ``invitable`` to be ``False``.

.. note::
    You can also add ``invitable=False`` to the :meth:`~TextChannel.create_thread` call, meaning only moderators can invite people to it, mentions from regular members will not work.

The thread will not show up in the text channel, as previously shown with a public thread. The member list will then look like the following:

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
    async def add_to_thread(ctx: commands.Context, *, member: discord.Member) -> None:
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

    async def create_daily_thread(ctx: commands.Context) -> None:
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
