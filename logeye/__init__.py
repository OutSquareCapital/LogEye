import time

from .config import config
from .core import log, watch
from .formatting import reset_output_formatter, set_output_formatter
from .pipe import l

w = watch

_g_start_time = time.perf_counter()

__all__ = [
	"log",
	"l",
	"watch",
	"w",
	"config",
	"set_output_formatter",
	"reset_output_formatter",
]
