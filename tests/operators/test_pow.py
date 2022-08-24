import pysel


def test_operator_returns_correct_value():
    assert pysel.Expression("3 ** 3").evaluate() == 27
