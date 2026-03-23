from logeye import log


def test_basic_assignment(capsys):
	x = log("world")

	out = capsys.readouterr().out
	assert "(set) x =" in out
	assert "world" in out
	assert x == "world"


def test_numeric_assignment(capsys):
	x = log(42)

	out = capsys.readouterr().out
	assert "(set) x = 42" in out


def test_multiple_assignments(capsys):
	a = log("a")
	b = log("b")

	out = capsys.readouterr().out
	assert "(set) a =" in out
	assert "(set) b =" in out


def test_tuple_unpacking(capsys):
	a, b = log("x"), log("y")

	out = capsys.readouterr().out

	assert "(set) a = 'x'" in out
	assert "(set) b = 'y'" in out
