import collections
import enum
import typing as t

T = t.TypeVar("T")

__all__ = ["SymbolTable", "Opcode", "Instruction", "VirtualMachine"]


class SymbolTable:
    __slots__ = ("_literals", "_next_literal_id", "_references", "_next_reference_id")

    def __init__(self) -> None:
        self._literals: t.Dict[int, t.Any] = {}
        self._next_literal_id = 0

        self._references: t.Dict[int, str] = {}
        self._next_reference_id = 0

    @property
    def literals(self) -> t.Dict[int, t.Any]:
        return self._literals

    @property
    def references(self) -> t.Dict[int, str]:
        return self._references

    def add_literal(self, val: t.Any) -> int:
        if val in self._literals.values():
            return [k for k, v in self._literals.items() if v == val][0]

        symbol_id = self._next_literal_id
        self._literals[symbol_id] = val

        self._next_literal_id += 1
        return symbol_id

    def add_reference(self, ref: str) -> int:
        if ref in self._references.values():
            return [k for k, v in self._references.items() if v == ref][0]

        symbol_id = self._next_reference_id
        self._references[symbol_id] = ref

        self._next_reference_id += 1
        return symbol_id


class Opcode(enum.IntEnum):
    # Loaders
    LOAD_CONST = 0
    LOAD_REF = 1
    # Unary operators
    NOT = 2
    NEGATE = 3
    POSITIVE = 4
    # Binary operators
    EQUALS = 5
    NOT_EQUALS = 6
    GREATER_THAN = 7
    LESS_THAN = 8
    GREATER_THAN_EQUALS = 9
    LESS_THAN_EQUALS = 10
    ADD = 11
    SUBTRACT = 12
    MULTIPLY = 13
    TRUEDIV = 14
    FLOORDIV = 15
    MODULO = 16
    POWER = 17
    # Special operators
    CALL = 18
    GETITEM = 19
    GETATTR = 20
    # Jumps
    POP_JUMP_IF_TRUE = 21
    POP_JUMP_IF_FALSE = 22
    JUMP_IF_TRUE = 23
    JUMP_IF_FALSE = 24
    JUMP = 25
    # Misc
    POP = 26


class Instruction(t.NamedTuple):
    opcode: Opcode
    operand: t.Optional[int]


class VirtualMachine(t.Generic[T]):
    __slots__ = ("_code", "_symbols")

    def __init__(self, code: t.List[Instruction], symbols: SymbolTable) -> None:
        self._code = code
        self._symbols = symbols

    def format_code(self) -> str:
        lines: t.List[str] = []

        for n, instruction in enumerate(self._code):
            lines.append(
                f"{n}  {instruction.opcode.name}{f' {instruction.operand}' if instruction.operand is not None else ''}"
            )

        return "\n".join(lines)

    def run(self, context: t.Dict[str, t.Any]) -> T:
        literals, references = self._symbols.literals, self._symbols.references
        stack = collections.deque()

        pc = 0
        while pc < len(self._code):
            instruction = self._code[pc]
            offset = 1

            if instruction.opcode == Opcode.LOAD_CONST:
                stack.append(literals[instruction.operand])
            elif instruction.opcode == Opcode.LOAD_REF:
                stack.append(context[references[instruction.operand]])
            elif instruction.opcode == Opcode.NOT:
                stack.append(not stack.pop())
            elif instruction.opcode == Opcode.NEGATE:
                stack.append(-(stack.pop()))
            elif instruction.opcode == Opcode.POSITIVE:
                stack.append(+(stack.pop()))
            elif instruction.opcode == Opcode.EQUALS:
                stack.append(stack.pop() == stack.pop())
            elif instruction.opcode == Opcode.NOT_EQUALS:
                stack.append(stack.pop() != stack.pop())
            elif instruction.opcode == Opcode.GREATER_THAN:
                stack.append(stack.pop() > stack.pop())
            elif instruction.opcode == Opcode.LESS_THAN:
                stack.append(stack.pop() < stack.pop())
            elif instruction.opcode == Opcode.GREATER_THAN_EQUALS:
                stack.append(stack.pop() >= stack.pop())
            elif instruction.opcode == Opcode.LESS_THAN_EQUALS:
                stack.append(stack.pop() <= stack.pop())
            elif instruction.opcode == Opcode.ADD:
                stack.append(stack.pop() + stack.pop())
            elif instruction.opcode == Opcode.SUBTRACT:
                stack.append(stack.pop() - stack.pop())
            elif instruction.opcode == Opcode.MULTIPLY:
                stack.append(stack.pop() * stack.pop())
            elif instruction.opcode == Opcode.TRUEDIV:
                stack.append(stack.pop() / stack.pop())
            elif instruction.opcode == Opcode.FLOORDIV:
                stack.append(stack.pop() // stack.pop())
            elif instruction.opcode == Opcode.MODULO:
                stack.append(stack.pop() % stack.pop())
            elif instruction.opcode == Opcode.POWER:
                stack.append(stack.pop() ** stack.pop())
            elif instruction.opcode == Opcode.CALL:
                stack.append(stack.pop()(*[stack.pop() for _ in range(instruction.operand)]))
            elif instruction.opcode == Opcode.GETITEM:
                operated_on = stack.pop()
                items = [stack.pop() for _ in range(instruction.operand)]

                if len(items) == 1:
                    stack.append(operated_on[items[0]])
                else:
                    stack.append(operated_on[slice(*items)])
            elif instruction.opcode == Opcode.GETATTR:
                stack.append(getattr(stack.pop(), stack.pop()))
            elif instruction.opcode == Opcode.POP_JUMP_IF_TRUE:
                value = stack.pop()
                if value:
                    offset = instruction.operand + 1
            elif instruction.opcode == Opcode.POP_JUMP_IF_FALSE:
                value = stack.pop()
                if not value:
                    offset = instruction.operand + 1
            elif instruction.opcode == Opcode.JUMP_IF_TRUE:
                value = stack.pop()
                if value:
                    offset = instruction.operand + 1
                stack.append(value)
            elif instruction.opcode == Opcode.JUMP_IF_FALSE:
                value = stack.pop()
                if not value:
                    offset = instruction.operand + 1
                stack.append(value)
            elif instruction.opcode == Opcode.JUMP:
                offset = instruction.operand + 1
            elif instruction.opcode == Opcode.POP:
                stack.pop()

            pc += offset

        return stack.pop()
