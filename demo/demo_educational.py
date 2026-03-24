from logeye import log


@log(mode="edu")
def radix_sort_lsd(arr):
	if not arr:
		return arr

	max_num = max(arr)
	exp = 1  # 1, 10, 100...

	while max_num // exp > 0:
		buckets = [[] for _ in range(10)]

		# Distribute into buckets
		for num in arr:
			digit = (num // exp) % 10
			buckets[digit].append(num)

		# Collect back
		arr = []
		for i, bucket in enumerate(buckets):
			arr.extend(bucket)

		# Wrapper options automatically passed here!!!!
		log("After pass: $arr")

		exp *= 10

	return arr


if __name__ == "__main__":
	data = [170, 45, 75, 90, 802, 24, 2, 66]

	sorted_data = radix_sort_lsd(data)

	# Match pretty output
	log("Sorted: $sorted_data", show_file=False, show_lineno=False)
