.. currentmodule:: discord

.. _guide_topic_markdown:

Markdown
==========

Before we get into the grit of things, it's good to explain what Markdown actually *is*. It's a popular markup language
that's used on platforms like Discord, GitHub, and many more. If you've used any of those platforms, you've probably
used Markdown already without realising!

Just like a programming language, a markup language (like Markdown!) is interpreted by a computer, but instead of
describing a *program*, a markup language describes a *document* instead. While the exact details differ between each
different markup language, you'll usually find yourself using one if you'd like to add formatting and structure to a
text document in a way that still makes sense to a human.

Markdown is an incredibly widespread language, and not everybody agrees on *how* things should be done. Unfortunately,
this means that there are a great many *flavours* of Markdown in use, with each flavour having its own design goals and
differences. Because this guide revolves around discord.py, **this section will focus specifically on the flavour of
Markdown used by Discord**, as opposed to the flavour used by other platforms like GitHub or Slack.

If you'd like more information about Markdown outside of Discord, you should have a look at the `CommonMark website
<https://commonmark.org/>`_ or the `GitHub Flavoured Markdown specification <https://github.github.com/gfm/>`_. 

With all that said, let's get into it!

Text styling
--------------

Markdown makes it quite straightforward to style text, and Discord is no different in this regard. All of the usual
suspects are supported, so you can use **bold** text, *italic* text, :strike:`strikethrough` and :underline:`underline`.

.. note::

    The way text is processed and displayed differs significantly between Discord clients, so mixing formatting styles
    may not behave as you expect.

