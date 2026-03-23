from collections.abc import Mapping

from . import config
from .emmiter import _emit
from .introspection import _caller_frame, _get_location


def _path(obj):
	"""
	Return a readable name/path for a callable or object
	"""

	if hasattr(obj, "__qualname__"):
		return obj.__qualname__.replace(".<locals>.", ".")

	return getattr(obj, "__name__", str(obj))


def _unwrap_value(value):
	"""
	Recursively unwrap logged containers into plain Python values.
	Used for log payloads so mutation logs stay readable
	"""

	if isinstance(value, LoggedObject):
		return value.to_dict()

	if isinstance(value, LoggedList):
		return [_unwrap_value(v) for v in list(value)]

	if isinstance(value, LoggedDict):
		return {k: _unwrap_value(v) for k, v in dict.items(value)}

	if isinstance(value, LoggedSet):
		return {_unwrap_value(v) for v in set(value)}

	if isinstance(value, list):
		return [_unwrap_value(v) for v in value]

	if isinstance(value, tuple):
		return tuple(_unwrap_value(v) for v in value)

	if isinstance(value, set):
		return {_unwrap_value(v) for v in value}

	if isinstance(value, dict):
		return {k: _unwrap_value(v) for k, v in value.items()}

	return value


def _emit_change(name, op, state=None, filename=None, lineno=None, **details):
	"""
	Emit a mutation event with a readable payload
	"""

	if not config._ENABLED:
		return

	payload = {"op": op}

	for key, value in details.items():
		payload[key] = _unwrap_value(value)

	if state is not None:
		payload["state"] = _unwrap_value(state)

	_emit("change", name, payload, filename=filename, lineno=lineno)


def _wrap_value(value, name=None):
	"""
	Recursively wrap values so nested structures are tracked

	- mappings -> LoggedDict
	- lists    -> LoggedList
	- sets     -> LoggedSet
	- objects with __dict__ -> LoggedObject
	- already wrapped -> returned as-is
	"""
	if isinstance(
			value,
			(LoggedObject, LoggedList, LoggedDict, LoggedSet),
	):
		return value

	if isinstance(value, Mapping):
		return LoggedDict(value, name=name)

	if isinstance(value, list):
		return LoggedList(value, name=name)

	if isinstance(value, dict):
		return LoggedDict(value, name=name)

	if isinstance(value, set):
		return LoggedSet(value, name=name)

	if hasattr(value, "__dict__") and not isinstance(value, type):
		return LoggedObject(value, name=name)

	return value


class LoggedObject:
	"""
	A wrapper around mappings / objects that logs all mutations

	- Stores data internally in `_data`
	- Tracks attribute and item changes
	- Recursively wraps nested values
	"""

	def __init__(self, initial=None, name="set"):
		object.__setattr__(self, "_data", {})
		object.__setattr__(self, "_log_name", name)

		if initial is None:
			return

		if isinstance(initial, Mapping):
			items = initial.items()
		elif hasattr(initial, "__dict__"):
			items = vars(initial).items()
		else:
			raise TypeError("LoggedObject can only wrap mappings or objects with __dict__")

		for key, value in items:
			self._data[key] = _wrap_value(value, name=f"{self._log_name}.{key}")

	def __getattr__(self, name):
		data = object.__getattribute__(self, "_data")

		if name in data:
			return data[name]

		raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

	def __setattr__(self, name, value):
		if name.startswith("_"):
			object.__setattr__(self, name, value)
			return

		data = object.__getattribute__(self, "_data")
		log_name = object.__getattribute__(self, "_log_name")

		wrapped = _wrap_value(value, name=f"{log_name}.{name}")
		data[name] = wrapped

		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)

			if callable(wrapped):
				_emit("set", f"{log_name}.{name}", f"<func {_path(wrapped)}>", filename=filename, lineno=lineno)
			else:
				_emit("set", f"{log_name}.{name}", wrapped, filename=filename, lineno=lineno)
		finally:
			del frame

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		log_name = object.__getattribute__(self, "_log_name")
		wrapped = _wrap_value(value, name=f"{log_name}.{key}")
		self._data[key] = wrapped

		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)

			if callable(wrapped):
				_emit("set", f"{log_name}.{key}", f"<func {_path(wrapped)}>", filename=filename, lineno=lineno)
			else:
				_emit("set", f"{log_name}.{key}", wrapped, filename=filename, lineno=lineno)
		finally:
			del frame

	def __delattr__(self, name):
		if name.startswith("_"):
			raise AttributeError(name)

		data = object.__getattribute__(self, "_data")
		log_name = object.__getattribute__(self, "_log_name")

		if name not in data:
			raise AttributeError(name)

		del data[name]

		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)
			_emit("set", f"{log_name}.{name}", "<deleted>", filename=filename, lineno=lineno)
		finally:
			del frame

	def __delitem__(self, key):
		log_name = object.__getattribute__(self, "_log_name")
		del self._data[key]

		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)
			_emit("set", f"{log_name}.{key}", "<deleted>", filename=filename, lineno=lineno)
		finally:
			del frame

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
		def unwrap(v):
			return _unwrap_value(v)

		return {k: unwrap(v) for k, v in self._data.items()}

	def __repr__(self):
		return f"{type(self).__name__}({self._data!r})"

	def __dir__(self):
		return sorted(set(super().__dir__()) | set(self._data.keys()))


