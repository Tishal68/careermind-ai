import pytest
from app.core.request_limits import _expensive

@pytest.fixture(autouse=True)
def isolate_rate_limit_state():
    # Each fixture's user IDs belong to a different isolated database.
    _expensive.entries.clear()
    yield
    _expensive.entries.clear()
