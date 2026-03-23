from logeye import log


@log
def add(a, b):
	result = a + b
	return result


def test_logged_function(capsys):
	res = add(2, 3)

	out = capsys.readouterr().out

	assert "call" in out
	assert "return" in out
	assert res == 5
