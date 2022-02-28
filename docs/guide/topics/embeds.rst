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

Alright! Now, let's add two more fields to tell us the humidity and wind speed.

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

.. code-block:: python3

    my_weather_embed.set_author(
        name="Today's Weather",
        url="https://goo.gl/search/Weather+In+San+Francisco",
        icon_url=bot.user.display_avatar
    )

In this example, we use the :meth:`Bot.user.display_avatar <ClientUser.display_avatar>`, which is an :class:`Asset` instance, for the icon.
However, you can use any image URL for ``icon_url``.

.. image:: /images/guide/topics/embeds/author_embed.png
    :scale: 50%

Images
~~~~~~~

There are two ways to add images to an embed:

- As the embed's ``image``.
- As the embed's ``thumbnail``.

We will use this `image of the Golden Gate Bridge`_ on the weather embed by calling
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

Rather than setting the URL, we are going to attach a file for the thumbnail.

.. code-block:: python3

    my_file = discord.File('./images/sunny_weather.png', 'thumbnail.png')

    my_weather_embed.set_thumbnail(url="attachment://thumbnail.png")

    await channel.send(embed=my_weather_embed, file=my_file)

What we do here is first retrieve the file from the local filesystem via :class:`discord.File`,
and then refer to the filename in the embed.

In this case the we provide the filename as ``thumbnail.png``,
so to refer to it, we use ``attachment://thumbnail.png``.

.. note::

    ``attachment://`` is a special URI scheme that Discord understands and will automatically
    place the attached file as the thumbnail of the embed.

.. warning::

    Make sure to provide the file with the ``file`` parameter before sending the message.
