from logeye import log, logoff, logon, set_path_mode


def test_logoff(capsys):
	logoff()
	log("hidden")

	out = capsys.readouterr().out
	assert out == ""


def test_logon(capsys):
	logon()
	log("visible")

	out = capsys.readouterr().out
	assert "visible" in out


def test_path_modes(capsys):
	set_path_mode("absolute")
	log("test")

	out = capsys.readouterr().out
	assert "/" in out  # crude but works
