# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2019 Rapptz

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

import datetime

from .enums import ActivityType, try_enum
from .colour import Colour
from .utils import _get_as_snowflake

__all__ = (
    'Activity',
    'Streaming',
    'Game',
    'Spotify',
)

"""If curious, this is the current schema for an activity.

It's fairly long so I will document it here:

All keys are optional.

state: str (max: 128),
details: str (max: 128)
timestamps: dict
    start: int (min: 1)
    end: int (min: 1)
assets: dict
    large_image: str (max: 32)
    large_text: str (max: 128)
    small_image: str (max: 32)
    small_text: str (max: 128)
party: dict
    id: str (max: 128),
    size: List[int] (max-length: 2)
        elem: int (min: 1)
secrets: dict
    match: str (max: 128)
    join: str (max: 128)
    spectate: str (max: 128)
instance: bool
application_id: str
name: str (max: 128)
url: str
type: int
sync_id: str
session_id: str
flags: int

There are also activity flags which are mostly uninteresting for the library atm.

t.ActivityFlags = {
    INSTANCE: 1,
    JOIN: 2,
    SPECTATE: 4,
    JOIN_REQUEST: 8,
    SYNC: 16,
    PLAY: 32
}
"""

class _ActivityTag:
    __slots__ = ()

class Activity(_ActivityTag):
    """Represents an activity in Discord.

    This could be an activity such as streaming, playing, listening
    or watching.

    For memory optimisation purposes, some activities are offered in slimmed
    down versions:

    - :class:`Game`
    - :class:`Streaming`

    Attributes
    ------------
    application_id: :class:`int`
        The application ID of the game.
    name: :class:`str`
        The name of the activity.
    url: :class:`str`
        A stream URL that the activity could be doing.
    type: :class:`ActivityType`
        The type of activity currently being done.
    state: :class:`str`
        The user's current state. For example, "In Game".
    details: :class:`str`
        The detail of the user's current activity.
    timestamps: :class:`dict`
        A dictionary of timestamps. It contains the following optional keys:

        - ``start``: Corresponds to when the user started doing the
          activity in milliseconds since Unix epoch.
        - ``end``: Corresponds to when the user will finish doing the
          activity in milliseconds since Unix epoch.

    assets: :class:`dict`
        A dictionary representing the images and their hover text of an activity.
        It contains the following optional keys:

        - ``large_image``: A string representing the ID for the large image asset.
        - ``large_text``: A string representing the text when hovering over the large image asset.
        - ``small_image``: A string representing the ID for the small image asset.
        - ``small_text``: A string representing the text when hovering over the small image asset.

    party: :class:`dict`
        A dictionary representing the activity party. It contains the following optional keys:

        - ``id``: A string representing the party ID.
        - ``size``: A list of up to two integer elements denoting (current_size, maximum_size).
    """

    __slots__ = ('state', 'details', 'timestamps', 'assets', 'party',
                 'flags', 'sync_id', 'session_id', 'type', 'name', 'url', 'application_id')

    def __init__(self, **kwargs):
        self.state = kwargs.pop('state', None)
        self.details = kwargs.pop('details', None)
        self.timestamps = kwargs.pop('timestamps', {})
        self.assets = kwargs.pop('assets', {})
        self.party = kwargs.pop('party', {})
        self.application_id = _get_as_snowflake(kwargs, 'application_id')
        self.name = kwargs.pop('name', None)
        self.url = kwargs.pop('url', None)
        self.flags = kwargs.pop('flags', 0)
        self.sync_id = kwargs.pop('sync_id', None)
        self.session_id = kwargs.pop('session_id', None)
        self.type = try_enum(ActivityType, kwargs.pop('type', -1))

    def to_dict(self):
        ret = {}
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, dict) and len(value) == 0:
                continue

            ret[attr] = value
        ret['type'] = self.type.value
        return ret

    @property
    def start(self):
        """Optional[:class:`datetime.datetime`]: When the user started doing this activity in UTC, if applicable."""
        try:
            return datetime.datetime.utcfromtimestamp(self.timestamps['start'] / 1000)
        except KeyError:
            return None

    @property
    def end(self):
        """Optional[:class:`datetime.datetime`]: When the user will stop doing this activity in UTC, if applicable."""
        try:
            return datetime.datetime.utcfromtimestamp(self.timestamps['end'] / 1000)
        except KeyError:
            return None

    @property
    def large_image_url(self):
        """Optional[:class:`str`]: Returns a URL pointing to the large image asset of this activity if applicable."""
        if self.application_id is None:
            return None

        try:
            large_image = self.assets['large_image']
        except KeyError:
            return None
        else:
            return 'https://cdn.discordapp.com/app-assets/{0}/{1}.png'.format(self.application_id, large_image)

    @property
    def small_image_url(self):
        """Optional[:class:`str`]: Returns a URL pointing to the small image asset of this activity if applicable."""
        if self.application_id is None:
            return None

        try:
            small_image = self.assets['small_image']
        except KeyError:
            return None
        else:
            return 'https://cdn.discordapp.com/app-assets/{0}/{1}.png'.format(self.application_id, small_image)
    @property
    def large_image_text(self):
        """Optional[:class:`str`]: Returns the large image asset hover text of this activity if applicable."""
        return self.assets.get('large_text', None)

    @property
    def small_image_text(self):
        """Optional[:class:`str`]: Returns the small image asset hover text of this activity if applicable."""
        return self.assets.get('small_text', None)


