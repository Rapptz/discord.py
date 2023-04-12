:orphan:

.. currentmodule:: discord

.. _intro:

Introduction
==============

This is the documentation for discord.py, a library for Python to aid
in creating applications that utilise the Discord API.

Prerequisites
---------------

discord.py works with Python 3.8 or higher. Support for earlier versions of Python
is not provided. Python 2.7 or lower is not supported. Python 3.7 or lower is not supported.


.. _installing:

Installing
-----------

You can get the library directly from PyPI: ::

    python3 -m pip install -U discord.py

If you are using Windows, then the following should be used instead: ::

    py -3 -m pip install -U discord.py


To get voice support, you should use ``discord.py[voice]`` instead of ``discord.py``, e.g. ::

    python3 -m pip install -U discord.py[voice]

On Linux environments, installing voice requires getting the following dependencies:

- `libffi <https://github.com/libffi/libffi>`_
- `libnacl <https://github.com/saltstack/libnacl>`_
- `python3-dev <https://packages.debian.org/python3-dev>`_

For a Debian-based system, the following command will get these dependencies:

.. code-block:: shell

    $ apt install libffi-dev libnacl-dev python3-dev

Remember to check your permissions!

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Sometimes you want to keep libraries from polluting system installs or use a different version of
libraries than the ones installed on the system. You might also not have permissions to install libraries system-wide.
For this purpose, the standard library as of Python 3.3 comes with a concept called "Virtual Environment"s to
help maintain these separate versions.

A more in-depth tutorial is found on :doc:`py:tutorial/venv`.

However, for the quick and dirty:

1. Go to your project's working directory:

    .. code-block:: shell

        $ cd your-bot-source
        $ python3 -m venv bot-env

2. Activate the virtual environment:

    .. code-block:: shell

        $ source bot-env/bin/activate

    On Windows you activate it with:

    .. code-block:: shell

        $ bot-env\Scripts\activate.bat

3. Use pip like usual:

    .. code-block:: shell

        $ pip install -U discord.py

Congratulations. You now have a virtual environment all set up.

.. note::

    Scripts executed with ``py -3`` will ignore any currently active virtual
    environment, as the ``-3`` specifies a global scope.

Basic Concepts
---------------

discord.py revolves around the concept of :ref:`events <discord-api-events>`.
An event is something you listen to and then respond to. For example, when a message
happens, you will receive an event about it that you can respond to.

A quick example to showcase how events work:

.. code-block:: python3

    # This example requires the 'message_content' intent.

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print(f'Logged on as {self.user}!')

        async def on_message(self, message):
            print(f'Message from {message.author}: {message.content}')

    intents = discord.Intents.default()
    intents.message_content = True

    client = MyClient(intents=intents)
    client.run('my token goes here')

