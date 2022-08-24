import pytest

import pysel


def test_getitem_returns_correct_value_with_single_param():
    assert pysel.Expression("'foo'[0]").evaluate() == "f"


def test_getitem_returns_correct_value_with_two_params():
    assert pysel.Expression("'foo'[0:-1]").evaluate() == "fo"


def test_getitem_returns_correct_value_with_three_arguments():
    assert pysel.Expression("'foobar'[4:1:-1]").evaluate() == "abo"


def test_getitem_returns_correct_value_with_single_colon():
    assert pysel.Expression("'foo'[:]").evaluate() == "foo"


def test_getitem_returns_correct_value_with_two_colons():
    assert pysel.Expression("'foo'[::]").evaluate() == "foo"


def test_getitem_returns_correct_value_missing_first_param():
    assert pysel.Expression("'foo'[:2]").evaluate() == "fo"


def test_getitem_returns_correct_value_missing_second_param():
    assert pysel.Expression("'foo'[1:]").evaluate() == "oo"


def test_getitem_returns_correct_value_missing_first_and_second_param():
    assert pysel.Expression("'foo'[::-1]").evaluate() == "oof"


def test_getitem_rasies_error_when_no_params():
    with pytest.raises(pysel.errors.ExpressionSyntaxError):
        pysel.Expression("'foo'[]").evaluate()
