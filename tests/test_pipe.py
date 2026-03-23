from logeye import l


def test_pipe_basic(capsys):
	x = 10 | l

	out = capsys.readouterr().out
	assert "(set) x =" in out
	assert "10" in out


def test_pipe_expression(capsys):
	x = (5 + 5) | l

	out = capsys.readouterr().out
	assert "10" in out


def test_callable_l(capsys):
	x = l(20)

	out = capsys.readouterr().out
	assert "(set) x =" in out
	assert "20" in out
