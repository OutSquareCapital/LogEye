from logeye import log, l

x = log(10)
message = log("Hello from {name}", name="Matt")


@log(level="call")
def add(a, b):
	something = 2 + 2
	return a + b


add(2, 2)

name = "Matt"
message2 = log("Hello from $name")

config = log({"debug": True, "port": 8080})
config.port = 9090
config["debug"] = False

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

email = "mattfor@relaxy.xyz"
log("\nCurrent user: $name\nEmail: $email")

log("\nCurrent user: {}\nEmail: {}", "Matt", "mattfor@relaxy.xyz")


@log
class User:
	def __init__(self):
		self.name = "Matt"
		self.active = True


user = l(User())
user.name = "For"

q = log(10)
w = l(20)
e = 30 | l

r, t = log("hello"), log("world")

f = (10 + 5) | l
g = l(100 + 200)
