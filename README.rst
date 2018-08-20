discord.py
==========

.. image:: https://img.shields.io/pypi/v/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py

discord.py is an API wrapper for Discord written in Python.

This was written to allow easier writing of bots or chat logs. Make sure to familiarise yourself with the API using the `documentation <http://discordpy.rtfd.org/en/latest>`__.

Breaking Changes
---------------

The discord API is constantly changing and the wrapper API is as well. There will be no effort to keep backwards compatibility in versions before ``v1.0.0``.

I recommend joining either the `official discord.py server <https://discord.gg/r3sSKJJ>`_ or the `Discord API server <https://discord.gg/discord-api>`_ for help and discussion about the library.

Installing
----------

```
python3 -m pip install -U git+https://github.com/Crypti-x/discord.py@rewrite#egg=discord.py[voice]
```

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. ``apt``, ``yum``, etc) before running the above command:

* libffi-dev (or ``libffi-devel`` on some systems)
* python-dev (e.g. ``python3.5-dev`` for Python 3.5)

Quick Example
------------

.. code:: py

   client = discord.Client()

f = open('f.pcm', 'wb')

@client.event
async def on_ready():
	print("up!")


@client.event
async def on_message(msg):
	if msg.author.id != 332864061496623104:
		return

	if msg.content == "join":
		await msg.author.voice.channel.connect()





@client.event
async def on_voice_receive(vc, user, data):
    f.write(data)



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

