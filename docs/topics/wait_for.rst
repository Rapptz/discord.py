:orphan:
.. currentmodule:: discord

.. _guide_wait_for:

Waiting For Events
=============================
When creating commands or handling events, you often find yourself wanting to wait for an action or user response. In discord.py, we use the :meth:`Client.wait_for` method. 

What is ``wait_for``?
~~~~~~~~~~~~~~~~~~~~~
:meth:`Client.wait_for` is similar to client.event/listen, however instead of calling a function, it instead halts execution of your code until the event has been dispatched, and returns the data that was in the event. 


Here is a quick example

.. code-block:: python3
   :emphasize-lines: 2

    await channel.send('say hi!')
    msg: discord.Message = await client.wait_for('message') # wait for a message, the wait_for will return the message it finds
    await msg.reply('hello!')

The key line here is line 2. We are waiting for an event to happen, in this case, a message event.

``wait_for`` is commonly used to control code flow, waiting for message replies or reactions to be added. You can wait for any event you want.

Checks and Timeouts
~~~~~~~~~~~~~~~~~~~~
While the example above allows us to wait for an event, this will pass as soon as *any* event of that type is dispatched. Sometimes, we want to filter it. To do this, we use the ``check`` keyword argument.

.. code-block:: python3
   :emphasize-lines: 2, 3, 4

    await message.channel.send('say hi!')
    def check(m: discord.Message):
        return m.author == message.author # check that the author is the one who sent the original message
    msg: discord.Message = await client.wait_for('message', check=check)
    await msg.reply('hello!')

In this example, ``wait_for`` will only accept the incoming event and move on when the check returns ``True``, in this case when the message author is equal to the original author.
The check function takes the same arguments the event would take, in this case a paramter named ``m``, which represents a ``discord.Message`` instance. This is similar to `:meth:`Client.on_message`.

Sometimes, we only want to wait for a specific amount of time, before timing out the wait_for and allowing the code to continue. 

.. code-block:: python3
   :emphasize-lines: 2, 3, 4, 5

    await message.channel.send('say hi!')
    try:
        msg: discord.Message = await client.wait_for('message', timeout=5.0) # timeout in seconds.
    except asyncio.TimeoutError: 
        await message.channel.send('You did not respond :(')
    else:
        await msg.reply('hello!')

We pass the timeout in seconds to the ``timeout`` kwarg of wait_for. If the wait_for does not complete successfully within the given time it will be terminated and :class:`asyncio.TimeoutError` will be raised.
.. warning::

    avoid using wait_for within a loop to catch events of a specific type. Due to the async nature of discord.py, events may be fired between loops, causing your wait_for to miss the event dispatch.

Examples
~~~~~~~~~~~~~~~~~~~~
Wait for reaction
+++++++++++++++++

.. code-block:: python3

    def check(reaction: discord.Reaction, user: discord.User):
        return user == message.author and reaction.message == message # check that the reaction is on a specific message and by a specific user

    reaction: discord.Reaction, user: discord.User = await client.wait_for('reaction_add', check = check)
    await message.channel.send(f'You reacted with {reaction.emoji}!')

Notive the ``reaction`` event, unlike the ``message`` event, takes 2 arguments. Thus, the check function takes the same arguments as that, ``reaction, user``.
Additionally, the wait_for will now return a tuple of the arguments the event recieved, which we are unwraping when recieving. 
This is how it works for *any* event that takes more than one argument, a few examples being ``typing`` or ``message_edit``.

Inline check
++++++++++++

.. code-block:: python3 

    await client.wait_for('message', check = lambda m: m.author == message.author)

As the check kwarg simply takes a function, we can make it inline by making use of a lambda function

Closing Remarks
~~~~~~~~~~~~~~~~~~~~
``wait_for`` is a powerful tool used often to wait for responses in code. The examples above only shows 2 types of ``wait_for``, reactions and messages, but you can wait for any event! A full list of events can be seen here: :ref:`event reference <discord-api-events>`. 


