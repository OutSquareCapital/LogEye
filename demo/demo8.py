from logeye import *


@log
class User:
	def __init__(self):
		self.name = "Matt"
		self.active = True


user = l(User())
user.name = "For"
