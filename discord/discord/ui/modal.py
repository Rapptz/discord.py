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

import asyncio
import logging
import os
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, ClassVar, List

from ..utils import MISSING, find
from .._types import ClientT
from .item import Item
from .view import View

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..interactions import Interaction
    from ..types.interactions import ModalSubmitComponentInteractionData as ModalSubmitComponentInteractionDataPayload


# fmt: off
__all__ = (
    'Modal',
)
# fmt: on


_log = logging.getLogger(__name__)


class Modal(View):
    """Represents a UI modal.

    This object must be inherited to create a modal popup window within discord.

    .. versionadded:: 2.0

    Examples
    ----------

    .. code-block:: python3

        from discord import ui

        class Questionnaire(ui.Modal, title='Questionnaire Response'):
            name = ui.TextInput(label='Name')
            answer = ui.TextInput(label='Answer', style=discord.TextStyle.paragraph)

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message(f'Thanks for your response, {self.name}!', ephemeral=True)

    Parameters
    -----------
    title: :class:`str`
        The title of the modal. Can only be up to 45 characters.
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the UI before no longer accepting input.
        If ``None`` then there is no timeout.
    custom_id: :class:`str`
        The ID of the modal that gets received during an interaction.
        If not given then one is generated for you.
        Can only be up to 100 characters.

    Attributes
    ------------
    title: :class:`str`
        The title of the modal.
    custom_id: :class:`str`
        The ID of the modal that gets received during an interaction.
    """

    if TYPE_CHECKING:
        title: str

    __discord_ui_modal__ = True
    __modal_children_items__: ClassVar[Dict[str, Item[Self]]] = {}

    def __init_subclass__(cls, *, title: str = MISSING) -> None:
        if title is not MISSING:
            cls.title = title

        children = {}
        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if isinstance(member, Item):
                    children[name] = member

        cls.__modal_children_items__ = children

    def _init_children(self) -> List[Item]:
        children = []
        for name, item in self.__modal_children_items__.items():
            item = deepcopy(item)
            setattr(self, name, item)
            item._view = self
            children.append(item)
        return children

    def __init__(
        self,
        *,
        title: str = MISSING,
        timeout: Optional[float] = None,
        custom_id: str = MISSING,
    ) -> None:
        if title is MISSING and getattr(self, 'title', MISSING) is MISSING:
            raise ValueError('Modal must have a title')
        elif title is not MISSING:
            self.title = title
        self.custom_id: str = os.urandom(16).hex() if custom_id is MISSING else custom_id

        super().__init__(timeout=timeout)

    async def on_submit(self, interaction: Interaction[ClientT], /) -> None:
        """|coro|

        Called when the modal is submitted.

        Parameters
        -----------
        interaction: :class:`.Interaction`
            The interaction that submitted this modal.
        """
        pass

    async def on_error(self, interaction: Interaction[ClientT], error: Exception, /) -> None:
        """|coro|

        A callback that is called when :meth:`on_submit`
        fails with an error.

        The default implementation logs to the library logger.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that led to the failure.
        error: :class:`Exception`
            The exception that was raised.
        """
        _log.error('Ignoring exception in modal %r:', self, exc_info=error)

    def _refresh(self, interaction: Interaction, components: Sequence[ModalSubmitComponentInteractionDataPayload]) -> None:
        for component in components:
            if component['type'] == 1:
                self._refresh(interaction, component['components'])
            else:
                item = find(lambda i: i.custom_id == component['custom_id'], self._children)  # type: ignore
                if item is None:
                    _log.debug("Modal interaction referencing unknown item custom_id %s. Discarding", component['custom_id'])
                    continue
                item._refresh_state(interaction, component)  # type: ignore

    async def _scheduled_task(self, interaction: Interaction, components: List[ModalSubmitComponentInteractionDataPayload]):
        try:
            self._refresh_timeout()
            self._refresh(interaction, components)

            allow = await self.interaction_check(interaction)
            if not allow:
                return

            await self.on_submit(interaction)
        except Exception as e:
            return await self.on_error(interaction, e)
        else:
            # No error, so assume this will always happen
            # In the future, maybe this will require checking if we set an error response.
            self.stop()

    def _dispatch_submit(
        self, interaction: Interaction, components: List[ModalSubmitComponentInteractionDataPayload]
    ) -> None:
        asyncio.create_task(self._scheduled_task(interaction, components), name=f'discord-ui-modal-dispatch-{self.id}')

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            'custom_id': self.custom_id,
            'title': self.title,
            'components': self.to_components(),
        }

        return payload
