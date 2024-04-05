# PySEL

The Python Simple Expression Language (PySEL) is a simple but powerful expression language that supports
manipulation and creation of basic python literals (`str`, `float`, `int`) using a majority of the available
operators, but also offers notable features such as attribute/property accessors and method invocation, as well
as a global scope at runtime in which you can inject any python object.

This is somewhat influenced by the 
[Spring Expression Language (SpEL)](https://docs.spring.io/spring-framework/docs/3.0.x/reference/expressions.html),
widely used by the Spring portfolio.

## Installation

PySEL can be installed using pip:

```shell
$ pip install pysel-lang
```

## Feature Overview

The expression language supports the following functionality:

- Literal expressions
- Logical, relational and mathematical operators
- Attribute/property access
- Method invocation
- Getitem (list indexing, slicing, dict accessing, etc)
- Ternary operator
- Environment value substitution

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
you can call the `compile()` method of the `Expression` class. This will parse and validate the expression and return
the compiled code object.

Invalid Expression:
```python
>>> import pysel
>>> exp = pysel.Expression("'foo")  # Invalid due to unclosed quotes
>>> exp.compile()
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
>>> exp.compile()
<code object <...? at 0x..., file "pysel_expr", line 1>
```

## Language Reference

### Literals

PySEL currently supports four different types of literals - string literals, integer literals, float literals, and `None`.

A string literal is any set of characters surrounded by a matching pair of quotes. Quotes can be either single quotation
marks (`'`) or double quotation marks (`"`). You can also include quotation marks in the string by escaping them using
a backslash:

```python
>>> pysel.Expression("'foo'").evaluate()
'foo'
>>> pysel.Expression('"foo"').evaluate()
'foo'
>>> pysel.Expression("'foo\\'s'").evaluate()
"foo's"
```

An integer literal is any set of consecutive digits (`0-9`). Unlike Python, PySEL allows integer literals to begin
with a `0` digit:

```python
>>> pysel.Expression("1234").evaluate()
1234
>>> pysel.Expression("01234").evaluate()
1234
```

A float literal is any set of consecutive digits `0-9` followed by a dot `.`. Float literals can also optionally
include digits after the decimal place - if none are specified, e.g. `2.` then the number will still parse correctly:

```python
>>> pysel.Expression("1.5").evaluate()
1.5
>>> pysel.Expression("1.").evaluate()
1.0
```

`None` is implemented identically to Python.

### Logical, relational and mathematical operators

The logical operators that are supported are `&&` (`and`), `||` (`or`) and `!` (`not`). Their use is shown below:

```python
# --- NOT ---
>>> pysel.Expression("!foo").evaluate({"foo": True})
False
>>> pysel.Expression("!foo").evaluate({"foo": False})
True
# --- AND ---
>>> pysel.Expression("foo && bar").evaluate({"foo": True, "bar": False})
False
>>> pysel.Expression("foo && bar").evaluate({"foo": True, "bar": True})
True
# --- OR ---
>>> pysel.Expression("foo || bar").evaluate({"foo": False, "bar": False})
False
>>> pysel.Expression("foo || bar").evaluate({"foo": False, "bar": True})
True
```

The relational operators that are supported are `==`, `!=`, `>`, `<`, `>=`, and `<=` - all using standard operator
notation:

```python
>>> pysel.Expression("2 == 2").evaluate()
True
>>> pysel.Expression("2 < 5").evaluate()
True
>>> pysel.Expression("2 != 2").evaluate()
False
...
```

PySEL supports all the same mathematical operators supported by Python, excluding the bitwise operators (for now).
Operator precedence follows the order specified in the "Operator Precedence" section.

```python
>>> pysel.Expression("2 + 2").evaluate()
4
>>> pysel.Expression("2 * 3").evaluate()
6
>>> pysel.Expression("5 // 2").evaluate()
2
...
```

### Attribute/property access

Attribute access in PySEL functions identically to that of Python - using the `.` operator:

```python
>>> pysel.Expression("'foo'.__class__").evaluate()
<class 'str'>
```

You can also chain attribute accessors to an unlimited depth, as with python:

```python
>>> pysel.Expression("'foo'.__class__.__name__").evaluate()
'str'
```

### Method invocation

As with attribute access, methods are invoked identically to the way you would using Python:

```python
>>> pysel.Expression("str()").evaluate()
''
```

PySEL also supports calling methods with an infinite number of arguments - however you should note that all
arguments will be passed **positionally**. Keyword arguments are not implemented:

```python
>>> pysel.Expression("str(10)").evaluate()
'10'
```

### Getitem (indexing, slicing, dict accessing)

PySEL's syntax for this is completely identical to Python's. A pair of square brackets immediately following any
expression are intepreted as a call to `object.__getitem__`, as with Python. This allows you to perform indexing,
slicing, and dictionary accessing as you would normally:

```python
>>> pysel.Expression("'foobar'[0]").evaluate()
'f'
>>> pysel.Expression("'foobar'[::-1]").evaluate()
'raboof'
>>> pysel.Expression("dict['foo']").evaluate({"dict": {"foo": "bar"}})
'bar'
```

### Ternary operator

PySEL supports the standard ternary operator found in many other languages including but not limited
to: C, JS, Java, etc. 

The syntax is: `condition ? when_true : when_false`.

This is functionally equivalent to:
```python
when_true if some_condition else when_false
```

Example:
```python
>>> pysel.Expression("cond ? 'foo' : 'bar'").evaluate({"cond": True})
'foo'
>>> pysel.Expression("cond ? 'foo' : 'bar'").evaluate({"cond": False})
'bar'
```

### Environment value substitution

As you may have seen in the previous sections, PySEL allows values to be substituted in place of identifiers in
any given expression. When calling `Expression.evaluate()`, you can optionally pass a mapping of identifier name
to value which will be accessible from the expression when it is run:

```python
>>> pysel.Expression("foo").evaluate({"foo": "bar"})
'bar'
```

The default environment contains four identifiers - `str`, `int`, `float` and `bool` - which are intended to be used
for casting values to different types within expressions, but of course you can use them for whatever you wish.

If you pass a mapping to the `evaluate` method, and some of the identifier names conflict with the ones mentioned above,
then the default identifiers will be overridden with the value that you passed:

```python
>>> pysel.Expression("str").evaluate()
<class 'str'>
>>> pysel.Expression("str").evaluate({"str": "foo"})
'foo'
```

## Operator Precedence

- Literals, parentheses
- Accessor (`.`, i.e. `foo.bar`)
- Method call (i.e. `foo()`), getitem (i.e. `'foo'[0]`)
- `**` (exponent)
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
all characters = ? All characters valid in a python string ?;

letter = ? All characters in set [a-zA-Z] ?;

digit = ? All characters in set [0-9] ?;

unop = "-" | "+" | "!";

binop = "==" | "!=" | ">" | "<" | ">=" | "<=" | "&&" | "||" |
        "+" | "-" | "*" | "/" | "%" | "//" | "**";

int = { digit };

float = int, "." [, int];

str = ("'" [, { all characters - "'" | "\'" }], "'") |
        ('"' [, { all characters - '"' | '\"' }], '"');

expr = int | str | float | expr binop expr | unop expr | ternary | identifier | accessor | methodcall | getitem;

ternary = expr, "?", expr, ":", expr;

identifier = (letter | "_") [, { letter | digit | "_" }];

accessor = expr, ".", identifier;

methodcall = expr, "(", expr [, { ",", expr }], ")";

slice = [expr, ] ":" [, expr] [, ":" [expr]]

getitem = expr "[", slice | expr, "]"
```
