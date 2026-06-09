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
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Tuple, TypeVar, Dict

import os

from ..utils import MISSING
from ..components import FileUploadComponent
from ..enums import ComponentType
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..message import Attachment
    from ..interactions import Interaction
    from ..types.interactions import ModalSubmitTextInputInteractionData as ModalSubmitFileUploadInteractionDataPayload
    from ..types.components import FileUploadComponent as FileUploadComponentPayload
    from .view import BaseView
    from ..app_commands.namespace import ResolveKey


# fmt: off
__all__ = (
    'FileUpload',
)
# fmt: on

V = TypeVar('V', bound='BaseView', covariant=True)


class FileUpload(Item[V]):
    """Represents a file upload component within a modal.

    .. versionadded:: 2.7

    Parameters
    ------------
    id: Optional[:class:`int`]
        The ID of the component. This must be unique across the view.
    custom_id: Optional[:class:`str`]
        The custom ID of the file upload component.
    max_values: Optional[:class:`int`]
        The maximum number of files that can be uploaded in this component.
        Must be between 1 and 10. Defaults to 1.
    min_values: Optional[:class:`int`]
        The minimum number of files that must be uploaded in this component.
        Must be between 0 and 10. Defaults to 0.
    required: :class:`bool`
        Whether this component is required to be filled before submitting the modal.
        Defaults to ``True``.
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'id',
        'custom_id',
        'max_values',
        'min_values',
        'required',
    )

    def __init__(
        self,
        *,
        custom_id: str = MISSING,
        required: bool = True,
        min_values: Optional[int] = None,
        max_values: Optional[int] = None,
        id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._provided_custom_id = custom_id is not MISSING
        custom_id = os.urandom(16).hex() if custom_id is MISSING else custom_id
        if not isinstance(custom_id, str):
            raise TypeError(f'expected custom_id to be str not {custom_id.__class__.__name__}')

        self._underlying: FileUploadComponent = FileUploadComponent._raw_construct(
            id=id,
            custom_id=custom_id,
            max_values=max_values,
            min_values=min_values,
            required=required,
        )
        self.id = id
        self._values: List[Attachment] = []

    @property
    def id(self) -> Optional[int]:
        """Optional[:class:`int`]: The ID of this component."""
        return self._underlying.id

    @id.setter
    def id(self, value: Optional[int]) -> None:
        self._underlying.id = value

    @property
    def values(self) -> List[Attachment]:
        """List[:class:`discord.Attachment`]: The list of attachments uploaded by the user.

        You can call :meth:`~discord.Attachment.to_file` on each attachment
        to get a :class:`~discord.File` for sending.
        """
        return self._values

    @property
    def custom_id(self) -> str:
        """:class:`str`: The ID of the component that gets received during an interaction."""
        return self._underlying.custom_id

    @custom_id.setter
    def custom_id(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError('custom_id must be a str')

        self._underlying.custom_id = value
        self._provided_custom_id = True

    @property
    def min_values(self) -> int:
        """:class:`int`: The minimum number of files that must be user upload before submitting the modal."""
        return self._underlying.min_values

    @min_values.setter
    def min_values(self, value: int) -> None:
        self._underlying.min_values = int(value)

    @property
    def max_values(self) -> int:
        """:class:`int`: The maximum number of files that the user must upload before submitting the modal."""
        return self._underlying.max_values

    @max_values.setter
    def max_values(self, value: int) -> None:
        self._underlying.max_values = int(value)

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the component is required or not."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool) -> None:
        self._underlying.required = bool(value)

    @property
    def width(self) -> int:
        return 5

    def to_component_dict(self) -> FileUploadComponentPayload:
        return self._underlying.to_dict()

    def _refresh_component(self, component: FileUploadComponent) -> None:
        self._underlying = component

    def _handle_submit(
        self, interaction: Interaction, data: ModalSubmitFileUploadInteractionDataPayload, resolved: Dict[ResolveKey, Any]
    ) -> None:
        self._values = [v for k, v in resolved.items() if k.id in data.get('values', [])]

    @classmethod
    def from_component(cls, component: FileUploadComponent) -> Self:
        self = cls(
            id=component.id,
            custom_id=component.custom_id,
            max_values=component.max_values,
            min_values=component.min_values,
            required=component.required,
        )
        return self

    @property
    def type(self) -> Literal[ComponentType.file_upload]:
        return self._underlying.type

    def is_dispatchable(self) -> bool:
        return False
