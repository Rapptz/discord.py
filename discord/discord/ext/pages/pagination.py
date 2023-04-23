"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

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
from typing import Dict, List, Optional, Union

import discord
from discord.ext.bridge import BridgeContext
from discord.ext.commands import Context

__all__ = (
    "PaginatorButton",
    "Paginator",
    "PageGroup",
    "PaginatorMenu",
    "Page",
)


class PaginatorButton(discord.ui.Button):
    """Creates a button used to navigate the paginator.

    Parameters
    ----------
    button_type: :class:`str`
        The type of button being created.
        Must be one of ``first``, ``prev``, ``next``, ``last``, or ``page_indicator``.
    label: :class:`str`
        The label shown on the button.
        Defaults to a capitalized version of ``button_type`` (e.g. "Next", "Prev", etc.)
    emoji: Union[:class:`str`, :class:`discord.Emoji`, :class:`discord.PartialEmoji`]
        The emoji shown on the button in front of the label.
    disabled: :class:`bool`
        Whether to initially show the button as disabled.
    loop_label: :class:`str`
        The label shown on the button when ``loop_pages`` is set to ``True`` in the Paginator class.

    Attributes
    ----------
    paginator: :class:`Paginator`
        The paginator class where this button is being used.
        Assigned to the button when ``Paginator.add_button`` is called.
    """

    def __init__(
        self,
        button_type: str,
        label: str = None,
        emoji: Union[str, discord.Emoji, discord.PartialEmoji] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.green,
        disabled: bool = False,
        custom_id: str = None,
        row: int = 0,
        loop_label: str = None,
    ):
        super().__init__(
            label=label if label or emoji else button_type.capitalize(),
            emoji=emoji,
            style=style,
            disabled=disabled,
            custom_id=custom_id,
            row=row,
        )
        self.button_type = button_type
        self.label = label if label or emoji else button_type.capitalize()
        self.emoji: Union[str, discord.Emoji, discord.PartialEmoji] = emoji
        self.style = style
        self.disabled = disabled
        self.loop_label = self.label if not loop_label else loop_label
        self.paginator = None

    async def callback(self, interaction: discord.Interaction):
        """|coro|

        The coroutine that is called when the navigation button is clicked.

        Parameters
        -----------
        interaction: :class:`discord.Interaction`
            The interaction created by clicking the navigation button.
        """
        if self.button_type == "first":
            self.paginator.current_page = 0
        elif self.button_type == "prev":
            if self.paginator.loop_pages and self.paginator.current_page == 0:
                self.paginator.current_page = self.paginator.page_count
            else:
                self.paginator.current_page -= 1
        elif self.button_type == "next":
            if self.paginator.loop_pages and self.paginator.current_page == self.paginator.page_count:
                self.paginator.current_page = 0
            else:
                self.paginator.current_page += 1
        elif self.button_type == "last":
            self.paginator.current_page = self.paginator.page_count
        await self.paginator.goto_page(page_number=self.paginator.current_page, interaction=interaction)


class Page:
    """Represents a page shown in the paginator.

    Allows for directly referencing and modifying each page as a class instance.

    Parameters
    ----------
    content: :class:`str`
        The content of the page. Corresponds to the :class:`discord.Message.content` attribute.
    embeds: Optional[List[Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]
        The embeds of the page. Corresponds to the :class:`discord.Message.embeds` attribute.
    files: Optional[List[:class:`discord.File`]]
        A list of local files to be shown with the page.
    custom_view: Optional[:class:`discord.ui.View`]
        The custom view shown when the page is visible. Overrides the `custom_view` attribute of the main paginator.
    """

    def __init__(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Union[List[discord.Embed], discord.Embed]]] = None,
        custom_view: Optional[discord.ui.View] = None,
        files: Optional[List[discord.File]] = None,
        **kwargs,
    ):
        if content is None and embeds is None:
            raise discord.InvalidArgument("A page cannot have both content and embeds equal to None.")
        self._content = content
        self._embeds = embeds or []
        self._custom_view = custom_view
        self._files = files or []

    async def callback(self, interaction: Optional[discord.Interaction] = None):
        """|coro|

        The coroutine associated to a specific page. If `Paginator.page_action()` is used, this coroutine is called.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction associated with the callback, if any.
        """
        pass

    def update_files(self) -> Optional[List[discord.File]]:
        """Updates the files associated with the page by re-uploading them.
        Typically used when the page is changed."""
        for file in self._files:
            with open(file.fp.name, "rb") as fp:  # type: ignore
                self._files[self._files.index(file)] = discord.File(
                    fp,  # type: ignore
                    filename=file.filename,
                    description=file.description,
                    spoiler=file.spoiler,
                )
        return self._files

    @property
    def content(self) -> Optional[str]:
        """Gets the content for the page."""
        return self._content

    @content.setter
    def content(self, value: Optional[str]):
        """Sets the content for the page."""
        self._content = value

    @property
    def embeds(self) -> Optional[List[Union[List[discord.Embed], discord.Embed]]]:
        """Gets the embeds for the page."""
        return self._embeds

    @embeds.setter
    def embeds(self, value: Optional[List[Union[List[discord.Embed], discord.Embed]]]):
        """Sets the embeds for the page."""
        self._embeds = value

    @property
    def custom_view(self) -> Optional[discord.ui.View]:
        """Gets the custom view assigned to the page."""
        return self._custom_view

    @custom_view.setter
    def custom_view(self, value: Optional[discord.ui.View]):
        """Assigns a custom view to be shown when the page is displayed."""
        self._custom_view = value

    @property
    def files(self) -> Optional[List[discord.File]]:
        """Gets the files associated with the page."""
        return self._files

    @files.setter
    def files(self, value: Optional[List[discord.File]]):
        """Sets the files associated with the page."""
        self._files = value


