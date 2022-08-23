import pysel


def test_operator_returns_correct_value():
    assert pysel.Expression("-1").evaluate() == -1
