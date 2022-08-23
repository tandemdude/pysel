import pysel


def test_operator_returns_correct_value():
    assert pysel.Expression("5 // 2").evaluate() == 2
