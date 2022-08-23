import typing as t

from pysel import ast
from pysel import lexer
from pysel import tokens
from pysel import errors

__all__ = ["ast", "lexer", "tokens", "Expression"]

__version__ = "0.0.1"


class Expression:
    __slots__ = ("raw", "ast")

    def __init__(self, raw: str) -> None:
        self.raw: str = raw
        self.ast: t.Optional[ast.Node] = None

    def to_ast(self) -> ast.Node:
        if self.ast is not None:
            return self.ast
        self.ast = ast.Parser(self.raw, lexer.Lexer(self.raw).tokenize()).compilation_unit()
        return self.ast

    def evaluate(self, env: t.Optional[t.Mapping[str, t.Any]] = None) -> t.Any:
        return self.to_ast().evaluate(env or {})
