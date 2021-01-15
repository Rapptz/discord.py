# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from . import utils
from .user import User
from .asset import Asset
from .team import Team


class AppInfo:
    """Represents the application info for the bot provided by Discord.


    Attributes
    -------------
    id: :class:`int`
        The application ID.
    name: :class:`str`
        The application name.
    owner: :class:`User`
        The application owner.
    team: Optional[:class:`Team`]
        The application's team.

        .. versionadded:: 1.3

    icon: Optional[:class:`str`]
        The icon hash, if it exists.
    description: Optional[:class:`str`]
        The application description.
    bot_public: :class:`bool`
        Whether the bot can be invited by anyone or if it is locked
        to the application owner.
    bot_require_code_grant: :class:`bool`
        Whether the bot requires the completion of the full oauth2 code
        grant flow to join.
    rpc_origins: Optional[List[:class:`str`]]
        A list of RPC origin URLs, if RPC is enabled.
    summary: :class:`str`
        If this application is a game sold on Discord,
        this field will be the summary field for the store page of its primary SKU

        .. versionadded:: 1.3

    verify_key: :class:`str`
        The base64 encoded key for the GameSDK's GetTicket

        .. versionadded:: 1.3

    guild_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the guild to which it has been linked

        .. versionadded:: 1.3

    primary_sku_id: Optional[:class:`int`]
        If this application is a game sold on Discord,
        this field will be the id of the "Game SKU" that is created, if exists

        .. versionadded:: 1.3

    slug: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the URL slug that links to the store page

        .. versionadded:: 1.3

    cover_image: Optional[:class:`str`]
        If this application is a game sold on Discord,
        this field will be the hash of the image on store embeds

        .. versionadded:: 1.3
    """
    __slots__ = ('_state', 'description', 'id', 'name', 'rpc_origins',
                 'bot_public', 'bot_require_code_grant', 'owner', 'icon',
                 'summary', 'verify_key', 'team', 'guild_id', 'primary_sku_id',
                  'slug', 'cover_image')

    def __init__(self, state, data):
        self._state = state

        self.id = int(data['id'])
        self.name = data['name']
        self.description = data['description']
        self.icon = data['icon']
        self.rpc_origins = data['rpc_origins']
        self.bot_public = data['bot_public']
        self.bot_require_code_grant = data['bot_require_code_grant']
        self.owner = User(state=self._state, data=data['owner'])

        team = data.get('team')
        self.team = Team(state, team) if team else None

        self.summary = data['summary']
        self.verify_key = data['verify_key']

        self.guild_id = utils._get_as_snowflake(data, 'guild_id')

        self.primary_sku_id = utils._get_as_snowflake(data, 'primary_sku_id')
        self.slug = data.get('slug')
        self.cover_image = data.get('cover_image')

    def __repr__(self):
        return '<{0.__class__.__name__} id={0.id} name={0.name!r} description={0.description!r} public={0.bot_public} ' \
               'owner={0.owner!r}>'.format(self)

    @property
    def icon_url(self):
        """:class:`.Asset`: Retrieves the application's icon asset.

        This is equivalent to calling :meth:`icon_url_as` with
        the default parameters ('webp' format and a size of 1024).

        .. versionadded:: 1.3
        """
        return self.icon_url_as()

    def icon_url_as(self, *, format='webp', size=1024):
        """Returns an :class:`Asset` for the icon the application has.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.6

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the icon to. Defaults to 'webp'.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_icon(self._state, self, 'app', format=format, size=size)


    @property
    def cover_image_url(self):
        """:class:`.Asset`: Retrieves the cover image on a store embed.

        This is equivalent to calling :meth:`cover_image_url_as` with
        the default parameters ('webp' format and a size of 1024).

        .. versionadded:: 1.3
        """
        return self.cover_image_url_as()

    def cover_image_url_as(self, *, format='webp', size=1024):
        """Returns an :class:`Asset` for the image on store embeds
        if this application is a game sold on Discord.

        The format must be one of 'webp', 'jpeg', 'jpg' or 'png'.
        The size must be a power of 2 between 16 and 4096.

        .. versionadded:: 1.6

        Parameters
        -----------
        format: :class:`str`
            The format to attempt to convert the image to. Defaults to 'webp'.
        size: :class:`int`
            The size of the image to display.

        Raises
        ------
        InvalidArgument
            Bad image format passed to ``format`` or invalid ``size``.

        Returns
        --------
        :class:`Asset`
            The resulting CDN asset.
        """
        return Asset._from_cover_image(self._state, self, format=format, size=size)

    @property
    def guild(self):
        """Optional[:class:`Guild`]: If this application is a game sold on Discord,
        this field will be the guild to which it has been linked

        .. versionadded:: 1.3
        """
        return self._state._get_guild(int(self.guild_id))
