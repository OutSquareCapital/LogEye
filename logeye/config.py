import os
import sys
from dataclasses import dataclass
from typing import ClassVar, Literal, TypeAlias

from typing_extensions import Self

PathMode: TypeAlias = Literal["absolute", "project", "file"]

Mode: TypeAlias = Literal["edu", "educational", "full"]


# =========
#  TOGGLES
# =========
@dataclass(slots=True)
class Config:
	_instance: ClassVar[Self | None] = None
	logs: bool | None = None
	log_file: bool | None = None
	log_path: str | None = None
	decorators: bool | None = None
	message_metadata: bool | None = None
	mode: Mode | None = None
	path_mode: PathMode | None = None
	_g_enabled: bool = True
	_g_path_mode: str = "file"
	_g_show_message_meta: bool = True
	_g_deco_only: bool = False
	_g_log_mode: str = "full"
	_g_show_time: bool = True
	_g_show_file: bool = True
	_g_show_lineno: bool = True
	_g_log_file: str | None = None
	_g_log_file_enabled: bool = True
	_g_project_root: str = os.getcwd()
	_g_library_root: str = os.path.dirname(__file__)
	_g_exec_root: str = os.path.dirname(os.path.abspath(sys.argv[0]))
	_g_log_pipe_name: str = "l"
	_g_start_time: float | None = None

	def __new__(cls) -> Self:
		if cls._instance is None:
			cls._instance = object.__new__(cls)
		return cls._instance

	def toggle_logs(self, enabled: bool) -> None:
		self._g_enabled = enabled

	def toggle_global_log_file(self, enabled: bool) -> None:
		self._g_log_file_enabled = enabled

	def toggle_decorator_log_only(self, enabled: bool) -> None:
		"""
		Toggle only @log-decorated tracing.
		"""
		self._g_deco_only = enabled

	def toggle_message_metadata(self, enabled: bool) -> None:
		"""
		Enable or disable metadata for message logs

		If disabled:
			log("hello") -> prints just "hello"

		If enabled:
			log("hello") -> prints "[time] file:line hello"
		"""
		self._g_show_message_meta = enabled

	# =========
	#  SETTERS
	# =========
	def set_mode(self, mode: Mode) -> None:
		"""
		Set global logging mode
		full or  edu / educational
		"""

		self._g_log_mode = mode

	def set_global_log_file(self, filepath: str | None) -> None:
		"""
		Route LogEye output to this file globally.
		"""
		self._g_log_file = os.fspath(filepath) if filepath is not None else None

	def set_path_mode(self, mode: PathMode) -> None:
		if mode not in ("absolute", "project", "file"):
			raise ValueError(f"Invalid path mode: {mode!r}")
		self._g_path_mode = mode

	def _normalize_mode(self, mode: Mode) -> str:
		"""Normalize mode to 'full' or 'educational'."""
		if mode in ("edu", "educational"):
			return "educational"
		return "full"


config = Config()
