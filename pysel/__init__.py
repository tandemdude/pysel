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

__all__ = ["ast", "lexer", "tokens", "Expression"]

__version__ = "0.0.4"

T = t.TypeVar("T")


class Expression(t.Generic[T]):
    __slots__ = ("raw", "ast", "py_code", "code_obj")

    def __init__(self, raw: str) -> None:
        self.raw: str = raw

        self.ast: t.Optional[ast.Node] = None
        self.py_code: t.Optional[str] = None
        self.code_obj: t.Optional[types.CodeType] = None

    def compile(self) -> types.CodeType:
        if self.code_obj is not None:
            return self.code_obj

        self.ast = ast.Parser(self.raw, lexer.Lexer(self.raw).tokenize()).compilation_unit()
        self.py_code = self.ast.compile()
        self.code_obj = compile(self.py_code, "pysel_expr", "single")

        return self.code_obj

    def evaluate(self, env: t.Optional[t.Dict[str, t.Any]] = None, use_ast: bool = False) -> T:
        """
        Evaluate this expression under the given environment.

        Args:
            env (dict | None): Environment to use to resolve references in the expression.
            use_ast (bool): Whether to run as an AST walker instead of transpiling the AST to python and running
                using ``eval`` instead.

        Returns:
            The output of the expression.
        """

        env = env or {}
        for primitive in (bool, float, int, str):
            env.setdefault(primitive.__name__, primitive)
        env.setdefault("None", None)

        if use_ast:
            self.compile()
            return t.cast(T, self.ast.evaluate(env))

        return t.cast(T, eval(self.compile(), env))
