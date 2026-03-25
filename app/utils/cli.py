from __future__ import annotations

from pathlib import Path

from app.config import get_default_db_path


def resolve_db_path(db_path: str | None) -> Path:
    return Path(db_path) if db_path else get_default_db_path()
