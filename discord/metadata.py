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

from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Tuple, Union

from .utils import parse_time


class Metadata:
    """Represents a raw model from Discord.

    Because of how unstable and wildly varying some metadata in Discord can be, this is a simple class
    that just provides access to the raw data using dot notation. This means that ``None`` is returned
    for unknown attributes instead of raising an exception. This class can be used similarly to a dictionary.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two metadata objects are equal.

        .. describe:: x != y

            Checks if two metadata objects are not equal.

        .. describe:: x[key]

            Returns a metadata value if it is found, otherwise raises a :exc:`KeyError`.

        .. describe:: key in x

            Checks if a metadata value is present.

        .. describe:: len(x)

            Returns the number of metadata values present.

        .. describe:: iter(x)
            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.
    """

    def __init__(self, data: Optional[MetadataObject] = None) -> None:
        if not data:
            return

        for key, value in data.items():
            if isinstance(value, dict):
                value = Metadata(value)
            elif key.endswith('_id') and isinstance(value, str) and value.isdigit():
                value = int(value)
            elif (key.endswith('_at') or key.endswith('_date')) and isinstance(value, str):
                try:
                    value = parse_time(value)
                except ValueError:
                    pass
            elif isinstance(value, list):
                value = [Metadata(x) if isinstance(x, dict) else x for x in value]

            self.__dict__[key] = value

    def __repr__(self) -> str:
        if not self.__dict__:
            return '<Metadata>'
        return f'<Metadata {" ".join(f"{k}={v!r}" for k, v in self.__dict__.items())}>'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Metadata):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Metadata):
            return True
        return self.__dict__ != other.__dict__

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        yield from self.__dict__.items()

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.__dict__[key] = value

    def __getattr__(self, _) -> Any:
        return None

    def __contains__(self, key: str) -> bool:
        return key in self.__dict__

    def __len__(self) -> int:
        return len(self.__dict__)

    def keys(self):
        """A set-like object providing a view on the metadata's keys."""
        return self.__dict__.keys()

    def values(self):
        """A set-like object providing a view on the metadata's values."""
        return self.__dict__.values()

    def items(self):
        """A set-like object providing a view on the metadata's items."""
        return self.__dict__.items()


if TYPE_CHECKING:
    MetadataObject = Union[Metadata, Dict[str, Any]]
