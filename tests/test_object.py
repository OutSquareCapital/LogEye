from logeye import log


def test_object_tracking(capsys):
	obj = log({"x": 1})

	obj.x = 10

	out = capsys.readouterr().out
	assert "obj.x" in out
	assert "10" in out


def test_nested_object(capsys):
	obj = log({"a": {"b": 1}})

	obj.a.b = 5

	out = capsys.readouterr().out
	assert "a.b" in out
