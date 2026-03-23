from logeye import log, watch, set_output_formatter, reset_output_formatter


def custom_formatter(elapsed, kind, name, value):
	return f"{elapsed:0.3f}s | {kind:<6} | {name} = {value!r}"


set_output_formatter(custom_formatter)


@log
def outer(seed):
	base = seed * 2

	@log
	def middle(step):
		total = base + step

		def inner(x):
			temp = x * x
			temp = temp + total
			return temp

		a = inner(1)
		b = inner(2)
		total = a + b
		return total

	first = middle(3)
	second = middle(5)
	result = first + second
	return result


@log
def factorial(n):
	if n <= 1:
		return 1
	return n * factorial(n - 1)


@log
def compute(values):
	running = 0

	def add_one(v):
		part = v + 1
		return part

	for item in values:
		item = watch(item)
		running = running + add_one(item)

	if running > 10:
		running = running * 2
	else:
		running = running - 2

	return running


if __name__ == "__main__":
	x = watch(10)
	y = watch(25)

	a = outer(4)
	b = factorial(5)
	c = compute([1, 2, 3, 4])

	reset_output_formatter()
	z = watch(99)

	print("results:", a, b, c, z)
