import typing as t

__all__ = ["ExpressionSyntaxError"]


class ExpressionSyntaxError(SyntaxError):
    def __init__(self, message: str, expr: t.Optional[str], at: t.Sequence[int]) -> None:
        built_message = [message]
        if expr:
            built_message.append((" " * 4) + repr(expr))
            if at:
                error_arrows = [" " for _ in range(5 + len(expr))]
                for idx in at:
                    error_arrows[5 + idx] = "^"
                built_message.append("".join(error_arrows))
        super().__init__("\n".join(built_message))
