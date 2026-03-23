import os
import inspect

from .. import config


def _get_location(frame):
	if frame is None:
		return None, None

	return frame.f_code.co_filename, frame.f_lineno


def _caller_frame():
	frame = inspect.currentframe()

	try:
		frame = frame.f_back

		library_root = os.path.abspath(config._LIBRARY_ROOT)

		while frame:
			filename = frame.f_code.co_filename

			if filename:
				filename = os.path.abspath(filename)

				if not filename.startswith(library_root):
					return frame

			frame = frame.f_back

		return None
	finally:
		del frame


__all__ = [
	"_get_location",
	"_caller_frame",
]
