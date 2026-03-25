#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DB_PATH
from app.db import bootstrap_database


def main() -> None:
    conn = bootstrap_database()
    conn.close()
    print(f"数据库已初始化: {DB_PATH}")


if __name__ == "__main__":
    main()

