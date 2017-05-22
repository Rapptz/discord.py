.. currentmodule:: discord

.. _intro:

Introduction
==============

This is the documentation for discord.py, a library for Python to aid
in creating applications that utilise the Discord API.

Prerequisites
---------------

discord.py works with Python 3.4.2 or higher. Support for earlier versions of Python
is not provided. Python 2.7 or lower is not supported. Python 3.3 is not supported
due to one of the dependencies (``aiohttp``) not supporting Python 3.3.


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

- libffi
- libnacl
- python3-dev

For a debian-based system, the following command will help get those dependencies:

.. code-block:: shell

    $ apt install libffi-dev libnacl-dev python3-dev

Remember to check your permissions!

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Sometimes we don't want to pollute our system installs with a library or we want to maintain
different versions of a library than the currently system installed one. Or we don't have permissions to
install a library along side with the system installed ones. For this purpose, the standard library as
of 3.3 comes with a concept called "Virtual Environment" to help maintain these separate versions.

A more in-depth tutorial is found on `the official documentation. <https://docs.python.org/3/tutorial/venv.html>`_

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

Congratulations. You now have a virtual environment all set up without messing with your system installation.

Basic Concepts
---------------

discord.py revolves around the concept of :ref:`events <discord-api-events>`.
An event is something you listen to and then respond to. For example, when a message
happens, you will receive an event about it and you can then respond to it.

A quick example to showcase how events work:

.. code-block:: python3

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged on as {0}!'.format(self.user))

        async def on_message(self, message):
            print('Message from {0.author}: {0.content}'.format(message))

    client = MyClient()
    client.run('my token goes here')