class LoggedList(list):
	"""
	List wrapper that logs mutations like append, sort, pop, extend, etc
	"""

	def __init__(self, initial=None, name="set"):
		object.__setattr__(self, "_log_name", name)
		if initial is None:
			initial = []

		items = [_wrap_value(v, name=f"{name}[{i}]") for i, v in enumerate(initial)]
		super().__init__(items)

	def _emit(self, op, **details):
		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)
			_emit_change(self._log_name, op, state=self, filename=filename, lineno=lineno, **details)
		finally:
			del frame

	def __setitem__(self, key, value):
		if isinstance(key, slice):
			wrapped = [_wrap_value(v, name=f"{self._log_name}[{i}]") for i, v in enumerate(value)]
			super().__setitem__(key, wrapped)
			self._emit("setitem", key=str(key), value=value)
			return

		wrapped = _wrap_value(value, name=f"{self._log_name}[{key}]")
		super().__setitem__(key, wrapped)

		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)

			full_name = f"{self._log_name}.{key}"

			_emit(
				"change",
				full_name,
				{
					"op": "setitem",
					"value": _unwrap_value(value),
					"state": _unwrap_value(self),
				},
				filename=filename,
				lineno=lineno,
			)
		finally:
			del frame

	def __delitem__(self, key):
		super().__delitem__(key)
		self._emit("delitem", key=key)

	def append(self, value):
		wrapped = _wrap_value(value, name=f"{self._log_name}[{len(self)}]")
		super().append(wrapped)
		self._emit("append", value=value)

	def extend(self, iterable):
		items = list(iterable)
		wrapped = [_wrap_value(v, name=f"{self._log_name}[{len(self) + i}]") for i, v in enumerate(items)]
		super().extend(wrapped)
		self._emit("extend", value=items)

	def insert(self, index, value):
		wrapped = _wrap_value(value, name=f"{self._log_name}[{index}]")
		super().insert(index, wrapped)
		self._emit("insert", index=index, value=value)

	def pop(self, index=-1):
		value = super().pop(index)
		self._emit("pop", index=index, value=value)
		return value

	def remove(self, value):
		super().remove(value)
		self._emit("remove", value=value)

	def clear(self):
		super().clear()
		self._emit("clear")

	def sort(self, *args, **kwargs):
		super().sort(*args, **kwargs)
		self._emit("sort", args=args, kwargs=kwargs)

	def reverse(self):
		super().reverse()
		self._emit("reverse")

	def __iadd__(self, other):
		self.extend(other)
		return self

	def __imul__(self, other):
		super().__imul__(other)
		self._emit("imul", factor=other)
		return self

	def to_list(self):
		return [_unwrap_value(v) for v in list(self)]

	def __repr__(self):
		return f"{type(self).__name__}({list(self)!r})"


