from .core import log
from .emmiter import _emit
from .introspection import _caller_frame, _get_location, _infer_name_from_frame


class _LogPipe:
	"""
	Implements the pipe-style logging interface: `value | l`

	Allows logging values inline without calling `log(...)` explicitly
	"""

	def __call__(self, value: object, *args: object, **kwargs: object) -> object:
		"""
		Allow `l(value)` to behave exactly like `log(value)`
		This makes the pipe object usable as a normal function as well
		"""

		return log(value, *args, **kwargs)

	def __ror__(self, other: object):
		"""
		Right-hand pipe operator: `value | l`

		- Get value on the left
		- Infer variable name
		- Emit log
		- Return back the value
		"""

		frame = _caller_frame()

		try:
			name = _infer_name_from_frame(frame)
			filename, lineno = _get_location(frame)

			if name != "set":
				_emit("set", name, other, filename=filename, lineno=lineno)
			else:
				_emit("message", "message", other, filename=filename, lineno=lineno)
		finally:
			del frame

		return other


l = _LogPipe()
