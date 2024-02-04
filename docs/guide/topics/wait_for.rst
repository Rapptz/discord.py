:orphan:
.. currentmodule:: discord

.. _guide_wait_for:

Waiting for Events
==================
A common step when creating commands or handling events involves having to wait for an action or user-input. To aid with this, the library offers a special method :meth:`Client.wait_for` to wait for an event in-line instead of having to define a separate event listener.

What is ``wait_for``?
~~~~~~~~~~~~~~~~~~~~~
Similar to callbacks decorated with ``@client.event``, :meth:`Client.wait_for` waits for the first event it finds tied to the passed event name (without the `on_` prefix!) and returns the event's arguments.

Here is a quick example:

.. code-block:: python3
   :emphasize-lines: 2

    await channel.send('say hi!')
    msg = await client.wait_for('message') 
    await msg.reply('hello!')

The key line here is line 2. We are waiting for an event to happen, in this case a message event. After one is recieved, the method will return the message associated with the event.

``wait_for`` is commonly used to control code flow, waiting for message replies or reactions to be added. The key takeaway here is any event that works with `@client.event` can also be waited on with this method.

Checks and Timeouts
~~~~~~~~~~~~~~~~~~~
Whilst the above example shows off waiting for a message, this will return as soon as *any* message is sent.
Oftentimes, we want to narrow it down to a specific message, which we can do by passing a predicate to the ``check`` keyword-argument

.. code-block:: python3
   :emphasize-lines: 2, 3, 4

    await message.channel.send('say hi!')

    def check(m: discord.Message):
        # check that the author is the one who sent the original message
        return m.author == message.author 

    msg: discord.Message = await client.wait_for('message', check=check)
    await msg.reply('hello!')

In this example, ``wait_for`` will only accept the incoming message when the predicate returns ``True``.
The arguments passed to the predicate match the signature of the corresponding event.
For example, when defining a message event handler we do ``async def on_message(message)`` - a predicate would similarly be defined with ``def check(message)``.

Likewise, a predicate for `reaction_add` would take `def check(reaction, user)`.

It's common to also include a timeout in addition to a check so our code doesn't potentially end up waiting indefinitely, or to add a limited time window for the author to send a message.

.. code-block:: python3
   :emphasize-lines: 2, 3, 4, 5

    await message.channel.send('say hi!')
    try:
        msg: discord.Message = await client.wait_for('message', timeout=5.0) # timeout in seconds.
    except asyncio.TimeoutError: 
        await message.channel.send('You did not respond :(')
    else:
        await msg.reply('hello!')

We pass the timeout in seconds to the ``timeout`` keyword-argument. Timeouts behave like :meth:`asyncio.wait_for`, so we do the usual `try` and `except`, catching :class:`asyncio.TimeoutError`:

.. warning::

    Avoid calling :meth:`Client.wait_for` within a loop to catch events. Due to the nature of async IO, events may be fired between loops, causing the loop to miss events. See the example for multiple events.

Examples
~~~~~~~~

Wait for Reaction
+++++++++++++++++

.. code-block:: python3

    def check(reaction: discord.Reaction, user: discord.User):
        return user == message.author and reaction.message == message # check that the reaction is on a specific message and by a specific user

    reaction, user = await client.wait_for('reaction_add', check=check)
    await message.channel.send(f'You reacted with {reaction.emoji}!')

Notice the ``reaction_add`` event, unlike the ``message`` event, takes 2 arguments. Thus, the check function takes the same arguments as that, ``reaction, user``.
wait_for will follow the same constraints and nuances as the corresponding event, in this case: :meth:`discord.on_reaction_add`.

Waiting for Multiple Events
+++++++++++++++++++++++++++

.. code-block:: python3
   :emphasize-lines: 2, 5, 6, 7

   participants = []

   def check(message: discord.Message):
       participants.append(message.author)
       if len(participants) >= 10:
           return True
       return False

   await client.wait_for('message', check=check)

   mentions = ', '.join([user.mention for user in particpants])
   await message.channel.send(f'Welcome {mentions}!')

Instead of creating a new wait_for for every new message, in order to catch all new messages sent, we allow our check function to accept all messages until a condition is met, saving `inside` the check itself.


Closing Remarks
~~~~~~~~~~~~~~~~~~~~
``wait_for`` is a powerful tool used often to wait for responses in code. The examples above show only 2 types of ``wait_for``, reactions and messages, but you can wait for any event! A full list of events can be seen here: :ref:`event reference <discord-api-events>`. 


