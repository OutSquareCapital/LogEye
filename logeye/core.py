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


# ===============
#  CLASS LOGGING
# ===============

def _log_class(cls):
	"""
	Wrap a class so its instances become LoggedObjects

	Overrides __init__ to:

	- replace `self` with a LoggedObject wrapper
	- preserve original initialization logic
	"""

	original_init = cls.__init__

	@functools.wraps(original_init)
	def new_init(self, *args, **kwargs):
		# Wrap for tracking
		wrapped_self = LoggedObject(self, name=cls.__name__.lower())

		# Replace self in-place
		object.__setattr__(wrapped_self, "_data", {})
		object.__setattr__(wrapped_self, "_log_name", cls.__name__.lower())

		# Run original init on wrapped object
		original_init(wrapped_self, *args, **kwargs)

		return None

	cls.__init__ = _log_function(new_init)
	return cls


# =====================
# WATCH (value logging)
# =====================

def watch(value, name=None):
	"""
	Log without changing behaviour
	"""

	if not config._ENABLED:
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

def _log_function(func):
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

		call_frame = _caller_frame()
		call_filename, call_lineno = _get_location(call_frame)

		_emit(
			"call",
			call_name,
			{"args": args, "kwargs": kwargs},
			filename=call_filename,
			lineno=call_lineno,
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

						if old != value:
							if callable(value):
								display = _path(value)
								_emit(
									"set",
									f"{call_name}.{key}",
									f"<func {display}>",
									filename=filename,
									lineno=lineno,
								)
							else:
								_emit(
									"set",
									f"{call_name}.{key}",
									value,
									filename=filename,
									lineno=lineno,
								)

							last_values[key] = value

				elif event == "return":
					_emit(
						"return",
						call_name,
						arg,
						filename=filename,
						lineno=lineno,
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

def log(obj, *args, **kwargs):
	"""
	Dispatches behaviour based on input type:

	- class     -> wrap class (__init__)
	- function  -> trace execution
	- string    -> formatted message
	- mapping/object -> LoggedObject wrapper
	- other     -> simple value logging
	"""

	if inspect.isclass(obj):
		return _log_class(obj)

	if callable(obj):
		return _log_function(obj)

	if isinstance(obj, str):
		return _log_message(obj, *args, **kwargs)

	if isinstance(obj, Mapping) or hasattr(obj, "__dict__"):
		return _log_object(obj)

	return watch(obj)
