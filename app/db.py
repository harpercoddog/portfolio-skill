from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import BASE_DIR, DB_PATH


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema_path = BASE_DIR / "docs" / "schema.sql"
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()


def bootstrap_database(db_path: str | Path | None = None) -> sqlite3.Connection:
    conn = get_connection(db_path=db_path)
    init_db(conn)
    return conn

