.. currentmodule:: discord

.. _guide_topic_embeds:


.. todo
    - cover footer
    - cover timestamp

Embeds
=======

Embeds are a fundamental part of Discord's message format.

They allow you to embed rich content into your messages.

Discord typically uses embeds to display information related to links:

.. image:: /images/guide/topics/embeds/link_embed.png
    :scale: 50%

Bots are also able to send embeds without any links in the message content:

.. image:: /images/guide/topics/embeds/simple_embed.png
    :scale: 50%

Defining an Embed
------------------

Embeds are fairly straightforward to define in discord.py.

Let's try recreating the image above.
First, we'll need to construct a :class:`Embed` object.

.. code-block:: python3

    my_embed = discord.Embed()

We should set the colour of the embed next.

Seems like it's conveniently the same colour as :meth:`Colour.purple`!
So, all we need to do is provide it to the ``colour`` parameter of the constructor.

.. code-block:: python3
    :emphasize-lines: 2

    my_embed = discord.Embed(
        colour=discord.Colour.purple()
    )

.. tip::

    There is also a ``color`` parameter, and respective aliases for ``discord.Color``.
    In case you prefer that spelling.

Next, we'll set the title of the embed.

Just like ``colour``, it's another parameter of the constructor, called ``title``.

.. code-block:: python3
    :emphasize-lines: 3

    my_embed = discord.Embed(
        colour=discord.Colour.purple(),
        title="Hello, World!",
    )

Let's see how that looks so far if we send it.

.. code-block:: python3

    await channel.send(embed=my_embed)


.. image:: /images/guide/topics/embeds/simple_embed_2.png
    :scale: 38%

So close! Now, all we need to do is add the description.

.. code-block:: python3

    my_embed = discord.Embed(
        colour=discord.Colour.purple(),
        title="Hello, World!",
        description="This bot is running on discord.py!"
    )

.. image:: /images/guide/topics/embeds/simple_embed_final.png
    :scale: 38%

And that's it!

As you can see, the interface that discord.py provides is essentially a direct mapping of what you see in the Discord client.

To summarise, we call the constructor for :class:`Embed` and provide the following keyword arguments:

- ``colour`` to set the colour of the embed.
- ``title`` to set the title of the embed.
- ``description`` to set the description of the embed.

Let's take a look at what else we can add to an embed.

Using Embed Components
-----------------------

The :class:`Embed` class allows usage of the `factory` pattern.

.. hint::

    This means that certain methods will return a modified instance of the embed class,
    so you can chain method calls.

    We will discover this as we go through the guide.

Markdown
~~~~~~~~~

An embed's description and fields allow you to use markdown, so
that includes **this**, *that*, and even ``this`` -- read more about it at :ref:`_guide_topic_markdown`.

Usually, in a message's content it is not possible to send hyperlinks.
However, embeds allow you to include them! So you can do little tricks like:

.. code-block:: python3

    my_embed.description = """**Hello**! My name is Danny!
    Check out my GitHub: [click here!](https://github.com/Rapptz)
    I have a page dedicated to [`C++ Tutorials`](https://rapptz.github.io/cpptuts)!
    """

.. image:: /images/guide/topics/embeds/hyperlink_description_embed.png
    :scale: 38%

.. tip::

    Hyperlinks in markdown follow a specific format: ``[text](link)``.

It is also possible to add tooltips to hyperlinks, which are displayed when you hover over the hyperlink.

.. code-block:: python3

    my_embed.description = """**Hello**! My name is Danny!
    Check out my GitHub: [click here!](https://github.com/Rapptz "My GitHub")
    I have a page dedicated to [`C++ Tutorials`](https://rapptz.github.io/cpptuts)!
    """

.. image:: /images/guide/topics/embeds/hyperlink_tooltip_description_embed.png
    :scale: 38%

Fields
~~~~~~~

Fields can be used to add subsections to an embed, they can contain two articles of information; a name and a value.

Let's make an embed that tells us the weather in San Francisco.

We'll start off with the simple stuff, a colour, a title and a description.

.. code-block:: python3

    my_weather_embed = discord.Embed(
        colour=discord.Colour.yellow(),
        title="Weather in San Francisco, CA",
        description="Clear with a high of 59 degrees Fahrenheit.",
    )

That should look like this:

.. image:: /images/guide/topics/embeds/field_weather_embed_1.png
    :scale: 38%

Now, let's add a field that tells us the precipitation in San Francisco.

We should use :meth:`my_weather_embed.add_field() <Embed.add_field>` to add it.

.. code-block:: python3

    my_weather_embed.add_field(name="Precipitation", value="2%")

Let's see what that looks like:

