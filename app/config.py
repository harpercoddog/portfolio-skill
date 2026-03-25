from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DB_FILENAME = "portfolio.db"
DEFAULT_PROVIDER = os.getenv("PORTFOLIO_PRICE_PROVIDER", "auto")


def get_default_db_path() -> Path:
    return Path(os.getenv("PORTFOLIO_DB_PATH", DATA_DIR / DEFAULT_DB_FILENAME))
