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


class crayon_colour(colour):
    """Represents a Discord role colour with crayon colour presets.

    """
    @classmethod
    def black(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x000000``."""
        return cls(0x000000)

    @classmethod
    def purple_mountains__majesty(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9D81BA``."""
        return cls(0x9D81BA)

    @classmethod
    def electric_lime(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCEFF1D``."""
        return cls(0xCEFF1D)

    @classmethod
    def chestnut(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xBC5D58``."""
        return cls(0xBC5D58)

    @classmethod
    def tumbleweed(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xDEAA88``."""
        return cls(0xDEAA88)

    @classmethod
    def wild_strawberry(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF43A4``."""
        return cls(0xFF43A4)

    @classmethod
    def shocking_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFB7EFD``."""
        return cls(0xFB7EFD)

    @classmethod
    def sunglow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFCF48``."""
        return cls(0xFFCF48)

    @classmethod
    def razzle_dazzle_rose(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF48D0``."""
        return cls(0xFF48D0)

    @classmethod
    def wisteria(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCDA4DE``."""
        return cls(0xCDA4DE)

    @classmethod
    def razzmatazz(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xE3256B``."""
        return cls(0xE3256B)

    @classmethod
    def wild_blue_yonder(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xA2ADD0``."""
        return cls(0xA2ADD0)

    @classmethod
    def laser_lemon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFEFE22``."""
        return cls(0xFEFE22)

    @classmethod
    def blush(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xDE5D83``."""
        return cls(0xDE5D83)

    @classmethod
    def blue_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0D98BA``."""
        return cls(0x0D98BA)

    @classmethod
    def blue_bell(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xA2A2D0``."""
        return cls(0xA2A2D0)

    @classmethod
    def fuzzy_wuzzy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCC6666``."""
        return cls(0xCC6666)

    @classmethod
    def fuchsia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC364C5``."""
        return cls(0xC364C5)

    @classmethod
    def gray(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x95918C``."""
        return cls(0x95918C)

    @classmethod
    def denim(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x2B6CC4``."""
        return cls(0x2B6CC4)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xEE204D``."""
        return cls(0xEE204D)

    @classmethod
    def yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFCE883``."""
        return cls(0xFCE883)

    @classmethod
    def peach(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFCFAB``."""
        return cls(0xFFCFAB)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1F75FE``."""
        return cls(0x1F75FE)

    @classmethod
    def green_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xF0E891``."""
        return cls(0xF0E891)

    @classmethod
    def screamin__green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x76FF7A``."""
        return cls(0x76FF7A)

    @classmethod
    def canary(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFFF99``."""
        return cls(0xFFFF99)

    @classmethod
    def caribbean_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x00CC99``."""
        return cls(0x00CC99)

    @classmethod
    def sepia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xA5694F``."""
        return cls(0xA5694F)

    @classmethod
    def almond(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xEFDECD``."""
        return cls(0xEFDECD)

    @classmethod
    def burnt_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF7F49``."""
        return cls(0xFF7F49)

    @classmethod
    def mango_tango(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF8243``."""
        return cls(0xFF8243)

    @classmethod
    def pine_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x158078``."""
        return cls(0x158078)

    @classmethod
    def silver(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCDC5C2``."""
        return cls(0xCDC5C2)

    @classmethod
    def fern(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x71BC78``."""
        return cls(0x71BC78)

    @classmethod
    def lavender(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFCB4D5``."""
        return cls(0xFCB4D5)

    @classmethod
    def orchid(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xE6A8D7``."""
        return cls(0xE6A8D7)

    @classmethod
    def sky_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x80DAEB``."""
        return cls(0x80DAEB)

    @classmethod
    def granny_smith_apple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xA8E4A0``."""
        return cls(0xA8E4A0)

    @classmethod
    def scarlet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFC2847``."""
        return cls(0xFC2847)

    @classmethod
    def brown(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xB4674D``."""
        return cls(0xB4674D)

    @classmethod
    def red_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF5349``."""
        return cls(0xFF5349)

    @classmethod
    def vivid_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8F509D``."""
        return cls(0x8F509D)

    @classmethod
    def yellow_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC5E384``."""
        return cls(0xC5E384)

    @classmethod
    def cadet_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xB0B7C6``."""
        return cls(0xB0B7C6)

    @classmethod
    def orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF7538``."""
        return cls(0xFF7538)

    @classmethod
    def neon_carrot(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFA343``."""
        return cls(0xFFA343)

    @classmethod
    def yellow_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFAE42``."""
        return cls(0xFFAE42)

    @classmethod
    def red_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC0448F``."""
        return cls(0xC0448F)

    @classmethod
    def carnation_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFAACC``."""
        return cls(0xFFAACC)

    @classmethod
    def turquoise_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x77DDE7``."""
        return cls(0x77DDE7)

    @classmethod
    def banana_mania(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFAE7B5``."""
        return cls(0xFAE7B5)

    @classmethod
    def magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xF664AF``."""
        return cls(0xF664AF)

    @classmethod
    def robin_s_egg_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1FCECB``."""
        return cls(0x1FCECB)

    @classmethod
    def eggplant(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6E5160``."""
        return cls(0x6E5160)

    @classmethod
    def white(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFFFFF``."""
        return cls(0xFFFFFF)

    @classmethod
    def purple_pizzazz(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFE4EDA``."""
        return cls(0xFE4EDA)

    @classmethod
    def shamrock(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x45CEA2``."""
        return cls(0x45CEA2)

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1CAC78``."""
        return cls(0x1CAC78)

    @classmethod
    def mountain_meadow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x30BA8F``."""
        return cls(0x30BA8F)

    @classmethod
    def sunset_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFD5E53``."""
        return cls(0xFD5E53)

    @classmethod
    def tickle_me_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFC89AC``."""
        return cls(0xFC89AC)

    @classmethod
    def manatee(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x979AAA``."""
        return cls(0x979AAA)

    @classmethod
    def desert_sand(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xEFCDB8``."""
        return cls(0xEFCDB8)

    @classmethod
    def indigo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x5D76CB``."""
        return cls(0x5D76CB)

    @classmethod
    def brick_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCB4154``."""
        return cls(0xCB4154)

    @classmethod
    def asparagus(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x87A96B``."""
        return cls(0x87A96B)

    @classmethod
    def blue_violet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7366BD``."""
        return cls(0x7366BD)

    @classmethod
    def gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xE7C697``."""
        return cls(0xE7C697)

    @classmethod
    def dandelion(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFDDB6D``."""
        return cls(0xFDDB6D)

    @classmethod
    def cotton_candy(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFBCD9``."""
        return cls(0xFFBCD9)

    @classmethod
    def bittersweet(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFD7C6E``."""
        return cls(0xFD7C6E)

    @classmethod
    def aquamarine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x78DBE2``."""
        return cls(0x78DBE2)

    @classmethod
    def purple_heart(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7442C8``."""
        return cls(0x7442C8)

    @classmethod
    def copper(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xDD9475``."""
        return cls(0xDD9475)

    @classmethod
    def pacific_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1CA9C9``."""
        return cls(0x1CA9C9)

    @classmethod
    def outrageous_orange(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF6E4A``."""
        return cls(0xFF6E4A)

    @classmethod
    def midnight_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1A4876``."""
        return cls(0x1A4876)

    @classmethod
    def cerulean(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1DACD6``."""
        return cls(0x1DACD6)

    @classmethod
    def sea_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x93DFB8``."""
        return cls(0x93DFB8)

    @classmethod
    def beaver(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9F8170``."""
        return cls(0x9F8170)

    @classmethod
    def wild_watermelon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFC6C85``."""
        return cls(0xFC6C85)

    @classmethod
    def cornflower(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x9ACEEB``."""
        return cls(0x9ACEEB)

    @classmethod
    def royal_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7851A9``."""
        return cls(0x7851A9)

    @classmethod
    def salmon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF9BAA``."""
        return cls(0xFF9BAA)

    @classmethod
    def unmellow_yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFFF66``."""
        return cls(0xFFFF66)

    @classmethod
    def plum(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8E4585``."""
        return cls(0x8E4585)

    @classmethod
    def mahogany(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCD4A4C``."""
        return cls(0xCD4A4C)

    @classmethod
    def raw_sienna(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xD68A59``."""
        return cls(0xD68A59)

    @classmethod
    def spring_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xECEABE``."""
        return cls(0xECEABE)

    @classmethod
    def cerise(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xDD4492``."""
        return cls(0xDD4492)

    @classmethod
    def tan(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFAA76C``."""
        return cls(0xFAA76C)

    @classmethod
    def jazzberry_jam(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCA3767``."""
        return cls(0xCA3767)

    @classmethod
    def periwinkle(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC5D0E6``."""
        return cls(0xC5D0E6)

    @classmethod
    def pink_sherbert(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xF78FA7``."""
        return cls(0xF78FA7)

    @classmethod
    def melon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFDBCB4``."""
        return cls(0xFDBCB4)

    @classmethod
    def jungle_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x3BB08F``."""
        return cls(0x3BB08F)

    @classmethod
    def hot_magenta(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF1DCE``."""
        return cls(0xFF1DCE)

    @classmethod
    def apricot(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFDD9B5``."""
        return cls(0xFDD9B5)

    @classmethod
    def navy_blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x1974D2``."""
        return cls(0x1974D2)

    @classmethod
    def goldenrod(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFCD975``."""
        return cls(0xFCD975)

    @classmethod
    def tropical_rain_forest(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x17806D``."""
        return cls(0x17806D)

    @classmethod
    def violet_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xF75394``."""
        return cls(0xF75394)

    @classmethod
    def vivid_tangerine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFA089``."""
        return cls(0xFFA089)

    @classmethod
    def olive_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xBAB86C``."""
        return cls(0xBAB86C)

    @classmethod
    def inchworm(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xB2EC5D``."""
        return cls(0xB2EC5D)

    @classmethod
    def forest_green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x6DAE81``."""
        return cls(0x6DAE81)

    @classmethod
    def macaroni_and_cheese(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFBD88``."""
        return cls(0xFFBD88)

    @classmethod
    def atomic_tangerine(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFA474``."""
        return cls(0xFFA474)

    @classmethod
    def maroon(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC8385A``."""
        return cls(0xC8385A)

    @classmethod
    def antique_brass(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xCD9575``."""
        return cls(0xCD9575)

    @classmethod
    def timberwolf(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xDBD7D2``."""
        return cls(0xDBD7D2)

    @classmethod
    def outer_space(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x414A4C``."""
        return cls(0x414A4C)

    @classmethod
    def violet_purple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x926EAE``."""
        return cls(0x926EAE)

    @classmethod
    def shadow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x8A795D``."""
        return cls(0x8A795D)

    @classmethod
    def radical_red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFF496C``."""
        return cls(0xFF496C)

    @classmethod
    def burnt_sienna(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xEA7E5D``."""
        return cls(0xEA7E5D)

    @classmethod
    def mauvelous(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xEF98AA``."""
        return cls(0xEF98AA)

    @classmethod
    def pink_flamingo(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFC74FD``."""
        return cls(0xFC74FD)

    @classmethod
    def piggy_pink(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFDDDE6``."""
        return cls(0xFDDDE6)

