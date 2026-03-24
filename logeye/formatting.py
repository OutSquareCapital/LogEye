from collections.abc import Callable
import os
from string import Template

from . import config
from .introspection.frames import _caller_frame, _get_location


def _default_formatter(
		elapsed: float,
		kind: str,
		name: str,
		value: object,
		filename: str | None,
		lineno: int | None,
		*,
		show_time: bool=True,
		show_file: bool=True,
		show_lineno: bool=True,
):
	parts = []

	if config._LOG_MODE == "educational":
		show_file = False
		show_lineno = False

	stamp = f"{elapsed:0.3f}s"
	time_prefix = f"[{stamp}] " if show_time else ""

	if show_file and filename:
		path = _format_path(filename)
		loc = path
		if show_lineno and lineno:
			loc += f":{lineno}"
		parts.append(loc)

	location_prefix = " ".join(parts)
	if location_prefix:
		location_prefix += " "

	prefix = f"{time_prefix}{location_prefix}"

	if config._LOG_MODE == "educational":
		if isinstance(value, dict) and "op" in value:
			op = value["op"]
			val = value.get("value")
			state = value.get("state")

			short_name = name.split(".")[-1]

			if op == "append":
				return f"{prefix}Added {val} to the end of {short_name} -> {state}"

			if op == "extend":
				if not val:
					return None

				if len(val) == 1:
					return f"{prefix}Added {val[0]} to {short_name} -> {state}"

				return f"{prefix}Added {val} to {short_name} -> {state}"

			if op == "setitem":
				return f"{prefix}set {short_name} = {val} -> {state}"

			return f"{prefix}{short_name} changed -> {state}"

		if kind == "set":
			parts = name.split(".")

			if len(parts) > 1:
				parts = parts[1:]

			short_name = ".".join(parts[-2:]) if len(parts) >= 2 else parts[0]

			return f"{prefix}{short_name} = {value!r}"

		if kind == "call":
			parts = name.split(".")

			# Drop module part if present (first element)
			if len(parts) > 1:
				parts = parts[1:]

			func_name = ".".join(parts[-2:]) if len(parts) >= 2 else parts[0]

			if isinstance(value, dict):
				args = value.get("args", ())
				kwargs = value.get("kwargs", {})

				arg_parts = []

				if args:
					arg_parts.append(", ".join(repr(a) for a in args))

				if kwargs:
					arg_parts.append(", ".join(f"{k}={v!r}" for k, v in kwargs.items()))

				args_str = ", ".join(arg_parts)

				return f"{prefix}Calling {func_name}({args_str})"

			return f"{prefix}Calling {func_name}"

		if kind == "return":
			return f"{prefix}Returned {value!r}"

	if kind == "message":
		if not config._SHOW_MESSAGE_META:
			return f"{value}"

		return f"{prefix}{value}"

	return f"{prefix}({kind}) {name} = {value!r}"


_formatter = _default_formatter


def _format_path(filename: str | None) -> str:
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


def set_output_formatter(func: Callable[..., object]) -> None:
	global _formatter
	_formatter = func


def reset_output_formatter() -> None:
	global _formatter
	_formatter = _default_formatter


def _format_message(text: str, *args: object, **kwargs: object) -> str:
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
