from __future__ import annotations
from types import FrameType
from logeye.wrappers import LoggedObject
import sys
import inspect
import functools
from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Literal,  TypeVar, ParamSpec,  overload

from . import config
from .emmiter import _emit
from .formatting import _format_message
from .introspection.ast import (
	_infer_name_from_frame,
	_get_assignment_target_for_call,
)
from .introspection.templates import _expand_template
from .wrappers import (
	LoggedObject,
	LoggedList,
	LoggedDict,
	LoggedSet,
	_wrap_value,
	_path,
)
from .introspection.frames import _caller_frame, _get_location
if TYPE_CHECKING:
	from .config import Mode
_NO_VALUE = object()
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
P = ParamSpec("P")

Level = Literal["call", "state", "full"]
Kind = Literal["change", "message", "set", "call", "return"]
def _resolve_filepath(file: str |None =None, filepath: str | None=None) -> str | None:
	if file is not None and filepath is not None:
		raise TypeError("Use only one of 'file' or 'filepath'")
	return file if file is not None else filepath


# ===============
#  CLASS LOGGING
# ===============

def _log_class(
		cls: type,
		*,
		filepath: str | None=None,
		show_time: bool=True,
		show_file: bool=True,
		show_lineno: bool=True
) -> type:
	"""
	Wrap a class so its instances become LoggedObjects

	Overrides __init__ to:

	- replace `self` with a LoggedObject wrapper
	- preserve original initialization logic
	"""

	original_init = cls.__init__
	class_name = cls.__name__.lower()
	qualname = cls.__qualname__.replace(".<locals>.", ".")

	class LoggedClass(cls):
		@functools.wraps(original_init)
		def __init__(self, *args: object, **kwargs: object):
			if not config._ENABLED:
				original_init(self, *args, **kwargs)
				return

			call_frame = _caller_frame()
			call_filename, call_lineno = _get_location(call_frame)

			_emit(
				"call",
				f"{qualname}.__init__",
				{"args": args, "kwargs": kwargs},
				filename=call_filename,
				lineno=call_lineno,
				filepath=filepath,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)

			original_init(self, *args, **kwargs)

		def __setattr__(self, name: str, value: object) -> None:
			if name.startswith("_"):
				object.__setattr__(self, name, value)
				return

			wrapped = _wrap_value(value, name=f"{class_name}.{name}")
			object.__setattr__(self, name, wrapped)

			frame = _caller_frame()
			try:
				filename, lineno = _get_location(frame)

				if callable(wrapped):
					_emit(
						"set",
						f"{class_name}.{name}",
						f"<func {_path(wrapped)}>",
						filename=filename,
						lineno=lineno,
						filepath=filepath,
						show_time=show_time,
						show_file=show_file,
						show_lineno=show_lineno
					)
				else:
					_emit(
						"set",
						f"{class_name}.{name}",
						wrapped,
						filename=filename,
						lineno=lineno,
						filepath=filepath,
						show_time=show_time,
						show_file=show_file,
						show_lineno=show_lineno
					)
			finally:
				del frame

	LoggedClass.__name__ = cls.__name__
	LoggedClass.__qualname__ = cls.__qualname__
	LoggedClass.__module__ = cls.__module__

	return LoggedClass


# =====================
# WATCH (value logging)
# =====================

def watch(value: T, name: str | None=None, *, show_time: bool=True, show_file: bool=True, show_lineno: bool=True) -> T:
	"""
	Log without changing behaviour
	"""

	if not config._ENABLED or config._DECORATORS_ONLY:
		return value

	frame = _caller_frame()

	try:
		if name is None:
			name = _infer_name_from_frame(frame)

		filename, lineno = _get_location(frame)

		# Lambdas
		if callable(value):
			wrapped = _log_function(
				value,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)

			_emit(
				"set",
				name,
				f"<func {_path(value)}>",
				filename=filename,
				lineno=lineno,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)
			return wrapped

	finally:
		del frame

	_emit(
		"set",
		name,
		value,
		filename=filename,
		lineno=lineno,
		show_time=show_time,
		show_file=show_file,
		show_lineno=show_lineno
	)

	return value


# ========================
#     FUNCTION LOGGING
# ========================

