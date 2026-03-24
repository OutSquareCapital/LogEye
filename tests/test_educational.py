from logeye import log, set_mode


def test_call_formatting(capsys):
	@log(mode="edu")
	def foo(x):
		return x

	foo(5)

	out = capsys.readouterr().out

	assert "Calling foo(5)" in out
	assert "(call)" not in out
	assert "test_" not in out


def test_return_formatting(capsys):
	@log(mode="edu")
	def foo():
		return 123

	foo()

	out = capsys.readouterr().out

	assert "foo() returned 123" in out
	assert "(return)" not in out


def test_args_and_kwargs(capsys):
	@log(mode="edu")
	def foo(a, b=2):
		return a + b

	foo(1, b=3)

	out = capsys.readouterr().out

	assert "Calling foo(1, b=3)" in out


def test_no_kwargs_noise(capsys):
	@log(mode="edu")
	def foo(x):
		return x

	foo(10)

	out = capsys.readouterr().out

	assert "{}" not in out
	assert "kwargs" not in out


def test_nested_function_name(capsys):
	@log(mode="edu")
	def outer():
		def inner():
			return 5

		return inner()

	outer()

	out = capsys.readouterr().out

	assert "Calling inner()" in out or "Calling outer.inner()" in out


def test_append_human_readable(capsys):
	@log(mode="edu")
	def foo():
		arr = []
		arr.append(5)

	foo()

	out = capsys.readouterr().out

	assert "Added 5 to the end of arr" in out


def test_extend_single_value(capsys):
	@log(mode="edu")
	def foo():
		arr = []
		arr.extend([7])

	foo()

	out = capsys.readouterr().out

	assert "Added 7 to arr" in out


def test_extend_multiple_values(capsys):
	@log(mode="edu")
	def foo():
		arr = []
		arr.extend([1, 2, 3])

	foo()

	out = capsys.readouterr().out

	assert "Added [1, 2, 3] to arr" in out


def test_no_set_prefix(capsys):
	@log(mode="edu")
	def foo():
		x = 10
		return x

	foo()

	out = capsys.readouterr().out

	assert "(set)" not in out


def test_variable_visible(capsys):
	@log(mode="edu")
	def foo():
		x = 42
		return x

	foo()

	out = capsys.readouterr().out

	assert "x = 42" in out or "foo.x = 42" in out


def test_log_inside_function_inherits_mode(capsys):
	@log(mode="edu")
	def foo():
		x = 5
		log("Value is $x")

	foo()

	out = capsys.readouterr().out

	assert "Value is 5" in out
	assert "test_" not in out


def test_no_file_info(capsys):
	@log(mode="edu")
	def foo():
		x = 1

	foo()

	out = capsys.readouterr().out

	assert ".py:" not in out


def test_time_present(capsys):
	@log(mode="edu")
	def foo():
		pass

	foo()

	out = capsys.readouterr().out

	assert "[" in out and "s]" in out


def test_algorithm_like_flow(capsys):
	@log(mode="edu")
	def simple():
		arr = []
		arr.append(3)
		arr.append(1)
		arr.extend([2])

		log("Final: $arr")

		return arr

	simple()

	out = capsys.readouterr().out

	assert "Added 3 to the end of arr" in out
	assert "Added 1 to the end of arr" in out
	assert "Added 2 to arr" in out
	assert "Final: [3, 1, 2]" in out


def test_global_mode_full(capsys):
	set_mode("full")

	try:

		@log
		def foo():
			return 1

		foo()

		out = capsys.readouterr().out

		assert "(call)" in out
		assert "Calling" not in out
	finally:
		set_mode("full")


def test_global_mode_edu(capsys):
	set_mode("edu")

	try:

		@log
		def foo():
			return 1

		foo()

		out = capsys.readouterr().out

		assert "Calling foo()" in out
		assert "(call)" not in out
	finally:
		set_mode("full")


def test_mode_toggle_mid_execution(capsys):
	set_mode("full")

	try:

		@log
		def foo():
			a = 1  # full mode
			set_mode("edu")
			b = 2  # edu mode
			set_mode("full")
			c = 3  # back to full

		foo()

		out = capsys.readouterr().out

		assert "(set)" in out or "foo.a" in out
		assert "(set)" in out or "foo.c" in out
		assert "b = 2" in out

	finally:
		set_mode("full")
