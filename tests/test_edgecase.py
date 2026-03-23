import pytest
from logeye import log


def test_inline_expression(capsys):
	x = "a" + log("b")

	out = capsys.readouterr().out

	assert "b" in out
	assert x == "ab"


def test_tuple_unpacking(capsys):
	a, b = log("x"), log("y")

	out = capsys.readouterr().out

	assert "(set) a =" in out
	assert "(set) b =" in out


def test_inline_expression_error():
	with pytest.raises(TypeError):
		x = 1 + log("a")


def test_invalid_path_mode():
	from logeye import set_path_mode

	with pytest.raises(ValueError):
		set_path_mode("invalid")