.. list-table::
    :widths: 20 25 55

    * - Style
      - Example
      - Remarks

    * - Wrap text in asterisks (``*``) for *italics*.
      - .. rst-class:: markdown-example

            ``This is *italicised*``

        .. image:: /images/guide/markdown_italicised.png
            :scale: 60%
            :alt: The word "italicised" is displayed in italics.

      - A single underscore may also be used instead of an asterisk, so the text ``This is _italicised_`` is equivalent
        to ``This is *italicised*``.

    * - Wrap text in dual asterisks (``**``) for **bold** text.
      - .. rst-class:: markdown-example

          ``This is **bold**``

        .. image:: /images/guide/markdown_bold.png
            :scale: 60%
            :alt: The word "bold" is displayed in bold.

      -

    * - Wrap text in dual underscores (``__``) for :underline:`underlined` text.
      - .. rst-class:: markdown-example

            ``This is... __underlined__!``

        .. image:: /images/guide/markdown_underline.png
            :scale: 60%
            :alt: The word "underlined" is underlined.

      - Underlining text requires exactly two underscores. Using only a *single* underscore will italicise text instead.

    * - Wrap text in dual tildes (``~~``) for :strike:`crossed out` text.
      - .. rst-class:: markdown-example

            ``This is ~~crossed out~~``

        .. image:: /images/guide/markdown_strikethrough.png
            :scale: 60%
            :alt: The phrase "crossed out" is crossed out.

      -

    * - Wrap text in single or double backticks (````` or ``````) to produce ``raw`` text.
      - .. rst-class:: markdown-example

            ```This text is *raw*!```

        .. image:: /images/guide/markdown_raw_text.png
            :scale: 60%
            :alt: The text is displayed in a monospace font atop a darker background.

      - The usual formatting rules are *not* processed inside of ``raw`` text, so you can use symbols like ``*``, ``~``,
        and ``_`` without needing to escape them. See the :ref:`section on escaping special
        characters<escaping-special-characters>` for more information.

    * - Wrap text in double vertical bars (``||``) to "spoiler" text. 
      - .. rst-class:: markdown-example

            ``This is ||a big secret!||``

        .. image:: /images/guide/markdown_spoiler.png
            :scale: 60%
            :alt: The phrase "a big secret" is obscured, and is only revealed when clicked/tapped on.

        .. image:: /images/guide/markdown_spoiler_revealed.png
            :scale: 60%
            :alt: The phrase "a big secret" is visible after being clicked/tapped on.

      - Spoilered text is obscured until a user reveals it by explicitly clicking/tapping on it. If the text contains an
        embeddable URL, the embed will be blurred until the spoiler is revealed.

Codeblocks
------------

While Discord supports adding attachments to messages, it's often more convenient to share snippets of code directly
*within* a message, rather than as an attachment. It can be hard to read code without a monospace font or syntax
highlighting, so Markdown allows you to place code inside of *codeblocks* to display it in a more readable manner.

Codeblocks are created by wrapping text inside triple backticks, like so:

.. code-block:: none

    ``` print("Hello documentation!") ```

.. note::

    The usual formatting rules are *not* processed with codeblocks, so you can use symbols like ``*``, ``~``, and ``_``
    without needing to escape them. See the :ref:`section on escaping special characters<escaping-special-characters>`
    for more information.

When displayed on Discord, they use a monospace font and have a darker background.

.. image:: /images/guide/markdown_codeblock.png
    :align: left
    :alt: Code that displays text to the terminal, enclosed within a codeblock.


.. note::

    Discord will always display codeblocks on their own, so you can't have text to the left or right of them. For
    example, the following text

    .. code-block:: none

        Hello from before the codeblock! ``` print("Hello documentation!") ``` Hello from after the codeblock!

    \... is actually displayed like this:

    .. image:: /images/guide/markdown_codeblock_display.png
        :align: left
        :alt: The phrases "Hello from before the codeblock!" and "Hello from after the codeblock!" are displayed on
            their own lines, with the codeblock in the middle.

If you'd like to use syntax highlighting within a codeblock, you'll have to specify *what* language to use for
highlighting. This can be done by following the opening sequence of backticks with a language name or file extension,
such as ``python`` or ``py``, ``ruby`` or ``rb``, or similar.

For example, we can highlight Python source code by adding ``py`` after the opening backticks:

.. code-block:: none

    ```py four = 2 * 2 print(f"This is a demo of syntax highlighting. 2 + 2 is {four}") ```

When displayed on Discord, the code is highlighted accordingly:

.. image:: /images/guide/markdown_codeblock_syntax_highlighting.png
    :align: left
    :alt: Code that displays text to the terminal, enclosed within a codeblock. Segments of the code are highlighted based
        on their role - string and integer literals are highlighted a dark turquoise, whereas symbols and names are left
        plain.

.. note::

    While syntax highlighting is supported for many different languages, it's impossible for Discord to support syntax
    highlighting for *everything*. Likewise, the colour scheme used for syntax highlighting differs between Discord
    clients, and some clients do not support syntax highlighting within codeblocks at all.

Mentions
----------

Discord supports *mentions* to reference users, roles and channels, and additionally supports a few "special" mentions
like ``@here`` and ``@everyone``. Role and user mentions (as well as ``@here`` and ``@everyone``) are typically used to
notify groups of users en masse for important announcements, whereas channel mentions just act as shortcuts that make it
easier to navigate Discord.

.. note::

    You can use the :class:`~discord.AllowedMentions` class to prevent mentions from notifying other users. See its
    documentation for more details.

.. list-table::
    :widths: 20 25 65

    * - Format
      - Example
      - Remarks

    * - ``@here``
      - .. rst-class:: markdown-example

            ``Hello @here!``

        .. image:: /images/guide/markdown_here_mention.png
            :scale: 60%
            :alt: A message containing an ``@here`` mention.

      - ``@here`` mentions notify all **online** members that have :attr:`~discord.Permissions.read_messages`
        permissions in the containing channel.

    * - ``@everyone``
      - .. rst-class:: markdown-example

            ``Greetings @everyone!``

        .. image:: /images/guide/markdown_everyone_mention.png
            :scale: 60%
            :alt: A message containing an ``@everyone`` mention.

      - ``@everyone`` mentions notify **all** members that have :attr:`~discord.Permissions.read_messages` permissions
        in the containing channel. Unlike ``@here`` mentions, ``@everyone`` mentions will notify members regardless of
        whether they are online or not.

    * - ``<@USER>`` or ``<@!USER>``, where *USER* is a user ID.
      - .. rst-class:: markdown-example

            ``Good morning <@636797375184240640>!``

        .. image:: /images/guide/markdown_user_mention.png
            :scale: 50%
            :alt: A message that mentions a user named ``Documentation Mention Scapegoat``.

      - User mentions notify the user with the specified ID. Unfortunately, the way invalid mentions are displayed
        differs between clients - mobile clients will display ``@invalid-user`` for invalid mentions, whereas desktop
        clients will simply display the raw markdown.

        It's also important to note that there was previously a distinction between the ``@`` and ``@!`` forms of user
        mentions, but most Discord clients now treat them identically. Because this complicates the process of detecting
        mentions in messages, you should use :attr:`discord.Message.mentions` instead of trying to parse them yourself.

        Likewise, instead of formatting the mention string yourself, you should use :attr:`discord.User.mention` or
        :attr:`discord.Member.mention` instead.

    * - ``<@&ROLE>``, where *ROLE* is a role ID.
      - .. rst-class:: markdown-example

            ``<@&953783101891436546> Hello!``

        .. image:: /images/guide/markdown_role_mention.png
            :scale: 60%
            :alt: A message that mentions a role named ``Documentation Role``.

      - If a role is :attr:`~discord.Role.mentionable`, a role mention will notify all members with the role. If a role
        with the specified ID is not found, the mention will display as ``@deleted-role`` instead.

        Instead of formatting the mention string yourself, you should use :attr:`discord.Role.mention`.

    * - ``<#CHANNEL>``, where *CHANNEL* is a channel ID.
      - .. rst-class:: markdown-example
            
            ``This is the <#953783075588952074> channel.``

        .. image:: /images/guide/markdown_channel_mention.png
            :scale: 60%
            :alt: A message that mentions a channel named ``documentation``.

      - Channel mentions act as simple shortcuts to the channel they represent. If a channel with the specified ID is
        not found, the mention will display as ``@deleted-channel`` instead.

        Instead of formatting the mention string yourself, you should use :attr:`discord.TextChannel.mention`.

Timestamp formatting
------------------------

Formatting date

.. list-table::
    :widths: 20 25 55

    * - Style
      - Example
      - Remarks

Emoji
-------


Suppressing embeds
--------------------

.. note::

    If you wish to make your own content embeddable on Discord, you might be interested in adding `OpenGraph metadata
    <https://ogp.me/>`_ to your website.

Discord supports "embedding" links to provide more helpful information about the linked content, such as a title or
thumbnail. For services like YouTube and Spotify, Discord will embed a media player so that you can watch or listen
without leaving the app. Neat!

As an example, Discord will display an embed if you link to a GitHub repository:

.. image:: /images/guide/markdown_url_embed.png
    :align: left
    :alt: A link to discord.py's GitHub repository, with an embedded image displayed below it.

Discord embeds *each* link in a message, so messages that contain multiple links might take up more vertical space than
you'd like. Because this isn't always desirable, Discord allows you to suppress embeds from an individual URL by
wrapping the URL in angle brackets.

Since the embed from the example above is quite large, we might want to hide it next time

.. code-block:: none

    This URL won't be embedded! <https://github.com/Rapptz/discord.py>

We wrapped the URL in ``<`` and ``>``, so Discord won't display an embed for it:

.. image:: /images/guide/markdown_url_suppressed.png
    :align: left
    :alt: A link to discord.py's GitHub repository.

.. note::

    Users with the :attr:`~discord.Permissions.manage_messages` permission can suppress embeds in any message. See the
    ``suppress`` parameter of :meth:`~discord.Message.edit` for more details.

.. _escaping-special-characters:

Escaping special characters
-----------------------------