class Game(_ActivityTag):
    """A slimmed down version of :class:`Activity` that represents a Discord game.

    This is typically displayed via **Playing** on the official Discord client.

    .. container:: operations

        .. describe:: x == y

            Checks if two games are equal.

        .. describe:: x != y

            Checks if two games are not equal.

        .. describe:: hash(x)

            Returns the game's hash.

        .. describe:: str(x)

            Returns the game's name.

    Parameters
    -----------
    name: :class:`str`
        The game's name.
    start: Optional[:class:`datetime.datetime`]
        A naive UTC timestamp representing when the game started. Keyword-only parameter. Ignored for bots.
    end: Optional[:class:`datetime.datetime`]
        A naive UTC timestamp representing when the game ends. Keyword-only parameter. Ignored for bots.

    Attributes
    -----------
    name: :class:`str`
        The game's name.
    """

    __slots__ = ('name', '_end', '_start')

    def __init__(self, name, **extra):
        self.name = name

        try:
            timestamps = extra['timestamps']
        except KeyError:
            self._extract_timestamp(extra, 'start')
            self._extract_timestamp(extra, 'end')
        else:
            self._start = timestamps.get('start', 0)
            self._end = timestamps.get('end', 0)

    def _extract_timestamp(self, data, key):
        try:
            dt = data[key]
        except KeyError:
            setattr(self, '_' + key, 0)
        else:
            setattr(self, '_' + key, dt.timestamp() * 1000.0)

    @property
    def type(self):
        """Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.playing`.
        """
        return ActivityType.playing

    @property
    def start(self):
        """Optional[:class:`datetime.datetime`]: When the user started playing this game in UTC, if applicable."""
        if self._start:
            return datetime.datetime.utcfromtimestamp(self._start / 1000)
        return None

    @property
    def end(self):
        """Optional[:class:`datetime.datetime`]: When the user will stop playing this game in UTC, if applicable."""
        if self._end:
            return datetime.datetime.utcfromtimestamp(self._end / 1000)
        return None

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return '<Game name={0.name!r}>'.format(self)

    def to_dict(self):
        timestamps = {}
        if self._start:
            timestamps['start'] = self._start

        if self._end:
            timestamps['end'] = self._end

        return {
            'type': ActivityType.playing.value,
            'name': str(self.name),
            'timestamps': timestamps
        }

    def __eq__(self, other):
        return isinstance(other, Game) and other.name == self.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

class Streaming(_ActivityTag):
    """A slimmed down version of :class:`Activity` that represents a Discord streaming status.

    This is typically displayed via **Streaming** on the official Discord client.

    .. container:: operations

        .. describe:: x == y

            Checks if two streams are equal.

        .. describe:: x != y

            Checks if two streams are not equal.

        .. describe:: hash(x)

            Returns the stream's hash.

        .. describe:: str(x)

            Returns the stream's name.

    Attributes
    -----------
    name: :class:`str`
        The stream's name.
    url: :class:`str`
        The stream's URL. Currently only twitch.tv URLs are supported. Anything else is silently
        discarded.
    details: Optional[:class:`str`]
        If provided, typically the game the streamer is playing.
    assets: :class:`dict`
        A dictionary comprising of similar keys than those in :attr:`Activity.assets`.
    """

    __slots__ = ('name', 'url', 'details', 'assets')

    def __init__(self, *, name, url, **extra):
        self.name = name
        self.url = url
        self.details = extra.pop('details', None)
        self.assets = extra.pop('assets', {})

    @property
    def type(self):
        """Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.streaming`.
        """
        return ActivityType.streaming

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return '<Streaming name={0.name!r}>'.format(self)

    @property
    def twitch_name(self):
        """Optional[:class:`str`]: If provided, the twitch name of the user streaming.

        This corresponds to the ``large_image`` key of the :attr:`Streaming.assets`
        dictionary if it starts with ``twitch:``. Typically set by the Discord client.
        """

        try:
            name = self.assets['large_image']
        except KeyError:
            return None
        else:
            return name[7:] if name[:7] == 'twitch:' else None

    def to_dict(self):
        ret = {
            'type': ActivityType.streaming.value,
            'name': str(self.name),
            'url': str(self.url),
            'assets': self.assets
        }
        if self.details:
            ret['details'] = self.details
        return ret

    def __eq__(self, other):
        return isinstance(other, Streaming) and other.name == self.name and other.url == self.url

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

