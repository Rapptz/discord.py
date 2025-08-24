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

from typing import Optional, TYPE_CHECKING


from .asset import Asset
from .enums import NameplatePalette, CollectibleType, try_enum
from .utils import parse_time


if TYPE_CHECKING:
    from datetime import datetime

    from .state import ConnectionState
    from .types.user import (
        Collectible as CollectiblePayload,
    )


__all__ = ('Collectible',)


class Collectible:
    """Represents a user's collectible.

    .. versionadded:: 2.7

    Attributes
    ----------
    label: :class:`str`
        The label of the collectible.
    palette: Optional[:class:`NameplatePalette`]
        The palette of the collectible.
        This is only available if ``type`` is
        :class:`CollectibleType.nameplate`.
    sku_id: :class:`int`
        The SKU ID of the collectible.
    type: :class:`CollectibleType`
        The type of the collectible.
    expires_at: Optional[:class:`datetime.datetime`]
        The expiration date of the collectible. If applicable.
    """

    __slots__ = (
        'type',
        'sku_id',
        'label',
        'expires_at',
        'palette',
        '_state',
        '_asset',
    )

    def __init__(self, *, state: ConnectionState, type: str, data: CollectiblePayload) -> None:
        self._state: ConnectionState = state
        self.type: CollectibleType = try_enum(CollectibleType, type)
        self._asset: str = data['asset']
        self.sku_id: int = int(data['sku_id'])
        self.label: str = data['label']
        self.expires_at: Optional[datetime] = parse_time(data.get('expires_at'))

        # nameplate
        self.palette: Optional[NameplatePalette]
        try:
            self.palette = try_enum(NameplatePalette, data['palette'])  # type: ignore
        except KeyError:
            self.palette = None

    @property
    def static(self) -> Asset:
        """:class:`Asset`: The static asset of the collectible."""
        return Asset._from_user_collectible(self._state, self._asset)

    @property
    def animated(self) -> Asset:
        """:class:`Asset`: The animated asset of the collectible."""
        return Asset._from_user_collectible(self._state, self._asset, animated=True)

    def __repr__(self) -> str:
        attrs = ['sku_id']
        if self.palette:
            attrs.append('palette')

        joined_attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in attrs)
        return f'<{self.type.name.title()} {joined_attrs}>'
