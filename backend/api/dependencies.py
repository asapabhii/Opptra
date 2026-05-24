from __future__ import annotations

import os
from pathlib import Path

import aiosqlite


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "decisions.db"


def get_database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))


async def get_db() -> aiosqlite.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return aiosqlite.connect(db_path)
