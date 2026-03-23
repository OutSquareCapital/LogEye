from logeye import log


def inner():
	return log("inner")


def outer():
	return inner()


def test_nested_calls(capsys):
	x = outer()

	out = capsys.readouterr().out

	assert "inner" in out
	assert x == "inner"
