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

from typing import Optional

from .errors import UnexpectedQuoteError, InvalidEndOfQuotedStringError, ExpectedClosingQuoteError

# map from opening quotes to closing quotes
_quotes = {
    '"': '"',
    "‘": "’",
    "‚": "‛",
    "“": "”",
    "„": "‟",
    "⹂": "⹂",
    "「": "」",
    "『": "』",
    "〝": "〞",
    "﹁": "﹂",
    "﹃": "﹄",
    "＂": "＂",
    "｢": "｣",
    "«": "»",
    "‹": "›",
    "《": "》",
    "〈": "〉",
}
_all_quotes = set(_quotes.keys()) | set(_quotes.values())


class StringView:
    def __init__(self, buffer: str) -> None:
        self.index: int = 0
        self.buffer: str = buffer
        self.end: int = len(buffer)
        self.previous = 0

    @property
    def current(self) -> Optional[str]:
        return None if self.eof else self.buffer[self.index]

    @property
    def eof(self) -> bool:
        return self.index >= self.end

    def undo(self) -> None:
        self.index = self.previous

    def skip_ws(self) -> bool:
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

    def skip_string(self, string: str) -> bool:
        strlen = len(string)
        if self.buffer[self.index : self.index + strlen] == string:
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def read_rest(self) -> str:
        result = self.buffer[self.index :]
        self.previous = self.index
        self.index = self.end
        return result

    def read(self, n: int) -> str:
        result = self.buffer[self.index : self.index + n]
        self.previous = self.index
        self.index += n
        return result

    def get(self) -> Optional[str]:
        try:
            result = self.buffer[self.index + 1]
        except IndexError:
            result = None

        self.previous = self.index
        self.index += 1
        return result

    def get_word(self) -> str:
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if current.isspace():
                    break
                pos += 1
            except IndexError:
                break
        self.previous: int = self.index
        result = self.buffer[self.index : self.index + pos]
        self.index += pos
        return result

    def get_quoted_word(self) -> Optional[str]:
        current = self.current
        if current is None:
            return None

        close_quote = _quotes.get(current)
        is_quoted = bool(close_quote)
        if is_quoted:
            result = []
            _escaped_quotes = (current, close_quote)
        else:
            result = [current]
            _escaped_quotes = _all_quotes

        while not self.eof:
            current = self.get()
            if not current:
                if is_quoted:
                    # unexpected EOF
                    raise ExpectedClosingQuoteError(close_quote)
                return ''.join(result)

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            if current == '\\':
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise ExpectedClosingQuoteError(close_quote)
                    # if we aren't then we just let it through
                    return ''.join(result)

                if next_char in _escaped_quotes:
                    # escaped quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            if not is_quoted and current in _all_quotes:
                # we aren't quoted
                raise UnexpectedQuoteError(current)

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or next_char.isspace()
                if not valid_eof:
                    raise InvalidEndOfQuotedStringError(next_char)  # type: ignore # this will always be a string

                # we're quoted so it's okay
                return ''.join(result)

            if current.isspace() and not is_quoted:
                # end of word found
                return ''.join(result)

            result.append(current)

    def __repr__(self) -> str:
        return f'<StringView pos: {self.index} prev: {self.previous} end: {self.end} eof: {self.eof}>'
