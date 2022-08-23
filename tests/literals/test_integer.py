import pysel


def test_literal_returns_correct_value():
    assert pysel.Expression("1234567").evaluate() == 1234567
