# discord.py

[![PyPI](https://img.shields.io/pypi/v/discord.py.svg)](https://pypi.python.org/pypi/discord.py/)
[![PyPI](https://img.shields.io/pypi/pyversions/discord.py.svg)](https://pypi.python.org/pypi/discord.py/)

discord.py is an API wrapper for Discord written in Python.

This was written to allow easier writing of bots or chat logs. Make sure to familiarise yourself with the API using the [documentation][doc].

[doc]: http://discordpy.rtfd.org/en/latest

### Breaking Changes

The discord API is constantly changing and the wrapper API is as well. There will be no effort to keep backwards compatibility in versions before `v1.0.0`.

I recommend that you follow the discussion in the [unofficial Discord API discord channel][ch] and update your installation periodically. I will attempt to make note of breaking changes in the API channel so make sure to subscribe to library news by typing `?sub news` in the channel.

[ch]: https://discord.gg/0SBTUU1wZTUzBx2q

## Installing

To install the library without full voice support, you can just run the following command:

```
python3 -m pip install -U discord.py
```

Otherwise to get voice support you should run the following command:

```
python3 -m pip install -U discord.py[voice]
```

To install the development version, do the following:

```
python3 -m pip install -U https://github.com/Rapptz/discord.py/archive/master.zip#egg=discord.py[voice]
```

or the more long winded from cloned source:

```
$ git clone https://github.com/Rapptz/discord.py
$ cd discord.py
$ python3 -m pip install -U .[voice]
```

Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. `apt`, `yum`, etc) before running the above command:

- libffi-dev (or `libffi-devel` on some systems)
- python<version>-dev (e.g. `python3.5-dev` for Python 3.5)

## Quick Example

```py
import discord
import asyncio

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')

client.run('token')
```

Note that in Python 3.4 you use `@asyncio.coroutine` instead of `async def` and `yield from` instead of `await`.

You can find examples in the examples directory.

## Requirements

- Python 3.4.2+
- `aiohttp` library
- `websockets` library
- `PyNaCl` library (optional, for voice only)
    - On Linux systems this requires the `libffi` library. You can install in
      debian based systems by doing `sudo apt-get install libffi-dev`.

Usually `pip` will handle these for you.

## Related Projects

- [discord.js](https://github.com/discord-js/discord.js)
- [discord.io](https://github.com/izy521/discord.io)
- [Discord.NET](https://github.com/RogueException/Discord.Net)
- [DiscordSharp](https://github.com/Luigifan/DiscordSharp)
- [Discord4J](https://github.com/knobody/Discord4J)
- [discordrb](https://github.com/meew0/discordrb)
