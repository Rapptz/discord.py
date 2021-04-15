.. discord.py documentation master file, created by
   sphinx-quickstart on Fri Aug 21 05:43:30 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to discord.py
===========================

.. image:: /images/snake.svg
.. image:: /images/snake_dark.svg

discord.py is a modern, easy to use, feature-rich, and async ready API wrapper
for Discord.

**Features:**

- Modern Pythonic API using ``async``\/``await`` syntax
- Sane rate limit handling that prevents 429s
- Implements the entire Discord API
- Command extension to aid with bot creation
- Easy to use with an object oriented design
- Optimised for both speed and memory

Getting started
-----------------

Is this your first time using the library? This is the place to get started!

- **First steps:** :doc:`intro` | :doc:`quickstart` | :doc:`logging`
- **Working with Discord:** :doc:`discord` | :doc:`intents`
- **Examples:** Many examples are available in the :resource:`repository <examples>`.

Getting help
--------------

If you're having trouble with something, these resources might help.

- Try the :doc:`faq` first, it's got answers to all common questions.
- Ask us and hang out with us in our :resource:`Discord <discord>` server.
- If you're looking for something specific, try the :ref:`index <genindex>` or :ref:`searching <search>`.
- Report bugs in the :resource:`issue tracker <issues>`.
- Ask in our :resource:`GitHub discussions page <discussions>`.

Extensions
------------

These extensions help you during development when it comes to common tasks.

.. toctree::
  :maxdepth: 1

  ext/commands/index.rst
  ext/tasks/index.rst

Manuals
---------

These pages go into great detail about everything the API can do.

.. toctree::
  :maxdepth: 1

  api
  discord.ext.commands API Reference <ext/commands/api.rst>
  discord.ext.tasks API Reference <ext/tasks/index.rst>

Meta
------

If you're looking for something related to the project itself, it's here.

.. toctree::
  :maxdepth: 1

  whats_new
  version_guarantees
  migrating