class Spotify:
    """Represents a Spotify listening activity from Discord. This is a special case of
    :class:`Activity` that makes it easier to work with the Spotify integration.

    .. container:: operations

        .. describe:: x == y

            Checks if two activities are equal.

        .. describe:: x != y

            Checks if two activities are not equal.

        .. describe:: hash(x)

            Returns the activity's hash.

        .. describe:: str(x)

            Returns the string 'Spotify'.
    """

    __slots__ = ('_state', '_details', '_timestamps', '_assets', '_party', '_sync_id', '_session_id')

    def __init__(self, **data):
        self._state = data.pop('state', None)
        self._details = data.pop('details', None)
        self._timestamps = data.pop('timestamps', {})
        self._assets = data.pop('assets', {})
        self._party = data.pop('party', {})
        self._sync_id = data.pop('sync_id')
        self._session_id = data.pop('session_id')

    @property
    def type(self):
        """Returns the activity's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.listening`.
        """
        return ActivityType.listening

    @property
    def colour(self):
        """Returns the Spotify integration colour, as a :class:`Colour`.

        There is an alias for this named :meth:`color`"""
        return Colour(0x1db954)

    @property
    def color(self):
        """Returns the Spotify integration colour, as a :class:`Colour`.

        There is an alias for this named :meth:`colour`"""
        return self.colour

    def to_dict(self):
        return {
            'flags': 48, # SYNC | PLAY
            'name': 'Spotify',
            'assets': self._assets,
            'party': self._party,
            'sync_id': self._sync_id,
            'session_id': self._session_id,
            'timestamps': self._timestamps,
            'details': self._details,
            'state': self._state
        }

    @property
    def name(self):
        """:class:`str`: The activity's name. This will always return "Spotify"."""
        return 'Spotify'

    def __eq__(self, other):
        return (isinstance(other, Spotify) and other._session_id == self._session_id
                and other._sync_id == self._sync_id and other.start == self.start)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._session_id)

    def __str__(self):
        return 'Spotify'

    def __repr__(self):
        return '<Spotify title={0.title!r} artist={0.artist!r} track_id={0.track_id!r}>'.format(self)

    @property
    def title(self):
        """:class:`str`: The title of the song being played."""
        return self._details

    @property
    def artists(self):
        """List[:class:`str`]: The artists of the song being played."""
        return self._state.split('; ')

    @property
    def artist(self):
        """:class:`str`: The artist of the song being played.

        This does not attempt to split the artist information into
        multiple artists. Useful if there's only a single artist.
        """
        return self._state

    @property
    def album(self):
        """:class:`str`: The album that the song being played belongs to."""
        return self._assets.get('large_text', '')

    @property
    def album_cover_url(self):
        """:class:`str`: The album cover image URL from Spotify's CDN."""
        large_image = self._assets.get('large_image', '')
        if large_image[:8] != 'spotify:':
            return ''
        album_image_id = large_image[8:]
        return 'https://i.scdn.co/image/' + album_image_id

    @property
    def track_id(self):
        """:class:`str`: The track ID used by Spotify to identify this song."""
        return self._sync_id

    @property
    def start(self):
        """:class:`datetime.datetime`: When the user started playing this song in UTC."""
        return datetime.datetime.utcfromtimestamp(self._timestamps['start'] / 1000)

    @property
    def end(self):
        """:class:`datetime.datetime`: When the user will stop playing this song in UTC."""
        return datetime.datetime.utcfromtimestamp(self._timestamps['end'] / 1000)

    @property
    def duration(self):
        """:class:`datetime.timedelta`: The duration of the song being played."""
        return self.end - self.start

    @property
    def party_id(self):
        """:class:`str`: The party ID of the listening party."""
        return self._party.get('id', '')

def create_activity(data):
    if not data:
        return None

    game_type = try_enum(ActivityType, data.get('type', -1))
    if game_type is ActivityType.playing:
        if 'application_id' in data or 'session_id' in data:
            return Activity(**data)
        return Game(**data)
    elif game_type is ActivityType.streaming:
        if 'url' in data:
            return Streaming(**data)
        return Activity(**data)
    elif game_type is ActivityType.listening and 'sync_id' in data and 'session_id' in data:
        return Spotify(**data)
    return Activity(**data)
