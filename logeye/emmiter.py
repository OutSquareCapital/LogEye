from __future__ import annotations
import os
import time
from typing import TYPE_CHECKING

from . import config
from .formatting import _formatter
from .introspection import _is_user_code
if TYPE_CHECKING:
	from .core import Kind

def _write_line_to_file(filepath: str, line: str) -> None:
	directory = os.path.dirname(filepath)
	if directory:
		os.makedirs(directory, exist_ok=True)

	with open(filepath, "a", encoding="utf-8") as f:
		f.write(line + "\n")


def _emit(kind: Kind, name: str, value: object, *, filename: str | None=None, lineno: int | None=None, filepath: str | None=None, show_time: bool=True, show_file: bool=True, show_lineno: bool=True) -> None:
	if config._START_TIME is None:
		config._START_TIME = time.perf_counter()

	if not config._ENABLED:
		return

	if filename and not _is_user_code(filename):
		return

	if config._LOG_MODE == "educational":
		if kind == "change" and isinstance(value, dict):
			if value.get("op") == "extend" and not value.get("value"):
				return

	if config._LOG_MODE == "educational":
		filename = None
		lineno = None

	elapsed = time.perf_counter() - config._START_TIME
	line = _formatter(
		elapsed,
		kind,
		name,
		value,
		filename,
		lineno,
		show_time=show_time,
		show_file=show_file,
		show_lineno=show_lineno,
	)

	# Educational mode is on, ignoring stuff
	if not line:
		return

	if filepath is not None:
		_write_line_to_file(filepath, line)
		return

	if config._GLOBAL_LOG_FILE_ENABLED and config._GLOBAL_LOG_FILE:
		_write_line_to_file(config._GLOBAL_LOG_FILE, line)
		return

	print(line)
