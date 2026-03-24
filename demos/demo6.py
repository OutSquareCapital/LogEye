from logeye import log

x = log(10)
message = log("Hello from {name}", name="Matt")

name = "Matt"
message2 = log("Hello from $name")

config = log({"debug": True, "port": 8080})
config.port = 9090
config["debug"] = False
