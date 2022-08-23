import pytest

import pysel


def test_string_has_correct_value_single_quotes():
    assert pysel.Expression("'foo'").evaluate() == "foo"


def test_string_has_correct_value_double_quotes():
    assert pysel.Expression('"foo"').evaluate() == "foo"


def test_string_has_correct_value_escaped_quotes():
    assert pysel.Expression("'foo\\'s'").evaluate() == "foo's"


def test_raises_ExpressionSyntaxError_error_for_unclosed_quotes():
    with pytest.raises(pysel.errors.ExpressionSyntaxError) as ex:
        pysel.Expression("'foo").evaluate()
