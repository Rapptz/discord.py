:orphan:

.. currentmodule:: discord

.. _guide_intro:

Introduction
=============

Welcome to discord.py, a library for Python to aid in creating applications for Discord.

Prerequisites
--------------

discord.py requires Python 3.8.0 or higher. Support for earlier versions is not provided as they have been deprecated.

.. _guide_intro_installation:

Installation
-------------

discord.py is available on PyPI: ::

    python3 -m pip install -U discord.py

If you are on Windows, you should use the following command instead: ::

    py -3 -m pip install -U discord.py

Voice support (e.g. joining voice channels and playing music) is not supported by default, and can be installed by installing ``discord.py[voice]`` instead of ``discord.py``; ::

    pip install -U discord.py[voice]

Linux environments may need to install additional dependencies to get full voice support.

For **Debian/Ubuntu** systems:

.. code-block:: shell

    $ sudo apt install libffi-dev libsodium-dev python3-dev

For **Fedora/CentOS** systems:

.. code-block:: shell

    $ sudo dnf install libffi-devel libsodium-devel python3-devel

For **Arch Linux** systems:

.. code-block:: shell

    $ pacman -Syu libsodium

For other distributions, please use your package manager to find libraries for ``libffi``, ``libsodium``, and the Python 3 development headers.

Windows will not need additional dependencies as they are bundled with discord.py.

Virtual Environments
~~~~~~~~~~~~~~~~~~~~~

Virtual environment (or "venv") is a concept introduced by Python 3.3 used to help separate project dependencies from the global Python installation, thereby not polluting
other projects using the same Python version. They also allow you to install libraries that you may not have permission to install globally.

To quickly get a virtual environment working in your project folder:

1. Ensure you are in your project's root directory.

    .. code-block:: shell

        $ cd your_bot_source
        $ python3 -m venv .venv

    The ``.venv`` argument is the output folder of the virtual environment, this can be named anything but be sure to keep it in mind.

2. Activate the virtual environment:

    .. code-block:: shell

        $ source .venv/bin/activate

    On Windows, use the following:

    .. code-block:: shell

        $ .\.venv\Scripts\activate.bat

3. You can then use ``pip`` and ``python`` without interferring with other projects:

    .. code-block:: shell

        $ pip install -U discord.py  # note the lack of ``py -3 -m`` or ``python3 -m``
        $ python your_bot.py

For a more in-depth look into virtual environments, see :doc:`py:tutorial/venv`.

Next Steps
-----------

Now that you've installed discord.py, the next step would be to begin making your bot application. See :ref:`guide_quickstart` for a simple explanation on the commands extension.
