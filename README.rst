discord.py
==========

.. image:: https://img.shields.io/pypi/v/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py

discord.py is an API wrapper for Discord written in Python.

This was written to allow easier writing of bots or chat logs. Make sure to familiarise yourself with the API using the `documentation <http://discordpy.rtfd.org/en/latest>`__.

Breaking Changes
----------------

The discord API is constantly changing and the wrapper API is as well. There will be no effort to keep backwards compatibility in versions before ``v1.0.0``.

I recommend joining either the `official discord.py server <https://discord.gg/r3sSKJJ>`_ or the `Discord API server <https://discord.gg/discord-api>`_ for help and discussion about the library.

Installing
----------

To install the library without full voice support, you can just run the following command:

.. code:: sh

    python3 -m pip install -U discord.py

Otherwise to get voice support you should run the following command:

.. code:: sh

    python3 -m pip install -U discord.py[voice]


To install the development version, do the following:

.. code:: sh

    python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/master.zip#egg=discord.py[voice]

or the more long winded from cloned source:

.. code:: sh

    $ git clone https://github.com/Rapptz/discord.py
    $ cd discord.py
    $ python3 -m pip install -U .[voice]

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. ``apt``, ``yum``, etc) before running the above command:

* libffi-dev (or ``libffi-devel`` on some systems)
* python-dev (e.g. ``python3.5-dev`` for Python 3.5)

Quick Example
-------------

.. code:: py

    import discord
    import asyncio

    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged in as')
            print(self.user.name)
            print(self.user.id)
            print('------')

        async def on_message(self, message):
            # don't respond to ourselves
            if message.author == self.user:
                return
            if message.content.startswith('!test'):
                counter = 0
                tmp = await message.channel.send('Calculating messages...')
                async for msg in message.channel.history(limit=100):
                    if msg.author == message.author:
                        counter += 1

                await tmp.edit(content='You have {} messages.'.format(counter))
            elif message.content.startswith('!sleep'):
                with message.channel.typing():
                    await asyncio.sleep(5.0)
                    await message.channel.send('Done sleeping.')

    client = MyClient()
    client.run('token')

You can find examples in the examples directory.

Requirements
------------

* Python 3.5.3+
* ``aiohttp`` library
* ``websockets`` library
* ``PyNaCl`` library (optional, for voice only)

  - On Linux systems this requires the ``libffi`` library. You can install in
    debian based systems by doing ``sudo apt-get install libffi-dev``.

Usually ``pip`` will handle these for you.

