import pysel

exp = pysel.Expression("10 + 9.8")
print(exp.to_ast())
