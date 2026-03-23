from logeye import log


def test_plain_message(capsys):
	log("hello")

	out = capsys.readouterr().out
	assert "hello" in out
	assert "(set)" not in out


def test_format_args(capsys):
	x = 5
	log("value is {}", x)

	out = capsys.readouterr().out
	assert "value is 5" in out


def test_template_expand(capsys):
	x = 10
	log("x is $x")

	out = capsys.readouterr().out
	assert "x is 10" in out
