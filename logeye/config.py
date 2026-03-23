import os
import sys
import time

_ENABLED = True
_START_TIME = time.perf_counter()

# "absolute" -> full path
# "project"  -> relative to project root
# "file"     -> filename only
_PATH_MODE = "file"

# Whether message logs include timestamp + file info
_SHOW_MESSAGE_META = True

_PROJECT_ROOT = os.getcwd()
_LIBRARY_ROOT = os.path.dirname(__file__)
_EXEC_ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))

_LOG_PIPE_NAME = "l"


def logoff():
	global _ENABLED
	_ENABLED = False


def logon():
	global _ENABLED
	_ENABLED = True


def set_path_mode(mode: str):
	global _PATH_MODE

	if mode not in ("absolute", "project", "file"):
		raise ValueError("mode must be: absolute, project, file")

	_PATH_MODE = mode


def set_message_metadata(enabled: bool):
	"""
	Enable or disable metadata for message logs

	If disabled:
		log("hello") -> prints just "hello"

	If enabled:
		log("hello") -> prints "[time] file:line hello"
	"""

	global _SHOW_MESSAGE_META
	_SHOW_MESSAGE_META = enabled