def _log_function(
		func: Callable[P, T],
		*,
		filepath: str | None=None,
		level: Level="full",
		filter_set: set[str] | None=None,
		mode: Mode="full",
		show_time: bool=True,
		show_file: bool=True,
		show_lineno: bool=True
) -> Callable[P, T]:
	"""
	Wrap a function to trace:
	- calls (arguments)
	- local variable changes
	- return values

	Uses sys.settrace to monitor execution line-by-line
	"""

	owner = getattr(func, "__qualname__", "")
	func_path = owner.replace(".<locals>.", ".")
	call_counter = 0

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		nonlocal call_counter

		prev_mode = config._LOG_MODE
		prev_time = config._SHOW_TIME
		prev_file = config._SHOW_FILE
		prev_lineno = config._SHOW_LINENO

		config._LOG_MODE = mode
		config._SHOW_TIME = show_time
		config._SHOW_FILE = show_file
		config._SHOW_LINENO = show_lineno

		if not config._ENABLED:
			return func(*args, **kwargs)

		# Track multiple calls f.e recursion / repeat calls
		call_counter += 1
		call_id = call_counter
		call_name = f"{func_path}{'' if call_counter == 1 else f'_{call_id}'}"

		def _should_emit(kind: Kind, name: str) -> bool:
			if mode == "educational":
				var = name.split(".")[-1]

				# Always allow meaningful structural events
				if kind in ("change", "message"):
					return True

				# Only allow SOME "set" events
				if kind == "set":

					# Ignore obvious noise
					if var in ("_",):
						return False

					# Ignore loop counters
					# if len(var) == 1 and var.isalpha():
					# 	return False

					# Ignore frequently changing temp vars
					if var in ("i", "j", "k", "idx", "tmp", "val"):
						return False

					# Should work for basic scalars
					return True

			# LEVEL CONTROL
			if level == "call" and kind not in ("call", "return"):
				return False

			if level == "state" and kind == "call":
				return False

			# FILTER CONTROL
			if filter_set:
				var_name = name.split(".")[-1]
				if var_name not in filter_set:
					return False

			return True

		call_frame = _caller_frame()
		call_filename, call_lineno = _get_location(call_frame)

		if _should_emit("call", call_name):
			_emit(
				"call",
				call_name,
				{"args": args, "kwargs": kwargs},
				filename=call_filename,
				lineno=call_lineno,
				filepath=filepath,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)

		last_values = {}

		try:
			def tracer(frame: FrameType, event: str, arg: object):
				code = frame.f_code

				if not (
						code is func.__code__
						or frame.f_back and frame.f_back.f_code is func.__code__
				):
					return tracer

				filename = code.co_filename
				lineno = frame.f_lineno

				# Filter noise
				if not filename.startswith(call_filename) or "site-packages" in filename or "/lib/python" in filename:
					return tracer

				if event == "call":
					if code is not func.__code__:
						nested_name = code.co_name

						if nested_name.startswith("__"):
							return tracer

						if nested_name in ("currentframe", "abspath", "join", "parse"):
							return tracer

						if _should_emit("call", nested_name):
							_emit(
								"call",
								f"{call_name}.{nested_name}",
								{"args": (), "kwargs": {}},
								filename=filename,
								lineno=lineno,
								filepath=filepath,
								show_time=show_time,
								show_file=show_file,
								show_lineno=show_lineno
							)

					return tracer

				if frame.f_code is func.__code__:
					if event == "line":
						current = dict(frame.f_locals)

						for key, value in current.items():
							if mode == "educational" and key in ("_"):  # , "i", "j", "k"):
								continue

							old = last_values.get(key, object())

							if not isinstance(value, (LoggedObject, LoggedList, LoggedDict, LoggedSet)):
								wrapped = _wrap_value(value, name=f"{call_name}.{key}")
								if wrapped is not value:
									frame.f_locals[key] = wrapped
									value = wrapped

							name = f"{call_name}.{key}"
							if old != value:
								if callable(value):
									display = _path(value)
									if _should_emit("set", name):
										_emit(
											"set",
											name,
											f"<func {display}>",
											filename=filename,
											lineno=lineno,
											filepath=filepath,
											show_time=show_time,
											show_file=show_file,
											show_lineno=show_lineno
										)
								else:
									if _should_emit("set", name):
										_emit(
											"set",
											name,
											value,
											filename=filename,
											lineno=lineno,
											filepath=filepath,
											show_time=show_time,
											show_file=show_file,
											show_lineno=show_lineno
										)
								last_values[key] = value
					elif event == "return":
						if _should_emit("return", call_name):
							_emit(
								"return",
								call_name,
								arg,
								filename=filename,
								lineno=lineno,
								filepath=filepath,
								show_time=show_time,
								show_file=show_file,
								show_lineno=show_lineno
							)

				return tracer

			old_trace = sys.gettrace()
			sys.settrace(tracer)

			try:
				return func(*args, **kwargs)
			finally:
				sys.settrace(old_trace)
		finally:
			config._LOG_MODE = prev_mode
			config._SHOW_TIME = prev_time
			config._SHOW_FILE = prev_file
			config._SHOW_LINENO = prev_lineno

	return wrapper


# ========================
# OBJECT / MESSAGE LOGGING
# ========================

