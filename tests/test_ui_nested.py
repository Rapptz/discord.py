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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import discord
import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@dataclass
class ViewFixture:
    layout: discord.ui.LayoutView
    container: discord.ui.Container
    row: discord.ui.ActionRow
    item: discord.ui.Item


@pytest.fixture(params=["button", "select"])
def ui_item(request: pytest.FixtureRequest):
    if request.param == "button":
        return (discord.ui.Button, discord.ui.button)
    elif request.param == "select":
        return (discord.ui.Select, discord.ui.select)


@pytest_asyncio.fixture(params=["class", "constructor", "add_item"])
async def view(
    request: pytest.FixtureRequest, ui_item: "tuple[type[discord.ui.Item], Any]"
) -> ViewFixture:
    item_type, decorator = ui_item

    async def on_error(interaction, error: Exception, item):
        # do not let errors (especially asserts) be silenced by the default on_error handler
        raise error

    def check_callback(interaction: discord.Interaction, button: discord.ui.Item):
        row = button.parent
        assert isinstance(row, discord.ui.ActionRow)
        container = row.parent
        assert isinstance(container, discord.ui.Container)
        assert container.parent is None
        assert button.view == row.view == container.view is not None

    class Item(item_type):
        async def callback(self, interaction):
            check_callback(interaction, self)

    # return a tuple of layout-container-actionrow-button, pre-configured in different ways
    if request.param == "class":

        class Row(discord.ui.ActionRow):
            @decorator()
            async def item(self, interaction, item: discord.ui.Item):
                assert item.parent == self
                check_callback(interaction, item)

        class Container(discord.ui.Container):
            myrow = Row()

        class Layout(discord.ui.LayoutView):
            container = Container()

            async def on_error(self, interaction, error: Exception, item) -> None:
                await on_error(interaction, error, item)

        layout = Layout()
        container = layout.container
        row = container.myrow
        item = row.item

    elif request.param == "constructor":
        item = Item()
        row = discord.ui.ActionRow(item)
        container = discord.ui.Container(row)
        layout = discord.ui.LayoutView()
        layout.on_error = on_error
        layout.add_item(container)

    elif request.param == "add_item":
        item = Item()
        row = discord.ui.ActionRow()
        row.add_item(item)
        container = discord.ui.Container()
        container.add_item(row)
        layout = discord.ui.LayoutView()
        layout.on_error = on_error
        layout.add_item(container)

    return ViewFixture(layout, container, row, item)


# test that all "parent" attributes are properly set
def test_parent(view: ViewFixture):
    assert view.container.parent is None
    assert view.row.parent == view.container
    assert view.item.parent == view.row


# test that all "view" attributes are properly set
def test_view(view: ViewFixture):
    assert view.layout is not None
    assert view.container.view == view.layout
    assert view.row.view == view.layout
    assert view.item.view == view.layout


@pytest.mark.asyncio
async def test_dispatch(view: ViewFixture, mocker: "MockerFixture"):
    spy1 = mocker.spy(view.layout, "interaction_check")
    spy2 = mocker.spy(view.container, "interaction_check")
    spy3 = mocker.spy(view.row, "interaction_check")
    spy4 = mocker.spy(view.item, "interaction_check")

    interaction = mocker.NonCallableMagicMock(spec=discord.Interaction)
    task = view.layout._dispatch_item(view.item, interaction)
    assert task is not None
    # let the task finish and retrieve any potential exception
    await task
    exc = task.exception()
    if exc:
        raise exc

    # verify that ALL interaction_check methods are being called
    spy1.assert_awaited_once_with(interaction)
    spy2.assert_awaited_once_with(interaction)
    spy3.assert_awaited_once_with(interaction)
    spy4.assert_awaited_once_with(interaction)
