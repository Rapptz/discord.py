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

import io
import os
from typing import Any, Literal, Optional, TYPE_CHECKING, Tuple, Union, Dict
from .errors import DiscordException
from . import utils
from .file import File

import yarl

# fmt: off
__all__ = (
    'Asset',
)
# fmt: on

if TYPE_CHECKING:
    from typing_extensions import Self

    from .state import ConnectionState
    from .webhook.async_ import _WebhookState

    _State = Union[ConnectionState, _WebhookState]

    ValidStaticFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png']
    ValidAssetFormatTypes = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']

VALID_STATIC_FORMATS = frozenset({'jpeg', 'jpg', 'webp', 'png'})
VALID_ASSET_FORMATS = VALID_STATIC_FORMATS | {'gif'}


MISSING = utils.MISSING


class AssetMixin:
    __slots__ = ()
    url: str
    _state: Optional[Any]

    async def read(self) -> bytes:
        """|coro|

        Retrieves the content of this asset as a :class:`bytes` object.

        Raises
        ------
        DiscordException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        -------
        :class:`bytes`
            The content of the asset.
        """
        if self._state is None:
            raise DiscordException('Invalid state (no ConnectionState provided)')

        return await self._state.http.get_from_cdn(self.url)

    async def save(self, fp: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase], *, seek_begin: bool = True) -> int:
        """|coro|

        Saves this asset into a file-like object.

        Parameters
        ----------
        fp: Union[:class:`io.BufferedIOBase`, :class:`os.PathLike`]
            The file-like object to save this asset to or the filename
            to use. If a filename is passed then a file is created with that
            filename and used instead.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after saving is
            successfully done.

        Raises
        ------
        DiscordException
            There was no internal connection state.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        --------
        :class:`int`
            The number of bytes written.
        """

        data = await self.read()
        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written
        else:
            with open(fp, 'wb') as f:
                return f.write(data)

    async def to_file(
        self,
        *,
        filename: Optional[str] = MISSING,
        description: Optional[str] = None,
        spoiler: bool = False,
    ) -> File:
        """|coro|

        Converts the asset into a :class:`File` suitable for sending via
        :meth:`abc.Messageable.send`.

        .. versionadded:: 2.0

        Parameters
        -----------
        filename: Optional[:class:`str`]
            The filename of the file. If not provided, then the filename from
            the asset's URL is used.
        description: Optional[:class:`str`]
            The description for the file.
        spoiler: :class:`bool`
            Whether the file is a spoiler.

        Raises
        ------
        DiscordException
            The asset does not have an associated state.
        ValueError
            The asset is a unicode emoji.
        TypeError
            The asset is a sticker with lottie type.
        HTTPException
            Downloading the asset failed.
        NotFound
            The asset was deleted.

        Returns
        -------
        :class:`File`
            The asset as a file suitable for sending.
        """

        data = await self.read()
        file_filename = filename if filename is not MISSING else yarl.URL(self.url).name
        return File(io.BytesIO(data), filename=file_filename, description=description, spoiler=spoiler)


