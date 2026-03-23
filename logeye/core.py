import sys
import inspect
import functools
from collections.abc import Mapping

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

_NO_VALUE = object()


def _resolve_filepath(file=None, filepath=None):
	if file is not None and filepath is not None:
		raise TypeError("Use only one of 'file' or 'filepath'")
	return file if file is not None else filepath


# ===============
#  CLASS LOGGING
# ===============

def _log_class(cls, *, filepath=None):
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
		def __init__(self, *args, **kwargs):
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
				filepath=filepath
			)

			original_init(self, *args, **kwargs)

		def __setattr__(self, name, value):
			if name.startswith("_"):
				object.__setattr__(self, name, value)
				return

			wrapped = _wrap_value(value, name=f"{class_name}.{name}")
			object.__setattr__(self, name, wrapped)

			frame = _caller_frame()
			try:
				filename, lineno = _get_location(frame)

				if callable(wrapped):
					_emit("set", f"{class_name}.{name}", f"<func {_path(wrapped)}>", filename=filename, lineno=lineno,
					      filepath=filepath)
				else:
					_emit("set", f"{class_name}.{name}", wrapped, filename=filename, lineno=lineno, filepath=filepath)
			finally:
				del frame

	LoggedClass.__name__ = cls.__name__
	LoggedClass.__qualname__ = cls.__qualname__
	LoggedClass.__module__ = cls.__module__

	return LoggedClass


# =====================
# WATCH (value logging)
# =====================

def watch(value, name=None):
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
			wrapped = _log_function(value)
			_emit("set", name, f"<func {_path(value)}>", filename=filename, lineno=lineno)
			return wrapped

	finally:
		del frame

	_emit("set", name, value, filename=filename, lineno=lineno)
	return value


# ========================
#     FUNCTION LOGGING
# ========================

def _log_function(func, *, filepath=None, level="full", filter_set=None):
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

		if not config._ENABLED:
			return func(*args, **kwargs)

		# Track multiple calls f.e recursion / repeat calls
		call_counter += 1
		call_id = call_counter
		call_name = f"{func_path}{'' if call_counter == 1 else f'_{call_id}'}"

		def _should_emit(kind, name):
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
				filepath=filepath
			)

		last_values = {}

		def tracer(frame, event, arg):
			if frame.f_code is func.__code__:
				filename = frame.f_code.co_filename
				lineno = frame.f_lineno

				if event == "line":
					current = dict(frame.f_locals)

					for key, value in current.items():
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
										filepath=filepath
									)
							else:
								if _should_emit("set", name):
									_emit(
										"set",
										name,
										value,
										filename=filename,
										lineno=lineno,
										filepath=filepath
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
							filepath=filepath
						)

			return tracer

		old_trace = sys.gettrace()
		sys.settrace(tracer)

		try:
			return func(*args, **kwargs)
		finally:
			sys.settrace(old_trace)

	return wrapper


# ========================
# OBJECT / MESSAGE LOGGING
# ========================

def _log_object(obj, name=None):
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

	_emit("set", name, value, filename=filename, lineno=lineno)

	return wrapped


def _log_message(text, *args, **kwargs):
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
			_emit("set", name, rendered, filename=filename, lineno=lineno)
		else:
			_emit("message", "message", rendered, filename=filename, lineno=lineno)

	finally:
		del frame

	return rendered


# =====================
#   PUBLIC ENTRYPOINT
# =====================

def log(obj=_NO_VALUE, *args, file=None, filepath=None, level="full", filter=None, **kwargs):
	"""
	Dispatches behaviour based on input type:

	- class     -> wrap class (__init__)
	- function  -> trace execution
	- string    -> formatted message
	- mapping/object -> LoggedObject wrapper
	- other     -> simple value logging
	"""

	deco_path = _resolve_filepath(file=file, filepath=filepath)

	if obj is _NO_VALUE:
		def decorator(target):
			if inspect.isclass(target):
				return _log_class(target, filepath=deco_path)
			if callable(target):
				return _log_function(
					target,
					filepath=deco_path,
					level=level,
					filter_set=set(filter) if filter else None,
				)
			raise TypeError("@log(...) can only decorate a function or class")

		return decorator

	if inspect.isclass(obj):
		return _log_class(obj, filepath=deco_path)

	if callable(obj):
		return _log_function(
			obj,
			filepath=deco_path,
			level=level,
			filter_set=set(filter) if filter else None
		)

	if isinstance(obj, str):
		return _log_message(obj, *args, **kwargs)

	if isinstance(obj, Mapping) or hasattr(obj, "__dict__"):
		return _log_object(obj)

	return watch(obj)
