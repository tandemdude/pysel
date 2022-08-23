import pysel


def test_float_returns_correct_value_with_numbers_after_decimal_point():
    assert pysel.Expression("16.5").evaluate() == 16.5


def test_float_returns_correct_value_with_no_numbers_after_decimal_point():
    assert pysel.Expression("2.").evaluate() == 2.0
