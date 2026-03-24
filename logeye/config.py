import os
import sys

from typing import Literal, TypeAlias

_g_enabled = True
_g_start_time = None

# "absolute" -> full path
# "project"  -> relative to project root
# "file"     -> filename only
_g_path_mode = "file"

# Whether message logs include timestamp + file info
_g_show_message_meta = True
_g_deco_only = False
_g_log_mode = "full"  # "full" | "educational"

_g_show_time = True
_g_show_file = True
_g_show_lineno = True

_g_project_root = os.getcwd()
_g_library_root = os.path.dirname(__file__)
_g_exec_root = os.path.dirname(os.path.abspath(sys.argv[0]))

_g_log_pipe_name = "l"

_g_log_file = None
_g_log_file_enabled = True
PathMode: TypeAlias = Literal["absolute", "project", "file"]

Mode: TypeAlias = Literal["edu", "educational", "full"]


# =========
#  TOGGLES
# =========


def toggle_logs(enabled: bool) -> None:
	global _g_enabled
	_g_enabled = enabled


def toggle_global_log_file(enabled: bool) -> None:
	global _g_log_file_enabled
	_g_log_file_enabled = enabled


def toggle_decorator_log_only(enabled: bool) -> None:
	"""
	Toggle only @log-decorated tracing.
	"""

	global _g_deco_only
	_g_deco_only = enabled


def toggle_message_metadata(enabled: bool) -> None:
	"""
	Enable or disable metadata for message logs

	If disabled:
		log("hello") -> prints just "hello"

	If enabled:
		log("hello") -> prints "[time] file:line hello"
	"""

	global _g_show_message_meta
	_g_show_message_meta = enabled


# =========
#  SETTERS
# =========
def set_mode(mode: Mode) -> None:
	"""
	Set global logging mode
	full or  edu / educational
	"""

	global _g_log_mode
	_g_log_mode = _normalize_mode(mode)


def set_global_log_file(filepath: str | None) -> None:
	"""
	Route LogEye output to this file globally.
	"""
	global _g_log_file
	_g_log_file = None if filepath is None else os.fspath(filepath)


def set_path_mode(mode: PathMode) -> None:
	global _g_path_mode

	if mode not in ("absolute", "project", "file"):
		raise ValueError("mode must be: absolute, project, file")

	_g_path_mode = mode


def _normalize_mode(mode: Mode) -> Mode:
	if mode in ("edu", "educational"):
		return "educational"

	if mode == "full":
		return "full"

	raise ValueError("mode must be: full, edu, educational")
