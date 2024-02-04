.. currentmodule:: discord

.. _guide_install:

Installation
=============

Welcome to discord.py, a library for Python to aid in creating applications for Discord.

Prerequisites
--------------

To install discord.py you'll need Python version 3.8 or higher. Earlier versions of Python are not supported.

.. _guide_install_primer:

Primer
-------------

On Unix systems you can run the following command to install discord.py from PyPI.

.. code-block:: shell

    python3 -m pip install -U discord.py

On Windows systems, you can use the following command instead.

.. code-block:: shell

    py -3 -m pip install -U discord.py

Voice Support
~~~~~~~~~~~~~~

Voice support (e.g. playing audio in voice channels) is not enabled by default and can be enabled by installing ``discord.py[voice]`` instead of ``discord.py``. ::

    pip install -U "discord.py[voice]"

Linux systems may need to install additional dependencies via your package manager to get full voice support:-

.. tab:: Debian/Ubuntu

    .. code-block:: shell

        $ sudo apt install libffi-dev libsodium-dev python3-dev

.. tab:: Fedora/CentOS

    .. code-block:: shell

        $ sudo dnf install libffi-devel libsodium-devel python3-devel

.. tab:: Arch Linux

    .. code-block:: shell

        $ pacman -Syu libsodium

For other distributions, please use your package manager to find libraries for ``libffi``, ``libsodium``, and the Python 3 development headers.

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Global Python environments get cluttered with dependencies very easily - virtual environments can help separate your projects into clean, organized folders.
Virtual environments (or "venvs") help separate project dependencies from the global Python installation, avoiding polluting
other projects using the same Python version. They also allow you to install libraries that you may not have permission to install globally.

To quickly get a virtual environment working in your project folder:

1. Ensure you are in your project's root directory.

    .. code-block:: shell

        $ cd your_bot_source
        $ python3 -m venv .venv

    The ``.venv`` argument is the output folder of the virtual environment, this can be named anything but be sure to remember it.

2. Activate the virtual environment:

    .. code-block:: shell

        $ source .venv/bin/activate

    On Windows, use the following:

    .. code-block:: pwsh

        $ .\.venv\Scripts\activate

3. You can then use ``pip`` and ``python`` without interfering with other projects:

    .. code-block:: shell

        $ pip install -U discord.py  # note the lack of ``py -3 -m`` or ``python3 -m``
        $ python your_bot.py

For a more in-depth look into virtual environments, see :doc:`py:tutorial/venv`.

Next Steps
-----------

Now that you've installed discord.py, the next step is to begin making your bot application. See :ref:`_guide_intro` for further getting started steps.
