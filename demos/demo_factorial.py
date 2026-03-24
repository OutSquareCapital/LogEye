from logeye import log, l

l("FACTORIAL - BY ITERATION")


# Iteration
@log
def factorial(n):
	result = 1
	for i in range(1, n + 1):
		result *= i
	return result


factorial(5)

l("FACTORIAL - BY RECURSION")


# Recursion
@log
def factorial(n):
	if n == 1:
		return 1
	return n * factorial(n - 1)


factorial(5)
