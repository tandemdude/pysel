import pysel


def test_operator_returns_true():
    assert pysel.Expression("1 || 0").evaluate() == 1
    assert pysel.Expression("0 || 1").evaluate() == 1


def test_operator_returns_false():
    assert pysel.Expression("0 || 0").evaluate() == 0
