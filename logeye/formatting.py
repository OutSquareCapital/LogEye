import os
from string import Template

from . import config
from .introspection.frames import _caller_frame, _get_location


def _default_formatter(elapsed, kind, name, value, filename, lineno):
	stamp = f"{elapsed:0.3f}s"

	loc = ""
	if filename and lineno:
		path = _format_path(filename)
		loc = f"{path}:{lineno} "

	if kind == "message":
		if not config._SHOW_MESSAGE_META:
			return f"{value}"

		return f"[{stamp}] {loc}{value}"

	return f"[{stamp}] {loc}({kind}) {name} = {value!r}"


_formatter = _default_formatter


def _format_path(filename):
	if not filename:
		return ""

	if config._PATH_MODE == "absolute":
		return filename

	if config._PATH_MODE == "project":
		try:
			return os.path.relpath(filename, config._PROJECT_ROOT)
		except Exception:
			return filename

	if config._PATH_MODE == "file":
		return os.path.basename(filename)

	return filename


def set_output_formatter(func):
	global _formatter
	_formatter = func


def reset_output_formatter():
	global _formatter
	_formatter = _default_formatter


def _format_message(text, *args, **kwargs):
	try:
		return text.format(*args, **kwargs)
	except Exception:
		pass

	frame = _caller_frame()
	try:
		if frame is not None:
			namespace = {}
			namespace.update(frame.f_globals)
			namespace.update(frame.f_locals)

			filename, lineno = _get_location(frame)
			namespace["apath"] = filename or ""
			namespace["rpath"] = os.path.relpath(filename, config._PROJECT_ROOT) if filename else ""
			namespace["fpath"] = os.path.basename(filename) if filename else ""

			try:
				return text.format(**namespace)
			except Exception:
				pass

			try:
				return Template(text).safe_substitute(namespace)
			except Exception:
				pass
	finally:
		del frame

	return text
