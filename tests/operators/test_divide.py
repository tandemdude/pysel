import pysel


def test_operator_returns_correct_value():
    assert pysel.Expression("10 / 5").evaluate() == 2.0
