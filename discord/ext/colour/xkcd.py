# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

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
from discord import colour


class xkcd_colour(colour):
    """Represents a Discord role colour with XKCD colour poll presets.

    For a full list of color codes visit https://xkcd.com/color/rgb/
    """

    @classmethod
    def rust(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa83c09``."""
        return cls(0xa83c09)

    @classmethod
    def jade(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1fa774``."""
        return cls(0x1fa774)

    @classmethod
    def ice(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd6fffa``."""
        return cls(0xd6fffa)

    @classmethod
    def burgundy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x610023``."""
        return cls(0x610023)

    @classmethod
    def pastel_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb0ff9d``."""
        return cls(0xb0ff9d)

    @classmethod
    def caramel(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaf6f09``."""
        return cls(0xaf6f09)

    @classmethod
    def mauve(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xae7181``."""
        return cls(0xae7181)

    @classmethod
    def nice_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x107ab0``."""
        return cls(0x107ab0)

    @classmethod
    def pinkish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc8aca9``."""
        return cls(0xc8aca9)

    @classmethod
    def purply_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x661aee``."""
        return cls(0x661aee)

    @classmethod
    def sand_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfce166``."""
        return cls(0xfce166)

    @classmethod
    def purplish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7a687f``."""
        return cls(0x7a687f)

    @classmethod
    def warm_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x978a84``."""
        return cls(0x978a84)

    @classmethod
    def dark_blue_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x005249``."""
        return cls(0x005249)

    @classmethod
    def slate(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x516572``."""
        return cls(0x516572)

    @classmethod
    def mid_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x50a747``."""
        return cls(0x50a747)

    @classmethod
    def light_grass_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9af764``."""
        return cls(0x9af764)

    @classmethod
    def milk_chocolate(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f4e1e``."""
        return cls(0x7f4e1e)

    @classmethod
    def neon_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe019a``."""
        return cls(0xfe019a)

    @classmethod
    def blue_with_a_hint_of_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x533cc6``."""
        return cls(0x533cc6)

    @classmethod
    def bright_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x87fd05``."""
        return cls(0x87fd05)

    @classmethod
    def brownish_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc9b003``."""
        return cls(0xc9b003)

    @classmethod
    def pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff81c0``."""
        return cls(0xff81c0)

    @classmethod
    def stormy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x507b9c``."""
        return cls(0x507b9c)

    @classmethod
    def piss_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xddd618``."""
        return cls(0xddd618)

    @classmethod
    def gross_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa0bf16``."""
        return cls(0xa0bf16)

    @classmethod
    def kiwi_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8ee53f``."""
        return cls(0x8ee53f)

    @classmethod
    def pistachio(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc0fa8b``."""
        return cls(0xc0fa8b)

    @classmethod
    def pastel_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff964f``."""
        return cls(0xff964f)

    @classmethod
    def claret(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x680018``."""
        return cls(0x680018)

    @classmethod
    def shamrock_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02c14d``."""
        return cls(0x02c14d)

    @classmethod
    def azure(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x069af3``."""
        return cls(0x069af3)

    @classmethod
    def bubble_gum_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff69af``."""
        return cls(0xff69af)

    @classmethod
    def greeny_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x42b395``."""
        return cls(0x42b395)

    @classmethod
    def rust_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc45508``."""
        return cls(0xc45508)

    @classmethod
    def light_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbf77f6``."""
        return cls(0xbf77f6)

    @classmethod
    def toxic_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x61de2a``."""
        return cls(0x61de2a)

    @classmethod
    def mustard(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xceb301``."""
        return cls(0xceb301)

    @classmethod
    def light_light_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc8ffb0``."""
        return cls(0xc8ffb0)

    @classmethod
    def cinnamon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac4f06``."""
        return cls(0xac4f06)

    @classmethod
    def battleship_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6b7c85``."""
        return cls(0x6b7c85)

    @classmethod
    def blood_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe4b03``."""
        return cls(0xfe4b03)

    @classmethod
    def very_light_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd3b683``."""
        return cls(0xd3b683)

    @classmethod
    def dark_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb416b``."""
        return cls(0xcb416b)

    @classmethod
    def denim(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3b638c``."""
        return cls(0x3b638c)

    @classmethod
    def brown_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x922b05``."""
        return cls(0x922b05)

    @classmethod
    def dusty_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd58a94``."""
        return cls(0xd58a94)

    @classmethod
    def apricot(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffb16d``."""
        return cls(0xffb16d)

    @classmethod
    def red_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd3c06``."""
        return cls(0xfd3c06)

    @classmethod
    def slate_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x59656d``."""
        return cls(0x59656d)

    @classmethod
    def vibrant_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad03de``."""
        return cls(0xad03de)

    @classmethod
    def murky_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6c7a0e``."""
        return cls(0x6c7a0e)

    @classmethod
    def booger_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x96b403``."""
        return cls(0x96b403)

    @classmethod
    def purpleish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdf4ec8``."""
        return cls(0xdf4ec8)

    @classmethod
    def chocolate_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x411900``."""
        return cls(0x411900)

    @classmethod
    def chestnut(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x742802``."""
        return cls(0x742802)

    @classmethod
    def burnt_siena(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb75203``."""
        return cls(0xb75203)

    @classmethod
    def rust_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8b3103``."""
        return cls(0x8b3103)

    @classmethod
    def light_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xacfffc``."""
        return cls(0xacfffc)

    @classmethod
    def greenish_beige(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc9d179``."""
        return cls(0xc9d179)

    @classmethod
    def bright_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc760ff``."""
        return cls(0xc760ff)

    @classmethod
    def aqua_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x12e193``."""
        return cls(0x12e193)

    @classmethod
    def dark_indigo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1f0954``."""
        return cls(0x1f0954)

    @classmethod
    def grey_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x826d8c``."""
        return cls(0x826d8c)

    @classmethod
    def light_light_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcafffb``."""
        return cls(0xcafffb)

    @classmethod
    def dark_aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x05696b``."""
        return cls(0x05696b)

    @classmethod
    def light_eggplant(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x894585``."""
        return cls(0x894585)

    @classmethod
    def baby_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffb7ce``."""
        return cls(0xffb7ce)

    @classmethod
    def true_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x089404``."""
        return cls(0x089404)

    @classmethod
    def pea_soup_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x94a617``."""
        return cls(0x94a617)

    @classmethod
    def vomit_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc7c10c``."""
        return cls(0xc7c10c)

    @classmethod
    def dusty_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac86a8``."""
        return cls(0xac86a8)

    @classmethod
    def light_khaki(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe6f2a2``."""
        return cls(0xe6f2a2)

    @classmethod
    def light_mint_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa6fbb2``."""
        return cls(0xa6fbb2)

    @classmethod
    def boring_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x63b365``."""
        return cls(0x63b365)

    @classmethod
    def wintergreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x20f986``."""
        return cls(0x20f986)

    @classmethod
    def wisteria(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa87dc2``."""
        return cls(0xa87dc2)

    @classmethod
    def grey_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f7053``."""
        return cls(0x7f7053)

    @classmethod
    def dark_lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9c6da5``."""
        return cls(0x9c6da5)

    @classmethod
    def purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7e1e9c``."""
        return cls(0x7e1e9c)

    @classmethod
    def yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc8fd3d``."""
        return cls(0xc8fd3d)

    @classmethod
    def light_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd8dcd6``."""
        return cls(0xd8dcd6)

    @classmethod
    def bluegreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x017a79``."""
        return cls(0x017a79)

    @classmethod
    def deep_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02590f``."""
        return cls(0x02590f)

    @classmethod
    def leafy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x51b73b``."""
        return cls(0x51b73b)

    @classmethod
    def olive(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6e750e``."""
        return cls(0x6e750e)

    @classmethod
    def watermelon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd4659``."""
        return cls(0xfd4659)

    @classmethod
    def orangey_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdb915``."""
        return cls(0xfdb915)

    @classmethod
    def mud_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x606602``."""
        return cls(0x606602)

    @classmethod
    def flat_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x699d4c``."""
        return cls(0x699d4c)

    @classmethod
    def greenish_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x32bf84``."""
        return cls(0x32bf84)

    @classmethod
    def orange_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd411e``."""
        return cls(0xfd411e)

    @classmethod
    def red_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfa2a55``."""
        return cls(0xfa2a55)

    @classmethod
    def silver(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc5c9c7``."""
        return cls(0xc5c9c7)

    @classmethod
    def seaweed_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x35ad6b``."""
        return cls(0x35ad6b)

    @classmethod
    def barney(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac1db8``."""
        return cls(0xac1db8)

    @classmethod
    def bright_sea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x05ffa6``."""
        return cls(0x05ffa6)

    @classmethod
    def very_dark_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x062e03``."""
        return cls(0x062e03)

    @classmethod
    def camo_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x526525``."""
        return cls(0x526525)

    @classmethod
    def dusty_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x825f87``."""
        return cls(0x825f87)

    @classmethod
    def dark_olive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3c4d03``."""
        return cls(0x3c4d03)

    @classmethod
    def windows_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3778bf``."""
        return cls(0x3778bf)

    @classmethod
    def dark_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaf884a``."""
        return cls(0xaf884a)

    @classmethod
    def nasty_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x70b23f``."""
        return cls(0x70b23f)

    @classmethod
    def dark_cream(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfff39a``."""
        return cls(0xfff39a)

    @classmethod
    def yellowgreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbbf90f``."""
        return cls(0xbbf90f)

    @classmethod
    def warm_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x952e8f``."""
        return cls(0x952e8f)

    @classmethod
    def dirty_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x667e2c``."""
        return cls(0x667e2c)

    @classmethod
    def camouflage_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4b6113``."""
        return cls(0x4b6113)

    @classmethod
    def orangered(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe420f``."""
        return cls(0xfe420f)

    @classmethod
    def brown_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x706c11``."""
        return cls(0x706c11)

    @classmethod
    def very_dark_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1d0200``."""
        return cls(0x1d0200)

    @classmethod
    def grey_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5e9b8a``."""
        return cls(0x5e9b8a)

    @classmethod
    def apple_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76cd26``."""
        return cls(0x76cd26)

    @classmethod
    def cadet_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4e7496``."""
        return cls(0x4e7496)

    @classmethod
    def midnight(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x03012d``."""
        return cls(0x03012d)

    @classmethod
    def bright_lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc95efb``."""
        return cls(0xc95efb)

    @classmethod
    def bright_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01ff07``."""
        return cls(0x01ff07)

    @classmethod
    def taupe(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb9a281``."""
        return cls(0xb9a281)

    @classmethod
    def powder_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffb2d0``."""
        return cls(0xffb2d0)

    @classmethod
    def light_pastel_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb2fba5``."""
        return cls(0xb2fba5)

    @classmethod
    def puke_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9aae07``."""
        return cls(0x9aae07)

    @classmethod
    def canary_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffe40``."""
        return cls(0xfffe40)

    @classmethod
    def blood(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x770001``."""
        return cls(0x770001)

    @classmethod
    def mocha(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9d7651``."""
        return cls(0x9d7651)

    @classmethod
    def dark(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1b2431``."""
        return cls(0x1b2431)

    @classmethod
    def dark_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0a888a``."""
        return cls(0x0a888a)

    @classmethod
    def dark_sand(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa88f59``."""
        return cls(0xa88f59)

    @classmethod
    def lightish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa552e6``."""
        return cls(0xa552e6)

    @classmethod
    def sun_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffdf22``."""
        return cls(0xffdf22)

    @classmethod
    def cherry_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf7022a``."""
        return cls(0xf7022a)

    @classmethod
    def toupe(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc7ac7d``."""
        return cls(0xc7ac7d)

    @classmethod
    def light_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfbeeac``."""
        return cls(0xfbeeac)

    @classmethod
    def pale_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb1916e``."""
        return cls(0xb1916e)

    @classmethod
    def dark_sage(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x598556``."""
        return cls(0x598556)

    @classmethod
    def golden_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfec615``."""
        return cls(0xfec615)

    @classmethod
    def racing_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x014600``."""
        return cls(0x014600)

    @classmethod
    def vivid_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9900fa``."""
        return cls(0x9900fa)

    @classmethod
    def fresh_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x69d84f``."""
        return cls(0x69d84f)

    @classmethod
    def burnt_umber(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa0450e``."""
        return cls(0xa0450e)

    @classmethod
    def deep_sea_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x015482``."""
        return cls(0x015482)

    @classmethod
    def duck_egg_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc3fbf4``."""
        return cls(0xc3fbf4)

    @classmethod
    def maize(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf4d054``."""
        return cls(0xf4d054)

    @classmethod
    def sunny_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfff917``."""
        return cls(0xfff917)

    @classmethod
    def khaki(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaaa662``."""
        return cls(0xaaa662)

    @classmethod
    def dull_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5f9e8f``."""
        return cls(0x5f9e8f)

    @classmethod
    def dark_coral(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcf524e``."""
        return cls(0xcf524e)

    @classmethod
    def baby_poop_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8f9805``."""
        return cls(0x8f9805)

    @classmethod
    def light_aquamarine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7bfdc7``."""
        return cls(0x7bfdc7)

    @classmethod
    def lightish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3d7afd``."""
        return cls(0x3d7afd)

    @classmethod
    def brownish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x86775f``."""
        return cls(0x86775f)

    @classmethod
    def bluey_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x89a0b0``."""
        return cls(0x89a0b0)

    @classmethod
    def cornflower(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6a79f7``."""
        return cls(0x6a79f7)

    @classmethod
    def dirty_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc87606``."""
        return cls(0xc87606)

    @classmethod
    def straw(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfcf679``."""
        return cls(0xfcf679)

    @classmethod
    def sage_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x88b378``."""
        return cls(0x88b378)

    @classmethod
    def acid_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8ffe09``."""
        return cls(0x8ffe09)

    @classmethod
    def bluish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x748b97``."""
        return cls(0x748b97)

    @classmethod
    def pale_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdc1c5``."""
        return cls(0xfdc1c5)

    @classmethod
    def ultramarine_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1805db``."""
        return cls(0x1805db)

    @classmethod
    def neon_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcfff04``."""
        return cls(0xcfff04)

    @classmethod
    def light_neon_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4efd54``."""
        return cls(0x4efd54)

    @classmethod
    def bottle_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x044a05``."""
        return cls(0x044a05)

    @classmethod
    def twilight(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4e518b``."""
        return cls(0x4e518b)

    @classmethod
    def poop_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7a5901``."""
        return cls(0x7a5901)

    @classmethod
    def eggplant(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x380835``."""
        return cls(0x380835)

    @classmethod
    def fuchsia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xed0dd9``."""
        return cls(0xed0dd9)

    @classmethod
    def cool_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x95a3a6``."""
        return cls(0x95a3a6)

    @classmethod
    def sandstone(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc9ae74``."""
        return cls(0xc9ae74)

    @classmethod
    def vomit(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa2a415``."""
        return cls(0xa2a415)

    @classmethod
    def dark_aquamarine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x017371``."""
        return cls(0x017371)

    @classmethod
    def pinky_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc94cbe``."""
        return cls(0xc94cbe)

    @classmethod
    def washed_out_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbcf5a6``."""
        return cls(0xbcf5a6)

    @classmethod
    def dark_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc65102``."""
        return cls(0xc65102)

    @classmethod
    def grey_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6b8ba4``."""
        return cls(0x6b8ba4)

    @classmethod
    def dull_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd5869d``."""
        return cls(0xd5869d)

    @classmethod
    def very_dark_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2a0134``."""
        return cls(0x2a0134)

    @classmethod
    def tan_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xab7e4c``."""
        return cls(0xab7e4c)

    @classmethod
    def sea(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3c9992``."""
        return cls(0x3c9992)

    @classmethod
    def slate_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5b7c99``."""
        return cls(0x5b7c99)

    @classmethod
    def mint(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9ffeb0``."""
        return cls(0x9ffeb0)

    @classmethod
    def dull_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x49759c``."""
        return cls(0x49759c)

    @classmethod
    def lightblue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7bc8f6``."""
        return cls(0x7bc8f6)

    @classmethod
    def light_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7ef4cc``."""
        return cls(0x7ef4cc)

    @classmethod
    def purply_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf075e6``."""
        return cls(0xf075e6)

    @classmethod
    def dark_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x341c02``."""
        return cls(0x341c02)

    @classmethod
    def drab(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x828344``."""
        return cls(0x828344)

    @classmethod
    def orangish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb25f03``."""
        return cls(0xb25f03)

    @classmethod
    def vivid_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2fef10``."""
        return cls(0x2fef10)

    @classmethod
    def light_grey_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9dbcd4``."""
        return cls(0x9dbcd4)

    @classmethod
    def mushroom(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xba9e88``."""
        return cls(0xba9e88)

    @classmethod
    def royal_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4b006e``."""
        return cls(0x4b006e)

    @classmethod
    def pale_mauve(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfed0fc``."""
        return cls(0xfed0fc)

    @classmethod
    def dark_fuchsia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9d0759``."""
        return cls(0x9d0759)

    @classmethod
    def pastel_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdb5856``."""
        return cls(0xdb5856)

    @classmethod
    def golden_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb27a01``."""
        return cls(0xb27a01)

    @classmethod
    def marigold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfcc006``."""
        return cls(0xfcc006)

    @classmethod
    def light_yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xccfd7f``."""
        return cls(0xccfd7f)

    @classmethod
    def greyish_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x719f91``."""
        return cls(0x719f91)

    @classmethod
    def pale_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa5fbd5``."""
        return cls(0xa5fbd5)

    @classmethod
    def cool_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x33b864``."""
        return cls(0x33b864)

    @classmethod
    def dark_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x34013f``."""
        return cls(0x34013f)

    @classmethod
    def orangey_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb16002``."""
        return cls(0xb16002)

    @classmethod
    def pale_salmon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffb19a``."""
        return cls(0xffb19a)

    @classmethod
    def butterscotch(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdb147``."""
        return cls(0xfdb147)

    @classmethod
    def grey_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x647d8e``."""
        return cls(0x647d8e)

    @classmethod
    def viridian(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1e9167``."""
        return cls(0x1e9167)

    @classmethod
    def clay(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb66a50``."""
        return cls(0xb66a50)

    @classmethod
    def light_gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfddc5c``."""
        return cls(0xfddc5c)

    @classmethod
    def pale_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffa756``."""
        return cls(0xffa756)

    @classmethod
    def violet_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfb5ffc``."""
        return cls(0xfb5ffc)

    @classmethod
    def browny_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xca6b02``."""
        return cls(0xca6b02)

    @classmethod
    def greyblue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x77a1b5``."""
        return cls(0x77a1b5)

    @classmethod
    def greyish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7a6a4f``."""
        return cls(0x7a6a4f)

    @classmethod
    def indigo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x380282``."""
        return cls(0x380282)

    @classmethod
    def pale_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd9544d``."""
        return cls(0xd9544d)

    @classmethod
    def barf_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x94ac02``."""
        return cls(0x94ac02)

    @classmethod
    def dusk(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4e5481``."""
        return cls(0x4e5481)

    @classmethod
    def dark_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd5b60a``."""
        return cls(0xd5b60a)

    @classmethod
    def coffee(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa6814c``."""
        return cls(0xa6814c)

    @classmethod
    def really_light_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd4ffff``."""
        return cls(0xd4ffff)

    @classmethod
    def light_burgundy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa8415b``."""
        return cls(0xa8415b)

    @classmethod
    def leaf(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x71aa34``."""
        return cls(0x71aa34)

    @classmethod
    def chartreuse(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc1f80a``."""
        return cls(0xc1f80a)

    @classmethod
    def cream(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffc2``."""
        return cls(0xffffc2)

    @classmethod
    def icky_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8fae22``."""
        return cls(0x8fae22)

    @classmethod
    def sandy_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdee73``."""
        return cls(0xfdee73)

    @classmethod
    def light_periwinkle(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc1c6fc``."""
        return cls(0xc1c6fc)

    @classmethod
    def mango(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffa62b``."""
        return cls(0xffa62b)

    @classmethod
    def sand(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe2ca76``."""
        return cls(0xe2ca76)

    @classmethod
    def dark_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x033500``."""
        return cls(0x033500)

    @classmethod
    def royal_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0504aa``."""
        return cls(0x0504aa)

    @classmethod
    def emerald_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x028f1e``."""
        return cls(0x028f1e)

    @classmethod
    def khaki_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x728639``."""
        return cls(0x728639)

    @classmethod
    def orangeish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd8d49``."""
        return cls(0xfd8d49)

    @classmethod
    def dusty_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5a86ad``."""
        return cls(0x5a86ad)

    @classmethod
    def light_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd6b4fc``."""
        return cls(0xd6b4fc)

    @classmethod
    def blood_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x980002``."""
        return cls(0x980002)

    @classmethod
    def fluro_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0aff02``."""
        return cls(0x0aff02)

    @classmethod
    def dirt(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8a6e45``."""
        return cls(0x8a6e45)

    @classmethod
    def strong_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff0789``."""
        return cls(0xff0789)

    @classmethod
    def hunter_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0b4008``."""
        return cls(0x0b4008)

    @classmethod
    def charcoal_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3c4142``."""
        return cls(0x3c4142)

    @classmethod
    def brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x653700``."""
        return cls(0x653700)

    @classmethod
    def burnt_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc04e01``."""
        return cls(0xc04e01)

    @classmethod
    def rusty_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcd5909``."""
        return cls(0xcd5909)

    @classmethod
    def baby_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa2cffe``."""
        return cls(0xa2cffe)

    @classmethod
    def tomato_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xec2d01``."""
        return cls(0xec2d01)

    @classmethod
    def steel_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5a7d9a``."""
        return cls(0x5a7d9a)

    @classmethod
    def celadon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbefdb7``."""
        return cls(0xbefdb7)

    @classmethod
    def steel_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6f828a``."""
        return cls(0x6f828a)

    @classmethod
    def aqua_marine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2ee8bb``."""
        return cls(0x2ee8bb)

    @classmethod
    def medium_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2c6fbb``."""
        return cls(0x2c6fbb)

    @classmethod
    def puke(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa5a502``."""
        return cls(0xa5a502)

    @classmethod
    def sandy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf1da7a``."""
        return cls(0xf1da7a)

    @classmethod
    def dark_slate_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x214761``."""
        return cls(0x214761)

    @classmethod
    def dusty_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76a973``."""
        return cls(0x76a973)

    @classmethod
    def deep_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9a0200``."""
        return cls(0x9a0200)

    @classmethod
    def bile(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb5c306``."""
        return cls(0xb5c306)

    @classmethod
    def purpley(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8756e4``."""
        return cls(0x8756e4)

    @classmethod
    def light_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x90e4c1``."""
        return cls(0x90e4c1)

    @classmethod
    def pale_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb7fffa``."""
        return cls(0xb7fffa)

    @classmethod
    def peach(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffb07c``."""
        return cls(0xffb07c)

    @classmethod
    def light_peach(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffd8b1``."""
        return cls(0xffd8b1)

    @classmethod
    def rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcf6275``."""
        return cls(0xcf6275)

    @classmethod
    def soft_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6fc276``."""
        return cls(0x6fc276)

    @classmethod
    def warm_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x964e02``."""
        return cls(0x964e02)

    @classmethod
    def pinkish_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd99b82``."""
        return cls(0xd99b82)

    @classmethod
    def bubblegum_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe83cc``."""
        return cls(0xfe83cc)

    @classmethod
    def buff(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfef69e``."""
        return cls(0xfef69e)

    @classmethod
    def bright_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff000d``."""
        return cls(0xff000d)

    @classmethod
    def plum(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x580f41``."""
        return cls(0x580f41)

    @classmethod
    def medium_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9e43a2``."""
        return cls(0x9e43a2)

    @classmethod
    def wheat(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfbdd7e``."""
        return cls(0xfbdd7e)

    @classmethod
    def burnt_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9f2305``."""
        return cls(0x9f2305)

    @classmethod
    def crimson(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8c000f``."""
        return cls(0x8c000f)

    @classmethod
    def ugly_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcd7584``."""
        return cls(0xcd7584)

    @classmethod
    def turquoise_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x06b1c4``."""
        return cls(0x06b1c4)

    @classmethod
    def blush(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf29e8e``."""
        return cls(0xf29e8e)

    @classmethod
    def orangey_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfa4224``."""
        return cls(0xfa4224)

    @classmethod
    def key_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaeff6e``."""
        return cls(0xaeff6e)

    @classmethod
    def lemon_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdff38``."""
        return cls(0xfdff38)

    @classmethod
    def kelley_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x009337``."""
        return cls(0x009337)

    @classmethod
    def dark_hot_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd90166``."""
        return cls(0xd90166)

    @classmethod
    def baby_poop(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x937c00``."""
        return cls(0x937c00)

    @classmethod
    def red_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9e0168``."""
        return cls(0x9e0168)

    @classmethod
    def amethyst(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9b5fc0``."""
        return cls(0x9b5fc0)

    @classmethod
    def bruise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7e4071``."""
        return cls(0x7e4071)

    @classmethod
    def baby_puke_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb6c406``."""
        return cls(0xb6c406)

    @classmethod
    def beige(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe6daa6``."""
        return cls(0xe6daa6)

    @classmethod
    def ocre(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc69c04``."""
        return cls(0xc69c04)

    @classmethod
    def muted_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3b719f``."""
        return cls(0x3b719f)

    @classmethod
    def puke_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc2be0e``."""
        return cls(0xc2be0e)

    @classmethod
    def burple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6832e3``."""
        return cls(0x6832e3)

    @classmethod
    def lightish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x61e160``."""
        return cls(0x61e160)

    @classmethod
    def greenish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x96ae8d``."""
        return cls(0x96ae8d)

    @classmethod
    def butter(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffff81``."""
        return cls(0xffff81)

    @classmethod
    def cerulean_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x056eee``."""
        return cls(0x056eee)

    @classmethod
    def pinky(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfc86aa``."""
        return cls(0xfc86aa)

    @classmethod
    def reddish_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x997570``."""
        return cls(0x997570)

    @classmethod
    def light_mustard(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf7d560``."""
        return cls(0xf7d560)

    @classmethod
    def faded_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x916e99``."""
        return cls(0x916e99)

    @classmethod
    def wine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x80013f``."""
        return cls(0x80013f)

    @classmethod
    def bordeaux(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7b002c``."""
        return cls(0x7b002c)

    @classmethod
    def coral_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff6163``."""
        return cls(0xff6163)

    @classmethod
    def cool_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4984b8``."""
        return cls(0x4984b8)

    @classmethod
    def petrol(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x005f6a``."""
        return cls(0x005f6a)

    @classmethod
    def hot_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb00f5``."""
        return cls(0xcb00f5)

    @classmethod
    def violet_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x510ac9``."""
        return cls(0x510ac9)

    @classmethod
    def iris(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6258c4``."""
        return cls(0x6258c4)

    @classmethod
    def light_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff474c``."""
        return cls(0xff474c)

    @classmethod
    def purpley_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x947e94``."""
        return cls(0x947e94)

    @classmethod
    def fire_engine_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe0002``."""
        return cls(0xfe0002)

    @classmethod
    def camel(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc69f59``."""
        return cls(0xc69f59)

    @classmethod
    def vivid_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x152eff``."""
        return cls(0x152eff)

    @classmethod
    def lightgreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76ff7b``."""
        return cls(0x76ff7b)

    @classmethod
    def sky(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x82cafc``."""
        return cls(0x82cafc)

    @classmethod
    def pig_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe78ea5``."""
        return cls(0xe78ea5)

    @classmethod
    def ultramarine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2000b1``."""
        return cls(0x2000b1)

    @classmethod
    def dark_gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb59410``."""
        return cls(0xb59410)

    @classmethod
    def brick(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa03623``."""
        return cls(0xa03623)

    @classmethod
    def electric_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaa23ff``."""
        return cls(0xaa23ff)

    @classmethod
    def diarrhea(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9f8303``."""
        return cls(0x9f8303)

    @classmethod
    def dark_maroon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3c0008``."""
        return cls(0x3c0008)

    @classmethod
    def light_navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2e5a88``."""
        return cls(0x2e5a88)

    @classmethod
    def light_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfa5ff7``."""
        return cls(0xfa5ff7)

    @classmethod
    def kelly_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02ab2e``."""
        return cls(0x02ab2e)

    @classmethod
    def mustard_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac7e04``."""
        return cls(0xac7e04)

    @classmethod
    def green_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x544e03``."""
        return cls(0x544e03)

    @classmethod
    def pea_soup(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x929901``."""
        return cls(0x929901)

    @classmethod
    def orange_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffad01``."""
        return cls(0xffad01)

    @classmethod
    def dull_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x84597e``."""
        return cls(0x84597e)

    @classmethod
    def macaroni_and_cheese(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xefb435``."""
        return cls(0xefb435)

    @classmethod
    def pale_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xeecffe``."""
        return cls(0xeecffe)

    @classmethod
    def light_seafoam_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa7ffb5``."""
        return cls(0xa7ffb5)

    @classmethod
    def auburn(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9a3001``."""
        return cls(0x9a3001)

    @classmethod
    def electric_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x21fc0d``."""
        return cls(0x21fc0d)

    @classmethod
    def dark_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb5485d``."""
        return cls(0xb5485d)

    @classmethod
    def grass_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3f9b0b``."""
        return cls(0x3f9b0b)

    @classmethod
    def greenish_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00fbb0``."""
        return cls(0x00fbb0)

    @classmethod
    def brown_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb96902``."""
        return cls(0xb96902)

    @classmethod
    def deep_sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0d75f8``."""
        return cls(0x0d75f8)

    @classmethod
    def dark_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x363737``."""
        return cls(0x363737)

    @classmethod
    def shit_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7b5804``."""
        return cls(0x7b5804)

    @classmethod
    def bluey_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6241c7``."""
        return cls(0x6241c7)

    @classmethod
    def bright_aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0bf9ea``."""
        return cls(0x0bf9ea)

    @classmethod
    def off_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6ba353``."""
        return cls(0x6ba353)

    @classmethod
    def orange_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff6f52``."""
        return cls(0xff6f52)

    @classmethod
    def deep_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x017374``."""
        return cls(0x017374)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0343df``."""
        return cls(0x0343df)

    @classmethod
    def sunflower(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffc512``."""
        return cls(0xffc512)

    @classmethod
    def dark_forest_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x002d04``."""
        return cls(0x002d04)

    @classmethod
    def teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x029386``."""
        return cls(0x029386)

    @classmethod
    def dirty_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xca7b80``."""
        return cls(0xca7b80)

    @classmethod
    def french_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x436bad``."""
        return cls(0x436bad)

    @classmethod
    def wine_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7b0323``."""
        return cls(0x7b0323)

    @classmethod
    def light_indigo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6d5acf``."""
        return cls(0x6d5acf)

    @classmethod
    def bluish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2976bb``."""
        return cls(0x2976bb)

    @classmethod
    def baby_shit_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x889717``."""
        return cls(0x889717)

    @classmethod
    def squash(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf2ab15``."""
        return cls(0xf2ab15)

    @classmethod
    def cobalt_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x030aa7``."""
        return cls(0x030aa7)

    @classmethod
    def greyish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5e819d``."""
        return cls(0x5e819d)

    @classmethod
    def lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaaff32``."""
        return cls(0xaaff32)

    @classmethod
    def blue_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x137e6d``."""
        return cls(0x137e6d)

    @classmethod
    def very_light_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf6cefc``."""
        return cls(0xf6cefc)

    @classmethod
    def blue_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x607c8e``."""
        return cls(0x607c8e)

    @classmethod
    def bright_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01f9c6``."""
        return cls(0x01f9c6)

    @classmethod
    def tealish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x24bca8``."""
        return cls(0x24bca8)

    @classmethod
    def very_pale_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcffdbc``."""
        return cls(0xcffdbc)

    @classmethod
    def greeny_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc6f808``."""
        return cls(0xc6f808)

    @classmethod
    def sand_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcba560``."""
        return cls(0xcba560)

    @classmethod
    def pine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2b5d34``."""
        return cls(0x2b5d34)

    @classmethod
    def dandelion(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfedf08``."""
        return cls(0xfedf08)

    @classmethod
    def pale_olive(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb9cc81``."""
        return cls(0xb9cc81)

    @classmethod
    def swamp_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x748500``."""
        return cls(0x748500)

    @classmethod
    def brick_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8f1402``."""
        return cls(0x8f1402)

    @classmethod
    def greenish_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcdfd02``."""
        return cls(0xcdfd02)

    @classmethod
    def tree_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2a7e19``."""
        return cls(0x2a7e19)

    @classmethod
    def poop(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f5e00``."""
        return cls(0x7f5e00)

    @classmethod
    def blue_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2242c7``."""
        return cls(0x2242c7)

    @classmethod
    def brown_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8d8468``."""
        return cls(0x8d8468)

    @classmethod
    def neon_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbc13fe``."""
        return cls(0xbc13fe)

    @classmethod
    def dark_olive(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x373e02``."""
        return cls(0x373e02)

    @classmethod
    def bright_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe01b1``."""
        return cls(0xfe01b1)

    @classmethod
    def light_moss_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa6c875``."""
        return cls(0xa6c875)

    @classmethod
    def lemon_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbffe28``."""
        return cls(0xbffe28)

    @classmethod
    def deep_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc74767``."""
        return cls(0xc74767)

    @classmethod
    def dark_mauve(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x874c62``."""
        return cls(0x874c62)

    @classmethod
    def purple_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x673a3f``."""
        return cls(0x673a3f)

    @classmethod
    def dark_lime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7ebd01``."""
        return cls(0x7ebd01)

    @classmethod
    def soft_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdb0c0``."""
        return cls(0xfdb0c0)

    @classmethod
    def chocolate(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3d1c02``."""
        return cls(0x3d1c02)

    @classmethod
    def grape_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5d1451``."""
        return cls(0x5d1451)

    @classmethod
    def purple_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x990147``."""
        return cls(0x990147)

    @classmethod
    def greenish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x40a368``."""
        return cls(0x40a368)

    @classmethod
    def cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00ffff``."""
        return cls(0x00ffff)

    @classmethod
    def dark_pastel_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x56ae57``."""
        return cls(0x56ae57)

    @classmethod
    def pale_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd767ad``."""
        return cls(0xd767ad)

    @classmethod
    def shit_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x758000``."""
        return cls(0x758000)

    @classmethod
    def faded_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf0944d``."""
        return cls(0xf0944d)

    @classmethod
    def light_green_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x56fca2``."""
        return cls(0x56fca2)

    @classmethod
    def pastel_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa2bffe``."""
        return cls(0xa2bffe)

    @classmethod
    def terracotta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xca6641``."""
        return cls(0xca6641)

    @classmethod
    def purpleish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6140ef``."""
        return cls(0x6140ef)

    @classmethod
    def ice_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd7fffe``."""
        return cls(0xd7fffe)

    @classmethod
    def dark_mint_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x20c073``."""
        return cls(0x20c073)

    @classmethod
    def water_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0e87cc``."""
        return cls(0x0e87cc)

    @classmethod
    def light_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffe7a``."""
        return cls(0xfffe7a)

    @classmethod
    def pinkish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb17261``."""
        return cls(0xb17261)

    @classmethod
    def off_white(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffe4``."""
        return cls(0xffffe4)

    @classmethod
    def greyish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x82a67d``."""
        return cls(0x82a67d)

    @classmethod
    def fluorescent_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x08ff08``."""
        return cls(0x08ff08)

    @classmethod
    def deep_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdc4d01``."""
        return cls(0xdc4d01)

    @classmethod
    def medium_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7d7f7c``."""
        return cls(0x7d7f7c)

    @classmethod
    def white(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffff``."""
        return cls(0xffffff)

    @classmethod
    def lime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x89fe05``."""
        return cls(0x89fe05)

    @classmethod
    def merlot(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x730039``."""
        return cls(0x730039)

    @classmethod
    def desert(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xccad60``."""
        return cls(0xccad60)

    @classmethod
    def lipstick_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc0022f``."""
        return cls(0xc0022f)

    @classmethod
    def strawberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfb2943``."""
        return cls(0xfb2943)

    @classmethod
    def pale_aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb8ffeb``."""
        return cls(0xb8ffeb)

    @classmethod
    def sandy_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc4a661``."""
        return cls(0xc4a661)

    @classmethod
    def lemon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdff52``."""
        return cls(0xfdff52)

    @classmethod
    def minty_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0bf77d``."""
        return cls(0x0bf77d)

    @classmethod
    def dark_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x84b701``."""
        return cls(0x84b701)

    @classmethod
    def gunmetal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x536267``."""
        return cls(0x536267)

    @classmethod
    def darkish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x014182``."""
        return cls(0x014182)

    @classmethod
    def periwinkle(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8e82fe``."""
        return cls(0x8e82fe)

    @classmethod
    def sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x75bbfd``."""
        return cls(0x75bbfd)

    @classmethod
    def navy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01153e``."""
        return cls(0x01153e)

    @classmethod
    def blue_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5729ce``."""
        return cls(0x5729ce)

    @classmethod
    def pale_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffff84``."""
        return cls(0xffff84)

    @classmethod
    def orangish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf43605``."""
        return cls(0xf43605)

    @classmethod
    def dark_khaki(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9b8f55``."""
        return cls(0x9b8f55)

    @classmethod
    def powder_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb1d1fc``."""
        return cls(0xb1d1fc)

    @classmethod
    def blue_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5d06e9``."""
        return cls(0x5d06e9)

    @classmethod
    def sickly_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd0e429``."""
        return cls(0xd0e429)

    @classmethod
    def slime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x99cc04``."""
        return cls(0x99cc04)

    @classmethod
    def sickly_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x94b21c``."""
        return cls(0x94b21c)

    @classmethod
    def brownish_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb7723``."""
        return cls(0xcb7723)

    @classmethod
    def aubergine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3d0734``."""
        return cls(0x3d0734)

    @classmethod
    def forest(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0b5509``."""
        return cls(0x0b5509)

    @classmethod
    def light_olive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa4be5c``."""
        return cls(0xa4be5c)

    @classmethod
    def dirty_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3f829d``."""
        return cls(0x3f829d)

    @classmethod
    def purplish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb0054b``."""
        return cls(0xb0054b)

    @classmethod
    def parchment(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfefcaf``."""
        return cls(0xfefcaf)

    @classmethod
    def cornflower_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5170d7``."""
        return cls(0x5170d7)

    @classmethod
    def yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffff14``."""
        return cls(0xffff14)

    @classmethod
    def dark_taupe(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f684e``."""
        return cls(0x7f684e)

    @classmethod
    def deep_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x490648``."""
        return cls(0x490648)

    @classmethod
    def dark_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x045c5a``."""
        return cls(0x045c5a)

    @classmethod
    def dirt_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x836539``."""
        return cls(0x836539)

    @classmethod
    def indigo_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3a18b1``."""
        return cls(0x3a18b1)

    @classmethod
    def light_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffc5cb``."""
        return cls(0xffc5cb)

    @classmethod
    def sea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x53fca1``."""
        return cls(0x53fca1)

    @classmethod
    def muted_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5fa052``."""
        return cls(0x5fa052)

    @classmethod
    def terra_cotta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc9643b``."""
        return cls(0xc9643b)

    @classmethod
    def candy_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff63e9``."""
        return cls(0xff63e9)

    @classmethod
    def ugly_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd0c101``."""
        return cls(0xd0c101)

    @classmethod
    def darkish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x751973``."""
        return cls(0x751973)

    @classmethod
    def stone(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xada587``."""
        return cls(0xada587)

    @classmethod
    def pink_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf5054f``."""
        return cls(0xf5054f)

    @classmethod
    def seaweed(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x18d17b``."""
        return cls(0x18d17b)

    @classmethod
    def reddish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc44240``."""
        return cls(0xc44240)

    @classmethod
    def earth(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa2653e``."""
        return cls(0xa2653e)

    @classmethod
    def maroon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x650021``."""
        return cls(0x650021)

    @classmethod
    def putty(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbeae8a``."""
        return cls(0xbeae8a)

    @classmethod
    def muddy_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbfac05``."""
        return cls(0xbfac05)

    @classmethod
    def very_light_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd1ffbd``."""
        return cls(0xd1ffbd)

    @classmethod
    def mustard_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd2bd0a``."""
        return cls(0xd2bd0a)

    @classmethod
    def bright_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbe03fd``."""
        return cls(0xbe03fd)

    @classmethod
    def purplish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x94568c``."""
        return cls(0x94568c)

    @classmethod
    def kermit_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5cb200``."""
        return cls(0x5cb200)

    @classmethod
    def raw_sienna(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9a6200``."""
        return cls(0x9a6200)

    @classmethod
    def orchid(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc875c4``."""
        return cls(0xc875c4)

    @classmethod
    def darkish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x287c37``."""
        return cls(0x287c37)

    @classmethod
    def yellowish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfaee66``."""
        return cls(0xfaee66)

    @classmethod
    def dark_yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x728f02``."""
        return cls(0x728f02)

    @classmethod
    def butter_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffd74``."""
        return cls(0xfffd74)

    @classmethod
    def celery(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc1fd95``."""
        return cls(0xc1fd95)

    @classmethod
    def tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd1b26f``."""
        return cls(0xd1b26f)

    @classmethod
    def denim_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3b5b92``."""
        return cls(0x3b5b92)

    @classmethod
    def pale_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffcfdc``."""
        return cls(0xffcfdc)

    @classmethod
    def medium_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f5112``."""
        return cls(0x7f5112)

    @classmethod
    def clay_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb2713d``."""
        return cls(0xb2713d)

    @classmethod
    def leather(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac7434``."""
        return cls(0xac7434)

    @classmethod
    def shit(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f5f00``."""
        return cls(0x7f5f00)

    @classmethod
    def adobe(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbd6c48``."""
        return cls(0xbd6c48)

    @classmethod
    def lavender_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8b88f8``."""
        return cls(0x8b88f8)

    @classmethod
    def slate_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x658d6d``."""
        return cls(0x658d6d)

    @classmethod
    def very_dark_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x000133``."""
        return cls(0x000133)

    @classmethod
    def midnight_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x020035``."""
        return cls(0x020035)

    @classmethod
    def light_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x95d0fc``."""
        return cls(0x95d0fc)

    @classmethod
    def canary(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdff63``."""
        return cls(0xfdff63)

    @classmethod
    def greyish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa8a495``."""
        return cls(0xa8a495)

    @classmethod
    def army_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4b5d16``."""
        return cls(0x4b5d16)

    @classmethod
    def sap_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5c8b15``."""
        return cls(0x5c8b15)

    @classmethod
    def ivory(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffcb``."""
        return cls(0xffffcb)

    @classmethod
    def darkish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa90308``."""
        return cls(0xa90308)

    @classmethod
    def robin_egg_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8af1fe``."""
        return cls(0x8af1fe)

    @classmethod
    def light_bright_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x53fe5c``."""
        return cls(0x53fe5c)

    @classmethod
    def deep_aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x08787f``."""
        return cls(0x08787f)

    @classmethod
    def pumpkin_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfb7d07``."""
        return cls(0xfb7d07)

    @classmethod
    def sage(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x87ae73``."""
        return cls(0x87ae73)

    @classmethod
    def ochre(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbf9005``."""
        return cls(0xbf9005)

    @classmethod
    def gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdbb40c``."""
        return cls(0xdbb40c)

    @classmethod
    def dark_grey_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x29465b``."""
        return cls(0x29465b)

    @classmethod
    def grey_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc3909b``."""
        return cls(0xc3909b)

    @classmethod
    def dark_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x840000``."""
        return cls(0x840000)

    @classmethod
    def orange_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbe6400``."""
        return cls(0xbe6400)

    @classmethod
    def teal_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x25a36f``."""
        return cls(0x25a36f)

    @classmethod
    def greyish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x887191``."""
        return cls(0x887191)

    @classmethod
    def creme(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffb6``."""
        return cls(0xffffb6)

    @classmethod
    def bright_light_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2dfe54``."""
        return cls(0x2dfe54)

    @classmethod
    def muted_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd1768f``."""
        return cls(0xd1768f)

    @classmethod
    def dark_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x014d4e``."""
        return cls(0x014d4e)

    @classmethod
    def faded_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xde9dac``."""
        return cls(0xde9dac)

    @classmethod
    def apple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6ecb3c``."""
        return cls(0x6ecb3c)

    @classmethod
    def ocher(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbf9b0c``."""
        return cls(0xbf9b0c)

    @classmethod
    def dusky_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcc7a8b``."""
        return cls(0xcc7a8b)

    @classmethod
    def pale_peach(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffe5ad``."""
        return cls(0xffe5ad)

    @classmethod
    def ocean_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3d9973``."""
        return cls(0x3d9973)

    @classmethod
    def bright_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0165fc``."""
        return cls(0x0165fc)

    @classmethod
    def bright_olive(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9cbb04``."""
        return cls(0x9cbb04)

    @classmethod
    def bright_turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0ffef9``."""
        return cls(0x0ffef9)

    @classmethod
    def almost_black(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x070d0d``."""
        return cls(0x070d0d)

    @classmethod
    def lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc79fef``."""
        return cls(0xc79fef)

    @classmethod
    def cobalt(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1e488f``."""
        return cls(0x1e488f)

    @classmethod
    def pastel_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffbacd``."""
        return cls(0xffbacd)

    @classmethod
    def ugly_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa442a0``."""
        return cls(0xa442a0)

    @classmethod
    def poison_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x40fd14``."""
        return cls(0x40fd14)

    @classmethod
    def dark_peach(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xde7e5d``."""
        return cls(0xde7e5d)

    @classmethod
    def aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x13eac9``."""
        return cls(0x13eac9)

    @classmethod
    def cement(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa5a391``."""
        return cls(0xa5a391)

    @classmethod
    def eggshell_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc4fff7``."""
        return cls(0xc4fff7)

    @classmethod
    def hot_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x25ff29``."""
        return cls(0x25ff29)

    @classmethod
    def berry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x990f4b``."""
        return cls(0x990f4b)

    @classmethod
    def indian_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x850e04``."""
        return cls(0x850e04)

    @classmethod
    def deep_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x410200``."""
        return cls(0x410200)

    @classmethod
    def heather(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa484ac``."""
        return cls(0xa484ac)

    @classmethod
    def fawn(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcfaf7b``."""
        return cls(0xcfaf7b)

    @classmethod
    def pear(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcbf85f``."""
        return cls(0xcbf85f)

    @classmethod
    def pure_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0203e2``."""
        return cls(0x0203e2)

    @classmethod
    def greeny_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7ea07a``."""
        return cls(0x7ea07a)

    @classmethod
    def light_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdaa48``."""
        return cls(0xfdaa48)

    @classmethod
    def light_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdfc5fe``."""
        return cls(0xdfc5fe)

    @classmethod
    def dried_blood(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4b0101``."""
        return cls(0x4b0101)

    @classmethod
    def banana_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfafe4b``."""
        return cls(0xfafe4b)

    @classmethod
    def carnation(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd798f``."""
        return cls(0xfd798f)

    @classmethod
    def tiffany_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7bf2da``."""
        return cls(0x7bf2da)

    @classmethod
    def light_sage(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbcecac``."""
        return cls(0xbcecac)

    @classmethod
    def light_pea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc4fe82``."""
        return cls(0xc4fe82)

    @classmethod
    def grey_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x789b73``."""
        return cls(0x789b73)

    @classmethod
    def muddy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x657432``."""
        return cls(0x657432)

    @classmethod
    def hazel(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8e7618``."""
        return cls(0x8e7618)

    @classmethod
    def pink_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xef1de7``."""
        return cls(0xef1de7)

    @classmethod
    def very_light_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd5ffff``."""
        return cls(0xd5ffff)

    @classmethod
    def lipstick(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd5174e``."""
        return cls(0xd5174e)

    @classmethod
    def dark_sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x448ee4``."""
        return cls(0x448ee4)

    @classmethod
    def bright_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff5b00``."""
        return cls(0xff5b00)

    @classmethod
    def carolina_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8ab8fe``."""
        return cls(0x8ab8fe)

    @classmethod
    def mulberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x920a4e``."""
        return cls(0x920a4e)

    @classmethod
    def twilight_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0a437a``."""
        return cls(0x0a437a)

    @classmethod
    def kiwi(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9cef43``."""
        return cls(0x9cef43)

    @classmethod
    def algae(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x54ac68``."""
        return cls(0x54ac68)

    @classmethod
    def light_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffd1df``."""
        return cls(0xffd1df)

    @classmethod
    def spearmint(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1ef876``."""
        return cls(0x1ef876)

    @classmethod
    def pale_gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdde6c``."""
        return cls(0xfdde6c)

    @classmethod
    def pale_light_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb1fc99``."""
        return cls(0xb1fc99)

    @classmethod
    def bluish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x10a674``."""
        return cls(0x10a674)

    @classmethod
    def periwinkle_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8f99fb``."""
        return cls(0x8f99fb)

    @classmethod
    def green_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb5ce08``."""
        return cls(0xb5ce08)

    @classmethod
    def sienna(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa9561e``."""
        return cls(0xa9561e)

    @classmethod
    def carmine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9d0216``."""
        return cls(0x9d0216)

    @classmethod
    def snot_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9dc100``."""
        return cls(0x9dc100)

    @classmethod
    def aqua_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02d8e9``."""
        return cls(0x02d8e9)

    @classmethod
    def purple_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd725de``."""
        return cls(0xd725de)

    @classmethod
    def muted_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x805b87``."""
        return cls(0x805b87)

    @classmethod
    def deep_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x040273``."""
        return cls(0x040273)

    @classmethod
    def irish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x019529``."""
        return cls(0x019529)

    @classmethod
    def deep_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00555a``."""
        return cls(0x00555a)

    @classmethod
    def pale_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd0fefe``."""
        return cls(0xd0fefe)

    @classmethod
    def deep_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa0025c``."""
        return cls(0xa0025c)

    @classmethod
    def darkblue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x030764``."""
        return cls(0x030764)

    @classmethod
    def seafoam(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x80f9ad``."""
        return cls(0x80f9ad)

    @classmethod
    def muddy_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x886806``."""
        return cls(0x886806)

    @classmethod
    def ocean_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x03719c``."""
        return cls(0x03719c)

    @classmethod
    def bluey_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2bb179``."""
        return cls(0x2bb179)

    @classmethod
    def dark_sea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x11875d``."""
        return cls(0x11875d)

    @classmethod
    def fern_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x548d44``."""
        return cls(0x548d44)

    @classmethod
    def green_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x77926f``."""
        return cls(0x77926f)

    @classmethod
    def lime_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd0fe1d``."""
        return cls(0xd0fe1d)

    @classmethod
    def electric_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa8ff04``."""
        return cls(0xa8ff04)

    @classmethod
    def pea(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa4bf20``."""
        return cls(0xa4bf20)

    @classmethod
    def bluish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x703be7``."""
        return cls(0x703be7)

    @classmethod
    def poo_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x885f01``."""
        return cls(0x885f01)

    @classmethod
    def old_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc77986``."""
        return cls(0xc77986)

    @classmethod
    def fern(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x63a950``."""
        return cls(0x63a950)

    @classmethod
    def eggplant_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x430541``."""
        return cls(0x430541)

    @classmethod
    def drab_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x749551``."""
        return cls(0x749551)

    @classmethod
    def baby_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8cff9e``."""
        return cls(0x8cff9e)

    @classmethod
    def moss_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x658b38``."""
        return cls(0x658b38)

    @classmethod
    def spruce(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0a5f38``."""
        return cls(0x0a5f38)

    @classmethod
    def light_yellowish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc2ff89``."""
        return cls(0xc2ff89)

    @classmethod
    def light_beige(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffeb6``."""
        return cls(0xfffeb6)

    @classmethod
    def neon_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x04d9ff``."""
        return cls(0x04d9ff)

    @classmethod
    def dusty_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf0833a``."""
        return cls(0xf0833a)

    @classmethod
    def light_royal_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3a2efe``."""
        return cls(0x3a2efe)

    @classmethod
    def reddish_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf8481c``."""
        return cls(0xf8481c)

    @classmethod
    def british_racing_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x05480d``."""
        return cls(0x05480d)

    @classmethod
    def sea_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x047495``."""
        return cls(0x047495)

    @classmethod
    def true_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x010fcc``."""
        return cls(0x010fcc)

    @classmethod
    def brownish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9c6d57``."""
        return cls(0x9c6d57)

    @classmethod
    def yellow_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfcb001``."""
        return cls(0xfcb001)

    @classmethod
    def light_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x96f97b``."""
        return cls(0x96f97b)

    @classmethod
    def dark_seafoam_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3eaf76``."""
        return cls(0x3eaf76)

    @classmethod
    def light_maroon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa24857``."""
        return cls(0xa24857)

    @classmethod
    def pinkish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd648d7``."""
        return cls(0xd648d7)

    @classmethod
    def bland(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xafa88b``."""
        return cls(0xafa88b)

    @classmethod
    def brownish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6a6e09``."""
        return cls(0x6a6e09)

    @classmethod
    def greenish_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2afeb7``."""
        return cls(0x2afeb7)

    @classmethod
    def pale_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x82cbb2``."""
        return cls(0x82cbb2)

    @classmethod
    def light_bluish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76fda8``."""
        return cls(0x76fda8)

    @classmethod
    def mint_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8fff9f``."""
        return cls(0x8fff9f)

    @classmethod
    def amber(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfeb308``."""
        return cls(0xfeb308)

    @classmethod
    def rusty_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaf2f0d``."""
        return cls(0xaf2f0d)

    @classmethod
    def rich_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x720058``."""
        return cls(0x720058)

    @classmethod
    def sunshine_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffd37``."""
        return cls(0xfffd37)

    @classmethod
    def blue_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0f9b8e``."""
        return cls(0x0f9b8e)

    @classmethod
    def rich_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x021bf9``."""
        return cls(0x021bf9)

    @classmethod
    def terracota(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb6843``."""
        return cls(0xcb6843)

    @classmethod
    def purple_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe03fd8``."""
        return cls(0xe03fd8)

    @classmethod
    def light_mint(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb6ffbb``."""
        return cls(0xb6ffbb)

    @classmethod
    def green_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01c08d``."""
        return cls(0x01c08d)

    @classmethod
    def dark_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x856798``."""
        return cls(0x856798)

    @classmethod
    def cherry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcf0234``."""
        return cls(0xcf0234)

    @classmethod
    def saffron(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfeb209``."""
        return cls(0xfeb209)

    @classmethod
    def greenish_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbccb7a``."""
        return cls(0xbccb7a)

    @classmethod
    def dark_beige(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xac9362``."""
        return cls(0xac9362)

    @classmethod
    def mid_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x276ab3``."""
        return cls(0x276ab3)

    @classmethod
    def rosa(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe86a4``."""
        return cls(0xfe86a4)

    @classmethod
    def red_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x820747``."""
        return cls(0x820747)

    @classmethod
    def magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc20078``."""
        return cls(0xc20078)

    @classmethod
    def dusk_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x26538d``."""
        return cls(0x26538d)

    @classmethod
    def orangish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfc824a``."""
        return cls(0xfc824a)

    @classmethod
    def moss(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x769958``."""
        return cls(0x769958)

    @classmethod
    def dark_navy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x000435``."""
        return cls(0x000435)

    @classmethod
    def lemon_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xadf802``."""
        return cls(0xadf802)

    @classmethod
    def spring_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa9f971``."""
        return cls(0xa9f971)

    @classmethod
    def jade_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2baf6a``."""
        return cls(0x2baf6a)

    @classmethod
    def purpleish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x98568d``."""
        return cls(0x98568d)

    @classmethod
    def hot_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff028d``."""
        return cls(0xff028d)

    @classmethod
    def electric_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff0490``."""
        return cls(0xff0490)

    @classmethod
    def shocking_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe02a2``."""
        return cls(0xfe02a2)

    @classmethod
    def goldenrod(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfac205``."""
        return cls(0xfac205)

    @classmethod
    def puce(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa57e52``."""
        return cls(0xa57e52)

    @classmethod
    def dark_salmon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc85a53``."""
        return cls(0xc85a53)

    @classmethod
    def pale_lime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb1ff65``."""
        return cls(0xb1ff65)

    @classmethod
    def pale_lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe4cbff``."""
        return cls(0xe4cbff)

    @classmethod
    def faded_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x658cbb``."""
        return cls(0x658cbb)

    @classmethod
    def light_navy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x155084``."""
        return cls(0x155084)

    @classmethod
    def burnt_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd5ab09``."""
        return cls(0xd5ab09)

    @classmethod
    def dodger_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3e82fc``."""
        return cls(0x3e82fc)

    @classmethod
    def jungle_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x048243``."""
        return cls(0x048243)

    @classmethod
    def red_wine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8c0034``."""
        return cls(0x8c0034)

    @classmethod
    def primary_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0804f9``."""
        return cls(0x0804f9)

    @classmethod
    def grass(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5cac2d``."""
        return cls(0x5cac2d)

    @classmethod
    def ocean(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x017b92``."""
        return cls(0x017b92)

    @classmethod
    def cranberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9e003a``."""
        return cls(0x9e003a)

    @classmethod
    def dark_blue_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1f3b4d``."""
        return cls(0x1f3b4d)

    @classmethod
    def very_pale_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd6fffe``."""
        return cls(0xd6fffe)

    @classmethod
    def medium_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x39ad48``."""
        return cls(0x39ad48)

    @classmethod
    def bright_sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02ccfe``."""
        return cls(0x02ccfe)

    @classmethod
    def grapefruit(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfd5956``."""
        return cls(0xfd5956)

    @classmethod
    def camo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f8f4e``."""
        return cls(0x7f8f4e)

    @classmethod
    def turquoise_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x04f489``."""
        return cls(0x04f489)

    @classmethod
    def dark_green_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1f6357``."""
        return cls(0x1f6357)

    @classmethod
    def royal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0c1793``."""
        return cls(0x0c1793)

    @classmethod
    def tomato(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xef4026``."""
        return cls(0xef4026)

    @classmethod
    def avocado_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x87a922``."""
        return cls(0x87a922)

    @classmethod
    def seafoam_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7af9ab``."""
        return cls(0x7af9ab)

    @classmethod
    def dark_plum(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3f012c``."""
        return cls(0x3f012c)

    @classmethod
    def ruby(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xca0147``."""
        return cls(0xca0147)

    @classmethod
    def brick_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc14a09``."""
        return cls(0xc14a09)

    @classmethod
    def greenblue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x23c48b``."""
        return cls(0x23c48b)

    @classmethod
    def purplish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6b4247``."""
        return cls(0x6b4247)

    @classmethod
    def mahogany(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4a0100``."""
        return cls(0x4a0100)

    @classmethod
    def medium_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf36196``."""
        return cls(0xf36196)

    @classmethod
    def greenish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0b8b87``."""
        return cls(0x0b8b87)

    @classmethod
    def robins_egg_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x98eff9``."""
        return cls(0x98eff9)

    @classmethod
    def greenish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x696112``."""
        return cls(0x696112)

    @classmethod
    def purplish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x601ef9``."""
        return cls(0x601ef9)

    @classmethod
    def baby_shit_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad900d``."""
        return cls(0xad900d)

    @classmethod
    def ugly_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x31668a``."""
        return cls(0x31668a)

    @classmethod
    def yellowish_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffab0f``."""
        return cls(0xffab0f)

    @classmethod
    def avocado(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x90b134``."""
        return cls(0x90b134)

    @classmethod
    def frog_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x58bc08``."""
        return cls(0x58bc08)

    @classmethod
    def grey_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x86a17d``."""
        return cls(0x86a17d)

    @classmethod
    def yellowy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbff128``."""
        return cls(0xbff128)

    @classmethod
    def navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x001146``."""
        return cls(0x001146)

    @classmethod
    def light_aqua(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8cffdb``."""
        return cls(0x8cffdb)

    @classmethod
    def pale_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc7fdb5``."""
        return cls(0xc7fdb5)

    @classmethod
    def pale_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xceaefa``."""
        return cls(0xceaefa)

    @classmethod
    def faded_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd3494e``."""
        return cls(0xd3494e)

    @classmethod
    def reddish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe2c54``."""
        return cls(0xfe2c54)

    @classmethod
    def light_seafoam(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa0febf``."""
        return cls(0xa0febf)

    @classmethod
    def forrest_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x154406``."""
        return cls(0x154406)

    @classmethod
    def very_light_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfff4f2``."""
        return cls(0xfff4f2)

    @classmethod
    def prussian_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x004577``."""
        return cls(0x004577)

    @classmethod
    def heliotrope(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd94ff5``."""
        return cls(0xd94ff5)

    @classmethod
    def pale(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfff9d0``."""
        return cls(0xfff9d0)

    @classmethod
    def algae_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x21c36f``."""
        return cls(0x21c36f)

    @classmethod
    def olive_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x645403``."""
        return cls(0x645403)

    @classmethod
    def barbie_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe46a5``."""
        return cls(0xfe46a5)

    @classmethod
    def vomit_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x89a203``."""
        return cls(0x89a203)

    @classmethod
    def soft_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6488ea``."""
        return cls(0x6488ea)

    @classmethod
    def vibrant_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0339f8``."""
        return cls(0x0339f8)

    @classmethod
    def brownish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9e3623``."""
        return cls(0x9e3623)

    @classmethod
    def evergreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x05472a``."""
        return cls(0x05472a)

    @classmethod
    def bright_cyan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x41fdfe``."""
        return cls(0x41fdfe)

    @classmethod
    def night_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x040348``."""
        return cls(0x040348)

    @classmethod
    def deep_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb0162``."""
        return cls(0xcb0162)

    @classmethod
    def tealish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0cdc73``."""
        return cls(0x0cdc73)

    @classmethod
    def light_sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc6fcff``."""
        return cls(0xc6fcff)

    @classmethod
    def neon_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0cff0c``."""
        return cls(0x0cff0c)

    @classmethod
    def blurple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5539cc``."""
        return cls(0x5539cc)

    @classmethod
    def weird_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3ae57f``."""
        return cls(0x3ae57f)

    @classmethod
    def dirty_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x734a65``."""
        return cls(0x734a65)

    @classmethod
    def light_lime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb9ff66``."""
        return cls(0xb9ff66)

    @classmethod
    def dark_seafoam(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1fb57a``."""
        return cls(0x1fb57a)

    @classmethod
    def reddish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x910951``."""
        return cls(0x910951)

    @classmethod
    def bright_yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9dff00``."""
        return cls(0x9dff00)

    @classmethod
    def rouge(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xab1239``."""
        return cls(0xab1239)

    @classmethod
    def raw_umber(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa75e09``."""
        return cls(0xa75e09)

    @classmethod
    def plum_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4e0550``."""
        return cls(0x4e0550)

    @classmethod
    def green_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0cb577``."""
        return cls(0x0cb577)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe50000``."""
        return cls(0xe50000)

    @classmethod
    def booger(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9bb53c``."""
        return cls(0x9bb53c)

    @classmethod
    def pumpkin(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xe17701``."""
        return cls(0xe17701)

    @classmethod
    def purpley_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5f34e7``."""
        return cls(0x5f34e7)

    @classmethod
    def dull_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd8863b``."""
        return cls(0xd8863b)

    @classmethod
    def dull_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbb3f3f``."""
        return cls(0xbb3f3f)

    @classmethod
    def pinkish(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xd46a7e``."""
        return cls(0xd46a7e)

    @classmethod
    def purpley_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc83cb9``."""
        return cls(0xc83cb9)

    @classmethod
    def light_blue_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb7c9e2``."""
        return cls(0xb7c9e2)

    @classmethod
    def deep_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x36013f``."""
        return cls(0x36013f)

    @classmethod
    def faded_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfeff7f``."""
        return cls(0xfeff7f)

    @classmethod
    def forest_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x06470c``."""
        return cls(0x06470c)

    @classmethod
    def lighter_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x75fd63``."""
        return cls(0x75fd63)

    @classmethod
    def dark_periwinkle(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x665fd1``."""
        return cls(0x665fd1)

    @classmethod
    def dull_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x74a662``."""
        return cls(0x74a662)

    @classmethod
    def black(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x000000``."""
        return cls(0x000000)

    @classmethod
    def deep_lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x966ebd``."""
        return cls(0x966ebd)

    @classmethod
    def old_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc87f89``."""
        return cls(0xc87f89)

    @classmethod
    def light_forest_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4f9153``."""
        return cls(0x4f9153)

    @classmethod
    def seafoam_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x78d1b6``."""
        return cls(0x78d1b6)

    @classmethod
    def bright_lime_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x65fe08``."""
        return cls(0x65fe08)

    @classmethod
    def manilla(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffa86``."""
        return cls(0xfffa86)

    @classmethod
    def light_greenish_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x63f7b4``."""
        return cls(0x63f7b4)

    @classmethod
    def perrywinkle(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8f8ce7``."""
        return cls(0x8f8ce7)

    @classmethod
    def bright_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff08e8``."""
        return cls(0xff08e8)

    @classmethod
    def marine_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01386a``."""
        return cls(0x01386a)

    @classmethod
    def green_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc9ff27``."""
        return cls(0xc9ff27)

    @classmethod
    def mossy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x638b27``."""
        return cls(0x638b27)

    @classmethod
    def turtle_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x75b84f``."""
        return cls(0x75b84f)

    @classmethod
    def yellowish_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfcfc81``."""
        return cls(0xfcfc81)

    @classmethod
    def coral(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfc5a50``."""
        return cls(0xfc5a50)

    @classmethod
    def asparagus(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x77ab56``."""
        return cls(0x77ab56)

    @classmethod
    def light_mauve(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc292a1``."""
        return cls(0xc292a1)

    @classmethod
    def light_olive(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xacbf69``."""
        return cls(0xacbf69)

    @classmethod
    def golden(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf5bf03``."""
        return cls(0xf5bf03)

    @classmethod
    def flat_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3c73a8``."""
        return cls(0x3c73a8)

    @classmethod
    def darkish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xda467d``."""
        return cls(0xda467d)

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x15b01a``."""
        return cls(0x15b01a)

    @classmethod
    def sepia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x985e2b``."""
        return cls(0x985e2b)

    @classmethod
    def ecru(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfeffca``."""
        return cls(0xfeffca)

    @classmethod
    def greeny_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x696006``."""
        return cls(0x696006)

    @classmethod
    def foam_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x90fda9``."""
        return cls(0x90fda9)

    @classmethod
    def military_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x667c3e``."""
        return cls(0x667c3e)

    @classmethod
    def rose_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf7879a``."""
        return cls(0xf7879a)

    @classmethod
    def dark_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00035b``."""
        return cls(0x00035b)

    @classmethod
    def bubblegum(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff6cb5``."""
        return cls(0xff6cb5)

    @classmethod
    def azul(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1d5dec``."""
        return cls(0x1d5dec)

    @classmethod
    def leaf_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5ca904``."""
        return cls(0x5ca904)

    @classmethod
    def scarlet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbe0119``."""
        return cls(0xbe0119)

    @classmethod
    def blue_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x758da3``."""
        return cls(0x758da3)

    @classmethod
    def yellowish_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb0dd16``."""
        return cls(0xb0dd16)

    @classmethod
    def bright_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffd01``."""
        return cls(0xfffd01)

    @classmethod
    def grape(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6c3461``."""
        return cls(0x6c3461)

    @classmethod
    def banana(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffff7e``."""
        return cls(0xffff7e)

    @classmethod
    def barney_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa00498``."""
        return cls(0xa00498)

    @classmethod
    def light_blue_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7efbb3``."""
        return cls(0x7efbb3)

    @classmethod
    def strong_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0c06f7``."""
        return cls(0x0c06f7)

    @classmethod
    def light_urple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb36ff6``."""
        return cls(0xb36ff6)

    @classmethod
    def bright_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad0afd``."""
        return cls(0xad0afd)

    @classmethod
    def purple_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x632de9``."""
        return cls(0x632de9)

    @classmethod
    def highlighter_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1bfc06``."""
        return cls(0x1bfc06)

    @classmethod
    def salmon_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe7b7c``."""
        return cls(0xfe7b7c)

    @classmethod
    def light_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xad8150``."""
        return cls(0xad8150)

    @classmethod
    def bluegrey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x85a3b2``."""
        return cls(0x85a3b2)

    @classmethod
    def darkgreen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x054907``."""
        return cls(0x054907)

    @classmethod
    def lichen(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8fb67b``."""
        return cls(0x8fb67b)

    @classmethod
    def egg_shell(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffcc4``."""
        return cls(0xfffcc4)

    @classmethod
    def browny_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6f6c0a``."""
        return cls(0x6f6c0a)

    @classmethod
    def brownish_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76424e``."""
        return cls(0x76424e)

    @classmethod
    def pinkish_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff724c``."""
        return cls(0xff724c)

    @classmethod
    def pale_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb790d4``."""
        return cls(0xb790d4)

    @classmethod
    def clear_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x247afd``."""
        return cls(0x247afd)

    @classmethod
    def raspberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb00149``."""
        return cls(0xb00149)

    @classmethod
    def dusky_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xba6873``."""
        return cls(0xba6873)

    @classmethod
    def ugly_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7a9703``."""
        return cls(0x7a9703)

    @classmethod
    def cloudy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xacc2d9``."""
        return cls(0xacc2d9)

    @classmethod
    def bright_light_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x26f7fd``."""
        return cls(0x26f7fd)

    @classmethod
    def dark_mint(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x48c072``."""
        return cls(0x48c072)

    @classmethod
    def pinky_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfc2647``."""
        return cls(0xfc2647)

    @classmethod
    def dusty_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc0737a``."""
        return cls(0xc0737a)

    @classmethod
    def lightish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe2f4a``."""
        return cls(0xfe2f4a)

    @classmethod
    def yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc0fb2d``."""
        return cls(0xc0fb2d)

    @classmethod
    def pastel_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcaa0ff``."""
        return cls(0xcaa0ff)

    @classmethod
    def yellowy_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xae8b0c``."""
        return cls(0xae8b0c)

    @classmethod
    def rust_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaa2704``."""
        return cls(0xaa2704)

    @classmethod
    def green_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x06b48b``."""
        return cls(0x06b48b)

    @classmethod
    def light_salmon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfea993``."""
        return cls(0xfea993)

    @classmethod
    def olive_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc2b709``."""
        return cls(0xc2b709)

    @classmethod
    def pale_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbefd73``."""
        return cls(0xbefd73)

    @classmethod
    def radioactive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2cfa1f``."""
        return cls(0x2cfa1f)

    @classmethod
    def light_lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xedc8ff``."""
        return cls(0xedc8ff)

    @classmethod
    def teal_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01889f``."""
        return cls(0x01889f)

    @classmethod
    def tea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbdf8a3``."""
        return cls(0xbdf8a3)

    @classmethod
    def bronze(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa87900``."""
        return cls(0xa87900)

    @classmethod
    def reddy_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6e1005``."""
        return cls(0x6e1005)

    @classmethod
    def dark_grass_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x388004``."""
        return cls(0x388004)

    @classmethod
    def peachy_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff9a8a``."""
        return cls(0xff9a8a)

    @classmethod
    def dirty_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcdc50a``."""
        return cls(0xcdc50a)

    @classmethod
    def tangerine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff9408``."""
        return cls(0xff9408)

    @classmethod
    def deep_lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8d5eb7``."""
        return cls(0x8d5eb7)

    @classmethod
    def umber(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb26400``."""
        return cls(0xb26400)

    @classmethod
    def olive_drab(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6f7632``."""
        return cls(0x6f7632)

    @classmethod
    def baby_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xca9bf7``."""
        return cls(0xca9bf7)

    @classmethod
    def cerise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xde0c62``."""
        return cls(0xde0c62)

    @classmethod
    def melon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff7855``."""
        return cls(0xff7855)

    @classmethod
    def burnt_sienna(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb04e0f``."""
        return cls(0xb04e0f)

    @classmethod
    def vibrant_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0add08``."""
        return cls(0x0add08)

    @classmethod
    def yellowish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9b7a01``."""
        return cls(0x9b7a01)

    @classmethod
    def shamrock(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01b44c``."""
        return cls(0x01b44c)

    @classmethod
    def brown_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb29705``."""
        return cls(0xb29705)

    @classmethod
    def tan_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa9be70``."""
        return cls(0xa9be70)

    @classmethod
    def dark_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x960056``."""
        return cls(0x960056)

    @classmethod
    def purplish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xce5dae``."""
        return cls(0xce5dae)

    @classmethod
    def grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x929591``."""
        return cls(0x929591)

    @classmethod
    def mud_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x60460f``."""
        return cls(0x60460f)

    @classmethod
    def pea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8eab12``."""
        return cls(0x8eab12)

    @classmethod
    def pink_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdb4bda``."""
        return cls(0xdb4bda)

    @classmethod
    def reddish_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7f2b0a``."""
        return cls(0x7f2b0a)

    @classmethod
    def blush_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfe828c``."""
        return cls(0xfe828c)

    @classmethod
    def light_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xaefd6c``."""
        return cls(0xaefd6c)

    @classmethod
    def hot_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf504c9``."""
        return cls(0xf504c9)

    @classmethod
    def poop_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6f7c00``."""
        return cls(0x6f7c00)

    @classmethod
    def swamp(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x698339``."""
        return cls(0x698339)

    @classmethod
    def faded_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7bb274``."""
        return cls(0x7bb274)

    @classmethod
    def yellow_ochre(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcb9d06``."""
        return cls(0xcb9d06)

    @classmethod
    def dust(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb2996e``."""
        return cls(0xb2996e)

    @classmethod
    def soft_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa66fb5``."""
        return cls(0xa66fb5)

    @classmethod
    def light_lavendar(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xefc0fe``."""
        return cls(0xefc0fe)

    @classmethod
    def dark_royal_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x02066f``."""
        return cls(0x02066f)

    @classmethod
    def violet_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa50055``."""
        return cls(0xa50055)

    @classmethod
    def rosy_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf6688e``."""
        return cls(0xf6688e)

    @classmethod
    def lighter_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa55af4``."""
        return cls(0xa55af4)

    @classmethod
    def eggshell(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffd4``."""
        return cls(0xffffd4)

    @classmethod
    def greyish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc88d94``."""
        return cls(0xc88d94)

    @classmethod
    def russet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa13905``."""
        return cls(0xa13905)

    @classmethod
    def purply(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x983fb2``."""
        return cls(0x983fb2)

    @classmethod
    def red_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8b2e16``."""
        return cls(0x8b2e16)

    @classmethod
    def off_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf1f33f``."""
        return cls(0xf1f33f)

    @classmethod
    def warm_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4b57db``."""
        return cls(0x4b57db)

    @classmethod
    def metallic_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4f738e``."""
        return cls(0x4f738e)

    @classmethod
    def golden_rod(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf9bc08``."""
        return cls(0xf9bc08)

    @classmethod
    def pale_olive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb1d27b``."""
        return cls(0xb1d27b)

    @classmethod
    def dusty_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb9484e``."""
        return cls(0xb9484e)

    @classmethod
    def light_plum(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9d5783``."""
        return cls(0x9d5783)

    @classmethod
    def lilac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xcea2fd``."""
        return cls(0xcea2fd)

    @classmethod
    def dusky_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x895b7b``."""
        return cls(0x895b7b)

    @classmethod
    def green_apple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5edc1f``."""
        return cls(0x5edc1f)

    @classmethod
    def hospital_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9be5aa``."""
        return cls(0x9be5aa)

    @classmethod
    def lavender_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xdd85d7``."""
        return cls(0xdd85d7)

    @classmethod
    def light_grey_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb7e1a1``."""
        return cls(0xb7e1a1)

    @classmethod
    def topaz(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x13bbaf``."""
        return cls(0x13bbaf)

    @classmethod
    def dull_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x876e4b``."""
        return cls(0x876e4b)

    @classmethod
    def steel(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x738595``."""
        return cls(0x738595)

    @classmethod
    def rose_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbe013c``."""
        return cls(0xbe013c)

    @classmethod
    def aquamarine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x04d8b2``."""
        return cls(0x04d8b2)

    @classmethod
    def midnight_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x280137``."""
        return cls(0x280137)

    @classmethod
    def grassy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x419c03``."""
        return cls(0x419c03)

    @classmethod
    def charcoal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x343837``."""
        return cls(0x343837)

    @classmethod
    def puke_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x947706``."""
        return cls(0x947706)

    @classmethod
    def pinkish_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf10c45``."""
        return cls(0xf10c45)

    @classmethod
    def cocoa(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x875f42``."""
        return cls(0x875f42)

    @classmethod
    def baby_poo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xab9004``."""
        return cls(0xab9004)

    @classmethod
    def orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf97306``."""
        return cls(0xf97306)

    @classmethod
    def salmon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff796c``."""
        return cls(0xff796c)

    @classmethod
    def ugly_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7d7103``."""
        return cls(0x7d7103)

    @classmethod
    def purple_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x866f85``."""
        return cls(0x866f85)

    @classmethod
    def olive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x677a04``."""
        return cls(0x677a04)

    @classmethod
    def dull_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xeedc5b``."""
        return cls(0xeedc5b)

    @classmethod
    def blueberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x464196``."""
        return cls(0x464196)

    @classmethod
    def neon_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff073a``."""
        return cls(0xff073a)

    @classmethod
    def peacock_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x016795``."""
        return cls(0x016795)

    @classmethod
    def snot(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xacbb0d``."""
        return cls(0xacbb0d)

    @classmethod
    def tea(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x65ab7c``."""
        return cls(0x65ab7c)

    @classmethod
    def purple_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5d21d0``."""
        return cls(0x5d21d0)

    @classmethod
    def liliac(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc48efd``."""
        return cls(0xc48efd)

    @classmethod
    def easter_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc071fe``."""
        return cls(0xc071fe)

    @classmethod
    def pale_grey(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfdfdfe``."""
        return cls(0xfdfdfe)

    @classmethod
    def electric_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0652ff``."""
        return cls(0x0652ff)

    @classmethod
    def dark_mustard(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa88905``."""
        return cls(0xa88905)

    @classmethod
    def pastel_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffe71``."""
        return cls(0xfffe71)

    @classmethod
    def off_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5684ae``."""
        return cls(0x5684ae)

    @classmethod
    def marine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x042e60``."""
        return cls(0x042e60)

    @classmethod
    def dark_navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00022e``."""
        return cls(0x00022e)

    @classmethod
    def blue_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5a06ef``."""
        return cls(0x5a06ef)

    @classmethod
    def pale_sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xbdf6fe``."""
        return cls(0xbdf6fe)

    @classmethod
    def violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9a0eea``."""
        return cls(0x9a0eea)

    @classmethod
    def mustard_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xa8b504``."""
        return cls(0xa8b504)

    @classmethod
    def light_sea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x98f6b0``."""
        return cls(0x98f6b0)

    @classmethod
    def yellow_brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb79400``."""
        return cls(0xb79400)

    @classmethod
    def pine_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0a481e``."""
        return cls(0x0a481e)

    @classmethod
    def velvet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x750851``."""
        return cls(0x750851)

    @classmethod
    def navy_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x35530a``."""
        return cls(0x35530a)

    @classmethod
    def custard(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfffd78``."""
        return cls(0xfffd78)

    @classmethod
    def yellow_tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffe36e``."""
        return cls(0xffe36e)

    @classmethod
    def poo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8f7303``."""
        return cls(0x8f7303)

    @classmethod
    def mud(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x735c12``."""
        return cls(0x735c12)

    @classmethod
    def vermillion(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf4320c``."""
        return cls(0xf4320c)

    @classmethod
    def copper(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb66325``."""
        return cls(0xb66325)

    @classmethod
    def easter_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8cfd7e``."""
        return cls(0x8cfd7e)

    @classmethod
    def sunflower_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffda03``."""
        return cls(0xffda03)

    @classmethod
    def dark_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x35063e``."""
        return cls(0x35063e)

    @classmethod
    def brownish_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xc27e79``."""
        return cls(0xc27e79)

    @classmethod
    def emerald(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x01a049``."""
        return cls(0x01a049)

    @classmethod
    def carnation_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xff7fa7``."""
        return cls(0xff7fa7)

    @classmethod
    def dusky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x475f94``."""
        return cls(0x475f94)

    @classmethod
    def turquoise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x06c2ac``."""
        return cls(0x06c2ac)

    @classmethod
    def robins_egg(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6dedfd``."""
        return cls(0x6dedfd)

    @classmethod
    def sapphire(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2138ab``."""
        return cls(0x2138ab)

    @classmethod
    def dusty_teal(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4c9085``."""
        return cls(0x4c9085)

    @classmethod
    def lawn_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x4da409``."""
        return cls(0x4da409)

    @classmethod
    def cerulean(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0485d1``."""
        return cls(0x0485d1)

    @classmethod
    def sick_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9db92c``."""
        return cls(0x9db92c)

    @classmethod
    def warm_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfb5581``."""
        return cls(0xfb5581)
