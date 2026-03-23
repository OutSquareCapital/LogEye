from collections.abc import Mapping

from .emmiter import _emit
from .introspection import _caller_frame, _get_location


def _path(obj):
	"""
	Return a readable name/path for a callable or object
	"""
	if hasattr(obj, "__qualname__"):
		return obj.__qualname__.replace(".<locals>.", ".")

	return getattr(obj, "__name__", str(obj))


def _wrap_value(value, name=None):
	"""
	Recursively wrap values so nested structures are tracked

	- Mappings -> LoggedObject
	- Containers -> recursively wrapped
	- Already wrapped -> returned as-is
	"""
	if isinstance(value, LoggedObject):
		return value

	if isinstance(value, Mapping):
		return LoggedObject(value, name=name)

	if isinstance(value, list):
		return [_wrap_value(v, name=None) for v in value]

	if isinstance(value, tuple):
		return tuple(_wrap_value(v, name=None) for v in value)

	if isinstance(value, set):
		return {_wrap_value(v, name=None) for v in value}

	return value


class LoggedObject:
	"""
	A wrapper around mappings / objects that logs all mutations

	- Stores data internally in `_data`
	- Tracks attribute and item changes
	- Recursively wraps nested values
	"""

	def __init__(self, initial=None, name="set"):
		# Internal storage and log prefix (e.g. "config", "obj.x")
		object.__setattr__(self, "_data", {})
		object.__setattr__(self, "_log_name", name)

		if initial is None:
			return

		# Support dict-like objects or objects with __dict__
		if isinstance(initial, Mapping):
			items = initial.items()
		elif hasattr(initial, "__dict__"):
			items = vars(initial).items()
		else:
			raise TypeError("LoggedObject can only wrap mappings or objects with __dict__")

		# Populate internal data, wrapping nested values
		for key, value in items:
			self._data[key] = _wrap_value(value, name=f"{self._log_name}.{key}")

	def __getattr__(self, name):
		"""
		Allow attribute-style access to internal data
		"""
		data = object.__getattribute__(self, "_data")

		if name in data:
			return data[name]

		raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

	def __setattr__(self, name, value):
		"""
		Intercept attribute assignment:
		- wrap value
		- store it
		- emit log event
		"""

		# Allow internal attributes to behave normally
		if name.startswith("_"):
			object.__setattr__(self, name, value)
			return

		data = object.__getattribute__(self, "_data")
		log_name = object.__getattribute__(self, "_log_name")

		# Wrap value for nested tracking
		wrapped = _wrap_value(value, name=f"{log_name}.{name}")
		data[name] = wrapped

		# Get caller location for logging
		frame = _caller_frame()
		filename, lineno = _get_location(frame)

		if callable(wrapped):
			_emit("set", f"{log_name}.{name}", f"<func {_path(wrapped)}>", filename=filename, lineno=lineno)
		else:
			_emit("set", f"{log_name}.{name}", wrapped, filename=filename, lineno=lineno)

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		"""
		Intercept item assignment
		- wrap value
		- store it
		- emit log event
		"""

		log_name = object.__getattribute__(self, "_log_name")
		wrapped = _wrap_value(value, name=f"{log_name}.{key}")
		self._data[key] = wrapped

		frame = _caller_frame()
		filename, lineno = _get_location(frame)

		if callable(wrapped):
			_emit("set", f"{log_name}.{key}", f"<func {_path(wrapped)}>", filename=filename, lineno=lineno)
		else:
			_emit("set", f"{log_name}.{key}", wrapped, filename=filename, lineno=lineno)

	def __delattr__(self, name):
		"""
		Intercept attribute deletion
		"""

		if name.startswith("_"):
			raise AttributeError(name)

		data = object.__getattribute__(self, "_data")
		log_name = object.__getattribute__(self, "_log_name")

		if name not in data:
			raise AttributeError(name)

		del data[name]

		frame = _caller_frame()
		filename, lineno = _get_location(frame)
		_emit("set", f"{log_name}.{name}", "<deleted>", filename=filename, lineno=lineno)

	def __delitem__(self, key):
		"""
		Intercept item deletion
		"""

		log_name = object.__getattribute__(self, "_log_name")
		del self._data[key]

		frame = _caller_frame()
		filename, lineno = _get_location(frame)
		_emit("set", f"{log_name}.{key}", "<deleted>", filename=filename, lineno=lineno)

	def __iter__(self):
		return iter(self._data)

	def __len__(self):
		return len(self._data)

	def __contains__(self, key):
		return key in self._data

	def get(self, key, default=None):
		return self._data.get(key, default)

	def keys(self):
		return self._data.keys()

	def values(self):
		return self._data.values()

	def items(self):
		return self._data.items()

	def to_dict(self):
		"""
		Convert LoggedObject back into a plain Python structure by recursively unwrapping nested LoggedObjects
		"""

		def unwrap(v):
			if isinstance(v, LoggedObject):
				return v.to_dict()
			if isinstance(v, list):
				return [unwrap(x) for x in v]
			if isinstance(v, tuple):
				return tuple(unwrap(x) for x in v)
			if isinstance(v, set):
				return {unwrap(x) for x in v}
			return v

		return {k: unwrap(v) for k, v in self._data.items()}

	def __repr__(self):
		return f"{type(self).__name__}({self._data!r})"

	def __dir__(self):
		"""
		Expose dynamic attributes for autocomplete / introspection
		"""
		return sorted(set(super().__dir__()) | set(self._data.keys()))
