import os
from string import Template

from .. import config
from .frames import _caller_frame, _get_location


def _expand_template(text):
	frame = _caller_frame()
	try:
		if frame is None:
			return text

		namespace = {}
		namespace.update(frame.f_globals)
		namespace.update(frame.f_locals)

		filename, lineno = _get_location(frame)

		namespace["apath"] = filename or ""
		namespace["rpath"] = os.path.relpath(filename, config._PROJECT_ROOT) if filename else ""
		namespace["fpath"] = os.path.basename(filename) if filename else ""

		return Template(text).safe_substitute(namespace)
	finally:
		del frame


__all__ = [
	"_expand_template",
]
