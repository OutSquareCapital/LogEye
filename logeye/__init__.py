from .pipe import l
from .core import log, watch
from .formatting import set_output_formatter, reset_output_formatter
from .config import logon, logoff, set_path_mode, set_message_metadata

w = watch

__all__ = [
	"log",
	"watch",
	"w",
	"l",
	"logon",
	"logoff",
	"set_path_mode",
	"set_message_metadata",
	"set_output_formatter",
	"reset_output_formatter",
]
