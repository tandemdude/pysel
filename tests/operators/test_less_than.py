import pysel


def test_operator_returns_true():
    assert pysel.Expression("1 < 2").evaluate() is True


def test_operator_returns_false():
    assert pysel.Expression("1 < 1").evaluate() is False
