import pysel


def test_environment_substitution_returns_correct_value():
    assert pysel.Expression("foo").evaluate({"foo": 123}) == 123
