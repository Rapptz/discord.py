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

import discord
import pytest


def test_separator_init():
    separator = discord.ui.Separator()
    assert separator.visible is True
    assert separator.spacing == discord.SeparatorSpacing.small
    assert separator.id is None


def test_separator_with_parameters():
    separator = discord.ui.Separator(
        visible=False,
        spacing=discord.SeparatorSpacing.large,
        id=42,
    )
    assert separator.visible is False
    assert separator.spacing == discord.SeparatorSpacing.large
    assert separator.id == 42


def test_separator_is_v2():
    separator = discord.ui.Separator()
    assert separator._is_v2() is True


def test_separator_type():
    separator = discord.ui.Separator()
    assert separator.type == discord.ComponentType.separator


def test_separator_width():
    separator = discord.ui.Separator()
    assert separator.width == 5


def test_separator_setters():
    separator = discord.ui.Separator()

    separator.visible = False
    assert separator.visible is False

    separator.spacing = discord.SeparatorSpacing.large
    assert separator.spacing == discord.SeparatorSpacing.large

    separator.id = 123
    assert separator.id == 123


def test_separator_to_component_dict():
    separator = discord.ui.Separator(
        visible=True,
        spacing=discord.SeparatorSpacing.large,
        id=42,
    )
    component_dict = separator.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.separator.value
    assert component_dict.get('id') == 42


def test_text_display_init():
    text_display = discord.ui.TextDisplay("Hello, World!")
    assert text_display.content == "Hello, World!"
    assert text_display.id is None


def test_text_display_with_id():
    text_display = discord.ui.TextDisplay("Hello!", id=123)
    assert text_display.content == "Hello!"
    assert text_display.id == 123


def test_text_display_is_v2():
    text_display = discord.ui.TextDisplay("Test")
    assert text_display._is_v2() is True


def test_text_display_type():
    text_display = discord.ui.TextDisplay("Test")
    assert text_display.type == discord.ComponentType.text_display


def test_text_display_width():
    text_display = discord.ui.TextDisplay("Test")
    assert text_display.width == 5


def test_text_display_to_component_dict():
    text_display = discord.ui.TextDisplay("Hello, World!", id=42)
    component_dict = text_display.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.text_display.value
    assert component_dict['content'] == "Hello, World!"
    assert component_dict.get('id') == 42


def test_text_display_to_component_dict_no_id():
    text_display = discord.ui.TextDisplay("Hello!")
    component_dict = text_display.to_component_dict()
    assert 'id' not in component_dict


def test_container_init():
    container = discord.ui.Container()
    assert len(container.children) == 0
    assert container.spoiler is False
    assert container.accent_colour is None
    assert container.id is None


def test_container_with_children():
    text = discord.ui.TextDisplay("Hello!")
    container = discord.ui.Container(text)
    assert len(container.children) == 1


def test_container_with_parameters():
    container = discord.ui.Container(
        accent_colour=discord.Colour.red(),
        spoiler=True,
        id=42,
    )
    assert container.spoiler is True
    assert container.accent_colour == discord.Colour.red()
    assert container.id == 42


def test_container_accent_color_alias():
    container = discord.ui.Container(accent_color=discord.Color.blue())
    assert container.accent_colour == discord.Color.blue()
    assert container.accent_color == discord.Color.blue()


def test_container_is_v2():
    container = discord.ui.Container()
    assert container._is_v2() is True


def test_container_type():
    container = discord.ui.Container()
    assert container.type == discord.ComponentType.container


def test_container_width():
    container = discord.ui.Container()
    assert container.width == 5


def test_container_add_item():
    container = discord.ui.Container()
    text = discord.ui.TextDisplay("Hello!")

    result = container.add_item(text)

    assert len(container.children) == 1
    assert container.children[0].content == "Hello!"  # type: ignore
    assert result is container


def test_container_add_item_invalid():
    container = discord.ui.Container()
    with pytest.raises(TypeError):
        container.add_item("not an item")  # type: ignore


def test_container_remove_item():
    text = discord.ui.TextDisplay("Hello!")
    container = discord.ui.Container(text)

    result = container.remove_item(text)

    assert len(container.children) == 0
    assert result is container


def test_container_remove_item_not_found():
    container = discord.ui.Container()
    text = discord.ui.TextDisplay("Hello!")
    result = container.remove_item(text)
    assert result is container


def test_container_clear_items():
    text1 = discord.ui.TextDisplay("Hello!")
    text2 = discord.ui.TextDisplay("World!")
    container = discord.ui.Container(text1, text2)

    result = container.clear_items()

    assert len(container.children) == 0
    assert result is container


