discord.py
==========

.. image:: https://discord.com/api/guilds/336642139381301249/embed.png
   :target: https://discord.gg/r3sSKJJ
   :alt: Discord 伺服器邀請連結
.. image:: https://img.shields.io/pypi/v/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
   :alt: PyPI 版本資訊
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py
   :alt: PyPI 支援的 Python 版本

一個現代化、易於使用、功能豐富且支援非同步的 Discord Python API 封裝套件。

主要特色
-------------

- 使用 ``async`` 與 ``await`` 打造的現代化 Pythonic API。
- 妥善的速率限制（rate limit）處理機制。
- 在速度與記憶體使用上皆經過最佳化。

安裝方式
----------

**需要 Python 3.8 以上版本**

若要安裝不含完整語音支援的函式庫，只需執行以下指令：

.. note::

    建議使用 `虛擬環境 <https://docs.python.org/3/library/venv.html>`__ 來安裝此函式庫，
    尤其是在 Linux 系統上，因為系統內建的 Python 屬於外部託管，會限制可安裝的套件。


.. code:: sh

    # Linux/macOS
    python3 -m pip install -U discord.py

    # Windows
    py -3 -m pip install -U discord.py

若想取得語音支援，則應執行以下指令：

.. code:: sh

    # Linux/macOS
    python3 -m pip install -U "discord.py[voice]"

    # Windows
    py -3 -m pip install -U discord.py[voice]


若要安裝開發版本，請依照以下步驟操作：

.. code:: sh

    $ git clone https://github.com/Rapptz/discord.py
    $ cd discord.py
    $ python3 -m pip install -U .[voice]


選用套件
~~~~~~~~~~~~~~~~~~

* `PyNaCl <https://pypi.org/project/PyNaCl/>`__（用於語音支援）

請注意，若要在 Linux 上安裝語音支援，必須先透過你慣用的套件管理員（例如 ``apt``、``dnf`` 等）安裝以下套件，再執行上述指令：

* libffi-dev（在某些系統上為 ``libffi-devel``）
* python-dev（例如 Python 3.8 對應的 ``python3.8-dev``）

快速範例
--------------

.. code:: py

    import discord

    class MyClient(discord.Client):
        async def on_ready(self):
            print('Logged on as', self.user)

        async def on_message(self, message):
            # 不要回應自己發的訊息
            if message.author == self.user:
                return

            if message.content == 'ping':
                await message.channel.send('pong')

    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)
    client.run('token')

機器人（Bot）範例
~~~~~~~~~~~~~

.. code:: py

    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='>', intents=intents)

    @bot.command()
    async def ping(ctx):
        await ctx.send('pong')

    bot.run('token')

你可以在 examples 目錄中找到更多範例。

相關連結
------

- `官方文件 <https://discordpy.readthedocs.io/en/latest/index.html>`_
- `官方 Discord 伺服器 <https://discord.gg/r3sSKJJ>`_
- `Discord API <https://discord.gg/discord-api>`_