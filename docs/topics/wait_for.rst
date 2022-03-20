:orphan:
.. currentmodule:: discord

.. _guide_wait_for:

Waiting For Events
=============================
When creating commands or handling events, you often find yourself wanting to wait for an action or user response. In discord.py, we use the :meth:`Client.wait_for` method. 

What is ``wait_for``?
~~~~~~~~~~~~~~~~~~~~~
:meth:`Client.wait_for` is similar to client.event/listen, however instead of calling a function, it instead holds execution of your code until the event has been dispatched, and returns the data that was in the event. 


Here is a quick example

.. code-block:: python3
   :emphasize-lines: 2

    await channel.send('say hi!')
    message = await client.wait_for('message') # wait for a message, the wait_for will return the message it finds
    await message.reply('hello!')

The key line here is line 2. We are waiting for an event to happen, in this case, a message event.

Wait_for is commonly used to control flow in a code, waiting for message replies or reactions to be added. You can wait for any event you want.

Checks and Timeouts
~~~~~~~~~~~~~~~~~~~~
While the example above allows us to wait for an event, this will pass as soon as *any* event of that type is dispatched. Sometimes, we want to filter it. To do this, we use the check keyword argument.

.. code-block:: python3
   :emphasize-lines: 2, 3, 4

    await message.channel.send('say hi!')
    def check(m):
        return m.author == message.author # check that the author is the one who sent the original message
    msg = await client.wait_for('message', check=check)
    await msg.reply('hello!')

In this example, the wait_for will only terminate when the check returns ``True``, in this case when the message author is equal to the original author.
The check function takes the same arguments the event would take, in this case just ``m``, a message.

Sometimes, we only want to wait for a specific amount of time, before timing out the wait_for and allowing the code to continue. 

.. code-block:: python3
   :emphasize-lines: 2, 3, 4, 5

    await message.channel.send('say hi!')
    try:
        msg = await client.wait_for('message', timeout=5.0) # timeout in seconds.
    except asyncio.TimeoutError: 
        await message.channel.send('You did not respond :(')
    else:
        await msg.reply('hello!')

We pass the timeout in seconds to the timeout kwarg of wait_for. If the wait_for does not complete successfully within the given time it will be terminated and :class:`asyncio.TimeoutError` will be raised.
.. warning::

    avoid using wait_for within a loop to catch events of a specific type. Due to the async nature of discord.py, events may be fired between loops, causing your wait_for to miss the event dispatch.

Examples
~~~~~~~~~~~~~~~~~~~~
Wait for reaction

.. code-block:: python3

    def check(reaction, user):
        return user == message.author and reaction.message == message # check that the reaction is on a specific message and by a specific user

    reaction, user = await client.wait_for('reaction_add', check = check)
    await message.channel.send(f'You reacted with {reaction.emoji}!')

Inline check

.. code-block:: python3 

    await client.wait_for('message', check = lambda m: m.author == message.author)


