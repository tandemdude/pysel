# -*- coding: utf-8 -*-
# Copyright (c) 2022-present tandemdude
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import typing as t

from pysel import errors
from pysel import tokens

__all__ = ["Lexer"]


class Lexer:
    __slots__ = ("raw", "tokens", "idx", "eof")

    def __init__(self, raw: str) -> None:
        self.raw: str = raw
        self.tokens: t.List[tokens.Token] = []

        self.idx: int = -1
        self.eof: bool = False

    def next(self) -> t.Tuple[t.Optional[str], t.Optional[int]]:
        self.idx += 1

        if len(self.raw) <= self.idx:
            return None, None

        if self.raw[self.idx].isspace():
            return self.next()

        return self.raw[self.idx], self.idx

    def peek(self, n_ahead: int = 1) -> t.Optional[str]:
        idx = self.idx + n_ahead

        if len(self.raw) <= idx:
            return None

        return self.raw[idx]

    def peek_to_length(self, n_ahead: int = 1) -> str:
        return self.raw[self.idx : self.idx + n_ahead]

    def parse_while(
        self,
        char: t.Optional[str],
        condition: t.Callable[[t.Optional[str], int, t.List[str]], bool],
        fail_on_eof: bool = False,
    ) -> str:
        buf: t.List[str] = []
        offset: int = 0
        while condition(char, offset, buf):
            if fail_on_eof and char is None:
                raise errors.ExpressionSyntaxError("Unexpected EOF while parsing", self.raw, [self.idx])
            assert char is not None
            buf.append(char)
            char, offset = self.peek(offset + 1), offset + 1
        return "".join(buf)

    def as_token(self, char: str, charindex: int) -> t.Tuple[tokens.Token, int]:
        if char.isalpha() or char == "_":
            tkn = self.parse_while(char, lambda c, o, _: c is not None and (c.isalnum() or c == "_"))
            return tokens.IdentifierToken(tkn, charindex), len(tkn)
        if char == "'" or char == '"':
            looking_for = "'" if char == "'" else '"'

            tkn = self.parse_while(
                "",
                lambda c, o, _: c != looking_for or self.raw[self.idx + o - 1 : self.idx + o + 1] == f"\\{looking_for}",
                True,
            )
            return tokens.StringToken(tkn, charindex), len(tkn) + 2
        if char.isdecimal():
            tkn = self.parse_while(
                char,
                lambda c, _, b: c is not None and (c.isdecimal() or (c == "." and "." not in b)),
            )
            if "." in tkn:
                return tokens.FloatToken(tkn, charindex), len(tkn)
            return tokens.IntToken(tkn, charindex), len(tkn)

        for token_type in tokens.SORTED_TOKEN_TYPES:
            value: str = token_type.value
            if len(value) == 1:
                if char != value:
                    continue
                return tokens.OperatorToken(token_type, charindex), 1

            if (tkn := self.peek_to_length(len(value))) == value:
                return tokens.OperatorToken(token_type, charindex), len(tkn)

        return tokens.ErrorToken(char, charindex), 1

    def tokenize(self) -> t.List[tokens.Token]:
        while not self.eof:
            char, charindex = self.next()

            if char is None:
                self.eof = True
                break

            assert charindex is not None
            token, consumed = self.as_token(char, charindex)
            if consumed > 1:
                self.idx += consumed - 1

            self.tokens.append(token)

        if invalid := list(filter(lambda tk: isinstance(tk, tokens.ErrorToken), self.tokens)):
            raise errors.ExpressionSyntaxError(
                "Unexpected tokens encountered during lexing",
                self.raw,
                [i.at for i in invalid],
            )

        return self.tokens