def test_container_walk_children():
    text1 = discord.ui.TextDisplay("Hello!")
    text2 = discord.ui.TextDisplay("World!")
    container = discord.ui.Container(text1, text2)

    children = list(container.walk_children())

    assert len(children) == 2


def test_container_content_length():
    text1 = discord.ui.TextDisplay("Hello")
    text2 = discord.ui.TextDisplay("World")
    container = discord.ui.Container(text1, text2)

    assert container.content_length() == 10


def test_container_to_component_dict():
    text = discord.ui.TextDisplay("Hello!")
    container = discord.ui.Container(
        text,
        accent_colour=discord.Colour.red(),
        spoiler=True,
        id=42,
    )
    component_dict = container.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.container.value
    assert component_dict['spoiler'] is True
    assert component_dict['accent_color'] == discord.Colour.red().value
    assert component_dict.get('id') == 42
    assert len(component_dict['components']) == 1


def test_container_accent_colour_setter_invalid():
    container = discord.ui.Container()
    with pytest.raises(TypeError):
        container.accent_colour = "red"  # type: ignore


def test_section_init():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    assert len(section.children) == 0
    assert section.accessory is button
    assert section.id is None


def test_section_with_text():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("Hello, World!", accessory=button)
    assert len(section.children) == 1


def test_section_with_text_display():
    button = discord.ui.Button(label="Click me!")
    text = discord.ui.TextDisplay("Hello!")
    section = discord.ui.Section(text, accessory=button)
    assert len(section.children) == 1


def test_section_with_multiple_text():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("Line 1", "Line 2", "Line 3", accessory=button)
    assert len(section.children) == 3


def test_section_is_v2():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    assert section._is_v2() is True


def test_section_type():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    assert section.type == discord.ComponentType.section


def test_section_width():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    assert section.width == 5


def test_section_add_item_string():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)

    result = section.add_item("Hello!")

    assert len(section.children) == 1
    assert result is section


def test_section_add_item_text_display():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    text = discord.ui.TextDisplay("Hello!")

    result = section.add_item(text)

    assert len(section.children) == 1
    assert result is section


def test_section_add_item_exceeds_max():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("1", "2", "3", accessory=button)

    with pytest.raises(ValueError):
        section.add_item("4")


def test_section_add_item_invalid():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    with pytest.raises(TypeError):
        section.add_item(123)  # type: ignore


def test_section_remove_item():
    button = discord.ui.Button(label="Click me!")
    text = discord.ui.TextDisplay("Hello!")
    section = discord.ui.Section(text, accessory=button)

    result = section.remove_item(text)

    assert len(section.children) == 0
    assert result is section


def test_section_clear_items():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("1", "2", "3", accessory=button)

    result = section.clear_items()

    assert len(section.children) == 0
    assert result is section


def test_section_accessory_setter():
    button1 = discord.ui.Button(label="Button 1")
    button2 = discord.ui.Button(label="Button 2")
    section = discord.ui.Section(accessory=button1)

    section.accessory = button2

    assert section.accessory is button2


def test_section_accessory_setter_invalid():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section(accessory=button)
    with pytest.raises(TypeError):
        section.accessory = "not an item"  # type: ignore


def test_section_walk_children():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("Hello!", "World!", accessory=button)

    children = list(section.walk_children())

    assert len(children) == 3


def test_section_content_length():
    button = discord.ui.Button(label="Click me!")
    text1 = discord.ui.TextDisplay("Hello")
    text2 = discord.ui.TextDisplay("World")
    section = discord.ui.Section(text1, text2, accessory=button)

    assert section.content_length() == 10


def test_section_total_count():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("Hello!", "World!", accessory=button)
    assert section._total_count == 4


def test_section_to_component_dict():
    button = discord.ui.Button(label="Click me!")
    section = discord.ui.Section("Hello!", accessory=button, id=42)
    component_dict = section.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.section.value
    assert len(component_dict['components']) == 1
    assert 'accessory' in component_dict
    assert component_dict.get('id') == 42


def test_action_row_init():
    row = discord.ui.ActionRow()
    assert len(row.children) == 0
    assert row.id is None


def test_action_row_with_children():
    button = discord.ui.Button(label="Click me!")
    row = discord.ui.ActionRow(button)
    assert len(row.children) == 1


def test_action_row_with_id():
    row = discord.ui.ActionRow(id=42)
    assert row.id == 42


def test_action_row_type():
    row = discord.ui.ActionRow()
    assert row.type == discord.ComponentType.action_row


def test_action_row_width():
    row = discord.ui.ActionRow()
    assert row.width == 5


def test_action_row_add_item():
    row = discord.ui.ActionRow()
    button = discord.ui.Button(label="Click me!")

    result = row.add_item(button)

    assert len(row.children) == 1
    assert result is row


