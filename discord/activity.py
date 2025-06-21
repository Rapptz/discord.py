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

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, overload

from .asset import Asset
from .enums import ActivityType, try_enum
from .colour import Colour
from .partial_emoji import PartialEmoji
from .utils import _get_as_snowflake

__all__ = (
    'BaseActivity',
    'Activity',
    'Streaming',
    'Game',
    'Spotify',
    'CustomActivity',
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
buttons: list[str (max: 32)]

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

if TYPE_CHECKING:
    from .types.activity import (
        Activity as ActivityPayload,
        ActivityTimestamps,
        ActivityParty,
        ActivityAssets,
    )

    from .state import ConnectionState


class BaseActivity:
    """The base activity that all user-settable activities inherit from.
    A user-settable activity is one that can be used in :meth:`Client.change_presence`.

    The following types currently count as user-settable:

    - :class:`Activity`
    - :class:`Game`
    - :class:`Streaming`
    - :class:`CustomActivity`

    Note that although these types are considered user-settable by the library,
    Discord typically ignores certain combinations of activity depending on
    what is currently set. This behaviour may change in the future so there are
    no guarantees on whether Discord will actually let you set these types.

    .. versionadded:: 1.3
    """

    __slots__ = ('_created_at',)

    def __init__(self, **kwargs: Any) -> None:
        self._created_at: Optional[float] = kwargs.pop('created_at', None)

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user started doing this activity in UTC.

        .. versionadded:: 1.3
        """
        if self._created_at is not None:
            return datetime.datetime.fromtimestamp(self._created_at / 1000, tz=datetime.timezone.utc)

    def to_dict(self) -> ActivityPayload:
        raise NotImplementedError


class Activity(BaseActivity):
    """Represents an activity in Discord.

    This could be an activity such as streaming, playing, listening
    or watching.

    For memory optimisation purposes, some activities are offered in slimmed
    down versions:

    - :class:`Game`
    - :class:`Streaming`

    Attributes
    ------------
    application_id: Optional[:class:`int`]
        The application ID of the game.
    name: Optional[:class:`str`]
        The name of the activity.
    url: Optional[:class:`str`]
        A stream URL that the activity could be doing.
    type: :class:`ActivityType`
        The type of activity currently being done.
    state: Optional[:class:`str`]
        The user's current state. For example, "In Game".
    details: Optional[:class:`str`]
        The detail of the user's current activity.
    platform: Optional[:class:`str`]
        The user's current platform.

        .. versionadded:: 2.4
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
    buttons: List[:class:`str`]
        A list of strings representing the labels of custom buttons shown in a rich presence.

        .. versionadded:: 2.0

    emoji: Optional[:class:`PartialEmoji`]
        The emoji that belongs to this activity.
    """

    __slots__ = (
        'state',
        'details',
        'timestamps',
        'platform',
        'assets',
        'party',
        'flags',
        'sync_id',
        'session_id',
        'type',
        'name',
        'url',
        'application_id',
        'emoji',
        'buttons',
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.state: Optional[str] = kwargs.pop('state', None)
        self.details: Optional[str] = kwargs.pop('details', None)
        self.timestamps: ActivityTimestamps = kwargs.pop('timestamps', {})
        self.platform: Optional[str] = kwargs.pop('platform', None)
        self.assets: ActivityAssets = kwargs.pop('assets', {})
        self.party: ActivityParty = kwargs.pop('party', {})
        self.application_id: Optional[int] = _get_as_snowflake(kwargs, 'application_id')
        self.name: Optional[str] = kwargs.pop('name', None)
        self.url: Optional[str] = kwargs.pop('url', None)
        self.flags: int = kwargs.pop('flags', 0)
        self.sync_id: Optional[str] = kwargs.pop('sync_id', None)
        self.session_id: Optional[str] = kwargs.pop('session_id', None)
        self.buttons: List[str] = kwargs.pop('buttons', [])

        activity_type = kwargs.pop('type', -1)
        self.type: ActivityType = (
            activity_type if isinstance(activity_type, ActivityType) else try_enum(ActivityType, activity_type)
        )

        emoji = kwargs.pop('emoji', None)
        self.emoji: Optional[PartialEmoji] = PartialEmoji.from_dict(emoji) if emoji is not None else None

    def __repr__(self) -> str:
        attrs = (
            ('type', self.type),
            ('name', self.name),
            ('url', self.url),
            ('platform', self.platform),
            ('details', self.details),
            ('application_id', self.application_id),
            ('session_id', self.session_id),
            ('emoji', self.emoji),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<Activity {inner}>'

    def to_dict(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {}
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, dict) and len(value) == 0:
                continue

            ret[attr] = value
        ret['type'] = int(self.type)
        if self.emoji:
            ret['emoji'] = self.emoji.to_dict()
        return ret

    @property
    def start(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user started doing this activity in UTC, if applicable."""
        try:
            timestamp = self.timestamps['start'] / 1000  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            return None
        else:
            return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

    @property
    def end(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user will stop doing this activity in UTC, if applicable."""
        try:
            timestamp = self.timestamps['end'] / 1000  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            return None
        else:
            return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

    @property
    def large_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns a URL pointing to the large image asset of this activity, if applicable."""
        try:
            large_image = self.assets['large_image']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            return None
        else:
            return self._image_url(large_image)

    @property
    def small_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns a URL pointing to the small image asset of this activity, if applicable."""
        try:
            small_image = self.assets['small_image']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            return None
        else:
            return self._image_url(small_image)

    def _image_url(self, image: str) -> Optional[str]:
        if image.startswith('mp:'):
            return f'https://media.discordapp.net/{image[3:]}'
        elif self.application_id is not None:
            return Asset.BASE + f'/app-assets/{self.application_id}/{image}.png'

    @property
    def large_image_text(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the large image asset hover text of this activity, if applicable."""
        return self.assets.get('large_text', None)

    @property
    def small_image_text(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the small image asset hover text of this activity, if applicable."""
        return self.assets.get('small_text', None)


class Game(BaseActivity):
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

    Attributes
    -----------
    name: :class:`str`
        The game's name.
    platform: Optional[:class:`str`]
        Where the user is playing from (ie. PS5, Xbox).

        .. versionadded:: 2.4

    assets: :class:`dict`
        A dictionary representing the images and their hover text of a game.
        It contains the following optional keys:

        - ``large_image``: A string representing the ID for the large image asset.
        - ``large_text``: A string representing the text when hovering over the large image asset.
        - ``small_image``: A string representing the ID for the small image asset.
        - ``small_text``: A string representing the text when hovering over the small image asset.

        .. versionadded:: 2.4
    """

    __slots__ = ('name', '_end', '_start', 'platform', 'assets')

    def __init__(self, name: str, **extra: Any) -> None:
        super().__init__(**extra)
        self.name: str = name
        self.platform: Optional[str] = extra.get('platform')
        self.assets: ActivityAssets = extra.get('assets', {}) or {}

        try:
            timestamps: ActivityTimestamps = extra['timestamps']
        except KeyError:
            self._start = 0
            self._end = 0
        else:
            self._start = timestamps.get('start', 0)
            self._end = timestamps.get('end', 0)

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.playing`.
        """
        return ActivityType.playing

    @property
    def start(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user started playing this game in UTC, if applicable."""
        if self._start:
            return datetime.datetime.fromtimestamp(self._start / 1000, tz=datetime.timezone.utc)
        return None

    @property
    def end(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user will stop playing this game in UTC, if applicable."""
        if self._end:
            return datetime.datetime.fromtimestamp(self._end / 1000, tz=datetime.timezone.utc)
        return None

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f'<Game name={self.name!r} platform={self.platform!r}>'

    def to_dict(self) -> Dict[str, Any]:
        timestamps: Dict[str, Any] = {}
        if self._start:
            timestamps['start'] = self._start

        if self._end:
            timestamps['end'] = self._end

        return {
            'type': ActivityType.playing.value,
            'name': str(self.name),
            'timestamps': timestamps,
            'platform': str(self.platform) if self.platform else None,
            'assets': self.assets,
        }

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Game) and other.name == self.name

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)


class Streaming(BaseActivity):
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
    platform: Optional[:class:`str`]
        Where the user is streaming from (ie. YouTube, Twitch).

        .. versionadded:: 1.3

    name: Optional[:class:`str`]
        The stream's name.
    details: Optional[:class:`str`]
        An alias for :attr:`name`
    game: Optional[:class:`str`]
        The game being streamed.

        .. versionadded:: 1.3

    url: :class:`str`
        The stream's URL.
    assets: :class:`dict`
        A dictionary comprising of similar keys than those in :attr:`Activity.assets`.
    """

    __slots__ = ('platform', 'name', 'game', 'url', 'details', 'assets')

    def __init__(self, *, name: Optional[str], url: str, **extra: Any) -> None:
        super().__init__(**extra)
        self.platform: Optional[str] = name
        self.name: Optional[str] = extra.pop('details', name)
        self.game: Optional[str] = extra.pop('state', None)
        self.url: str = url
        self.details: Optional[str] = extra.pop('details', self.name)  # compatibility
        self.assets: ActivityAssets = extra.pop('assets', {})

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.streaming`.
        """
        return ActivityType.streaming

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f'<Streaming name={self.name!r} platform={self.platform!r}>'

    @property
    def twitch_name(self) -> Optional[str]:
        """Optional[:class:`str`]: If provided, the twitch name of the user streaming.

        This corresponds to the ``large_image`` key of the :attr:`Streaming.assets`
        dictionary if it starts with ``twitch:``. Typically set by the Discord client.
        """

        try:
            name = self.assets['large_image']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            return None
        else:
            return name[7:] if name[:7] == 'twitch:' else None

    def to_dict(self) -> Dict[str, Any]:
        ret: Dict[str, Any] = {
            'type': ActivityType.streaming.value,
            'name': str(self.name),
            'url': str(self.url),
            'assets': self.assets,
        }
        if self.details:
            ret['details'] = self.details
        return ret

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Streaming) and other.name == self.name and other.url == self.url

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
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

    __slots__ = ('_state', '_details', '_timestamps', '_assets', '_party', '_sync_id', '_session_id', '_created_at')

    def __init__(self, **data: Any) -> None:
        self._state: str = data.pop('state', '')
        self._details: str = data.pop('details', '')
        self._timestamps: ActivityTimestamps = data.pop('timestamps', {})
        self._assets: ActivityAssets = data.pop('assets', {})
        self._party: ActivityParty = data.pop('party', {})
        self._sync_id: str = data.pop('sync_id', '')
        self._session_id: Optional[str] = data.pop('session_id')
        self._created_at: Optional[float] = data.pop('created_at', None)

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the activity's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.listening`.
        """
        return ActivityType.listening

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: When the user started listening in UTC.

        .. versionadded:: 1.3
        """
        if self._created_at is not None:
            return datetime.datetime.fromtimestamp(self._created_at / 1000, tz=datetime.timezone.utc)

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: Returns the Spotify integration colour, as a :class:`Colour`.

        There is an alias for this named :attr:`color`"""
        return Colour(0x1DB954)

    @property
    def color(self) -> Colour:
        """:class:`Colour`: Returns the Spotify integration colour, as a :class:`Colour`.

        There is an alias for this named :attr:`colour`"""
        return self.colour

    def to_dict(self) -> Dict[str, Any]:
        return {
            'flags': 48,  # SYNC | PLAY
            'name': 'Spotify',
            'assets': self._assets,
            'party': self._party,
            'sync_id': self._sync_id,
            'session_id': self._session_id,
            'timestamps': self._timestamps,
            'details': self._details,
            'state': self._state,
        }

    @property
    def name(self) -> str:
        """:class:`str`: The activity's name. This will always return "Spotify"."""
        return 'Spotify'

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Spotify)
            and other._session_id == self._session_id
            and other._sync_id == self._sync_id
            and other.start == self.start
        )

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._session_id)

    def __str__(self) -> str:
        return 'Spotify'

    def __repr__(self) -> str:
        return f'<Spotify title={self.title!r} artist={self.artist!r} track_id={self.track_id!r}>'

    @property
    def title(self) -> str:
        """:class:`str`: The title of the song being played."""
        return self._details

    @property
    def artists(self) -> List[str]:
        """List[:class:`str`]: The artists of the song being played."""
        return self._state.split('; ')

    @property
    def artist(self) -> str:
        """:class:`str`: The artist of the song being played.

        This does not attempt to split the artist information into
        multiple artists. Useful if there's only a single artist.
        """
        return self._state

    @property
    def album(self) -> str:
        """:class:`str`: The album that the song being played belongs to."""
        return self._assets.get('large_text', '')

    @property
    def album_cover_url(self) -> str:
        """:class:`str`: The album cover image URL from Spotify's CDN."""
        large_image = self._assets.get('large_image', '')
        if large_image[:8] != 'spotify:':
            return ''
        album_image_id = large_image[8:]
        return 'https://i.scdn.co/image/' + album_image_id

    @property
    def track_id(self) -> str:
        """:class:`str`: The track ID used by Spotify to identify this song."""
        return self._sync_id

    @property
    def track_url(self) -> str:
        """:class:`str`: The track URL to listen on Spotify.

        .. versionadded:: 2.0
        """
        return f'https://open.spotify.com/track/{self.track_id}'

    @property
    def start(self) -> datetime.datetime:
        """:class:`datetime.datetime`: When the user started playing this song in UTC."""
        # the start key will be present here
        return datetime.datetime.fromtimestamp(self._timestamps['start'] / 1000, tz=datetime.timezone.utc)  # type: ignore

    @property
    def end(self) -> datetime.datetime:
        """:class:`datetime.datetime`: When the user will stop playing this song in UTC."""
        # the end key will be present here
        return datetime.datetime.fromtimestamp(self._timestamps['end'] / 1000, tz=datetime.timezone.utc)  # type: ignore

    @property
    def duration(self) -> datetime.timedelta:
        """:class:`datetime.timedelta`: The duration of the song being played."""
        return self.end - self.start

    @property
    def party_id(self) -> str:
        """:class:`str`: The party ID of the listening party."""
        return self._party.get('id', '')