.. image:: /images/guide/topics/embeds/field_weather_embed_2.png
    :scale: 38%

We should add two more fields to tell us the humidity and wind speed.

.. code-block:: python3

    my_weather_embed.add_field(name="Humidity", value="76%")
    my_weather_embed.add_field(name="Wind Speed", value="4 mph")

.. image:: /images/guide/topics/embeds/field_weather_embed_3.png
    :scale: 38%

Alright! Now, what happens if we try to add a fourth field...?

.. image:: /images/guide/topics/embeds/field_weather_embed_4.png
    :scale: 38%

.. hint::

    In the Discord client, each row of fields can contain a maximum of 3 fields.

If you wanted to, you could try using the ``inline`` keyword-only argument of :meth:`~Embed.add_field`.
This determines the positioning of the field within the embed.

By default, ``inline`` is set to ``True`` for all fields.
If it is set to ``False`` it will be displayed in a block, on its own.

Let's see what happens when we set it to ``False`` for the wind field.

.. code-block:: python3

    my_weather_embeds.add_field(name="Wind", value="4 mph", inline=False)

.. image:: /images/guide/topics/embeds/inline_field_embed.png
    :scale: 50%

.. note::

    If you want to set ``inline`` to ``False`` for a field in the middle, such as the
    ``Humidity`` field, it will appear as such:

    .. image:: /images/guide/topics/embeds/inline_middle_field_embed.png
        :scale: 50%

Author
~~~~~~~

Embeds can also have an author.
This is a small section of information that appears at the top of the embed,
it can contain an icon, a name, and a URL, which is opened when the user clicks on the name.

Let's set the author of the embed to "Today's Weather" and link to a Google search of "Weather In San Francisco".
We'll use the :meth:`my_weather_embed.set_author() <Embed.set_author>` to set these values.

.. code-block:: python3

    my_weather_embed.set_author(
        name="Today's Weather",
        url="https://goo.gl/search/Weather+In+San+Francisco",
    )

That should look a lot like this:

.. image:: /images/guide/topics/embeds/author_embed_1.png
    :scale: 38%

It appears like a "subtitle" above the title in the embed.

With the :attr:`Embed.author`, we can also set the icon of the author.
The ``icon_url`` keyword-only argument of :meth:`my_weather_embed.set_author() <Embed.set_author>` accepts a string, or anything that can be cast to a string, as the URL.
This allows us to conveniently use :class:`Asset` instances, which is used throughout the library.

In this example, we will use the :meth:`Bot.user.display_avatar <ClientUser.display_avatar>`, an :class:`Asset` instance, for the icon.

.. image:: /images/guide/topics/embeds/author_embed.png
    :scale: 50%

This isn't the only place you can add images though. Let's see how else we can incorporate images into our weather embed.

Images
~~~~~~~

There are two ways to add images to an embed:

- As the embed's ``image``.
- As the embed's ``thumbnail``.

We will add an `image of the Golden Gate Bridge`_ to the weather embed by calling
:meth:`my_weather_embed.set_image() <Embed.set_image>`:

.. code-block:: python3

    image_url = "https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg"
    my_weather_embed.set_image(url=image_url)

.. _image of the Golden Gate Bridge: https://commons.wikimedia.org/wiki/Golden_Gate_Bridge#/media/File:GoldenGateBridge-001.jpg

.. image:: /images/guide/topics/embeds/image_embed.png
    :scale: 50%

As seen above, when setting :attr:`Embed.image`, the provided URL will be displayed at the bottom of
the embed.

The alternative to this, is to set :attr:`Embed.thumbnail`, which would be displayed in the top right
corner of the embed.

Rather than setting the image to a URL like we did before, let's try attaching a file for thumbnail.

First, we have to construct a :class:`File` object. The first argument is the file path, and the second is the name of the attachment that will be used to refer to it within Discord.

.. code-block:: python3

    my_file = discord.File('./images/sunny_weather.png', 'thumbnail.png')

Next, we need to call :meth:`my_weather_embed.set_thumbnail() <Embed.set_thumbnail>` to set the thumbnail.
To refer to our attachment for the thumbnail, we will use a special URI scheme that Discord provides - ``attachment://``.

Since we called our file ``thumbnail.png``, we will set the ``url`` parameter to ``attachment://thumbnail.png``.

.. code-block:: python3

    my_weather_embed.set_thumbnail(url="attachment://thumbnail.png")

.. warning::

    Make sure to provide the file with the ``file`` parameter before sending the message.
    Otherwise, Discord will not know what attachment you are referring to within the embed.

    .. code-block:: python3

        await message.channel.send(embed=my_weather_embed, file=my_file)
