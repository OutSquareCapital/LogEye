from logeye import *

l("DIJKSTRA - SHORTEST PATH")


@log
def dijkstra(graph, start):
	distances = {node: float("inf") for node in graph}
	distances[start] = 0

	visited = set()
	queue = [(0, start)]

	while queue:
		current_dist, node = queue.pop(0)

		if node in visited:
			continue

		visited.add(node)

		for neighbor, weight in graph[node].items():
			new_dist = current_dist + weight

			if new_dist < distances[neighbor]:
				distances[neighbor] = new_dist
				queue.append((new_dist, neighbor))

		queue.sort()

	return distances


graph = {
	"A": {"B": 1, "C": 4},
	"B": {"C": 2, "D": 5},
	"C": {"D": 1},
	"D": {}
}

dijkstra(graph, "A")
