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
import types
import typing as t

from pysel import ast
from pysel import errors
from pysel import lexer
from pysel import tokens
from pysel import vm

__all__ = ["ast", "lexer", "tokens", "Expression"]

__version__ = "0.0.5"

T = t.TypeVar("T")


class Expression(t.Generic[T]):
    __slots__ = ("raw", "ast", "bytecode", "vm")

    def __init__(self, raw: str) -> None:
        self.raw: str = raw

        self.ast: t.Optional[ast.Node] = None
        self.bytecode: t.Optional[t.List[vm.Instruction]] = None
        self.vm: t.Optional[vm.VirtualMachine[T]] = None

    def compile(self) -> vm.VirtualMachine:
        if self.vm is not None:
            return self.vm

        self.ast = ast.Parser(self.raw, lexer.Lexer(self.raw).tokenize()).compilation_unit()

        symbol_table = vm.SymbolTable()
        self.bytecode = self.ast.compile(symbol_table)
        self.vm = vm.VirtualMachine(self.bytecode, symbol_table)

        return self.vm

    def evaluate(self, env: t.Optional[t.Dict[str, t.Any]] = None, use_ast: bool = False) -> T:
        """
        Evaluate this expression under the given environment.

        Args:
            env (dict | None): Environment to use to resolve references in the expression.
            use_ast (bool): Whether to run as an AST walker instead of compiling to PySEL bytecode and using
                the bytecode virtual machine.

        Returns:
            The output of the expression.
        """
        if self.ast is None:
            self.compile()

        env = env or {}
        for primitive in (bool, float, int, str):
            env.setdefault(primitive.__name__, primitive)
        env.setdefault("None", None)

        if use_ast:
            return t.cast(T, self.ast.evaluate(env))

        return t.cast(T, self.vm.run(env))
