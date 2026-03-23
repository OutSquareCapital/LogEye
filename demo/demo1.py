from logeye import log


@log
def total(a, b):
	result = a + b
	result = result * 2
	result = result + 5
	return result


if __name__ == "__main__":
	answer = total(3, 4)

	x = log("we")
	y = log(10)

	log("test is $x")

