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

class Separator:
    """An argument qualifier, which acts as the delimiter for arguments.
    
    .. code-block:: python3
    
        @bot.command(qualifier=Separator(','))
        async def foo(ctx, *c):
            await ctx.send(', '.join(c))
        
        # ?foo a b, c, d, e

        @bot.command(qualifier=Separator('|', strip_ws=False))
        async def bar(ctx, *c):
            await ctx.send(','.join(c))

        # ?bar a b test | c | e | f

    Attributes
    -----------
    key: :class:`str`
        The key that separates each argument. By default, it is ``' '``.
    strip_ws: :class:`bool`
        Whether or not to strip whitespace from the arguments. By default,
        it is ``True``.
    """
    def __init__(self, key=' ', *, strip_ws=True):
        self.key = key
        self.strip_ws = strip_ws

class Encapsulator:
    """An argument qualifier, which acts as a drop-in replacement for quotes.

    .. code-block:: python3

        @bot.command(qualifier=Encapsulator('-'))
        async def foo(ctx, *c):
            await ctx.send(', '.join(c))

        # ?foo -a b c- b

        @bot.command(qualifier=Encapsulator('(', ')'))
        async def bar(ctx, *c):
            await ctx.send(', '.join(c))

        # ?bar a b (c d e) f g

    Attributes
    -----------
    start: :class:`str`
        The starting key that represents the first quote character.
    end: Optional[:class:`str`]
        The ending key that represents the last quote character. If ``None``\,
        it will be set as the same key as ``start``.
    """
    def __init__(self, start, end=None):
        self.start = start
        self.end = end or start


class StringView:
    def __init__(self, buffer):
        self.index = 0
        self.buffer = buffer
        self.end = len(buffer)
        self.previous = 0
        self.available_quotes = _quotes
        self.separator = Separator()

    @property
    def current(self):
        return None if self.eof else self.buffer[self.index]

    @property
    def eof(self):
        return self.index >= self.end

    def is_separator(self, c):
        return c == self.separator.key

    def undo(self):
        self.index = self.previous

    def skip_ws(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if not self.is_separator(current):
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
                if self.is_separator(current):
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index:self.index + pos]
        self.index += pos
        return result

    def get_quoted_word(self):
        current = self.current
        if current is None:
            return None

        close_quote = self.available_quotes.get(current)
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

                r = ''.join(result)
                if self.separator.strip_ws:
                    r = r.strip()
                return r 

            # currently we accept strings in the format of "hello world"
            # to embed a quote inside the string you must escape it: "a \"world\""
            # separator characters (either a white space character or
            # a custom separator string) can also be escaped : hello\ world
            if current == '\\':
                next_char = self.get()
                if not next_char:
                    # string ends with \ and no character after it
                    if is_quoted:
                        # if we're quoted then we're expecting a closing quote
                        raise ExpectedClosingQuoteError(close_quote)
                    # if we aren't then we just let it through
                    return ''.join(result)

                if next_char == '"' or self.is_separator(next_char):
                    # escaped separator or quote
                    result.append(next_char)
                else:
                    # different escape character, ignore it
                    self.undo()
                    result.append(current)
                continue

            if not is_quoted and current in self.available_quotes:
                # we aren't quoted
                raise UnexpectedQuoteError(current)

            # closing quote
            if is_quoted and current == close_quote:
                next_char = self.get()
                valid_eof = not next_char or self.is_separator(next_char)
                if not valid_eof:
                    raise InvalidEndOfQuotedStringError(next_char)

                # we're quoted so it's okay
                return ''.join(result)

            if self.is_separator(current) and not is_quoted:
                # end of word found
                r = ''.join(result)
                if self.separator.strip_ws:
                    r = r.strip()

                return r

            result.append(current)


    def __repr__(self):
        return f'<StringView pos: {self.index} prev: {self.previous} end: {self.end} eof: {self.eof}>'
