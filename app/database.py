from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import DATABASE_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS robots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    platform TEXT NOT NULL,
    hardware_version TEXT DEFAULT '',
    firmware_version TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT DEFAULT '',
    compatible_platforms TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'lab',
    safety_boundary TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    robot_id INTEGER,
    skill_id INTEGER,
    environment TEXT DEFAULT '',
    model_version TEXT DEFAULT '',
    protocol TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'unknown',
    success_rate REAL DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    intervention_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    failure_summary TEXT DEFAULT '',
    log_path TEXT DEFAULT '',
    video_path TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(robot_id) REFERENCES robots(id) ON DELETE SET NULL,
    FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS trial_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_id INTEGER NOT NULL,
    timestamp REAL,
    event_type TEXT NOT NULL,
    label TEXT DEFAULT '',
    confidence REAL,
    value REAL,
    metadata TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(trial_id) REFERENCES trials(id) ON DELETE CASCADE
);
"""


def init_db(db_path: Path = DATABASE_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_db(db_path: Path = DATABASE_PATH) -> Iterator[sqlite3.Connection]:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()
