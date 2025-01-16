selfcord.py
===========

.. image:: https://img.shields.io/endpoint?color=neon&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2Fdpy_self
   :target: https://t.me/dpy_self
   :alt: Telegram chat
.. image:: https://img.shields.io/pypi/v/discord.py-self.svg
   :target: https://pypi.python.org/pypi/discord.py-self
   :alt: PyPI version info
.. image:: https://img.shields.io/pypi/pyversions/discord.py.svg
   :target: https://pypi.python.org/pypi/discord.py-self
   :alt: PyPI supported Python versions
.. image:: https://img.shields.io/pypi/dm/discord.py-self.svg
   :target: https://pypi.python.org/pypi/discord.py-self
   :alt: PyPI downloads per month

A modern, easy to use, feature-rich, and async ready API wrapper for Discord's user API written in Python. Check out the `master branch <https://github.com/dolfies/discord.py-self>`_ for more information. 

Notice
-------

This branch is just a copy of regular ``discord.py-self`` with the import name changed to ``selfcord``, so ``discord.py-self`` can be used alongside upstream ``discord.py``. Use of this branch is not recommended, and should only be used if you are using both ``discord.py`` and ``discord.py-self`` in the same *project*. Otherwise, utilize virtual environments to seperate the installs of the two libraries.

This library is 100% compatible with regular ``discord.py-self``, and any documentation, examples, etc. need only the import name changed.

Installing
----------

**Python 3.8 or higher is required**

This branch is synced with the master branch on every commit. Because of this, the branch always hosts the current development version.

Because of this, it is *highly* recommended to pin your installation to a certain commit. You can do this like so:

.. code:: sh

    # Linux/macOS
    python3 -m pip install git+https://github.com/dolfies/discord.py-self@2193ws21sf4cs74hdg317ac8ad076ed234d3dbf70g1#egg=selfcord.py[voice]

    # Windows
    py -3 -m pip install git+https://github.com/dolfies/discord.py-self@2193ws21sf4cs74hdg317ac8ad076ed234d3dbf70g1#egg=selfcord.py[voice]

Otherwise, you can install the current commit:

.. code:: sh

    # Linux/macOS
    python3 -m pip install git+https://github.com/dolfies/discord.py-self@renamed#egg=selfcord.py[voice]

    # Windows
    py -3 -m pip install git+https://github.com/dolfies/discord.py-self@renamed#egg=selfcord.py[voice]