class Asset(AssetMixin):
    """Represents a CDN asset on Discord.

    .. container:: operations

        .. describe:: str(x)

            Returns the URL of the CDN asset.

        .. describe:: len(x)

            Returns the length of the CDN asset's URL.

        .. describe:: x == y

            Checks if the asset is equal to another asset.

        .. describe:: x != y

            Checks if the asset is not equal to another asset.

        .. describe:: hash(x)

            Returns the hash of the asset.
    """

    __slots__: Tuple[str, ...] = (
        '_state',
        '_url',
        '_animated',
        '_key',
        '_format',
        '_size',
    )

    BASE = 'https://cdn.discordapp.com'

    def __init__(
        self,
        state: _State,
        *,
        url: str,
        key: str,
        animated: bool = False,
        format: Optional[ValidAssetFormatTypes] = None,
        size: Optional[int] = None,
    ) -> None:
        self._state: _State = state
        self._animated: bool = animated
        self._key: str = key
        self._size: Optional[int] = size

        if format is None:
            format = 'webp' if animated else 'png'

        self._format: ValidAssetFormatTypes = format

        query: Dict[str, str] = {}
        if size is not None:
            query['size'] = str(size)
        if animated and format == 'webp':
            query['animated'] = 'true'

        parsed = yarl.URL(url)
        path, _ = os.path.splitext(parsed.path)
        self._url: str = str(parsed.with_path(f'{path}.{format}').with_query(query))

    @classmethod
    def _from_default_avatar(cls, state: _State, index: int) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/embed/avatars/{index}',
            key=str(index),
            format='png',
        )

    @classmethod
    def _from_avatar(cls, state: _State, user_id: int, avatar: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/avatars/{user_id}/{avatar}',
            key=avatar,
            animated=avatar.startswith('a_'),
            size=1024,
        )

    @classmethod
    def _from_guild_avatar(cls, state: _State, guild_id: int, member_id: int, avatar: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/guilds/{guild_id}/users/{member_id}/avatars/{avatar}',
            key=avatar,
            animated=avatar.startswith('a_'),
            size=1024,
        )

    @classmethod
    def _from_guild_banner(cls, state: _State, guild_id: int, member_id: int, banner: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/guilds/{guild_id}/users/{member_id}/banners/{banner}',
            key=banner,
            animated=banner.startswith('a_'),
            size=1024,
        )

    @classmethod
    def _from_avatar_decoration(cls, state: _State, avatar_decoration: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/avatar-decoration-presets/{avatar_decoration}',
            key=avatar_decoration,
            animated=True,
            size=96,
        )

    @classmethod
    def _from_icon(cls, state: _State, object_id: int, icon_hash: str, path: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/{path}-icons/{object_id}/{icon_hash}',
            key=icon_hash,
            size=1024,
        )

    @classmethod
    def _from_app_icon(
        cls, state: _State, object_id: int, icon_hash: str, asset_type: Literal['icon', 'cover_image']
    ) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/app-icons/{object_id}/{asset_type}',
            key=icon_hash,
            size=1024,
        )

    @classmethod
    def _from_cover_image(cls, state: _State, object_id: int, cover_image_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/app-assets/{object_id}/store/{cover_image_hash}',
            key=cover_image_hash,
            size=1024,
        )

    @classmethod
    def _from_scheduled_event_cover_image(cls, state: _State, scheduled_event_id: int, cover_image_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/guild-events/{scheduled_event_id}/{cover_image_hash}',
            key=cover_image_hash,
            size=1024,
        )

    @classmethod
    def _from_guild_image(cls, state: _State, guild_id: int, image: str, path: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/{path}/{guild_id}/{image}',
            key=image,
            animated=image.startswith('a_'),
            size=1024,
        )

    @classmethod
    def _from_guild_icon(cls, state: _State, guild_id: int, icon_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/icons/{guild_id}/{icon_hash}',
            key=icon_hash,
            animated=icon_hash.startswith('a_'),
            size=1024,
        )

    @classmethod
    def _from_sticker_banner(cls, state: _State, banner: int) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/app-assets/710982414301790216/store/{banner}',
            key=str(banner),
        )

    @classmethod
    def _from_user_banner(cls, state: _State, user_id: int, banner_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/banners/{user_id}/{banner_hash}',
            key=banner_hash,
            animated=banner_hash.startswith('a_'),
            size=512,
        )

    @classmethod
    def _from_primary_guild(cls, state: _State, guild_id: int, icon_hash: str) -> Self:
        return cls(
            state,
            url=f'{cls.BASE}/guild-tag-badges/{guild_id}/{icon_hash}',
            key=icon_hash,
            size=64,
        )

    @classmethod
    def _from_user_collectible(cls, state: _State, asset: str, animated: bool = False) -> Self:
        name = 'static.png' if not animated else 'asset.webm'
        return cls(
            state,
            url=f'{cls.BASE}/assets/collectibles/{asset}{name}',
            key=asset,
            animated=animated,
        )

    def __str__(self) -> str:
        return self._url

    def __len__(self) -> int:
        return len(self._url)

    def __repr__(self) -> str:
        shorten = self._url.replace(self.BASE, '')
        return f'<Asset url={shorten!r}>'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Asset) and self._url == other._url

    def __hash__(self) -> int:
        return hash(self._url)

    @property
    def url(self) -> str:
        """:class:`str`: Returns the underlying URL of the asset."""
        return self._url

    @property
    def key(self) -> str:
        """:class:`str`: Returns the identifying key of the asset."""
        return self._key

    @property
    def format(self) -> Optional[ValidAssetFormatTypes]:
        """Optional[:class:`str`]: Returns the set format of the asset.

        Defaults to ``webp`` for animated assets and ``png`` for static assets.
        You can use :meth:`with_format`, :meth:`with_static_format`, and :meth:`replace`
        to set the format of the asset.

        .. versionadded:: 2.8
        """
        return self._format

    @property
    def size(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the set size of the asset.

        You can use :meth:`with_size` and :meth:`replace` to set the size of the asset.

        .. versionadded:: 2.8
        """
        return self._size

    def is_animated(self) -> bool:
        """:class:`bool`: Returns whether the asset is animated."""
        return self._animated

    def replace(
        self,
        *,
        size: int = MISSING,
        format: ValidAssetFormatTypes = MISSING,
        static_format: ValidStaticFormatTypes = MISSING,
    ) -> Self:
        """Returns a new asset with the passed components replaced.


        .. versionchanged:: 2.0
            ``static_format`` is now preferred over ``format``
            if both are present and the asset is not animated.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        -----------
        size: :class:`int`
            The new size of the asset.
        format: :class:`str`
            The new format to change it to. Must be either
            'webp', 'jpeg', 'jpg', 'png', or 'gif' if it's animated.

            .. note::
                If the asset is animated, consider using `webp` for the most compatibility.
        static_format: :class:`str`
            The new format to change it to if the asset isn't animated.
            Must be either 'webp', 'jpeg', 'jpg', or 'png'.

        Raises
        -------
        ValueError
            An invalid size or format was passed.

        Returns
        --------
        :class:`Asset`
            The newly updated asset.
        """
        new_format = self._format
        new_size = self._size

        if format is not MISSING:
            if self._animated:
                if format not in VALID_ASSET_FORMATS:
                    raise ValueError(f'format must be one of {VALID_ASSET_FORMATS}')
            else:
                if static_format is MISSING and format not in VALID_STATIC_FORMATS:
                    raise ValueError(f'format must be one of {VALID_STATIC_FORMATS}')

            new_format = format

        if static_format is not MISSING and not self._animated:
            if static_format not in VALID_STATIC_FORMATS:
                raise ValueError(f'static_format must be one of {VALID_STATIC_FORMATS}')

            new_format = static_format

        if size is not MISSING:
            if not utils.valid_icon_size(size):
                raise ValueError('size must be a power of 2 between 16 and 4096')

            new_size = size

        return self.__class__(
            state=self._state,
            url=self._url,
            key=self._key,
            animated=self._animated,
            format=new_format,
            size=new_size,
        )

    def with_size(self, size: int, /) -> Self:
        """Returns a new asset with the specified size.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        ------------
        size: :class:`int`
            The new size of the asset.

        Raises
        -------
        ValueError
            The asset had an invalid size.

        Returns
        --------
        :class:`Asset`
            The new updated asset.
        """
        if not utils.valid_icon_size(size):
            raise ValueError('size must be a power of 2 between 16 and 4096')

        return self.__class__(
            state=self._state,
            url=self._url,
            key=self._key,
            animated=self._animated,
            format=self._format,
            size=size,
        )

    def with_format(self, format: ValidAssetFormatTypes, /) -> Self:
        """Returns a new asset with the specified format.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        ------------
        format: :class:`str`
            The new format of the asset.

            .. note::
                If the asset is animated, consider using `webp` for the most compatibility.

        Raises
        -------
        ValueError
            The asset had an invalid format.

        Returns
        --------
        :class:`Asset`
            The new updated asset.
        """

        if self._animated:
            if format not in VALID_ASSET_FORMATS:
                raise ValueError(f'format must be one of {VALID_ASSET_FORMATS}')
        else:
            if format not in VALID_STATIC_FORMATS:
                raise ValueError(f'format must be one of {VALID_STATIC_FORMATS}')

        return self.__class__(
            state=self._state,
            url=self._url,
            key=self._key,
            animated=self._animated,
            format=format,
            size=self._size,
        )

    def with_static_format(self, format: ValidStaticFormatTypes, /) -> Self:
        """Returns a new asset with the specified static format.

        This only changes the format if the underlying asset is
        not animated. Otherwise, the asset is not changed.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        ------------
        format: :class:`str`
            The new static format of the asset.

        Raises
        -------
        ValueError
            The asset had an invalid format.

        Returns
        --------
        :class:`Asset`
            The new updated asset.
        """

        if self._animated:
            return self
        return self.with_format(format)
