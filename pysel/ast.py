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
from __future__ import annotations

import abc
import collections
import operator as operator_
import typing as t

from pysel import errors
from pysel import tokens as tokens_

__all__ = [
    "Node",
    "Literal",
    "Reference",
    "UnaryOp",
    "BinaryOp",
    "TernaryOp",
    "Accessor",
    "MethodCall",
    "Parser",
]

T = t.TypeVar("T")
UNARY_OPERATOR_MAPPING = {
    "!": operator_.not_,
    "-": operator_.neg,
    "+": operator_.pos,
}
BINARY_OPERATOR_MAPPING = {
    "==": operator_.eq,
    "!=": operator_.ne,
    ">": operator_.gt,
    "<": operator_.lt,
    ">=": operator_.ge,
    "<=": operator_.le,
    "+": operator_.add,
    "-": operator_.sub,
    "*": operator_.mul,
    "/": operator_.truediv,
    "//": operator_.floordiv,
    "%": operator_.mod,
    "**": operator_.pow,
}


class Node(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def compile(self) -> str:
        ...

    @abc.abstractmethod
    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        ...


class Literal(Node, t.Generic[T]):
    __slots__ = ("value",)

    def __init__(self, value: T) -> None:
        self.value: T = value

    def __repr__(self) -> str:
        return f"Literal({self.value!r})"

    def compile(self) -> str:
        return repr(self.value)

    def evaluate(self, env: t.Mapping[str, t.Any]) -> T:
        return self.value


class Reference(Node):
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"Reference({self.name!r})"

    def compile(self) -> str:
        return self.name

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return env[self.name]


class UnaryOp(Node):
    __slots__ = ("operator", "operand")

    def __init__(self, operator: str, operand: Node) -> None:
        self.operator = operator
        self.operand = operand

    def __repr__(self) -> str:
        return f"UnaryOp({self.operator}, {self.operand})"

    def compile(self) -> str:
        return f"{self.operator}({self.operand.compile()})" if self.operator != "!" else f"not ({self.operand.compile()})"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return UNARY_OPERATOR_MAPPING[self.operator](self.operand.evaluate(env))  # type: ignore[operator]


class BinaryOp(Node):
    __slots__ = ("lh", "operator", "rh")

    def __init__(self, lh: Node, operator: str, rh: Node) -> None:
        self.lh = lh
        self.operator = operator
        self.rh = rh

    def __repr__(self) -> str:
        return f"BinaryOp({self.lh}, {self.operator}, {self.rh})"

    def compile(self) -> str:
        # special case && , ||
        if self.operator == "&&" or self.operator == "||":
            return f"({self.lh.compile()}) {'and' if self.operator == '&&' else 'or'} ({self.rh.compile()})"

        return f"({self.lh.compile()}) {self.operator} ({self.rh.compile()})"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        # We process 'or' and 'and' separately to allow operator short-circuiting
        if self.operator == "||":
            return self.lh.evaluate(env) or self.rh.evaluate(env)
        elif self.operator == "&&":
            return self.lh.evaluate(env) and self.rh.evaluate(env)

        return BINARY_OPERATOR_MAPPING[self.operator](self.lh.evaluate(env), self.rh.evaluate(env))


class TernaryOp(Node):
    __slots__ = ("condition", "when_true", "when_false")

    def __init__(self, condition: Node, when_true: Node, when_false: Node) -> None:
        self.condition = condition
        self.when_true = when_true
        self.when_false = when_false

    def __repr__(self) -> str:
        return f"TernaryOp({self.condition} ? {self.when_true} : {self.when_false})"

    def compile(self) -> str:
        return f"({self.when_true.compile()}) if ({self.condition.compile()}) else ({self.when_false.compile()})"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        if self.condition.evaluate(env):
            return self.when_true.evaluate(env)
        return self.when_false.evaluate(env)


class Accessor(Node):
    __slots__ = ("operand", "attr")

    def __init__(self, operand: Node, attr: str) -> None:
        self.operand = operand
        self.attr = attr

    def __repr__(self) -> str:
        return f"Accessor({self.operand}, {self.attr!r})"

    def compile(self) -> str:
        return f"({self.operand.compile()}).{self.attr}"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return getattr(self.operand.evaluate(env), self.attr)


class MethodCall(Node):
    __slots__ = ("operand", "arguments")

    def __init__(self, operand: Node, arguments: t.Sequence[Node]) -> None:
        self.operand = operand
        self.arguments = arguments

    def __repr__(self) -> str:
        return f"MethodCall({self.operand}, args={self.arguments})"

    def compile(self) -> str:
        return f"({self.operand.compile()})({','.join(a.compile() for a in self.arguments)})"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return self.operand.evaluate(env)(*(a.evaluate(env) for a in self.arguments))


class Getitem(Node):
    __slots__ = ("operand", "params")

    def __init__(self, operand: Node, params: t.Sequence[t.Optional[Node]]) -> None:
        self.operand = operand
        self.params: t.List[t.Optional[Node]] = list(params)

    def __repr__(self) -> str:
        return f"Getitem({self.operand}, params={self.params})"

    def compile(self) -> str:
        params = ":".join("" if p is None else p.compile() for p in self.params)
        return f"({self.operand.compile()})[{params}]"

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        if len(self.params) > 1:
            self.params.extend([None] * (3 - len(self.params)))
            return self.operand.evaluate(env)[slice(*(p.evaluate(env) if p else None for p in self.params))]
        assert len(self.params) == 1 and self.params[0] is not None
        return self.operand.evaluate(env)[self.params[0].evaluate(env)]


class Parser:
    __slots__ = ("raw", "tokens", "idx", "error_stack")

    def __init__(self, raw: str, tokens: t.List[tokens_.Token]) -> None:
        self.raw = raw
        self.tokens = tokens

        self.idx = -1
        self.error_stack: collections.deque[str] = collections.deque()

    def syntax_error(self) -> t.NoReturn:
        char_indexes: t.List[int] = []

        if self.idx == -1:
            char_indexes.append(0)
        elif self.idx >= len(self.tokens):
            char_indexes.append(len(self.raw) - 1)
        else:
            curr_token = self.tokens[self.idx]
            char_indexes.extend(range(curr_token.at, curr_token.at + len(str(curr_token.value))))

        if self.error_stack:
            raise errors.ExpressionSyntaxError(
                f"Expected {self.error_stack.popleft()!r} was not found",
                self.raw,
                char_indexes,
            )

        next_token = self.tokens[self.idx + 1 :][0]
        char_indexes = [*range(next_token.at, next_token.at + len(str(next_token.value)))]
        raise errors.ExpressionSyntaxError("Unexpected token encountered while parsing", self.raw, char_indexes)

    def next_token(self) -> t.Optional[tokens_.Token]:
        self.idx += 1

        if len(self.tokens) <= self.idx:
            return None

        return self.tokens[self.idx]

    def peek_next_token(self) -> t.Optional[tokens_.Token]:
        token = self.next_token()
        self.idx -= 1
        return token

    def val(self) -> Node:
        if self.peek_next_token() is None:
            self.syntax_error()
        elif self.peek_next_token().value == "(":  # type: ignore[union-attr]
            self.next_token()
            self.error_stack.appendleft(")")
            node = self.ternary()
            if not getattr(self.peek_next_token(), "value", None) == ")":
                self.syntax_error()
            self.error_stack.popleft()
            self.next_token()
            return node
        elif isinstance(self.peek_next_token(), tokens_.IdentifierToken):
            return Reference(self.next_token().value)  # type: ignore[union-attr]
        elif isinstance(self.peek_next_token(), tokens_.LiteralMixin):
            return Literal(self.next_token().value)  # type: ignore[union-attr]
        self.syntax_error()

    def accessor(self, initial_node: t.Optional[Node] = None) -> Node:
        node = initial_node or self.val()

        while (nxt := self.peek_next_token()) is not None and nxt.value == ".":
            self.error_stack.appendleft("identifier")
            self.next_token()

            if self.peek_next_token() is None:
                self.syntax_error()

            node = Accessor(node, self.next_token().value)  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def getitem(self, initial_node: t.Optional[Node] = None) -> Node:
        node = self.accessor(initial_node)

        while (nxt := self.peek_next_token()) is not None and nxt.value == "[":
            self.error_stack.appendleft("]")
            self.next_token()
            if (tkn := self.peek_next_token()) is None or tkn.value == "]":
                self.error_stack.appendleft("expr | :")
                self.syntax_error()

            params: t.List[t.Optional[Node]] = [
                self.ternary() if getattr(self.peek_next_token(), "value", None) != ":" else None
            ]
            while (nxt2 := self.peek_next_token()) is not None and nxt2.value == ":":
                if len(params) >= 3:
                    self.syntax_error()

                self.error_stack.appendleft("expr | :")
                self.next_token()
                if (tkn := self.peek_next_token()) is not None and tkn.value == ":":
                    self.error_stack.popleft()
                    params.append(None)
                    continue

                params.append(
                    self.ternary() if getattr(self.peek_next_token(), "value", None) not in (":", "]") else None
                )
                self.error_stack.popleft()

            if (tkn := self.peek_next_token()) is None or tkn.value != "]":
                self.syntax_error()

            node = Getitem(node, params)
            self.next_token()  # Remove R_SQUARE_BRACKET
            self.error_stack.popleft()

            if (nxt := self.peek_next_token()) is not None and nxt.value == ".":
                # Chained call special case
                node = self.accessor(node)

        return node

    def method_call(self) -> Node:
        node = self.getitem()

        while (nxt := self.peek_next_token()) is not None and nxt.value == "(":
            self.next_token()
            self.error_stack.appendleft(")")
            if (nxt := self.peek_next_token()) is None:
                self.syntax_error()
            if nxt.value == ")":
                node = MethodCall(node, [])
            else:
                arguments = [self.ternary()]
                while (nxt3 := self.peek_next_token()) is not None and nxt3.value == ",":
                    self.next_token()
                    self.error_stack.appendleft("expr")
                    arguments.append(self.ternary())
                    self.error_stack.popleft()

                if (tkn := self.peek_next_token()) is None or tkn.value != ")":
                    self.syntax_error()

                node = MethodCall(node, arguments)
            self.next_token()  # Remove R_PAREN
            self.error_stack.popleft()

            if (nxt := self.peek_next_token()) is not None and nxt.value in ["[", "."]:
                # Chained call special case
                node = self.getitem(node)

        return node

    def pow(self) -> Node:
        node = self.method_call()

        while (nxt := self.peek_next_token()) is not None and nxt.value == "**":
            op = self.next_token().value  # type: ignore[union-attr]
            self.error_stack.appendleft("expr")
            node = BinaryOp(self.method_call(), op, node)
            self.error_stack.popleft()

        return node

    def unary_expr(self) -> Node:
        node = None
        while (nxt := self.peek_next_token()) is not None and nxt.value in ("-", "+"):
            self.next_token()
            self.error_stack.appendleft("expr")
            node = UnaryOp(nxt.value, self.pow())
            self.error_stack.popleft()

        return node or self.pow()

    def multi(self) -> Node:
        node = self.unary_expr()

        while (nxt := self.peek_next_token()) is not None and nxt.value in (
            "*",
            "/",
            "//",
            "%",
        ):
            self.error_stack.appendleft("expr")
            node = BinaryOp(node, self.next_token().value, self.unary_expr())  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def expr(self) -> Node:
        node = self.multi()

        while (nxt := self.peek_next_token()) is not None and nxt.value in ("+", "-"):
            self.error_stack.appendleft("expr")
            node = BinaryOp(node, self.next_token().value, self.multi())  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def comparison(self) -> Node:
        node = self.expr()

        while (nxt := self.peek_next_token()) is not None and nxt.value in (
            "==",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
        ):
            self.error_stack.appendleft("expr")
            node = BinaryOp(node, self.next_token().value, self.expr())  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def logical_not(self) -> Node:
        node = None
        while (nxt := self.peek_next_token()) is not None and nxt.value == "!":
            self.next_token()
            self.error_stack.appendleft("expr")
            node = UnaryOp(nxt.value, self.comparison())
            self.error_stack.popleft()

        return node or self.comparison()

    def logical_and(self) -> Node:
        node = self.logical_not()

        while (nxt := self.peek_next_token()) is not None and nxt.value == "&&":
            self.error_stack.appendleft("expr")
            node = BinaryOp(node, self.next_token().value, self.logical_not())  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def logical_or(self) -> Node:
        node = self.logical_and()

        while (nxt := self.peek_next_token()) is not None and nxt.value == "||":
            self.error_stack.appendleft("expr")
            node = BinaryOp(node, self.next_token().value, self.logical_and())  # type: ignore[union-attr]
            self.error_stack.popleft()

        return node

    def ternary(self) -> Node:
        node = self.logical_or()

        while (nxt := self.peek_next_token()) is not None and nxt.value == "?":
            self.next_token()
            self.error_stack.appendleft("expr")
            when_true = self.ternary()

            self.error_stack.appendleft(":")
            if (nxt2 := self.peek_next_token()) is not None and nxt2.value == ":":
                self.next_token()
                self.error_stack.popleft()
                node = TernaryOp(node, when_true, self.ternary())
            else:
                self.syntax_error()
            self.error_stack.popleft()

        return node

    def compilation_unit(self) -> Node:
        node = self.ternary()

        if self.tokens[self.idx + 1 :]:
            self.syntax_error()

        return node
