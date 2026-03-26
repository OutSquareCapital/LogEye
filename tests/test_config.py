from logeye import log, config


def test_logoff(capsys):
	config.toggle_logs(False)
	config.toggle_decorator_log_only(False)

	log("hidden")

	out = capsys.readouterr().out
	assert out == ""


def test_logon(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(False)

	log("visible")

	out = capsys.readouterr().out
	assert "visible" in out


def test_path_modes(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(False)

	config.set_path_mode("absolute")
	log("test")

	out = capsys.readouterr().out
	assert "/" in out


def test_decorator_only_blocks_normal_logs(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(True)

	log("should not appear")

	out = capsys.readouterr().out
	assert out == ""


def test_decorator_only_allows_decorated(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(True)

	@log
	def foo():
		x = 10
		return x

	foo()

	out = capsys.readouterr().out
	assert "foo" in out


def test_level_call_only(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(False)

	@log(level="call")
	def foo():
		x = 10
		return x

	foo()

	out = capsys.readouterr().out

	assert "(call)" in out
	assert "(return)" in out
	assert "(set)" not in out  # no variable logs


def test_level_state(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(False)

	@log(level="state")
	def foo():
		x = 10
		return x

	foo()

	out = capsys.readouterr().out

	assert "(set)" in out
	assert "(call)" not in out


def test_filter_variables(capsys):
	config.toggle_logs(True)
	config.toggle_decorator_log_only(False)

	@log(filter=["x"])
	def foo():
		x = 10
		y = 20
		return x + y

	foo()

	out = capsys.readouterr().out

	assert "foo.x" in out
	assert "foo.y" not in out
