# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz

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

from enum import Enum

class ChannelType(Enum):
    text = 'text'
    voice = 'voice'

    def __str__(self):
        return self.value

class ServerRegion(Enum):
    us_west = 'us-west'
    us_east = 'us-east'
    us_south = 'us-south'
    us_central = 'us-central'
    singapore = 'singapore'
    london = 'london'
    sydney = 'sydney'
    amsterdam = 'amsterdam'
    frankfurt = 'frankfurt'

    def __str__(self):
        return self.value

class Status(Enum):
    online = 'online'
    offline = 'offline'
    idle = 'idle'

    def __str__(self):
        return self.value

class DefaultAvatar(Enum):
    blurple = "6debd47ed13483642cf09e832ed0bc1b"
    grey = "322c936a8c8be1b803cd94861bdfa868"
    green = "dd4dbc0016779df1378e7812eabaa04d"
    orange = "0e291f67c9274a1abdddeb3fd919cbaa"
    red = "1cbd08c76f8af6dddce02c5138971129"

    def __new__(cls, url):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        obj.url = url
        return obj

    def __str__(self):
        return self.name