class PageGroup:
    """Creates a group of pages which the user can switch between.

    Each group of pages can have its own options, custom buttons, custom views, etc.

    .. note::

        If multiple ``PageGroup`` objects have different options, they should all be set explicitly when creating each instance.


    Parameters
    ----------
    pages: Union[List[:class:`str`], List[:class:`Page`], List[Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]
        The list of :class:`Page` objects, strings, embeds, or list of embeds to include in the page group.
    label: :class:`str`
        The label shown on the corresponding PaginatorMenu dropdown option.
        Also used as the SelectOption value.
    description: Optional[:class:`str`]
        The description shown on the corresponding PaginatorMenu dropdown option.
    emoji: Union[:class:`str`, :class:`discord.Emoji`, :class:`discord.PartialEmoji`]
        The emoji shown on the corresponding PaginatorMenu dropdown option.
    default: Optional[:class:`bool`]
        Whether the page group should be the default page group initially shown when the paginator response is sent.
        Only one ``PageGroup`` can be the default page group.
    show_disabled: :class:`bool`
        Whether to show disabled buttons.
    show_indicator: :class:`bool`
        Whether to show the page indicator when using the default buttons.
    author_check: :class:`bool`
        Whether only the original user of the command can change pages.
    disable_on_timeout: :class:`bool`
        Whether the buttons get disabled when the paginator view times out.
    use_default_buttons: :class:`bool`
        Whether to use the default buttons (i.e. ``first``, ``prev``, ``page_indicator``, ``next``, ``last``)
    default_button_row: :class:`int`
        The row where the default paginator buttons are displayed. Has no effect if custom buttons are used.
    loop_pages: :class:`bool`
        Whether to loop the pages when clicking prev/next while at the first/last page in the list.
    custom_view: Optional[:class:`discord.ui.View`]
        A custom view whose items are appended below the pagination buttons.
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the paginator before no longer accepting input.
    custom_buttons: Optional[List[:class:`PaginatorButton`]]
        A list of PaginatorButtons to initialize the Paginator with.
        If ``use_default_buttons`` is ``True``, this parameter is ignored.
    trigger_on_display: :class:`bool`
        Whether to automatically trigger the callback associated with a `Page` whenever it is displayed.
        Has no effect if no callback exists for a `Page`.
    """

    def __init__(
        self,
        pages: Union[List[str], List[Page], List[Union[List[discord.Embed], discord.Embed]]],
        label: str,
        description: Optional[str] = None,
        emoji: Union[str, discord.Emoji, discord.PartialEmoji] = None,
        default: Optional[bool] = None,
        show_disabled: Optional[bool] = None,
        show_indicator: Optional[bool] = None,
        author_check: Optional[bool] = None,
        disable_on_timeout: Optional[bool] = None,
        use_default_buttons: Optional[bool] = None,
        default_button_row: int = 0,
        loop_pages: Optional[bool] = None,
        custom_view: Optional[discord.ui.View] = None,
        timeout: Optional[float] = None,
        custom_buttons: Optional[List[PaginatorButton]] = None,
        trigger_on_display: Optional[bool] = None,
    ):
        self.label = label
        self.description: Optional[str] = description
        self.emoji: Union[str, discord.Emoji, discord.PartialEmoji] = emoji
        self.pages: Union[List[str], List[Union[List[discord.Embed], discord.Embed]]] = pages
        self.default: Optional[bool] = default
        self.show_disabled = show_disabled
        self.show_indicator = show_indicator
        self.author_check = author_check
        self.disable_on_timeout = disable_on_timeout
        self.use_default_buttons = use_default_buttons
        self.default_button_row = default_button_row
        self.loop_pages = loop_pages
        self.custom_view: discord.ui.View = custom_view
        self.timeout: float = timeout
        self.custom_buttons: List = custom_buttons
        self.trigger_on_display = trigger_on_display