class LoggedDict(dict):
	"""
	Dict wrapper that logs mutations like setitem, update, pop, clear, etc
	"""

	def __init__(self, initial=None, name="set", **kwargs):
		object.__setattr__(self, "_log_name", name)

		if initial is None:
			initial = {}

		if isinstance(initial, Mapping):
			items = dict(initial).items()
		else:
			items = dict(initial).items()

		items = list(items) + list(kwargs.items())

		super().__init__()
		for k, v in items:
			dict.__setitem__(self, k, _wrap_value(v, name=f"{name}.{k}"))

	def _emit(self, op, **details):
		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)
			_emit_change(self._log_name, op, state=self, filename=filename, lineno=lineno, **details)
		finally:
			del frame

	def __setitem__(self, key, value):
		wrapped = _wrap_value(value, name=f"{self._log_name}.{key}")
		super().__setitem__(key, wrapped)
		frame = _caller_frame()

		try:
			filename, lineno = _get_location(frame)

			full_name = f"{self._log_name}.{key}"

			_emit(
				"change",
				full_name,
				{
					"op": "setitem",
					"value": _unwrap_value(value),
					"state": _unwrap_value(self),
				},
				filename=filename,
				lineno=lineno,
			)
		finally:
			del frame

	def __delitem__(self, key):
		super().__delitem__(key)
		self._emit("delitem", key=key)

	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError as e:
			raise AttributeError(name) from e

	def __setattr__(self, name, value):
		if name.startswith("_"):
			object.__setattr__(self, name, value)
			return

		self[name] = value

	def __delattr__(self, name):
		if name.startswith("_"):
			raise AttributeError(name)

		del self[name]

	def update(self, *args, **kwargs):
		data = dict(*args, **kwargs)
		for k, v in data.items():
			dict.__setitem__(self, k, _wrap_value(v, name=f"{self._log_name}.{k}"))
		self._emit("update", value=data)

	def setdefault(self, key, default=None):
		if key in self:
			return self[key]

		wrapped = _wrap_value(default, name=f"{self._log_name}.{key}")
		super().__setitem__(key, wrapped)
		self._emit("setdefault", key=key, value=default)
		return wrapped

	def pop(self, key, default=...):
		if default is ...:
			value = super().pop(key)
			self._emit("pop", key=key, value=value)
			return value

		value = super().pop(key, default)
		self._emit("pop", key=key, value=value)
		return value

	def popitem(self):
		item = super().popitem()
		self._emit("popitem", value=item)
		return item

	def clear(self):
		super().clear()
		self._emit("clear")

	def to_dict(self):
		return {k: _unwrap_value(v) for k, v in dict.items(self)}

	def __repr__(self):
		return f"{type(self).__name__}({dict(self)!r})"


class LoggedSet(set):
	"""
	Set wrapper that logs mutations like add, remove, update, clear, etc
	"""

	def __init__(self, initial=None, name="set"):
		object.__setattr__(self, "_log_name", name)

		if initial is None:
			initial = set()

		wrapped = {_wrap_value(v, name=f"{name}.item") for v in initial}
		super().__init__(wrapped)

	def _emit(self, op, **details):
		frame = _caller_frame()
		try:
			filename, lineno = _get_location(frame)
			_emit_change(self._log_name, op, state=self, filename=filename, lineno=lineno, **details)
		finally:
			del frame

	def add(self, element):
		wrapped = _wrap_value(element, name=f"{self._log_name}.item")
		super().add(wrapped)
		self._emit("add", value=element)

	def update(self, *others):
		values = []
		for other in others:
			values.extend(list(other))

		wrapped = {_wrap_value(v, name=f"{self._log_name}.item") for v in values}
		super().update(wrapped)
		self._emit("update", value=values)

	def discard(self, element):
		super().discard(element)
		self._emit("discard", value=element)

	def remove(self, element):
		super().remove(element)
		self._emit("remove", value=element)

	def pop(self):
		value = super().pop()
		self._emit("pop", value=value)
		return value

	def clear(self):
		super().clear()
		self._emit("clear")

	def difference_update(self, *others):
		super().difference_update(*others)
		self._emit("difference_update", value=[list(o) for o in others])

	def intersection_update(self, *others):
		super().intersection_update(*others)
		self._emit("intersection_update", value=[list(o) for o in others])

	def symmetric_difference_update(self, other):
		super().symmetric_difference_update(other)
		self._emit("symmetric_difference_update", value=list(other))

	def __ior__(self, other):
		self.update(other)
		return self

	def __iand__(self, other):
		super().__iand__(other)
		self._emit("iand", value=list(other))
		return self

	def __isub__(self, other):
		super().__isub__(other)
		self._emit("isub", value=list(other))
		return self

	def __ixor__(self, other):
		super().__ixor__(other)
		self._emit("ixor", value=list(other))
		return self

	def to_set(self):
		return {_unwrap_value(v) for v in set(self)}

	def __repr__(self):
		return f"{type(self).__name__}({set(self)!r})"


__all__ = [
	"LoggedObject",
	"LoggedList",
	"LoggedDict",
	"LoggedSet",
	"_wrap_value",
	"_path",
]
