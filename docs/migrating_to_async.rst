:orphan:

.. currentmodule:: discord

.. _migrating-to-async:

Migrating to v0.10.0
======================

v0.10.0 is one of the biggest breaking changes in the library due to massive
fundamental changes in how the library operates.

The biggest major change is that the library has dropped support to all versions prior to
Python 3.4.2. This was made to support :mod:`asyncio`, in which more detail can be seen
:issue:`in the corresponding issue <50>`. To reiterate this, the implication is that
**python version 2.7 and 3.3 are no longer supported**.

Below are all the other major changes from v0.9.0 to v0.10.0.

Event Registration
--------------------

All events before were registered using :meth:`Client.event`. While this is still
possible, the events must be decorated with ``@asyncio.coroutine``.

Before:

.. code-block:: python3

    @client.event
    def on_message(message):
        pass

After:

.. code-block:: python3

    @client.event
    @asyncio.coroutine
    def on_message(message):
        pass

Or in Python 3.5+:

.. code-block:: python3

    @client.event
    async def on_message(message):
        pass

Because there is a lot of typing, a utility decorator (:meth:`Client.async_event`) is provided
for easier registration. For example:

.. code-block:: python3

    @client.async_event
    def on_message(message):
        pass


Be aware however, that this is still a coroutine and your other functions that are coroutines must
be decorated with ``@asyncio.coroutine`` or be ``async def``.

Event Changes
--------------

Some events in v0.9.0 were considered pretty useless due to having no separate states. The main
events that were changed were the ``_update`` events since previously they had no context on what
was changed.

Before:

.. code-block:: python3

    def on_channel_update(channel): pass
    def on_member_update(member): pass
    def on_status(member): pass
    def on_server_role_update(role): pass
    def on_voice_state_update(member): pass
    def on_socket_raw_send(payload, is_binary): pass


After:

.. code-block:: python3

    def on_channel_update(before, after): pass
    def on_member_update(before, after): pass
    def on_server_role_update(before, after): pass
    def on_voice_state_update(before, after): pass
    def on_socket_raw_send(payload): pass

Note that ``on_status`` was removed. If you want its functionality, use :func:`on_member_update`.
See :ref:`discord-api-events` for more information. Other removed events include ``on_socket_closed``, ``on_socket_receive``, and ``on_socket_opened``.


Coroutines
-----------

The biggest change that the library went through is that almost every function in :class:`Client`
was changed to be a `coroutine <py:library/asyncio-task.html>`_. Functions
that are marked as a coroutine in the documentation must be awaited from or yielded from in order
for the computation to be done. For example...

Before:

.. code-block:: python3

    client.send_message(message.channel, 'Hello')

After:

.. code-block:: python3

    yield from client.send_message(message.channel, 'Hello')

    # or in python 3.5+
    await client.send_message(message.channel, 'Hello')

In order for you to ``yield from`` or ``await`` a coroutine then your function must be decorated
with ``@asyncio.coroutine`` or ``async def``.

Iterables
----------

For performance reasons, many of the internal data structures were changed into a dictionary to support faster
lookup. As a consequence, this meant that some lists that were exposed via the API have changed into iterables
and not sequences. In short, this means that certain attributes now only support iteration and not any of the
sequence functions.

The affected attributes are as follows:

- :attr:`Client.servers`
- :attr:`Client.private_channels`
- :attr:`Server.channels`
- :attr:`Server.members`

Some examples of previously valid behaviour that is now invalid

.. code-block:: python3

    if client.servers[0].name == "test":
        # do something

Since they are no longer :obj:`list`\s, they no longer support indexing or any operation other than iterating.
In order to get the old behaviour you should explicitly cast it to a list.

.. code-block:: python3

    servers = list(client.servers)
    # work with servers

.. warning::

    Due to internal changes of the structure, the order you receive the data in
    is not in a guaranteed order.

Enumerations
------------

Due to dropping support for versions lower than Python 3.4.2, the library can now use
:doc:`py:library/enum` in places where it makes sense.

The common places where this was changed was in the server region, member status, and channel type.

Before:

.. code-block:: python3

    server.region == 'us-west'
    member.status == 'online'
    channel.type == 'text'

After:

.. code-block:: python3

    server.region == discord.ServerRegion.us_west
    member.status = discord.Status.online
    channel.type == discord.ChannelType.text