class Paginator(discord.ui.View):
    """Creates a paginator which can be sent as a message and uses buttons for navigation.

    Parameters
    ----------
    pages: Union[List[:class:`PageGroup`], List[:class:`Page`], List[:class:`str`], List[Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]
        The list of :class:`PageGroup` objects, :class:`Page` objects, strings, embeds, or list of embeds to paginate.
        If a list of :class:`PageGroup` objects is provided and `show_menu` is ``False``, only the first page group will be displayed.
    show_disabled: :class:`bool`
        Whether to show disabled buttons.
    show_indicator: :class:`bool`
        Whether to show the page indicator when using the default buttons.
    show_menu: :class:`bool`
        Whether to show a select menu that allows the user to switch between groups of pages.
    menu_placeholder: :class:`str`
        The placeholder text to show in the page group menu when no page group has been selected yet.
        Defaults to "Select Page Group" if not provided.
    author_check: :class:`bool`
        Whether only the original user of the command can change pages.
    disable_on_timeout: :class:`bool`
        Whether the buttons get disabled when the paginator view times out.
    use_default_buttons: :class:`bool`
        Whether to use the default buttons (i.e. ``first``, ``prev``, ``page_indicator``, ``next``, ``last``)
    default_button_row: :class:`int`
        The row where the default paginator buttons are displayed. Has no effect if custom buttons are used.
    loop_pages: :class:`bool`
        Whether to loop the pages when clicking prev/next while at the first/last page in the list.
    custom_view: Optional[:class:`discord.ui.View`]
        A custom view whose items are appended below the pagination components.
        If the currently displayed page has a `custom_view` assigned, it will replace these view components when that page is displayed.
    timeout: Optional[:class:`float`]
        Timeout in seconds from last interaction with the paginator before no longer accepting input.
    custom_buttons: Optional[List[:class:`PaginatorButton`]]
        A list of PaginatorButtons to initialize the Paginator with.
        If ``use_default_buttons`` is ``True``, this parameter is ignored.
    trigger_on_display: :class:`bool`
        Whether to automatically trigger the callback associated with a `Page` whenever it is displayed.
        Has no effect if no callback exists for a `Page`.

    Attributes
    ----------
    menu: Optional[List[:class:`PaginatorMenu`]]
        The page group select menu associated with this paginator.
    page_groups: Optional[List[:class:`PageGroup`]]
        List of :class:`PageGroup` objects the user can switch between.
    default_page_group: Optional[:class:`int`]
        The index of the default page group shown when the paginator is initially sent. Defined by setting ``default`` to ``True`` on a :class:`PageGroup`.
    current_page: :class:`int`
        A zero-indexed value showing the current page number.
    page_count: :class:`int`
        A zero-indexed value showing the total number of pages.
    buttons: Dict[:class:`str`, Dict[:class:`str`, Union[:class:`~PaginatorButton`, :class:`bool`]]]
        A dictionary containing the :class:`~PaginatorButton` objects included in this paginator.
    user: Optional[Union[:class:`~discord.User`, :class:`~discord.Member`]]
        The user or member that invoked the paginator.
    message: Union[:class:`~discord.Message`, :class:`~discord.WebhookMessage`]
        The message the paginator is attached to.
    """

    def __init__(
        self,
        pages: Union[List[PageGroup], List[Page], List[str], List[Union[List[discord.Embed], discord.Embed]]],
        show_disabled: bool = True,
        show_indicator=True,
        show_menu=False,
        menu_placeholder: str = "Select Page Group",
        author_check=True,
        disable_on_timeout=True,
        use_default_buttons=True,
        default_button_row: int = 0,
        loop_pages=False,
        custom_view: Optional[discord.ui.View] = None,
        timeout: Optional[float] = 180.0,
        custom_buttons: Optional[List[PaginatorButton]] = None,
        trigger_on_display: Optional[bool] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.timeout: float = timeout
        self.pages: Union[
            List[PageGroup], List[str], List[Page], List[Union[List[discord.Embed], discord.Embed]]
        ] = pages
        self.current_page = 0
        self.menu: Optional[PaginatorMenu] = None
        self.show_menu = show_menu
        self.menu_placeholder = menu_placeholder
        self.page_groups: Optional[List[PageGroup]] = None
        self.default_page_group: int = 0

        if all(isinstance(pg, PageGroup) for pg in pages):
            self.page_groups = self.pages if show_menu else None
            if sum(pg.default is True for pg in self.page_groups) > 1:
                raise ValueError("Only one PageGroup can be set as the default.")
            for pg in self.page_groups:
                if pg.default:
                    self.default_page_group = self.page_groups.index(pg)
                    break
            self.pages: List[Page] = self.get_page_group_content(self.page_groups[self.default_page_group])

        self.page_count = max(len(self.pages) - 1, 0)
        self.buttons = {}
        self.custom_buttons: List = custom_buttons
        self.show_disabled = show_disabled
        self.show_indicator = show_indicator
        self.disable_on_timeout = disable_on_timeout
        self.use_default_buttons = use_default_buttons
        self.default_button_row = default_button_row
        self.loop_pages = loop_pages
        self.custom_view: discord.ui.View = custom_view
        self.trigger_on_display = trigger_on_display
        self.message: Union[discord.Message, discord.WebhookMessage, None] = None

        if self.custom_buttons and not self.use_default_buttons:
            for button in custom_buttons:
                self.add_button(button)
        elif not self.custom_buttons and self.use_default_buttons:
            self.add_default_buttons()

        if self.show_menu:
            self.add_menu()

        self.usercheck = author_check
        self.user = None

    async def update(
        self,
        pages: Optional[
            Union[List[PageGroup], List[Page], List[str], List[Union[List[discord.Embed], discord.Embed]]]
        ] = None,
        show_disabled: Optional[bool] = None,
        show_indicator: Optional[bool] = None,
        show_menu: Optional[bool] = None,
        author_check: Optional[bool] = None,
        menu_placeholder: Optional[str] = None,
        disable_on_timeout: Optional[bool] = None,
        use_default_buttons: Optional[bool] = None,
        default_button_row: Optional[int] = None,
        loop_pages: Optional[bool] = None,
        custom_view: Optional[discord.ui.View] = None,
        timeout: Optional[float] = None,
        custom_buttons: Optional[List[PaginatorButton]] = None,
        trigger_on_display: Optional[bool] = None,
        interaction: Optional[discord.Interaction] = None,
    ):
        """Updates the existing :class:`Paginator` instance with the provided options.

        Parameters
        ----------
        pages: Optional[Union[List[:class:`PageGroup`], List[:class:`Page`], List[:class:`str`], List[Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]]
            The list of :class:`PageGroup` objects, :class:`Page` objects, strings, embeds, or list of embeds to paginate.
        show_disabled: :class:`bool`
            Whether to show disabled buttons.
        show_indicator: :class:`bool`
            Whether to show the page indicator when using the default buttons.
        show_menu: :class:`bool`
            Whether to show a select menu that allows the user to switch between groups of pages.
        author_check: :class:`bool`
            Whether only the original user of the command can change pages.
        menu_placeholder: :class:`str`
            The placeholder text to show in the page group menu when no page group has been selected yet.
            Defaults to "Select Page Group" if not provided.
        disable_on_timeout: :class:`bool`
            Whether the buttons get disabled when the paginator view times out.
        use_default_buttons: :class:`bool`
            Whether to use the default buttons (i.e. ``first``, ``prev``, ``page_indicator``, ``next``, ``last``)
        default_button_row: Optional[:class:`int`]
            The row where the default paginator buttons are displayed. Has no effect if custom buttons are used.
        loop_pages: :class:`bool`
            Whether to loop the pages when clicking prev/next while at the first/last page in the list.
        custom_view: Optional[:class:`discord.ui.View`]
            A custom view whose items are appended below the pagination components.
        timeout: Optional[:class:`float`]
            Timeout in seconds from last interaction with the paginator before no longer accepting input.
        custom_buttons: Optional[List[:class:`PaginatorButton`]]
            A list of PaginatorButtons to initialize the Paginator with.
            If ``use_default_buttons`` is ``True``, this parameter is ignored.
        trigger_on_display: :class:`bool`
            Whether to automatically trigger the callback associated with a `Page` whenever it is displayed.
            Has no effect if no callback exists for a `Page`.
        interaction: Optional[:class:`discord.Interaction`]
            The interaction to use when updating the paginator. If not provided, the paginator will be updated
            by using its stored :attr:`message` attribute instead.
        """

        # Update pages and reset current_page to 0 (default)
        self.pages: Union[List[PageGroup], List[str], List[Page], List[Union[List[discord.Embed], discord.Embed]]] = (
            pages if pages is not None else self.pages
        )
        self.show_menu = show_menu if show_menu is not None else self.show_menu
        if pages is not None and all(isinstance(pg, PageGroup) for pg in pages):
            self.page_groups = self.pages if self.show_menu else None
            if sum(pg.default is True for pg in self.page_groups) > 1:
                raise ValueError("Only one PageGroup can be set as the default.")
            for pg in self.page_groups:
                if pg.default:
                    self.default_page_group = self.page_groups.index(pg)
                    break
            self.pages: List[Page] = self.get_page_group_content(self.page_groups[self.default_page_group])
        self.page_count = max(len(self.pages) - 1, 0)
        self.current_page = 0
        # Apply config changes, if specified
        self.show_disabled = show_disabled if show_disabled is not None else self.show_disabled
        self.show_indicator = show_indicator if show_indicator is not None else self.show_indicator
        self.usercheck = author_check if author_check is not None else self.usercheck
        self.menu_placeholder = menu_placeholder if menu_placeholder is not None else self.menu_placeholder
        self.disable_on_timeout = disable_on_timeout if disable_on_timeout is not None else self.disable_on_timeout
        self.use_default_buttons = use_default_buttons if use_default_buttons is not None else self.use_default_buttons
        self.default_button_row = default_button_row if default_button_row is not None else self.default_button_row
        self.loop_pages = loop_pages if loop_pages is not None else self.loop_pages
        self.custom_view: discord.ui.View = None if custom_view is None else custom_view
        self.timeout: float = timeout if timeout is not None else self.timeout
        self.trigger_on_display = trigger_on_display if trigger_on_display is not None else self.trigger_on_display
        if custom_buttons and not self.use_default_buttons:
            self.buttons = {}
            for button in custom_buttons:
                self.add_button(button)
        else:
            self.buttons = {}
            self.add_default_buttons()

        await self.goto_page(self.current_page, interaction=interaction)

    async def on_timeout(self) -> None:
        """Disables all buttons when the view times out."""
        if self.disable_on_timeout:
            for item in self.children:
                item.disabled = True
            page = self.pages[self.current_page]
            page = self.get_page_content(page)
            files = page.update_files()
            await self.message.edit(
                view=self,
                files=files or [],
                attachments=[],
            )

    async def disable(
        self,
        include_custom: bool = False,
        page: Optional[Union[str, Page, Union[List[discord.Embed], discord.Embed]]] = None,
    ) -> None:
        """Stops the paginator, disabling all of its components.

        Parameters
        ----------
        include_custom: :class:`bool`
            Whether to disable components added via custom views.
        page: Optional[Union[:class:`str`, Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]
            The page content to show after disabling the paginator.
        """
        page = self.get_page_content(page)
        for item in self.children:
            if include_custom or not self.custom_view or item not in self.custom_view.children:
                item.disabled = True
        if page:
            await self.message.edit(
                content=page.content,
                embeds=page.embeds,
                view=self,
            )
        else:
            await self.message.edit(view=self)

    async def cancel(
        self,
        include_custom: bool = False,
        page: Optional[Union[str, Page, Union[List[discord.Embed], discord.Embed]]] = None,
    ) -> None:
        """Cancels the paginator, removing all of its components from the message.

        Parameters
        ----------
        include_custom: :class:`bool`
            Whether to remove components added via custom views.
        page: Optional[Union[:class:`str`, Union[List[:class:`discord.Embed`], :class:`discord.Embed`]]]
            The page content to show after canceling the paginator.
        """
        items = self.children.copy()
        page = self.get_page_content(page)
        for item in items:
            if include_custom or not self.custom_view or item not in self.custom_view.children:
                self.remove_item(item)
        if page:
            await self.message.edit(
                content=page.content,
                embeds=page.embeds,
                view=self,
            )
        else:
            await self.message.edit(view=self)

    async def goto_page(self, page_number: int = 0, *, interaction: Optional[discord.Interaction] = None) -> None:
        """Updates the paginator message to show the specified page number.

        Parameters
        ----------
        page_number: :class:`int`
            The page to display.

            .. note::

                Page numbers are zero-indexed when referenced internally, but appear as one-indexed when shown to the user.

        interaction: Optional[:class:`discord.Interaction`]
            The interaction to use when editing the message. If not provided, the message will be edited using the paginator's
            stored :attr:`message` attribute instead.

        Returns
        -------
        :class:`~discord.Message`
            The message associated with the paginator.
        """
        self.update_buttons()
        self.current_page = page_number
        if self.show_indicator:
            self.buttons["page_indicator"]["object"].label = f"{self.current_page + 1}/{self.page_count + 1}"

        page = self.pages[page_number]
        page = self.get_page_content(page)

        if page.custom_view:
            self.update_custom_view(page.custom_view)

        files = page.update_files()

        if interaction:
            await interaction.response.defer()  # needed to force webhook message edit route for files kwarg support
            await interaction.followup.edit_message(
                message_id=self.message.id,
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )
        else:
            await self.message.edit(
                content=page.content,
                embeds=page.embeds,
                attachments=[],
                files=files or [],
                view=self,
            )
        if self.trigger_on_display:
            await self.page_action(interaction=interaction)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.usercheck:
            return self.user == interaction.user
        return True

    def add_menu(self):
        """Adds the default :class:`PaginatorMenu` instance to the paginator."""
        self.menu = PaginatorMenu(self.page_groups, placeholder=self.menu_placeholder)
        self.menu.paginator = self
        self.add_item(self.menu)

    def add_default_buttons(self):
        """Adds the full list of default buttons that can be used with the paginator.
        Includes ``first``, ``prev``, ``page_indicator``, ``next``, and ``last``."""
        default_buttons = [
            PaginatorButton(
                "first",
                label="<<",
                style=discord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
            PaginatorButton(
                "prev",
                label="<",
                style=discord.ButtonStyle.red,
                loop_label="↪",
                row=self.default_button_row,
            ),
            PaginatorButton(
                "page_indicator",
                style=discord.ButtonStyle.gray,
                disabled=True,
                row=self.default_button_row,
            ),
            PaginatorButton(
                "next",
                label=">",
                style=discord.ButtonStyle.green,
                loop_label="↩",
                row=self.default_button_row,
            ),
            PaginatorButton(
                "last",
                label=">>",
                style=discord.ButtonStyle.blurple,
                row=self.default_button_row,
            ),
        ]
        for button in default_buttons:
            self.add_button(button)

    def add_button(self, button: PaginatorButton):
        """Adds a :class:`PaginatorButton` to the paginator."""
        self.buttons[button.button_type] = {
            "object": discord.ui.Button(
                style=button.style,
                label=button.label
                if button.label or button.emoji
                else button.button_type.capitalize()
                if button.button_type != "page_indicator"
                else f"{self.current_page + 1}/{self.page_count + 1}",
                disabled=button.disabled,
                custom_id=button.custom_id,
                emoji=button.emoji,
                row=button.row,
            ),
            "label": button.label,
            "loop_label": button.loop_label,
            "hidden": button.disabled if button.button_type != "page_indicator" else not self.show_indicator,
        }
        self.buttons[button.button_type]["object"].callback = button.callback
        button.paginator = self

    def remove_button(self, button_type: str):
        """Removes a :class:`PaginatorButton` from the paginator."""
        if button_type not in self.buttons.keys():
            raise ValueError(f"no button_type {button_type} was found in this paginator.")
        self.buttons.pop(button_type)

    def update_buttons(self) -> Dict:
        """Updates the display state of the buttons (disabled/hidden)

        Returns
        -------
        Dict[:class:`str`, Dict[:class:`str`, Union[:class:`~PaginatorButton`, :class:`bool`]]]
            The dictionary of buttons that were updated.
        """
        for key, button in self.buttons.items():
            if key == "first":
                if self.current_page <= 1:
                    button["hidden"] = True
                elif self.current_page >= 1:
                    button["hidden"] = False
            elif key == "last":
                if self.current_page >= self.page_count - 1:
                    button["hidden"] = True
                if self.current_page < self.page_count - 1:
                    button["hidden"] = False
            elif key == "next":
                if self.current_page == self.page_count:
                    if not self.loop_pages:
                        button["hidden"] = True
                        button["object"].label = button["label"]
                    else:
                        button["object"].label = button["loop_label"]
                elif self.current_page < self.page_count:
                    button["hidden"] = False
                    button["object"].label = button["label"]
            elif key == "prev":
                if self.current_page <= 0:
                    if not self.loop_pages:
                        button["hidden"] = True
                        button["object"].label = button["label"]
                    else:
                        button["object"].label = button["loop_label"]
                elif self.current_page >= 0:
                    button["hidden"] = False
                    button["object"].label = button["label"]
        self.clear_items()
        if self.show_indicator:
            self.buttons["page_indicator"]["object"].label = f"{self.current_page + 1}/{self.page_count + 1}"
        for key, button in self.buttons.items():
            if key != "page_indicator":
                if button["hidden"]:
                    button["object"].disabled = True
                    if self.show_disabled:
                        self.add_item(button["object"])
                else:
                    button["object"].disabled = False
                    self.add_item(button["object"])
            elif self.show_indicator:
                self.add_item(button["object"])

        if self.show_menu:
            self.add_menu()

        # We're done adding standard buttons and menus, so we can now add any specified custom view items below them
        # The bot developer should handle row assignments for their view before passing it to Paginator
        if self.custom_view:
            self.update_custom_view(self.custom_view)

        return self.buttons

    def update_custom_view(self, custom_view: discord.ui.View):
        """Updates the custom view shown on the paginator."""
        if isinstance(self.custom_view, discord.ui.View):
            for item in self.custom_view.children:
                self.remove_item(item)
        for item in custom_view.children:
            self.add_item(item)

    def get_page_group_content(self, page_group: PageGroup) -> List[Page]:
        """Returns a converted list of `Page` objects for the given page group based on the content of its pages."""
        return [self.get_page_content(page) for page in page_group.pages]

    @staticmethod
    def get_page_content(page: Union[Page, str, discord.Embed, List[discord.Embed]]) -> Page:
        """Converts a page into a :class:`Page` object based on its content."""
        if isinstance(page, Page):
            return page
        elif isinstance(page, str):
            return Page(content=page, embeds=[], files=[])
        elif isinstance(page, discord.Embed):
            return Page(content=None, embeds=[page], files=[])
        elif isinstance(page, discord.File):
            return Page(content=None, embeds=[], files=[page])
        elif isinstance(page, List):
            if all(isinstance(x, discord.Embed) for x in page):
                return Page(content=None, embeds=page, files=[])
            if all(isinstance(x, discord.File) for x in page):
                return Page(content=None, embeds=[], files=page)
            else:
                raise TypeError("All list items must be embeds or files.")
        else:
            raise TypeError(
                "Page content must be a Page object, string, an embed, a list of embeds, a file, or a list of files."
            )

    async def page_action(self, interaction: Optional[discord.Interaction] = None) -> None:
        """Triggers the callback associated with the current page, if any.

        Parameters
        ----------
        interaction: Optional[:class:`discord.Interaction`]
            The interaction that was used to trigger the page action.
        """
        if self.get_page_content(self.pages[self.current_page]).callback:
            await self.get_page_content(self.pages[self.current_page]).callback(interaction=interaction)

    async def send(
        self,
        ctx: Context,
        target: Optional[discord.abc.Messageable] = None,
        target_message: Optional[str] = None,
        reference: Optional[Union[discord.Message, discord.MessageReference, discord.PartialMessage]] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        mention_author: Optional[bool] = None,
        delete_after: Optional[float] = None,
    ) -> discord.Message:
        """Sends a message with the paginated items.

        Parameters
        ------------
        ctx: Union[:class:`~discord.ext.commands.Context`]
            A command's invocation context.
        target: Optional[:class:`~discord.abc.Messageable`]
            A target where the paginated message should be sent, if different from the original :class:`Context`
        target_message: Optional[:class:`str`]
            An optional message shown when the paginator message is sent elsewhere.
        reference: Optional[Union[:class:`discord.Message`, :class:`discord.MessageReference`, :class:`discord.PartialMessage`]]
            A reference to the :class:`~discord.Message` to which you are replying with the paginator. This can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`. You can control
            whether this mentions the author of the referenced message using the :attr:`~discord.AllowedMentions.replied_user`
            attribute of ``allowed_mentions`` or by setting ``mention_author``.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.
        delete_after: Optional[:class:`float`]
            If set, deletes the paginator after the specified time.

        Returns
        --------
        :class:`~discord.Message`
            The message that was sent with the paginator.
        """
        if not isinstance(ctx, Context):
            raise TypeError(f"expected Context not {ctx.__class__!r}")

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        if reference is not None and not isinstance(
            reference, (discord.Message, discord.MessageReference, discord.PartialMessage)
        ):
            raise TypeError(f"expected Message, MessageReference, or PartialMessage not {reference.__class__!r}")

        if allowed_mentions is not None and not isinstance(allowed_mentions, discord.AllowedMentions):
            raise TypeError(f"expected AllowedMentions not {allowed_mentions.__class__!r}")

        if mention_author is not None and not isinstance(mention_author, bool):
            raise TypeError(f"expected bool not {mention_author.__class__!r}")

        self.update_buttons()
        page = self.pages[self.current_page]
        page_content = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = ctx.author

        if target:
            if target_message:
                await ctx.send(
                    target_message,
                    reference=reference,
                    allowed_mentions=allowed_mentions,
                    mention_author=mention_author,
                )
            ctx = target

        self.message = await ctx.send(
            content=page_content.content,
            embeds=page_content.embeds,
            files=page_content.files,
            view=self,
            reference=reference,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            delete_after=delete_after,
        )

        return self.message

    async def edit(
        self,
        message: discord.Message,
        suppress: Optional[bool] = None,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
        delete_after: Optional[float] = None,
    ) -> Optional[discord.Message]:
        """Edits an existing message to replace it with the paginator contents.

        .. note::

            If invoked from an interaction, you will still need to respond to the interaction.


        Parameters
        -----------
        message: :class:`discord.Message`
            The message to edit with the paginator.
        suppress: :class:`bool`
            Whether to suppress embeds for the message. This removes
            all the embeds if set to ``True``. If set to ``False``
            this brings the embeds back if they were suppressed.
            Using this parameter requires :attr:`~.Permissions.manage_messages`.
        allowed_mentions: Optional[:class:`~discord.AllowedMentions`]
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.
        delete_after: Optional[:class:`float`]
            If set, deletes the paginator after the specified time.

        Returns
        --------
        Optional[:class:`discord.Message`]
            The message that was edited. Returns ``None`` if the operation failed.
        """
        if not isinstance(message, discord.Message):
            raise TypeError(f"expected Message not {message.__class__!r}")

        self.update_buttons()

        page: Union[Page, str, discord.Embed, List[discord.Embed]] = self.pages[self.current_page]
        page_content: Page = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        self.user = message.author

        try:
            self.message = await message.edit(
                content=page_content.content,
                embeds=page_content.embeds,
                files=page_content.files,
                attachments=[],
                view=self,
                suppress=suppress,
                allowed_mentions=allowed_mentions,
                delete_after=delete_after,
            )
        except (discord.NotFound, discord.Forbidden):
            pass

        return self.message

    async def respond(
        self,
        interaction: Union[discord.Interaction, BridgeContext],
        ephemeral: bool = False,
        target: Optional[discord.abc.Messageable] = None,
        target_message: str = "Paginator sent!",
    ) -> Union[discord.Message, discord.WebhookMessage]:
        """Sends an interaction response or followup with the paginated items.

        Parameters
        ------------
        interaction: Union[:class:`discord.Interaction`, :class:`BridgeContext`]
            The interaction or BridgeContext which invoked the paginator.
            If passing a BridgeContext object, you cannot make this an ephemeral paginator.
        ephemeral: :class:`bool`
            Whether the paginator message and its components are ephemeral.
            If ``target`` is specified, the ephemeral message content will be ``target_message`` instead.

            .. warning::

                If your paginator is ephemeral, it cannot have a timeout longer than 15 minutes (and cannot be persistent).

        target: Optional[:class:`~discord.abc.Messageable`]
            A target where the paginated message should be sent, if different from the original :class:`discord.Interaction`
        target_message: :class:`str`
            The content of the interaction response shown when the paginator message is sent elsewhere.

        Returns
        --------
        Union[:class:`~discord.Message`, :class:`~discord.WebhookMessage`]
            The :class:`~discord.Message` or :class:`~discord.WebhookMessage` that was sent with the paginator.
        """

        if not isinstance(interaction, (discord.Interaction, BridgeContext)):
            raise TypeError(f"expected Interaction or BridgeContext, not {interaction.__class__!r}")

        if target is not None and not isinstance(target, discord.abc.Messageable):
            raise TypeError(f"expected abc.Messageable not {target.__class__!r}")

        if ephemeral and (self.timeout >= 900 or self.timeout is None):
            raise ValueError(
                "paginator responses cannot be ephemeral if the paginator timeout is 15 minutes or greater"
            )

        self.update_buttons()

        page: Union[Page, str, discord.Embed, List[discord.Embed]] = self.pages[self.current_page]
        page_content: Page = self.get_page_content(page)

        if page_content.custom_view:
            self.update_custom_view(page_content.custom_view)

        if isinstance(interaction, discord.Interaction):
            self.user = interaction.user

            if target:
                await interaction.response.send_message(target_message, ephemeral=ephemeral)
                msg = await target.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
            elif interaction.response.is_done():
                msg = await interaction.followup.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                    ephemeral=ephemeral,
                )
                # convert from WebhookMessage to Message reference to bypass 15min webhook token timeout (non-ephemeral messages only)
                if not ephemeral:
                    msg = await msg.channel.fetch_message(msg.id)
            else:
                msg = await interaction.response.send_message(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                    ephemeral=ephemeral,
                )
        else:
            ctx = interaction
            self.user = ctx.author
            if target:
                await ctx.respond(target_message, ephemeral=ephemeral)
                msg = await ctx.send(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
            else:
                msg = await ctx.respond(
                    content=page_content.content,
                    embeds=page_content.embeds,
                    files=page_content.files,
                    view=self,
                )
        if isinstance(msg, (discord.Message, discord.WebhookMessage)):
            self.message = msg
        elif isinstance(msg, discord.Interaction):
            self.message = await msg.original_message()

        return self.message


class PaginatorMenu(discord.ui.Select):
    """Creates a select menu used to switch between page groups, which can each have their own set of buttons.

    Parameters
    ----------
    placeholder: :class:`str`
        The placeholder text that is shown if nothing is selected.

    Attributes
    ----------
    paginator: :class:`Paginator`
        The paginator class where this menu is being used.
        Assigned to the menu when ``Paginator.add_menu`` is called.
    """

    def __init__(
        self,
        page_groups: List[PageGroup],
        placeholder: Optional[str] = None,
        custom_id: Optional[str] = None,
    ):
        self.page_groups = page_groups
        self.paginator: Optional[Paginator] = None
        opts = [
            discord.SelectOption(
                label=page_group.label,
                value=page_group.label,
                description=page_group.description,
                emoji=page_group.emoji,
            )
            for page_group in self.page_groups
        ]
        super().__init__(placeholder=placeholder, max_values=1, min_values=1, options=opts, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        """|coro|

        The coroutine that is called when a menu option is selected.

        Parameters
        -----------
        interaction: :class:`discord.Interaction`
            The interaction created by selecting the menu option.
        """
        selection = self.values[0]
        for page_group in self.page_groups:
            if selection == page_group.label:
                return await self.paginator.update(
                    pages=page_group.pages,
                    show_disabled=page_group.show_disabled,
                    show_indicator=page_group.show_indicator,
                    author_check=page_group.author_check,
                    disable_on_timeout=page_group.disable_on_timeout,
                    use_default_buttons=page_group.use_default_buttons,
                    default_button_row=page_group.default_button_row,
                    loop_pages=page_group.loop_pages,
                    custom_view=page_group.custom_view,
                    timeout=page_group.timeout,
                    custom_buttons=page_group.custom_buttons,
                    trigger_on_display=page_group.trigger_on_display,
                    interaction=interaction,
                )
