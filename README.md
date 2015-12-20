# discord.py

[![PyPI](https://img.shields.io/pypi/v/discord.py.svg)](https://pypi.python.org/pypi/discord.py/)
[![PyPI](https://img.shields.io/pypi/dm/discord.py.svg)](https://pypi.python.org/pypi/discord.py/)
[![PyPI](https://img.shields.io/pypi/pyversions/discord.py.svg)](https://pypi.python.org/pypi/discord.py/)

discord.py is an API wrapper for Discord written in Python.

This was written to allow easier writing of bots or chat logs. Make sure to familiarise yourself with the API using the [documentation][doc].

[doc]: http://rapptz.github.io/discord.py/

### Breaking Changes

The discord API is constantly changing and the wrapper API is as well. There will be no effort to keep backwards compatibility in versions before `v1.0.0`.

I recommend that you follow the discussion in the [unofficial Discord API discord channel][ch] and update your installation periodically through `pip install --upgrade discord.py`. I will attempt to make note of breaking changes in the API channel.

[ch]: https://discord.gg/0SBTUU1wZTUzBx2q

## Installing

Installing is pretty easy.

```
pip install discord.py
```

Will install the latest 'stable' version of the library.

If you want to install the development version of the library, then do the following:

```
pip install git+https://github.com/Rapptz/discord.py@develop
```

Installing the async beta is similar.

```
pip install git+https://github.com/Rapptz/discord.py@async
```

Note that this requires `git` to be installed.

## Quick Example

```py
import discord
import asyncio

client = discord.Client()

@client.async_event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.async_event
def on_message(message):
    if message.content.startswith('!test'):
        logs = yield from client.logs_from(message.channel, limit=100)
        counter = 0
        tmp = yield from client.send_message(message.channel, 'Calculating messages...')
        for log in logs:
            if log.author == message.author:
                counter += 1

        yield from client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        yield from asyncio.sleep(5)
        yield from client.send_message(message.channel, 'Done sleeping')

def main_task():
    yield from client.login('email', 'password')
    yield from client.connect()

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main_task())
except Exception:
    loop.run_until_complete(client.close())
finally:
    loop.close()
```

You can find examples in the examples directory.

## Requirements

- Python 3.4.2+
- `aiohttp` library
- `websockets` library

Usually `pip` will handle these for you.

## Related Projects

- [discord.js](https://github.com/discord-js/discord.js)
- [discord.io](https://github.com/izy521/discord.io)
- [Discord.NET](https://github.com/RogueException/Discord.Net)
- [DiscordSharp](https://github.com/Luigifan/DiscordSharp)
- [Discord4J](https://github.com/knobody/Discord4J)
- [discordrb](https://github.com/meew0/discordrb)
