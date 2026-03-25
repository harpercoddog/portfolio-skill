from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.getenv("PORTFOLIO_DB_PATH", DATA_DIR / "portfolio.db"))
DEFAULT_PROVIDER = os.getenv("PORTFOLIO_PRICE_PROVIDER", "mock")

