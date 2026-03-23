from logeye import log, l


def test_lambda_direct(capsys):
	f = lambda: log("lambda")

	f()
	out = capsys.readouterr().out

	assert "lambda" in out


def test_lambda_assignment(capsys):
	f = lambda: log("inside")
	x = f()

	out = capsys.readouterr().out

	assert "inside" in out
	assert x == "inside"


def test_nested_lambda(capsys):
	f = lambda: (lambda: log("deep"))()

	result = f()
	out = capsys.readouterr().out

	assert "deep" in out
	assert result == "deep"


def test_lambda_returning_lambda(capsys):
	f = lambda: (lambda: log("inner"))

	inner = f()
	result = inner()

	out = capsys.readouterr().out

	assert "inner" in out
	assert result == "inner"


def test_nested_lambda_assignment(capsys):
	f = lambda: (lambda: log("nested"))()

	x = f()
	out = capsys.readouterr().out

	assert "nested" in out
	assert x == "nested"


def test_complex_nested_lambda(capsys):
	f = lambda: (lambda x: log(f"value {x}"))(5)

	result = f()
	out = capsys.readouterr().out

	assert "value 5" in out
	assert result == "value 5"


def test_lambda_wrapped(capsys):
	f = lambda x: x * 2
	f = l(f)

	f(3)
	out = capsys.readouterr().out

	assert "call" in out or "set" in out
