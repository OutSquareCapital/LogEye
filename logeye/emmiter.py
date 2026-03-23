import os
import time

from . import config
from .formatting import _formatter
from .introspection import _is_user_code


def _write_line_to_file(filepath, line):
	directory = os.path.dirname(filepath)
	if directory:
		os.makedirs(directory, exist_ok=True)

	with open(filepath, "a", encoding="utf-8") as f:
		f.write(line + "\n")


def _emit(kind, name, value, *, filename=None, lineno=None, filepath=None):
	if config._START_TIME is None:
		config._START_TIME = time.perf_counter()

	if not config._ENABLED:
		return

	if filename and not _is_user_code(filename):
		return

	elapsed = time.perf_counter() - config._START_TIME
	line = _formatter(elapsed, kind, name, value, filename, lineno)

	if filepath is not None:
		_write_line_to_file(filepath, line)
		return

	if config._GLOBAL_LOG_FILE_ENABLED and config._GLOBAL_LOG_FILE:
		_write_line_to_file(config._GLOBAL_LOG_FILE, line)
		return

	print(line)
