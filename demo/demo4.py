from logeye import log

obj = log({
	"x": 4,
	"y": {
		"z": 5
	}
})

obj.x = 4
obj.y.z = 5

a, b = log("x"), log("y")

c = log("z")

f = lambda: log("inside lambda")
f()
