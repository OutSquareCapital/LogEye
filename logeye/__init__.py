import time

from .pipe import l
from .core import log, watch
from .formatting import set_output_formatter, reset_output_formatter
from .config import (
	toggle_logs,
	toggle_decorator_log_only,
	toggle_message_metadata,
	toggle_global_log_file,
	set_mode,
	set_path_mode,
	set_global_log_file,
)

w = watch

_g_start_time = time.perf_counter()

__all__ = [
	"log",
	"l",
	"watch",
	"w",
	"toggle_logs",
	"toggle_global_log_file",
	"toggle_message_metadata",
	"toggle_decorator_log_only",
	"set_mode",
	"set_path_mode",
	"set_global_log_file",
	"set_output_formatter",
	"reset_output_formatter",
]
