from logeye import log

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