def test_action_row_add_item_exceeds_width():
    row = discord.ui.ActionRow()
    for i in range(5):
        row.add_item(discord.ui.Button(label=f"Button {i}"))

    with pytest.raises(ValueError):
        row.add_item(discord.ui.Button(label="Too many!"))


def test_action_row_add_item_invalid():
    row = discord.ui.ActionRow()
    with pytest.raises(AttributeError):
        row.add_item("not an item")  # type: ignore


def test_action_row_remove_item():
    button = discord.ui.Button(label="Click me!")
    row = discord.ui.ActionRow(button)

    result = row.remove_item(button)

    assert len(row.children) == 0
    assert result is row


def test_action_row_clear_items():
    button1 = discord.ui.Button(label="Button 1")
    button2 = discord.ui.Button(label="Button 2")
    row = discord.ui.ActionRow(button1, button2)

    result = row.clear_items()

    assert len(row.children) == 0
    assert result is row


def test_media_gallery_init():
    gallery = discord.ui.MediaGallery()
    assert len(gallery.items) == 0
    assert gallery.id is None


def test_media_gallery_with_items():
    item = discord.MediaGalleryItem("https://example.com/image.png")
    gallery = discord.ui.MediaGallery(item)
    assert len(gallery.items) == 1


def test_media_gallery_with_id():
    gallery = discord.ui.MediaGallery(id=42)
    assert gallery.id == 42


def test_media_gallery_is_v2():
    gallery = discord.ui.MediaGallery()
    assert gallery._is_v2() is True


def test_media_gallery_type():
    gallery = discord.ui.MediaGallery()
    assert gallery.type == discord.ComponentType.media_gallery


def test_media_gallery_width():
    gallery = discord.ui.MediaGallery()
    assert gallery.width == 5


def test_media_gallery_add_item():
    gallery = discord.ui.MediaGallery()

    result = gallery.add_item(media="https://example.com/image.png", description="Test image")

    assert len(gallery.items) == 1
    assert result is gallery


def test_media_gallery_add_item_exceeds_max():
    gallery = discord.ui.MediaGallery()
    for i in range(10):
        gallery.add_item(media=f"https://example.com/image{i}.png")

    with pytest.raises(ValueError):
        gallery.add_item(media="https://example.com/too-many.png")


def test_media_gallery_append_item():
    gallery = discord.ui.MediaGallery()
    item = discord.MediaGalleryItem("https://example.com/image.png")

    result = gallery.append_item(item)

    assert len(gallery.items) == 1
    assert result is gallery


def test_media_gallery_append_item_invalid():
    gallery = discord.ui.MediaGallery()
    with pytest.raises(TypeError):
        gallery.append_item("not a media item")  # type: ignore


def test_media_gallery_insert_item_at():
    item1 = discord.MediaGalleryItem("https://example.com/image1.png")
    item2 = discord.MediaGalleryItem("https://example.com/image2.png")
    gallery = discord.ui.MediaGallery(item1, item2)

    result = gallery.insert_item_at(1, media="https://example.com/inserted.png")

    assert len(gallery.items) == 3
    assert result is gallery


def test_media_gallery_remove_item():
    item = discord.MediaGalleryItem("https://example.com/image.png")
    gallery = discord.ui.MediaGallery(item)

    result = gallery.remove_item(item)

    assert len(gallery.items) == 0
    assert result is gallery


def test_media_gallery_clear_items():
    item1 = discord.MediaGalleryItem("https://example.com/image1.png")
    item2 = discord.MediaGalleryItem("https://example.com/image2.png")
    gallery = discord.ui.MediaGallery(item1, item2)

    result = gallery.clear_items()

    assert len(gallery.items) == 0
    assert result is gallery


def test_media_gallery_items_setter():
    gallery = discord.ui.MediaGallery()
    items = [discord.MediaGalleryItem(f"https://example.com/image{i}.png") for i in range(5)]

    gallery.items = items

    assert len(gallery.items) == 5


def test_media_gallery_items_setter_exceeds_max():
    gallery = discord.ui.MediaGallery()
    items = [discord.MediaGalleryItem(f"https://example.com/image{i}.png") for i in range(11)]

    with pytest.raises(ValueError):
        gallery.items = items


def test_thumbnail_init():
    thumbnail = discord.ui.Thumbnail("https://example.com/image.png")
    assert thumbnail.media.url == "https://example.com/image.png"
    assert thumbnail.description is None
    assert thumbnail.spoiler is False
    assert thumbnail.id is None


