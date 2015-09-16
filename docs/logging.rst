Setting Up Logging
===================

Newer version of *discord.py* have the capability of logging certain events via the `logging`_ python module.

This is helpful if you want to see certain issues in *discord.py* or want to listen to events yourself.

Setting up logging is fairly simple: ::

    import discord
    import logging

    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

This would create a logger that writes to a file called ``discord.log``. This is recommended as there are a lot of events
logged at a time and it would clog out the stdout of your program.

For more information, check the documentation and tutorial of the `logging`_ module.

.. _logging: https://docs.python.org/2/library/logging.html
