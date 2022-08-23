import operator

import pysel


def test_method_call_returns_correct_value():
    assert pysel.Expression("'foo'.upper()").evaluate() == "FOO"


def test_chained_method_call_returns_correct_value():
    assert pysel.Expression("'FoO'.upper().lower()").evaluate() == "foo"


def test_method_call_with_single_arg_returns_correct_value():
    assert pysel.Expression("'foo'.count('o')").evaluate() == 2


def test_method_call_with_multiple_args_returns_correct_value():
    assert pysel.Expression("op.add(1, 2)").evaluate({"op": operator}) == 3


def test_function_call_returns_correct_value():
    assert pysel.Expression("add(1, 2)").evaluate({"add": operator.add}) == 3
