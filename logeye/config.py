import os
import sys
from typing import Literal

_ENABLED = True
_START_TIME = None

# "absolute" -> full path
# "project"  -> relative to project root
# "file"     -> filename only
_PATH_MODE = "file"

# Whether message logs include timestamp + file info
_SHOW_MESSAGE_META = True
_DECORATORS_ONLY = False
_LOG_MODE = "full"  # "full" | "educational"

_SHOW_TIME = True
_SHOW_FILE = True
_SHOW_LINENO = True

_PROJECT_ROOT = os.getcwd()
_LIBRARY_ROOT = os.path.dirname(__file__)
_EXEC_ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))

_LOG_PIPE_NAME = "l"

_GLOBAL_LOG_FILE = None
_GLOBAL_LOG_FILE_ENABLED = True
type PathMode = Literal["absolute", "project", "file"]

type Mode = Literal["edu", "educational", "full"]

# =========
#  TOGGLES
# =========

def toggle_logs(enabled: bool) -> None:
	global _ENABLED
	_ENABLED = enabled


def toggle_global_log_file(enabled: bool) -> None:
	global _GLOBAL_LOG_FILE_ENABLED
	_GLOBAL_LOG_FILE_ENABLED = enabled


def toggle_decorator_log_only(enabled: bool) -> None:
	"""
	Toggle only @log-decorated tracing.
	"""

	global _DECORATORS_ONLY
	_DECORATORS_ONLY = enabled


def toggle_message_metadata(enabled: bool) -> None:
	"""
	Enable or disable metadata for message logs

	If disabled:
		log("hello") -> prints just "hello"

	If enabled:
		log("hello") -> prints "[time] file:line hello"
	"""

	global _SHOW_MESSAGE_META
	_SHOW_MESSAGE_META = enabled


# =========
#  SETTERS
# =========
def set_mode(mode: Mode) -> None:
	"""
	Set global logging mode
	full or  edu / educational
	"""

	global _LOG_MODE
	_LOG_MODE = _normalize_mode(mode)


def set_global_log_file(filepath: str | None) -> None:
	"""
	Route LogEye output to this file globally.
	"""
	global _GLOBAL_LOG_FILE
	_GLOBAL_LOG_FILE = None if filepath is None else os.fspath(filepath)


def set_path_mode(mode: PathMode) -> None:
	global _PATH_MODE

	_PATH_MODE = mode

def _normalize_mode(mode: Mode) -> Mode:
	if mode in ("edu", "educational"):
		return "educational"

	if mode == "full":
		return "full"
