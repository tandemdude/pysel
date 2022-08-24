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
import abc
import enum
import typing as t

__all__ = [
    "TokenType",
    "Token",
    "LiteralMixin",
    "OperatorToken",
    "IdentifierToken",
    "StringToken",
    "IntToken",
    "FloatToken",
    "ErrorToken",
]


class TokenType(enum.Enum):
    # Compound tokens
    IDENTIFIER = "\\w[\\w\\d]+"
    INT_LITERAL = "[\\d]+"
    FLOAT_LITERAL = "[\\d]+\\.[\\d]*"
    STRING_LITERAL = "'.*'"
    # Special tokens
    UNKNOWN = "UNKNOWN"
    # Operators
    OPERATOR_EQ = "=="
    OPERATOR_NOT_EQ = "!="
    OPERATOR_GREATER_THAN = ">"
    OPERATOR_LESS_THAN = "<"
    OPERATOR_GREATER_EQUALS = ">="
    OPERATOR_LESS_EQUALS = "<="
    OPERATOR_NOT = "!"
    OPERATOR_AND = "&&"
    OPERATOR_OR = "||"
    OPERATOR_ADD = "+"
    OPERATOR_SUB = "-"
    OPERATOR_MULTIPLY = "*"
    OPERATOR_DIVIDE = "/"
    OPERATOR_INTEGER_DIVIDE = "//"
    OPERATOR_MODULO = "%"
    OPERATOR_POW = "**"
    # Special characters
    QUESTION_MARK = "?"
    COLON = ":"
    ACCESSOR = "."
    COMMA = ","
    L_PAREN = "("
    R_PAREN = ")"
    L_SQUARE_BRACKET = "["
    R_SQUARE_BRACKET = "]"


EXCLUDED_TOKEN_TYPES = {
    TokenType.IDENTIFIER,
    TokenType.INT_LITERAL,
    TokenType.FLOAT_LITERAL,
    TokenType.STRING_LITERAL,
    TokenType.UNKNOWN,
}
SORTED_TOKEN_TYPES = sorted(
    set(TokenType).difference(EXCLUDED_TOKEN_TYPES),
    key=lambda itm: len(itm.value),
    reverse=True,
)


class Token(abc.ABC):
    __slots__ = ("value", "at", "type")

    value: t.Any
    at: int
    type: TokenType

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r}, type={self.type})"


class LiteralMixin:
    __slots__ = ()


class OperatorToken(Token):
    __slots__ = ()

    def __init__(self, type: TokenType, at: int) -> None:
        self.value = type.value
        self.at = at
        self.type = type


class IdentifierToken(Token):
    __slots__ = ()

    type: TokenType = TokenType.IDENTIFIER

    def __init__(self, value: str, at: int) -> None:
        self.value = value
        self.at = at


class StringToken(Token, LiteralMixin):
    __slots__ = ()

    type: TokenType = TokenType.STRING_LITERAL

    def __init__(self, value: str, at: int) -> None:
        self.value = value.replace("\\", "")
        self.at = at


class IntToken(Token, LiteralMixin):
    __slots__ = ()

    type: TokenType = TokenType.INT_LITERAL

    def __init__(self, value: str, at: int) -> None:
        self.value: int = int(value)
        self.at = at


class FloatToken(Token, LiteralMixin):
    __slots__ = ()

    type: TokenType = TokenType.FLOAT_LITERAL

    def __init__(self, value: str, at: int) -> None:
        self.value = float(value)
        self.at = at


class ErrorToken(Token):
    __slots__ = ()

    type: TokenType = TokenType.UNKNOWN

    def __init__(self, value: str, at: int) -> None:
        self.value: str = value
        self.at = at
