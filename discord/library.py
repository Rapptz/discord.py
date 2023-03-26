"""
The MIT License (MIT)

Copyright (c) 2021-present Dolfies

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

from typing import TYPE_CHECKING, Any, List, Optional

from .application import ApplicationActivityStatistics, ApplicationBranch, PartialApplication
from .entitlements import Entitlement
from .enums import SKUType, try_enum
from .flags import LibraryApplicationFlags
from .mixins import Hashable
from .utils import MISSING, _get_as_snowflake, find, parse_date, parse_time

if TYPE_CHECKING:
    from datetime import date, datetime

    from .asset import Asset
    from .state import ConnectionState
    from .types.application import Branch as BranchPayload
    from .types.library import LibraryApplication as LibraryApplicationPayload
    from .types.store import PartialSKU as PartialSKUPayload

__all__ = (
    'LibrarySKU',
    'LibraryApplication',
)


class LibrarySKU(Hashable):
    """Represents a partial store SKU for a library entry.

    .. container:: operations

        .. describe:: x == y

            Checks if two library SKUs are equal.

        .. describe:: x != y

            Checks if two library SKUs are not equal.

        .. describe:: hash(x)

            Returns the library SKU's hash.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The SKU's ID.
    type: :class:`SKUType`
        The type of the SKU.
    preorder_release_date: Optional[:class:`datetime.date`]
        The approximate date that the SKU will released for pre-order, if any.
    preorder_released_at: Optional[:class:`datetime.datetime`]
        The date that the SKU was released for pre-order, if any.
    premium: :class:`bool`
        Whether this SKU is provided for free to premium users.
    """

    __slots__ = (
        'id',
        'type',
        'preorder_release_date',
        'preorder_released_at',
        'premium',
    )

    def __init__(self, data: PartialSKUPayload):
        self.id: int = int(data['id'])
        self.type: SKUType = try_enum(SKUType, data['type'])
        self.preorder_release_date: Optional[date] = parse_date(data.get('preorder_approximate_release_date'))
        self.preorder_released_at: Optional[datetime] = parse_time(data.get('preorder_release_at'))
        self.premium: bool = data.get('premium', False)

    def __repr__(self) -> str:
        return f'<LibrarySKU id={self.id} type={self.type!r} preorder_release_date={self.preorder_release_date!r} preorder_released_at={self.preorder_released_at!r} premium={self.premium!r}>'


class LibraryApplication:
    """Represents a library entry.

    .. container:: operations

        .. describe:: x == y

            Checks if two library entries are equal.

        .. describe:: x != y

            Checks if two library entries are not equal.

        .. describe:: hash(x)

            Returns the library entry's hash.

        .. describe:: str(x)

            Returns the library entry's name.

    .. versionadded:: 2.0

    Attributes
    -----------
    created_at: :class:`datetime.datetime`
        When this library entry was created.
    application: :class:`PartialApplication`
        The application that this library entry is for.
    sku_id: :class:`int`
        The ID of the SKU that this library entry is for.
    sku: :class:`LibrarySKU`
        The SKU that this library entry is for.
    entitlements: List[:class:`Entitlement`]
        The entitlements that this library entry has.
    branch_id: :class:`int`
        The ID of the branch that this library entry installs.
    branch: :class:`ApplicationBranch`
        The branch that this library entry installs.
    """

    __slots__ = (
        'created_at',
        'application',
        'sku_id',
        'sku',
        'entitlements',
        'branch_id',
        'branch',
        '_flags',
        '_state',
    )

    def __init__(self, *, state: ConnectionState, data: LibraryApplicationPayload):
        self._state = state
        self._update(data)

    def _update(self, data: LibraryApplicationPayload):
        state = self._state

        self.created_at: datetime = parse_time(data['created_at'])
        self.application: PartialApplication = PartialApplication(state=state, data=data['application'])
        self.sku_id: int = int(data['sku_id'])
        self.sku: LibrarySKU = LibrarySKU(data=data['sku'])
        self.entitlements: List[Entitlement] = [Entitlement(state=state, data=e) for e in data.get('entitlements', [])]
        self._flags = data.get('flags', 0)

        self.branch_id: int = int(data['branch_id'])
        branch: Optional[BranchPayload] = data.get('branch')
        if not branch:
            branch = {'id': self.branch_id, 'name': 'master'}
        self.branch: ApplicationBranch = ApplicationBranch(state=state, data=branch, application_id=self.application.id)

    def __repr__(self) -> str:
        return f'<LibraryApplication created_at={self.created_at!r} application={self.application!r} sku={self.sku!r} branch={self.branch!r}>'

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LibraryApplication):
            return self.application.id == other.application.id and self.branch_id == other.branch_id
        return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, LibraryApplication):
            return self.application.id != other.application.id or self.branch_id != other.branch_id
        return True

    def __hash__(self) -> int:
        return hash((self.application.id, self.branch_id))

    def __str__(self) -> str:
        return self.application.name

    @property
    def name(self) -> str:
        """:class:`str`: The library entry's name."""
        return self.application.name

    @property
    def icon(self) -> Optional[Asset]:
        """:class:`Asset`: The library entry's icon asset, if any."""
        return self.application.icon

    @property
    def flags(self) -> LibraryApplicationFlags:
        """:class:`LibraryApplicationFlags`: The library entry's flags."""
        return LibraryApplicationFlags._from_value(self._flags)

    async def activity_statistics(self) -> ApplicationActivityStatistics:
        """|coro|

        Gets the activity statistics for this library entry.

        Raises
        -------
        HTTPException
            Getting the activity statistics failed.

        Returns
        --------
        :class:`ApplicationActivityStatistics`
            The activity statistics for this library entry.
        """
        state = self._state
        data = await state.http.get_activity_statistics()
        app = find(lambda a: _get_as_snowflake(a, 'application_id') == self.application.id, data)
        return ApplicationActivityStatistics(
            data=app
            or {'application_id': self.application.id, 'total_duration': 0, 'last_played_at': '1970-01-01T00:00:00+00:00'},
            state=state,
        )

    async def mark_installed(self) -> None:
        """|coro|

        Marks the library entry as installed.

        Raises
        -------
        HTTPException
            Marking the library entry as installed failed.
        """
        await self._state.http.mark_library_entry_installed(self.application.id, self.branch_id)

    async def edit(self, *, flags: LibraryApplicationFlags = MISSING) -> None:
        """|coro|

        Edits the library entry.

        All parameters are optional.

        Parameters
        -----------
        flags: :class:`LibraryApplicationFlags`
            The new flags to set for the library entry.

        Raises
        -------
        HTTPException
            Editing the library entry failed.
        """
        payload = {}
        if flags is not MISSING:
            payload['flags'] = flags.value

        data = await self._state.http.edit_library_entry(self.application.id, self.branch_id, payload)
        self._update(data)

    async def delete(self) -> None:
        """|coro|

        Deletes the library entry.

        Raises
        -------
        HTTPException
            Deleting the library entry failed.
        """
        await self._state.http.delete_library_entry(self.application.id, self.branch_id)
