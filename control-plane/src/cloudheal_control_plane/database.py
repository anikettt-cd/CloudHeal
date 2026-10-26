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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_key TEXT NOT NULL,
                status TEXT NOT NULL,
                classification TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                resolved_at TEXT,
                evidence TEXT NOT NULL DEFAULT '{}'
            )
            """
        )

        # Allow at most one open incident for each Kubernetes resource.
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_one_open_incident_per_resource
            ON incidents(resource_key)
            WHERE status = 'OPEN'
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recovery_attempts (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                reason_code TEXT,
                details TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                finished_at TEXT,
                FOREIGN KEY (incident_id)
                    REFERENCES incidents(incident_id)
            )
            """
        )

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_one_active_recovery_per_incident
            ON recovery_attempts(incident_id)
            WHERE status IN ('IN_PROGRESS', 'UNKNOWN')
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
def observe_incident(
    resource_key: str,
    classification: str,
    evidence: dict,
    observed_at: str,
) -> dict:
    """Create an incident or update an existing open incident."""

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT incident_id, first_seen
            FROM incidents
            WHERE resource_key = ? AND status = 'OPEN'
            """,
            (resource_key,),
        ).fetchone()

        is_new = row is None

        if is_new:
            cursor = connection.execute(
                """
                INSERT INTO incidents (
                    resource_key,
                    status,
                    classification,
                    first_seen,
                    last_seen,
                    evidence
                )
                VALUES (?, 'OPEN', ?, ?, ?, ?)
                """,
                (
                    resource_key,
                    classification,
                    observed_at,
                    observed_at,
                    json.dumps(evidence),
                ),
            )
            incident_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO events (
                    event_type, details, created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    "INCIDENT_OPENED",
                    json.dumps({
                        "incident_id": incident_id,
                        "resource_key": resource_key,
                        "classification": classification,
                        "evidence": evidence,
                    }),
                    observed_at,
                ),
            )
            first_seen = observed_at

        else:
            incident_id = row["incident_id"]
            first_seen = row["first_seen"]

            connection.execute(
                """
                UPDATE incidents
                SET last_seen = ?,
                    classification = ?,
                    evidence = ?
                WHERE incident_id = ?
                """,
                (
                    observed_at,
                    classification,
                    json.dumps(evidence),
                    incident_id,
                ),
            )

        return {
            "incident_id": incident_id,
            "resource_key": resource_key,
            "status": "OPEN",
            "classification": classification,
            "first_seen": first_seen,
            "last_seen": observed_at,
            "evidence": evidence,
            "created": is_new,
        }


def resolve_incident(
    resource_key: str,
    resolved_at: str,
) -> dict | None:
    """Resolve an incident unless its recovery outcome is still uncertain."""

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT incident_id, classification, first_seen
            FROM incidents
            WHERE resource_key = ? AND status = 'OPEN'
            """,
            (resource_key,),
        ).fetchone()

        if row is None:
            return None

        active_attempt = connection.execute(
            """
            SELECT attempt_id, status
            FROM recovery_attempts
            WHERE incident_id = ?
              AND status IN ('IN_PROGRESS', 'UNKNOWN')
            LIMIT 1
            """,
            (row["incident_id"],),
        ).fetchone()

        if active_attempt is not None:
            return {
                "incident_id": row["incident_id"],
                "resource_key": resource_key,
                "status": "OPEN",
                "resolution_blocked": True,
                "reason_code": "RECOVERY_OUTCOME_UNRESOLVED",
                "active_attempt_id": active_attempt["attempt_id"],
                "active_attempt_status": active_attempt["status"],
            }

        connection.execute(
            """
            UPDATE incidents
            SET status = 'RESOLVED',
                resolved_at = ?,
                last_seen = ?
            WHERE incident_id = ?
            """,
            (
                resolved_at,
                resolved_at,
                row["incident_id"],
            ),
        )

        connection.execute(
            """
            INSERT INTO events (
                event_type, details, created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                "INCIDENT_RESOLVED",
                json.dumps({
                    "incident_id": row["incident_id"],
                    "resource_key": resource_key,
                    "classification": row["classification"],
                    "first_seen": row["first_seen"],
                    "resolved_at": resolved_at,
                }),
                resolved_at,
            ),
        )

        return {
            "incident_id": row["incident_id"],
            "resource_key": resource_key,
            "status": "RESOLVED",
            "first_seen": row["first_seen"],
            "resolved_at": resolved_at,
        }

def claim_recovery_attempt(
    incident_id: int,
    action: str,
    details: dict | None = None,
) -> dict:
    """Atomically claim a recovery attempt for an open incident."""

    now = datetime.now(UTC).isoformat()

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        incident = connection.execute(
            """
            SELECT status
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()

        if incident is None:
            return {
                "claimed": False,
                "reason_code": "INCIDENT_NOT_FOUND",
            }

        if incident["status"] != "OPEN":
            return {
                "claimed": False,
                "reason_code": "INCIDENT_NOT_OPEN",
            }

        active_attempt = connection.execute(
            """
            SELECT attempt_id
            FROM recovery_attempts
            WHERE incident_id = ?
              AND status IN ('IN_PROGRESS', 'UNKNOWN')
            """,
            (incident_id,),
        ).fetchone()

        if active_attempt is not None:
            return {
                "claimed": False,
                "reason_code": "RECOVERY_ALREADY_ACTIVE",
                "attempt_id": active_attempt["attempt_id"],
            }

        # Automatic recovery is limited to one attempt per incident.
        # Check persisted attempt details so this guard survives restarts.
        is_automatic_recovery = (
            isinstance(details, dict)
            and details.get("trigger") == "automatic"
        )

        if is_automatic_recovery:
            previous_attempts = connection.execute(
                """
                SELECT attempt_id, status, details
                FROM recovery_attempts
                WHERE incident_id = ?
                ORDER BY attempt_id ASC
                """,
                (incident_id,),
            ).fetchall()

            for previous_attempt in previous_attempts:
                try:
                    previous_details = json.loads(
                        previous_attempt["details"] or "{}"
                    )
                except (TypeError, json.JSONDecodeError):
                    previous_details = {}

                if (
                    isinstance(previous_details, dict)
                    and previous_details.get("trigger") == "automatic"
                ):
                    return {
                        "claimed": False,
                        "reason_code": "AUTO_RECOVERY_ALREADY_ATTEMPTED",
                        "attempt_id": previous_attempt["attempt_id"],
                        "previous_status": previous_attempt["status"],
                    }

        cursor = connection.execute(
            """
            INSERT INTO recovery_attempts (
                incident_id,
                action,
                status,
                details,
                started_at,
                updated_at
            )
            VALUES (?, ?, 'IN_PROGRESS', ?, ?, ?)
            """,
            (
                incident_id,
                action,
                json.dumps(details or {}),
                now,
                now,
            ),
        )

        attempt_id = cursor.lastrowid

        connection.execute(
            """
            INSERT INTO events (event_type, details, created_at)
            VALUES (?, ?, ?)
            """,
            (
                "RECOVERY_ATTEMPT_CLAIMED",
                json.dumps({
                    "incident_id": incident_id,
                    "attempt_id": attempt_id,
                    "action": action,
                }),
                now,
            ),
        )

        return {
            "claimed": True,
            "attempt_id": attempt_id,
            "incident_id": incident_id,
            "action": action,
            "status": "IN_PROGRESS",
            "started_at": now,
        }


def finish_recovery_attempt(
    attempt_id: int,
    status: str,
    reason_code: str | None = None,
    details: dict | None = None,
) -> dict:
    """Persist a recovery outcome without silently releasing uncertain attempts."""

    allowed_statuses = {"SUCCEEDED", "FAILED", "UNKNOWN"}

    if status not in allowed_statuses:
        raise ValueError(
            f"Unsupported recovery outcome: {status}"
        )

    now = datetime.now(UTC).isoformat()

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        attempt = connection.execute(
            """
           SELECT status, details
           FROM recovery_attempts
           WHERE attempt_id = ?
            """,
            (attempt_id,),
        ).fetchone()

        if attempt is None:
            return {
                "updated": False,
                "reason_code": "ATTEMPT_NOT_FOUND",
            }

        if attempt["status"] != "IN_PROGRESS":
            return {
                "updated": False,
                "reason_code": "ATTEMPT_NOT_IN_PROGRESS",
                "status": attempt["status"],
            }

        try:
            existing_details = json.loads(
                attempt["details"] or "{}"
            )
        except (TypeError, json.JSONDecodeError):
            existing_details = {}

        if not isinstance(existing_details, dict):
            existing_details = {}

        final_details = {
            **existing_details,
            **(details or {}),
        }

        connection.execute(
            """
            UPDATE recovery_attempts
            SET status = ?,
                reason_code = ?,
                details = ?,
                updated_at = ?,
                finished_at = ?
            WHERE attempt_id = ?
            """,
            (
                status,
                reason_code,
                json.dumps(final_details),
                now,
                now,
                attempt_id,
            ),
        )

        connection.execute(
            """
            INSERT INTO events (event_type, details, created_at)
            VALUES (?, ?, ?)
            """,
            (
                f"RECOVERY_ATTEMPT_{status}",
                json.dumps({
                    "attempt_id": attempt_id,
                    "status": status,
                    "reason_code": reason_code,
                }),
                now,
            ),
        )

        return {
            "updated": True,
            "attempt_id": attempt_id,
            "status": status,
            "reason_code": reason_code,
            "updated_at": now,
        }

def get_unresolved_recovery_attempts() -> list[dict]:
    """Return recovery attempts whose outcomes need reconciliation."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                attempt_id,
                incident_id,
                action,
                status,
                reason_code,
                details,
                started_at,
                updated_at,
                finished_at
            FROM recovery_attempts
            WHERE status IN ('IN_PROGRESS', 'UNKNOWN')
            ORDER BY started_at ASC, attempt_id ASC
            """
        ).fetchall()

    attempts = []

    for row in rows:
        attempt = dict(row)
        attempt["details"] = json.loads(attempt["details"])
        attempts.append(attempt)

    return attempts


def list_incident_history(limit: int = 50) -> list[dict]:
    """Return recent incidents with their associated recovery attempts."""
    limit = max(1, min(int(limit), 200))

    with get_connection() as connection:
        incidents = connection.execute(
            """
            SELECT incident_id, resource_key, status, classification,
                   first_seen, last_seen, resolved_at, evidence
            FROM incidents
            ORDER BY incident_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        history = []

        for row in incidents:
            incident = dict(row)
            incident["evidence"] = json.loads(incident["evidence"] or "{}")

            attempts = connection.execute(
                """
                SELECT attempt_id, action, status, reason_code, details,
                       started_at, updated_at, finished_at
                FROM recovery_attempts
                WHERE incident_id = ?
                ORDER BY attempt_id DESC
                """,
                (incident["incident_id"],),
            ).fetchall()

            incident["recovery_attempts"] = []

            for attempt_row in attempts:
                attempt = dict(attempt_row)
                attempt["details"] = json.loads(attempt["details"] or "{}")
                incident["recovery_attempts"].append(attempt)

            history.append(incident)

        return history
