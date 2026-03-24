from logeye import log, set_output_formatter, reset_output_formatter


def custom_formatter(elapsed, kind, name, value):
	return f"{elapsed:0.2f}s | {kind.upper():6} | {name} -> {value!r}"


set_output_formatter(custom_formatter)

x = log(10)
message = log("hello")


@log
def total(a, b):
	result = a + b
	result = result * 2
	result = result + 5
	return result


if __name__ == "__main__":
	answer = total(3, 4)
	print("final answer:", answer)

	reset_output_formatter()
	y = log(99)
