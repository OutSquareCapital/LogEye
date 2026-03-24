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

def _log_class(
		cls,
		*,
		filepath=None,
		show_time=True,
		show_file=True,
		show_lineno=True
):
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
				filepath=filepath,
				show_time=show_time,
				show_file=show_file,
				show_lineno=show_lineno
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

def watch(value, name=None, *, show_time=True, show_file=True, show_lineno=True):
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

# Helpers
def _format_call_signature(name, args, kwargs):
	arg_parts = [", ".join(repr(a) for a in args)] if args else []
	kw_parts = [", ".join(f"{k}={v!r}" for k, v in kwargs.items())] if kwargs else []
	joined = ", ".join([p for p in arg_parts + kw_parts if p])
	return f"{name}({joined})"


def _shorten_name(name: str) -> str:
	parts = [p for p in name.split(".") if not p.startswith("test_")]
	return ".".join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def _log_function(
		func,
		*,
		filepath=None,
		level="full",
		filter_set=None,
		mode="full",
		show_time=True,
		show_file=True,
		show_lineno=True
):
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
		call_name = f"{func_path}{'' if call_counter == 1 else f'#{call_id}'}"

		def _should_emit(kind, name):
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

		short_name = _shorten_name(call_name)
		call_signature = _format_call_signature(short_name, args, kwargs)

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
			def tracer(frame, event, arg):
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
								{
									"value": arg,
									"call_signature": call_signature,
								},
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
		obj,
		name=None,
		*,
		show_time=True,
		show_file=True,
		show_lineno=True
):
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
		text,
		*args,
		show_time=True,
		show_file=True,
		show_lineno=True,
		**kwargs
):
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

def log(
		obj=_NO_VALUE,
		*args,
		file=None,
		filepath=None,
		level="full",
		filter=None,
		mode=None,
		show_time=None,
		show_file=None,
		show_lineno=None,
		**kwargs
):
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
		def decorator(target):
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