def test_thumbnail_with_parameters():
    thumbnail = discord.ui.Thumbnail(
        "https://example.com/image.png",
        description="A test image",
        spoiler=True,
        id=42,
    )
    assert thumbnail.description == "A test image"
    assert thumbnail.spoiler is True
    assert thumbnail.id == 42


def test_thumbnail_is_v2():
    thumbnail = discord.ui.Thumbnail("https://example.com/image.png")
    assert thumbnail._is_v2() is True


def test_thumbnail_type():
    thumbnail = discord.ui.Thumbnail("https://example.com/image.png")
    assert thumbnail.type == discord.ComponentType.thumbnail


def test_thumbnail_width():
    thumbnail = discord.ui.Thumbnail("https://example.com/image.png")
    assert thumbnail.width == 5


def test_thumbnail_media_setter_string():
    thumbnail = discord.ui.Thumbnail("https://example.com/image1.png")

    thumbnail.media = "https://example.com/image2.png"

    assert thumbnail.media.url == "https://example.com/image2.png"


def test_thumbnail_media_setter_unfurled():
    thumbnail = discord.ui.Thumbnail("https://example.com/image1.png")
    new_media = discord.UnfurledMediaItem("https://example.com/image2.png")

    thumbnail.media = new_media

    assert thumbnail.media.url == "https://example.com/image2.png"


def test_thumbnail_media_setter_invalid():
    thumbnail = discord.ui.Thumbnail("https://example.com/image.png")
    with pytest.raises(TypeError):
        thumbnail.media = 123  # type: ignore


def test_thumbnail_to_component_dict():
    thumbnail = discord.ui.Thumbnail(
        "https://example.com/image.png",
        description="Test",
        spoiler=True,
        id=42,
    )
    component_dict = thumbnail.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.thumbnail.value
    assert component_dict['spoiler'] is True
    assert component_dict.get('description') == "Test"
    assert component_dict.get('id') == 42


def test_file_upload_init():
    file_upload = discord.ui.FileUpload()
    assert file_upload.custom_id is not None
    assert file_upload.required is True
    assert file_upload.min_values is None
    assert file_upload.max_values is None
    assert file_upload.id is None


def test_file_upload_with_parameters():
    file_upload = discord.ui.FileUpload(
        custom_id="my-upload",
        required=False,
        min_values=1,
        max_values=5,
        id=42,
    )
    assert file_upload.custom_id == "my-upload"
    assert file_upload.required is False
    assert file_upload.min_values == 1
    assert file_upload.max_values == 5
    assert file_upload.id == 42


def test_file_upload_type():
    file_upload = discord.ui.FileUpload()
    assert file_upload.type == discord.ComponentType.file_upload


def test_file_upload_width():
    file_upload = discord.ui.FileUpload()
    assert file_upload.width == 5


def test_file_upload_setters():
    file_upload = discord.ui.FileUpload()

    file_upload.custom_id = "new-id"
    assert file_upload.custom_id == "new-id"

    file_upload.required = False
    assert file_upload.required is False

    file_upload.min_values = 2
    assert file_upload.min_values == 2

    file_upload.max_values = 8
    assert file_upload.max_values == 8

    file_upload.id = 123
    assert file_upload.id == 123


def test_file_upload_custom_id_invalid():
    with pytest.raises(TypeError):
        discord.ui.FileUpload(custom_id=123)  # type: ignore

    file_upload = discord.ui.FileUpload()
    with pytest.raises(TypeError):
        file_upload.custom_id = 123  # type: ignore


def test_file_upload_values_empty():
    file_upload = discord.ui.FileUpload()
    assert file_upload.values == []


def test_label_init():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(text="My Label", component=button)
    assert label.text == "My Label"
    assert label.description is None
    assert label.component is button
    assert label.id is None


def test_label_with_description():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(
        text="My Label",
        description="A helpful description",
        component=button,
        id=42,
    )
    assert label.description == "A helpful description"
    assert label.id == 42


def test_label_type():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(text="My Label", component=button)
    assert label.type == discord.ComponentType.label


def test_label_width():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(text="My Label", component=button)
    assert label.width == 5


def test_label_walk_children():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(text="My Label", component=button)

    children = list(label.walk_children())

    assert len(children) == 1
    assert children[0] is button


def test_label_to_component_dict():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(
        text="My Label",
        description="Description",
        component=button,
        id=42,
    )
    component_dict = label.to_component_dict()
    assert component_dict['type'] == discord.ComponentType.label.value
    assert component_dict['label'] == "My Label"
    assert component_dict.get('description') == "Description"
    assert component_dict.get('id') == 42
    assert 'component' in component_dict


def test_label_total_count():
    button = discord.ui.Button(label="Click me!")
    label = discord.ui.Label(text="My Label", component=button)
    assert label._total_count == 2

