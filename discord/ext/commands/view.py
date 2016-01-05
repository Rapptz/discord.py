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

from .errors import BadArgument

class StringView:
    def __init__(self, buffer):
        self.index = 0
        self.buffer = buffer
        self.end = len(buffer)
        self.previous = 0

    @property
    def current(self):
        return None if self.eof else self.buffer[self.index]

    @property
    def eof(self):
        return self.index >= self.end

    def undo(self):
        self.index = self.previous

    def skip_ws(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if not current.isspace():
                    break
                pos += 1
            except IndexError:
                break

        self.previous = self.index
        self.index += pos
        return self.previous != self.index

    def skip_string(self, string):
        strlen = len(string)
        if self.buffer[self.index:self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def read_rest(self):
        result = self.buffer[self.index:]
        self.previous = self.index
        self.index = self.end
        return result

    def read(self, n):
        result = self.buffer[self.index:self.index + n]
        self.previous = self.index
        self.index += n
        return result

    def get(self):
        try:
            result = self.buffer[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1
        return result

    def get_word(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if current.isspace():
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index:self.index + pos]
        self.index += pos
        return result

    def __repr__(self):
        return '<StringView pos: {0.index} prev: {0.previous} end: {0.end} eof: {0.eof}>'.format(self)

# Parser

def quoted_word(view):
    current = view.current

    if current is None:
        return None

    is_quoted = current == '"'
    result = [] if is_quoted else [current]

    while not view.eof:
        current = view.get()
        if not current:
            if is_quoted:
                # unexpected EOF
                raise BadArgument('Expected closing "')
            return ''.join(result)

        # currently we accept strings in the format of "hello world"
        # to embed a quote inside the string you must escape it: "a \"world\""
        if current == '\\':
            next_char = view.get()
            if not next_char:
                # string ends with \ and no character after it
                if is_quoted:
                    # if we're quoted then we're expecting a closing quote
                    raise BadArgument('Expected closing "')
                # if we aren't then we just let it through
                return ''.join(result)

            if next_char == '"':
                # escaped quote
                result.append('"')
            else:
                # different escape character, ignore it
                view.undo()
                result.append(current)
            continue

        # closing quote
        if current == '"':
            next_char = view.get()
            valid_eof = not next_char or next_char.isspace()
            if is_quoted:
                if not valid_eof:
                    raise BadArgument('Expected space after closing quotation')

                # we're quoted so it's okay
                return ''.join(result)
            else:
                # we aren't quoted
                raise BadArgument('Unexpected quote mark in non-quoted string')

        if current.isspace() and not is_quoted:
            # end of word found
            return ''.join(result)

        result.append(current)
