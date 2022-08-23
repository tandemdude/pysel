# PySEL

The Python Simple Expression Language (PySEL) is a simple but powerful expression language that supports
manipulation and creation of basic python literals (`str`, `float`, `int`) using a majority of the available
operators, but also offers notable features such as attribute/property accessors and method invocation, as well
as a global scope at runtime in which you can inject any python object.

This is somewhat influenced by the 
[Spring Expression Language (SpEL)](https://docs.spring.io/spring-framework/docs/3.0.x/reference/expressions.html),
widely used by the Spring portfolio.

## Feature Overview

The expression language supports the following functionality:

- Literal expressions
- Boolean, relational and mathematical operators
- Attribute/property access
- Method invocation
- Ternary operator
- Runtime environment injection

## Expression Evaluation

PySEL provides a utility class, `Expression` to allow you to run a valid expression in very few lines of code.

For example, the following expression, when evaluated, would return a string literal with value `Hello World!`:

```python
>>> import pysel
>>> exp = pysel.Expression("'Hello World!'")
```

To evaluate any expression, call the `evaluate()` method of the `Expression` object:

```python
>>> import pysel
>>> exp = pysel.Expression("'Hello World!")
>>> exp.evaluate()
'Hello World!'
```

You can also pass a mapping containing the execution environment for the expression. Any keys contained in the
environment can be accessed from within an expression using an identifier - the name of the key:

```python
>>> import pysel
>>> exp = pysel.Expression("foo")
>>> exp.evaluate({"foo": "bar"})
'bar'
```

If you do not wish to evaluate the expression immediately but would still like to know if it is syntactically valid,
you can call the `to_ast()` method of the `Expression` class. This will parse and validate the expression and return
the root node of the created abstract syntax tree.

Invalid Expression:
```python
>>> import pysel
>>> exp = pysel.Expression("'foo")  # Invalid due to unclosed quotes
>>> exp.to_ast()
Traceback (most recent call last):
  ...
    raise errors.ExpressionSyntaxError(
pysel.errors.ExpressionSyntaxError: Unexpected EOF while parsing
    "'foo"
     ^   
```

Valid Expression:
```python
>>> import pysel
>>> exp = pysel.Expression("'foo'")
>>> exp.to_ast()
Literal('foo')
```

## Operator Precedence

- Literals, parentheses
- Accessor (`.`, i.e. `foo.bar`)
- Method call (i.e. `foo()`)
- Unary `-`, `+`
- `*`, `/`, `//`, `%`
- Binary `-`, `+`
- `==`, `!=`, `>`, `<`, `>=`, `<=`
- `!`
- `&&`
- `||`
- Ternary (i.e. `expr ? expr : expr`)

## Grammar Specification

Note that this does not cover operator precedence, see the above section for that information.

The below is written using [Extended Backus-Naur form](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form):

```ebnf
all characters = /* All characters valid in a python string */;

letter = /* All characters in set [a-zA-Z] */;

digit = /* All characters in set [0-9] */;

unop = "-" | "+" | "!";

binop = "==" | "!=" | ">" | "<" | ">=" | "<=" | "&&" | "||" |
        "+" | "-" | "*" | "/" | "%" | "//";

int = { digit };

float = int, "." [, int];

str = ("'" [, { all characters - "'" | "\'" }], "'") |
        ('"' [, { all characters - '"' | '\"' }], '"');

expr = int | str | float | expr binop expr | unop expr | ternary | identifier | accessor | methodcall;

ternary = expr, "?", expr, ":", expr;

identifier = (letter | "_") [, { letter | digit | "_" }];

accessor = expr, ".", identifier;

methodcall = expr, "(", expr [, { ",", expr }], ")";
```

# TODO

- Language reference
- Docstrings
- Doc generation
