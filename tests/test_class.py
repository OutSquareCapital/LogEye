from logeye import log, l


@log
class User:
	def __init__(self):
		self.name = "Matt"


def test_class_logging(capsys):
	user = l(User())
	user.name = "For"

	out = capsys.readouterr().out
	assert "user.name" in out or "name" in out
