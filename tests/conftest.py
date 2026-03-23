import io
import sys
import pytest


@pytest.fixture
def capture_output():
	buffer = io.StringIO()
	old = sys.stdout
	sys.stdout = buffer
	try:
		yield buffer
	finally:
		sys.stdout = old
