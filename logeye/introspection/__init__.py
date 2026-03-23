from .ast import (
	_is_user_code,
	_is_assigned_call,
	_is_direct_log_call,
	_infer_callsite_name,
	_infer_name_from_frame,
	_get_call_index_in_line,
	_get_assignment_target_for_call,
	_get_assignment_target_for_pipe,
)
from .templates import _expand_template
from .frames import _caller_frame, _get_location