class CustomActivity(BaseActivity):
    """Represents a custom activity from Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two activities are equal.

        .. describe:: x != y

            Checks if two activities are not equal.

        .. describe:: hash(x)

            Returns the activity's hash.

        .. describe:: str(x)

            Returns the custom status text.

    .. versionadded:: 1.3

    Attributes
    -----------
    name: Optional[:class:`str`]
        The custom activity's name.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji to pass to the activity, if any.
    """

    __slots__ = ('name', 'emoji', 'state')

    def __init__(
        self, name: Optional[str], *, emoji: Optional[Union[PartialEmoji, Dict[str, Any], str]] = None, **extra: Any
    ) -> None:
        super().__init__(**extra)
        self.name: Optional[str] = name
        self.state: Optional[str] = extra.pop('state', name)
        if self.name == 'Custom Status':
            self.name = self.state

        self.emoji: Optional[PartialEmoji]
        if emoji is None:
            self.emoji = emoji
        elif isinstance(emoji, dict):
            self.emoji = PartialEmoji.from_dict(emoji)
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji(name=emoji)
        elif isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        else:
            raise TypeError(f'Expected str, PartialEmoji, or None, received {type(emoji)!r} instead.')

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the activity's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.custom`.
        """
        return ActivityType.custom

    def to_dict(self) -> Dict[str, Any]:
        if self.name == self.state:
            o = {
                'type': ActivityType.custom.value,
                'state': self.name,
                'name': 'Custom Status',
            }
        else:
            o = {
                'type': ActivityType.custom.value,
                'name': self.name,
            }

        if self.emoji:
            o['emoji'] = self.emoji.to_dict()
        return o

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CustomActivity) and other.name == self.name and other.emoji == self.emoji

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.name, str(self.emoji)))

    def __str__(self) -> str:
        if self.emoji:
            if self.name:
                return f'{self.emoji} {self.name}'
            return str(self.emoji)
        else:
            return str(self.name)

    def __repr__(self) -> str:
        return f'<CustomActivity name={self.name!r} emoji={self.emoji!r}>'


ActivityTypes = Union[Activity, Game, CustomActivity, Streaming, Spotify]


@overload
def create_activity(data: ActivityPayload, state: ConnectionState) -> ActivityTypes:
    ...


@overload
def create_activity(data: None, state: ConnectionState) -> None:
    ...


def create_activity(data: Optional[ActivityPayload], state: ConnectionState) -> Optional[ActivityTypes]:
    if not data:
        return None

    game_type = try_enum(ActivityType, data.get('type', -1))
    if game_type is ActivityType.playing:
        if 'application_id' in data or 'session_id' in data:
            return Activity(**data)
        return Game(**data)
    elif game_type is ActivityType.custom:
        try:
            name = data.pop('name')  # type: ignore
        except KeyError:
            ret = Activity(**data)
        else:
            # we removed the name key from data already
            ret = CustomActivity(name=name, **data)  # type: ignore
    elif game_type is ActivityType.streaming:
        if 'url' in data:
            # the url won't be None here
            return Streaming(**data)  # type: ignore
        return Activity(**data)
    elif game_type is ActivityType.listening and 'sync_id' in data and 'session_id' in data:
        return Spotify(**data)
    else:
        ret = Activity(**data)

    if isinstance(ret.emoji, PartialEmoji):
        ret.emoji._state = state
    return ret
