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

from typing import TYPE_CHECKING, List, Sequence

from .utils import SequenceProxy

if TYPE_CHECKING:
    from typing_extensions import Self

    from .state import ConnectionState
    from .types.gateway import Tutorial as TutorialPayload

# fmt: off
__all__ = (
    'Tutorial',
)
# fmt: on


class Tutorial:
    """Represents the Discord new user tutorial state.

    .. versionadded:: 2.1

    Attributes
    -----------
    suppressed: :class:`bool`
        Whether the tutorial is suppressed or not.
    """

    __slots__ = ('suppressed', '_indicators', '_state')

    def __init__(self, *, data: TutorialPayload, state: ConnectionState):
        self._state: ConnectionState = state
        self.suppressed: bool = data.get('indicators_suppressed', True)
        self._indicators: List[str] = data.get('indicators_confirmed', [])

    def __repr__(self) -> str:
        return f'<Tutorial suppressed={self.suppressed} indicators={self._indicators!r}>'

    @classmethod
    def default(cls, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.suppressed = True
        self._indicators = []
        return self

    @property
    def indicators(self) -> Sequence[str]:
        """Sequence[:class:`str`]: A list of the tutorial indicators that have been confirmed."""
        return SequenceProxy(self._indicators)

    async def suppress(self) -> None:
        """|coro|

        Permanently suppresses all tutorial indicators.

        Raises
        -------
        HTTPException
            Suppressing the tutorial failed.
        """
        await self._state.http.suppress_tutorial()
        self.suppressed = True

    async def confirm(self, *indicators: str) -> None:
        r"""|coro|

        Confirms a list of tutorial indicators.

        Parameters
        -----------
        \*indicators: :class:`str`
            The indicators to confirm.

        Raises
        -------
        HTTPException
            Confirming the tutorial indicators failed.
        """
        req = self._state.http.confirm_tutorial_indicator
        # The gateway does not send updates on the tutorial
        # So we keep the state updated ourselves
        for indicator in indicators:
            if indicator not in self.indicators:
                await req(indicator)
                self._indicators.append(indicator)

        # Indicators are sorted alphabetically
        self._indicators.sort()