The main reason for this change was to reduce the use of finicky strings in the API as this
could give users a false sense of power. More information can be found in the :ref:`discord-api-enums` page.

Properties
-----------

A lot of function calls that returned constant values were changed into Python properties for ease of use
in format strings.

The following functions were changed into properties:

+----------------------------------------+--------------------------------------+
|                 Before                 |                After                 |
+----------------------------------------+--------------------------------------+
| ``User.avatar_url()``                  | :attr:`User.avatar_url`              |
+----------------------------------------+--------------------------------------+
| ``User.mention()``                     | :attr:`User.mention`                 |
+----------------------------------------+--------------------------------------+
| ``Channel.mention()``                  | :attr:`Channel.mention`              |
+----------------------------------------+--------------------------------------+
| ``Channel.is_default_channel()``       | :attr:`Channel.is_default`           |
+----------------------------------------+--------------------------------------+
| ``Role.is_everyone()``                 | :attr:`Role.is_everyone`             |
+----------------------------------------+--------------------------------------+
| ``Server.get_default_role()``          | :attr:`Server.default_role`          |
+----------------------------------------+--------------------------------------+
| ``Server.icon_url()``                  | :attr:`Server.icon_url`              |
+----------------------------------------+--------------------------------------+
| ``Server.get_default_channel()``       | :attr:`Server.default_channel`       |
+----------------------------------------+--------------------------------------+
| ``Message.get_raw_mentions()``         | :attr:`Message.raw_mentions`         |
+----------------------------------------+--------------------------------------+
| ``Message.get_raw_channel_mentions()`` | :attr:`Message.raw_channel_mentions` |
+----------------------------------------+--------------------------------------+

Member Management
-------------------

Functions that involved banning and kicking were changed.

+--------------------------------+--------------------------+
| Before                         | After                    |
+--------------------------------+--------------------------+
| ``Client.ban(server, user)``   | ``Client.ban(member)``   |
+--------------------------------+--------------------------+
| ``Client.kick(server, user)``  | ``Client.kick(member)``  |
+--------------------------------+--------------------------+

.. migrating-renames:

Renamed Functions
-------------------

Functions have been renamed.

+------------------------------------+-------------------------------------------+
| Before                             | After                                     |
+------------------------------------+-------------------------------------------+
| ``Client.set_channel_permissions`` | :meth:`Client.edit_channel_permissions`   |
+------------------------------------+-------------------------------------------+

All the :class:`Permissions` related attributes have been renamed and the `can_` prefix has been
dropped. So for example, ``can_manage_messages`` has become ``manage_messages``.

Forced Keyword Arguments
-------------------------

Since 3.0+ of Python, we can now force questions to take in forced keyword arguments. A keyword argument is when you
explicitly specify the name of the variable and assign to it, for example: ``foo(name='test')``. Due to this support,
some functions in the library were changed to force things to take said keyword arguments. This is to reduce errors of
knowing the argument order and the issues that could arise from them.

The following parameters are now exclusively keyword arguments:

- :meth:`Client.send_message`
    - ``tts``
- :meth:`Client.logs_from`
    - ``before``
    - ``after``
- :meth:`Client.edit_channel_permissions`
    - ``allow``
    - ``deny``

In the documentation you can tell if a function parameter is a forced keyword argument if it is after ``\*,``
in the function signature.

.. _migrating-running:

Running the Client
--------------------

In earlier versions of discord.py, ``client.run()`` was a blocking call to the main thread
that called it. In v0.10.0 it is still a blocking call but it handles the event loop for you.
However, in order to do that you must pass in your credentials to :meth:`Client.run`.

Basically, before:

.. code-block:: python3

    client.login('token')
    client.run()

After:

.. code-block:: python3

    client.run('token')

.. warning::

    Like in the older ``Client.run`` function, the newer one must be the one of
    the last functions to call. This is because the function is **blocking**. Registering
    events or doing anything after :meth:`Client.run` will not execute until the function
    returns.

This is a utility function that abstracts the event loop for you. There's no need for
the run call to be blocking and out of your control. Indeed, if you want control of the
event loop then doing so is quite straightforward:

.. code-block:: python3

    import discord
    import asyncio

    client = discord.Client()

    @asyncio.coroutine
    def main_task():
        yield from client.login('token')
        yield from client.connect()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_task())
    except:
        loop.run_until_complete(client.logout())
    finally:
        loop.close()



