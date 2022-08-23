import pysel


def test_accessor_returns_correct_value():
    assert pysel.Expression("pysel.__version__").evaluate({"pysel": pysel}) == pysel.__version__


def test_chained_accessor_returns_correct_value():
    assert pysel.Expression("obj.__class__.__name__").evaluate({"obj": pysel.Expression("")}) == "Expression"
