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
from pysel.vm import Instruction
from pysel.vm import Opcode
from pysel.vm import SymbolTable

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
    "!": (operator_.not_, Opcode.NOT),
    "-": (operator_.neg, Opcode.NEGATE),
    "+": (operator_.pos, Opcode.POSITIVE),
}
BINARY_OPERATOR_MAPPING = {
    "==": (operator_.eq, Opcode.EQUALS),
    "!=": (operator_.ne, Opcode.NOT_EQUALS),
    ">": (operator_.gt, Opcode.GREATER_THAN),
    "<": (operator_.lt, Opcode.LESS_THAN),
    ">=": (operator_.ge, Opcode.GREATER_THAN_EQUALS),
    "<=": (operator_.le, Opcode.LESS_THAN_EQUALS),
    "+": (operator_.add, Opcode.ADD),
    "-": (operator_.sub, Opcode.SUBTRACT),
    "*": (operator_.mul, Opcode.MULTIPLY),
    "/": (operator_.truediv, Opcode.TRUEDIV),
    "//": (operator_.floordiv, Opcode.FLOORDIV),
    "%": (operator_.mod, Opcode.MODULO),
    "**": (operator_.pow, Opcode.POWER),
}


class Node(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def compile(self, st: SymbolTable) -> t.List[Instruction]:
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

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        return [Instruction(Opcode.LOAD_CONST, st.add_literal(self.value))]

    def evaluate(self, env: t.Mapping[str, t.Any]) -> T:
        return self.value


class Reference(Node):
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"Reference({self.name!r})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        return [Instruction(Opcode.LOAD_REF, st.add_reference(self.name))]

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return env[self.name]


class UnaryOp(Node):
    __slots__ = ("operator", "operand")

    def __init__(self, operator: str, operand: Node) -> None:
        self.operator = operator
        self.operand = operand

    def __repr__(self) -> str:
        return f"UnaryOp({self.operator}, {self.operand})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        return [*self.operand.compile(st), Instruction(UNARY_OPERATOR_MAPPING[self.operator][1], None)]

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return UNARY_OPERATOR_MAPPING[self.operator][0](self.operand.evaluate(env))  # type: ignore[operator]


class BinaryOp(Node):
    __slots__ = ("lh", "operator", "rh")

    def __init__(self, lh: Node, operator: str, rh: Node) -> None:
        self.lh = lh
        self.operator = operator
        self.rh = rh

    def __repr__(self) -> str:
        return f"BinaryOp({self.lh}, {self.operator}, {self.rh})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        lh_instruction = self.lh.compile(st)
        rh_instruction = self.rh.compile(st)

        # Special cases
        if self.operator == "||" or self.operator == "&&":
            return [
                *lh_instruction,
                Instruction(
                    Opcode.JUMP_IF_TRUE if self.operator == "||" else Opcode.JUMP_IF_FALSE, len(rh_instruction) + 1
                ),
                Instruction(Opcode.POP, None),
                *rh_instruction,
            ]

        return [*rh_instruction, *lh_instruction, Instruction(BINARY_OPERATOR_MAPPING[self.operator][1], None)]

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        # We process 'or' and 'and' separately to allow operator short-circuiting
        if self.operator == "||":
            return self.lh.evaluate(env) or self.rh.evaluate(env)
        elif self.operator == "&&":
            return self.lh.evaluate(env) and self.rh.evaluate(env)

        return BINARY_OPERATOR_MAPPING[self.operator][0](self.lh.evaluate(env), self.rh.evaluate(env))


class TernaryOp(Node):
    __slots__ = ("condition", "when_true", "when_false")

    def __init__(self, condition: Node, when_true: Node, when_false: Node) -> None:
        self.condition = condition
        self.when_true = when_true
        self.when_false = when_false

    def __repr__(self) -> str:
        return f"TernaryOp({self.condition} ? {self.when_true} : {self.when_false})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        instructions = [*self.condition.compile(st)]

        when_true_instructions = self.when_true.compile(st)
        when_false_instruction = self.when_false.compile(st)

        instructions.extend(
            [
                Instruction(Opcode.POP_JUMP_IF_FALSE, len(when_true_instructions) + 2),
                Instruction(Opcode.POP, None),
                *when_true_instructions,
                Instruction(Opcode.JUMP, len(when_false_instruction)),
                *when_false_instruction,
            ]
        )

        return instructions

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

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        return [
            Instruction(Opcode.LOAD_CONST, st.add_literal(self.attr)),
            *self.operand.compile(st),
            Instruction(Opcode.GETATTR, None),
        ]

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return getattr(self.operand.evaluate(env), self.attr)


class MethodCall(Node):
    __slots__ = ("operand", "arguments")

    def __init__(self, operand: Node, arguments: t.Sequence[Node]) -> None:
        self.operand = operand
        self.arguments = arguments

    def __repr__(self) -> str:
        return f"MethodCall({self.operand}, args={self.arguments})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        instructions: t.List[Instruction] = []
        for argument in self.arguments[::-1]:
            instructions.extend(argument.compile(st))

        instructions.extend(self.operand.compile(st))
        instructions.append(Instruction(Opcode.CALL, len(self.arguments)))

        return instructions

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        return self.operand.evaluate(env)(*(a.evaluate(env) for a in self.arguments))


class Getitem(Node):
    __slots__ = ("operand", "params")

    def __init__(self, operand: Node, params: t.Sequence[t.Optional[Node]]) -> None:
        self.operand = operand
        self.params: t.List[t.Optional[Node]] = list(params)

        if len(self.params) > 1:
            self.params.extend([None] * (3 - len(self.params)))

    def __repr__(self) -> str:
        return f"Getitem({self.operand}, params={self.params})"

    def compile(self, st: SymbolTable) -> t.List[Instruction]:
        none_const_id = st.add_literal(None)

        instructions: t.List[Instruction] = []
        if len(self.params) > 1:
            for param in self.params[::-1]:
                if param is None:
                    instructions.append(Instruction(Opcode.LOAD_CONST, none_const_id))
                else:
                    instructions.extend(param.compile(st))
        else:
            instructions.extend(self.params[0].compile(st))

        instructions.extend(self.operand.compile(st))
        instructions.append(Instruction(Opcode.GETITEM, len(self.params)))

        return instructions

    def evaluate(self, env: t.Mapping[str, t.Any]) -> t.Any:
        if len(self.params) > 1:
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
