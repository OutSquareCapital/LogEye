import time

from . import config
from .formatting import _formatter
from .introspection import _is_user_code


def _emit(kind, name, value, *, filename=None, lineno=None):
	if not config._ENABLED:
		return

	if filename and not _is_user_code(filename):
		return

	elapsed = time.perf_counter() - config._START_TIME
	print(_formatter(elapsed, kind, name, value, filename, lineno))
