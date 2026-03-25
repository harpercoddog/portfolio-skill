#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse

from app.db import bootstrap_database
from app.utils.cli import resolve_db_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化本地投资组合 SQLite 数据库。")
    parser.add_argument("--db-path", help="SQLite 数据库路径，默认 data/portfolio.db 或环境变量 PORTFOLIO_DB_PATH")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)
    conn = bootstrap_database(db_path=db_path)
    conn.close()
    print(f"数据库已初始化: {db_path}")


if __name__ == "__main__":
    main()
