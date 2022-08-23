import pysel


def test_ternary_returns_left_value_when_true():
    assert pysel.Expression("1 ? 2 : 3").evaluate() == 2


def test_ternary_returns_right_value_when_false():
    assert pysel.Expression("0 ? 1 : 2").evaluate() == 2


def test_nested_ternary_in_when_true_returns_inner_left_value():
    assert pysel.Expression("1 ? 1 ? 2 : 3 : 4").evaluate() == 2


def test_nested_ternary_in_when_true_returns_inner_right_value():
    assert pysel.Expression("1 ? 0 ? 2 : 3 : 4").evaluate() == 3


def test_nested_ternary_in_when_false_returns_inner_left_value():
    assert pysel.Expression("0 ? 1 : 2 ? 3 : 4").evaluate() == 3


def test_nested_ternary_in_when_false_returns_inner_right_value():
    assert pysel.Expression("0 ? 1 : 0 ? 2 : 3").evaluate() == 3
