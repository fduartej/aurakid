from __future__ import annotations

import pytest

from src.config import settings
from src.db.database import init_db


@pytest.fixture(autouse=True)
def _sqlite_temporal(tmp_path):
    """Cada test usa su propia base SQLite temporal, aislada de la real."""
    db_path = str(tmp_path / "test.db")
    object.__setattr__(settings, "sqlite_path", db_path)
    init_db(db_path)
    yield
