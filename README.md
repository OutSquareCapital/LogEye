![PyPI](https://img.shields.io/pypi/v/logeye)
![Python](https://img.shields.io/pypi/pyversions/logeye)
![License](https://img.shields.io/github/license/MattFor/LogEye)

# LogEye

Frictionless runtime logging for Python variables, objects, messages, and functions.

## Installation

```bash
pip install logeye
```

## Who is it for

LogEye is for people who want to understand exactly what happens, when and where in their code. (Python beginners rejoice!)

**No more print() debugging everywhere, no more need to launch the debugger, everything's automatic!**

It's incredibly useful in quickly seeing how algorithms work without hooking up frameworks or debuggers!  

LogEye is designed for debugging, learning, and development workflows. It is not intended for:  
- performance-critical paths
- production logging systems

Name inference is not always 100% accurate, however I've tried to the best of my abilities to have it work here.


## What it does

`logeye` lets you:

* log values as they are assigned, with automatic variable name inference (including tuple assignments and multi-line
  statements)
* wrap mappings and objects to track attribute and item changes in real time
* emit JSON-like snapshots of objects on creation, followed by granular change logs
* recursively track nested data structures (dicts, lists, tuples, sets)
* log functions to capture calls, arguments, local variable changes, and return values
* automatically wrap and log callable values (including lambdas when passed through `log`)
* print formatted messages using `str.format`, `$template`, and caller scope variables
* support inline logging via a pipe operator (`| l`) with or without assignment
* infer variable names from runtime context using AST analysis (including multi-line assignments)
* log multiple values correctly in tuple assignments on the same line
* provide lightweight value logging via `watch()` without altering behaviour
* enable or disable logging globally with zero overhead when turned off
* customise output formatting, metadata visibility, and file path display modes
* automatically label recurrency / nested calls f.e `factorial factorial_2 factorial_3`

## Limitations

* variable name inference is **best-effort** and may fail in complex or highly dynamic expressions
* some edge cases (e.g. deeply nested calls, chained expressions, unusual syntax) may fall back to a generic name like
  `"set"`
* lambda functions are **not automatically traced** unless explicitly wrapped with `log()`
* function tracing relies on `sys.settrace()` and may introduce overhead in performance-sensitive code
* logging inside heavily recursive or multithreaded code may produce noisy or hard-to-follow output
* AST-based analysis requires access to source files and may not work correctly in environments without source code (
  e.g. compiled/obfuscated code, some REPLs)
* tuple assignment tracking depends on call order and may behave unexpectedly in complex expressions
* object wrapping only supports mappings and objects with `__dict__`
* custom objects with unusual attribute behaviour may not be fully tracked
* logging output is intended for debugging and introspection, not structured logging or production telemetry

## Quick start

```python
from logeye import log

x = log(10)
message = log("Hello from {name}", name="Matt")

name = "Matt"
message2 = log("Hello from $name")

config = log({"debug": True, "port": 8080})
config.port = 9090
config["debug"] = False
```

Example output:

```commandline
[0.000s] demo6.py:3 (set) x = 10
[0.000s] demo6.py:4 (set) message = 'Hello from Matt'
[0.000s] demo6.py:7 (set) message2 = 'Hello from Matt'
[0.001s] demo6.py:10 (change) config.port = 9090
[0.001s] demo6.py:11 (change) config.debug = False
```

## Logging functions

Decorate a function or wrap it with `log`:

```python
from logeye import log


@log
def add(a, b):
	total = a + b
	return total


add(2, 3)
```

```commandline
[0.001s] demo9.py:17 (call) add = {'args': (2, 3), 'kwargs': {}}
[0.001s] demo9.py:13 (set) add.a = 2
[0.001s] demo9.py:13 (set) add.b = 3
[0.001s] demo9.py:14 (set) add.total = 5
[0.001s] demo9.py:14 (return) add = 5
```

This will log:

* the function call
* local variable changes inside the function
* the return value

## Logging objects

`log()` can wrap mappings and objects with `__dict__` into a `LoggedObject`:

```python
from logeye import log

settings = log({"theme": "dark", "volume": 3})
settings.theme = "light"
settings.volume += 1
```

You can also pass an object:

```python
from logeye import *


@log
class User:
	def __init__(self):
		self.name = "Matt"
		self.active = True


user = l(User())
user.name = "For"
```

```commandline
[0.001s] demo8.py:11 (call) User.__init__ = {'args': (<__main__.User object at 0x7fbacb1f0980>,), 'kwargs': {}}
[0.001s] demo8.py:7 (set) user.name = 'Matt'
[0.001s] demo8.py:8 (set) user.active = True
[0.001s] demo8.py:11 (set) user = {}
[0.001s] demo8.py:12 (set) user.name = 'For'
```

## Messages

Use `log()` with a string to emit a formatted message:

```python
from logeye import log

name = "Matt"
email = "mattfor@relaxy.xyz"
log("Current user: $name\nEmail: $email")

# Also works like this!
log("Current user: {}\nEmail: {}", "Matt", "mattfor@relaxy.xyz")
```

```commandline
[0.001s] demo9.py:5 
Current user: Matt
Email: mattfor@relaxy.xyz
[0.002s] demo9.py:7 
Current user: Matt
Email: mattfor@relaxy.xyz
```

`str.format()` is tried first. If that fails, the logger also tries caller globals / locals and template substitution.

## Utility functions

### `watch(value, name=None)`

Wraps a value for logging without changing its type unless needed.

### `logoff()` / `logon()`

Disable or enable logging globally.

### `set_path_mode(mode)`

Controls how file paths are shown in output.

Accepted values:

* `absolute`
* `project`
* `file`

### `set_output_formatter(func)`

Replace the default formatter.

Signature:

```python
func(elapsed, kind, name, value, filename, lineno)
```

### `reset_output_formatter()`

Restore the built-in formatter.

## Using `LoggedObject` directly

```python
from logeye import LoggedObject

obj = LoggedObject({"a": 1, "nested": {"b": 2}}, name="data")
obj.a = 5
obj.nested.b = 9
```

Convert it back to a plain dictionary with:

```python
plain = obj.to_dict()
```

## Output format

By default, messages look like this:  
(note, the path by default is relative to the run directory of the file you're launching the module in)

```commandline
[0.123s] path/to/file.py:42 (set) x = 10
```

For plain messages:

```commandline
[0.123s] path/to/file.py:42 some text
```

# Example

```python
from logeye import *

l("FACTORIAL - BY ITERATION")


# Iteration
@log
def factorial(n):
	result = 1
	for i in range(1, n + 1):
		result *= i
	return result


factorial(5)

l("FACTORIAL - BY RECURRENCY")


# Recurrency
@log
def factorial(n):
	if n == 1:
		return 1
	return n * factorial(n - 1)


factorial(5)
```

Output:
```commandline
[0.002s] demo_factorial.py:3 FACTORIAL - BY ITERATION
[0.002s] demo_factorial.py:15 (call) factorial = {'args': (5,), 'kwargs': {}}
[0.002s] demo_factorial.py:9 (set) factorial.n = 5
[0.002s] demo_factorial.py:10 (set) factorial.result = 1
[0.002s] demo_factorial.py:11 (set) factorial.i = 1
[0.002s] demo_factorial.py:11 (set) factorial.i = 2
[0.002s] demo_factorial.py:10 (set) factorial.result = 2
[0.002s] demo_factorial.py:11 (set) factorial.i = 3
[0.002s] demo_factorial.py:10 (set) factorial.result = 6
[0.002s] demo_factorial.py:11 (set) factorial.i = 4
[0.002s] demo_factorial.py:10 (set) factorial.result = 24
[0.002s] demo_factorial.py:11 (set) factorial.i = 5
[0.002s] demo_factorial.py:10 (set) factorial.result = 120
[0.002s] demo_factorial.py:12 (return) factorial = 120
[0.002s] demo_factorial.py:17 FACTORIAL - BY RECURRENCY
[0.002s] demo_factorial.py:28 (call) factorial = {'args': (5,), 'kwargs': {}}
[0.002s] demo_factorial.py:23 (set) factorial.n = 5
[0.002s] demo_factorial.py:25 (call) factorial_2 = {'args': (4,), 'kwargs': {}}
[0.002s] demo_factorial.py:23 (set) factorial_2.n = 4
[0.002s] demo_factorial.py:25 (call) factorial_3 = {'args': (3,), 'kwargs': {}}
[0.002s] demo_factorial.py:23 (set) factorial_3.n = 3
[0.002s] demo_factorial.py:25 (call) factorial_4 = {'args': (2,), 'kwargs': {}}
[0.002s] demo_factorial.py:23 (set) factorial_4.n = 2
[0.002s] demo_factorial.py:25 (call) factorial_5 = {'args': (1,), 'kwargs': {}}
[0.002s] demo_factorial.py:23 (set) factorial_5.n = 1
[0.002s] demo_factorial.py:24 (return) factorial_5 = 1
[0.002s] demo_factorial.py:25 (return) factorial_4 = 2
[0.002s] demo_factorial.py:25 (return) factorial_3 = 6
[0.002s] demo_factorial.py:25 (return) factorial_2 = 24
[0.002s] demo_factorial.py:25 (return) factorial = 120

Process finished with exit code 0
```

# Inspiration
Idea came to be during Warsaw IT Days 2026. During the Python lecture "Logging module adventures".  
I thought there definitely was an easier way to do it without repeating yourself constantly, and it turns out there was!

## Contact

If you have questions, ideas, or run into issues:

- please open an issue!
- or email me mattfor@relaxy.xyz
- or add me on discord @mattfor

## License

MIT License © 2026

See [LICENSE](LICENSE) for details.

