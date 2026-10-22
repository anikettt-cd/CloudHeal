import os
import sqlite3
from pathlib import Path
import json
from datetime import UTC, datetime


DEFAULT_DB_PATH = Path.home() / ".cloudheal" / "cloudheal.db"
DB_PATH = Path(os.environ.get("CLOUDHEAL_DB_PATH", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=10.0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")

    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workloads (
                workload_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                image TEXT NOT NULL,
                desired_state TEXT NOT NULL,
                actual_state TEXT NOT NULL,
                node_id TEXT,
                cpu_limit REAL NOT NULL,
                memory_limit_mb INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                hostname TEXT NOT NULL,
                address TEXT NOT NULL,
                status TEXT NOT NULL,
                last_seen TEXT,
                system_info TEXT NOT NULL DEFAULT '{}',
                runtime_info TEXT NOT NULL DEFAULT '{}'
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                workload_id TEXT,
                node_id TEXT,
                details TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
            """
        )

def record_event(
    event_type: str,
    workload_id: str | None = None,
    node_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Persist a timestamped CloudHeal event."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO events (
                event_type,
                workload_id,
                node_id,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_type,
                workload_id,
                node_id,
                json.dumps(details or {}),
                datetime.now(UTC).isoformat(),
            ),
        )        