def _log_object(
		obj: T | Mapping[K, V],
		name: str | None=None,
		*,
		show_time: bool=True,
		show_file: bool=True,
		show_lineno: bool=True
) 	 -> T | LoggedObject[T | Mapping[K, V]] | Mapping[K, V]:
	if not config._ENABLED or config._DECORATORS_ONLY:
		return obj

	if name is None:
		frame = _caller_frame()
		try:
			name = _get_assignment_target_for_call(frame)
		finally:
			del frame

	if not name:
		name = "set"

	wrapped = LoggedObject(obj, name=name)

	frame = _caller_frame()
	filename, lineno = _get_location(frame)
	del frame

	if isinstance(obj, Mapping):
		value = dict(obj)
	else:
		value = vars(obj)

	_emit(
		"set",
		name,
		value,
		filename=filename,
		lineno=lineno,
		show_time=show_time,
		show_file=show_file,
		show_lineno=show_lineno
	)

	return wrapped


def _log_message(
		text: str,
		*args: object,
		show_time: bool=True,
		show_file: bool=True,
		show_lineno: bool=True,
		**kwargs: object
) -> str:
	frame = _caller_frame()

	try:
		if args or kwargs:
			rendered = _format_message(text, *args, **kwargs)
		else:
			rendered = _expand_template(text)

		if not config._ENABLED or config._DECORATORS_ONLY:
			return rendered

		name = _get_assignment_target_for_call(frame)
		filename, lineno = _get_location(frame)

		if name:
			_emit(
				"set",
				name,
				rendered,
				filename=filename,
				lineno=lineno,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)
		else:
			_emit(
				"message",
				"message",
				rendered,
				filename=filename,
				lineno=lineno,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
			)

	finally:
		del frame

	return rendered


# =====================
#   PUBLIC ENTRYPOINT
# =====================

@overload
def log(
		obj: Mapping[K, V],
		*args: object,
		file: str | None=...,
		filepath: str | None=...,
		level: Level=...,
		filter: Iterable[str] | None=...,
		mode: Mode | None=...,
		show_time: bool | None=...,
		show_file: bool | None=...,
		show_lineno: bool | None=...,
		**kwargs: object
) -> Mapping[K, V]: ...
@overload
def log(
		obj: Callable[P, T],
		*args: object,
		file: str | None=...,
		filepath: str | None=...,
		level: Level=...,
		filter: Iterable[str] | None=...,
		mode: Mode | None=...,
		show_time: bool | None=...,
		show_file: bool | None=...,
		show_lineno: bool | None=...,
		**kwargs: object
) -> Callable[P, T]: ...
def log(
		obj: Callable[P, T] | Mapping[K, V] | object=_NO_VALUE,
		*args: object,
		file: str | None=None,
		filepath: str | None=None,
		level: Level="full",
		filter: Iterable[str] | None=None,
		mode: Mode | None=None,
		show_time: bool | None=None,
		show_file: bool | None=None,
		show_lineno: bool | None=None,
		**kwargs: object
) -> object:
	"""
	Dispatches behaviour based on input type:

	- class     -> wrap class (__init__)
	- function  -> trace execution
	- string    -> formatted message
	- mapping/object -> LoggedObject wrapper
	- other     -> simple value logging
	"""

	if mode is None:
		mode = config._LOG_MODE
	else:
		mode = config._normalize_mode(mode)

	filter_set = set(filter) if filter else None
	deco_path = _resolve_filepath(file=file, filepath=filepath)

	if show_time is None:
		show_time = config._SHOW_TIME

	if show_file is None:
		show_file = config._SHOW_FILE

	if show_lineno is None:
		show_lineno = config._SHOW_LINENO

	if obj is _NO_VALUE:
		def decorator(target: T):
			if inspect.isclass(target):
				return _log_class(
					target,
					filepath=deco_path,
					show_time=show_time,
					show_file=show_file,
					show_lineno=show_lineno
				)
			if callable(target):
				return _log_function(
					target,
					filepath=deco_path,
					level=level,
					filter_set=filter_set,
					mode=mode,
					show_time=show_time,
					show_file=show_file,
					show_lineno=show_lineno
				)
			raise TypeError("@log(...) can only decorate a function or class")

		return decorator

	if inspect.isclass(obj):
		return _log_class(
			obj,
			filepath=deco_path,
			show_time=show_time,
			show_file=show_file,
			show_lineno=show_lineno
		)

	if callable(obj):
		return _log_function(
			obj,
			filepath=deco_path,
			level=level,
			filter_set=filter_set,
			mode=mode,
			show_time=show_time,
			show_file=show_file,
			show_lineno=show_lineno
		)

	if isinstance(obj, str):
		return _log_message(
			obj,
			*args,
			show_time=show_time,
			show_file=show_file,
			show_lineno=show_lineno,
			**kwargs
		)

	if isinstance(obj, Mapping) or hasattr(obj, "__dict__"):
		return _log_object(
			obj,
			show_time=show_time,
			show_file=show_file,
			show_lineno=show_lineno
		)

	return watch(
		obj,
		show_time=show_time,
		show_file=show_file,
		show_lineno=show_lineno
	)
