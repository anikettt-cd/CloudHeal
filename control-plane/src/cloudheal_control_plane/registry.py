import json
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from cloudheal_control_plane.database import get_connection


class NodeIdentityConflictError(Exception):
    """Raised when another node ID already owns a hostname/address pair."""


HEARTBEAT_TIMEOUT_SECONDS = 30


class NodeRecord(BaseModel):
    node_id: str
    hostname: str
    address: str
    status: str = "healthy"
    last_seen: datetime | None = None
    system_info: dict[str, Any] = Field(default_factory=dict)
    runtime_info: dict[str, Any] = Field(default_factory=dict)


def _row_to_node(row: Any) -> NodeRecord:
    """Convert a SQLite row into a NodeRecord."""
    return NodeRecord(
        node_id=row["node_id"],
        hostname=row["hostname"],
        address=row["address"],
        status=row["status"],
        last_seen=row["last_seen"],
        system_info=json.loads(row["system_info"]),
        runtime_info=json.loads(row["runtime_info"]),
    )


def _save_node(node: NodeRecord) -> None:
    """Insert or update a node in SQLite."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO nodes (
                node_id,
                hostname,
                address,
                status,
                last_seen,
                system_info,
                runtime_info
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                hostname = excluded.hostname,
                address = excluded.address,
                status = excluded.status,
                last_seen = excluded.last_seen,
                system_info = excluded.system_info,
                runtime_info = excluded.runtime_info
            """,
            (
                node.node_id,
                node.hostname,
                node.address,
                node.status,
                node.last_seen.isoformat() if node.last_seen else None,
                json.dumps(node.system_info),
                json.dumps(node.runtime_info),
            ),
        )


def register_node(node: NodeRecord) -> NodeRecord:
    """Register a node or update its existing record.

    A node_id may update its own hostname or address. A different node_id may
    not reuse both the hostname and address of an existing node.
    """
    node.last_seen = datetime.now(timezone.utc)
    node.status = "healthy"

    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")

        conflict = connection.execute(
            """
            SELECT node_id
            FROM nodes
            WHERE hostname = ?
              AND address = ?
              AND node_id != ?
            """,
            (node.hostname, node.address, node.node_id),
        ).fetchone()

        if conflict is not None:
            raise NodeIdentityConflictError(
                "Another node ID already owns the "
                f"hostname/address combination: {node.hostname}/{node.address}"
            )

        connection.execute(
            """
            INSERT INTO nodes (
                node_id,
                hostname,
                address,
                status,
                last_seen,
                system_info,
                runtime_info
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                hostname = excluded.hostname,
                address = excluded.address,
                status = excluded.status,
                last_seen = excluded.last_seen,
                system_info = excluded.system_info,
                runtime_info = excluded.runtime_info
            """,
            (
                node.node_id,
                node.hostname,
                node.address,
                node.status,
                node.last_seen.isoformat(),
                json.dumps(node.system_info),
                json.dumps(node.runtime_info),
            ),
        )

    return node


def get_nodes() -> list[NodeRecord]:
    """Return all persisted nodes with refreshed health status."""
    refresh_node_statuses()

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM nodes"
        ).fetchall()

    return [_row_to_node(row) for row in rows]


def get_node(node_id: str) -> NodeRecord | None:
    """Return one persisted node with refreshed health status."""
    refresh_node_statuses()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM nodes WHERE node_id = ?",
            (node_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_node(row)


def refresh_node_statuses() -> None:
    """Mark nodes healthy or unhealthy and record health transitions."""
    now = datetime.now(timezone.utc)
    timeout = timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT node_id, last_seen, status FROM nodes"
        ).fetchall()

        for row in rows:
            previous_status = row["status"]
            last_seen_value = row["last_seen"]

            if last_seen_value is None:
                new_status = "unhealthy"
            else:
                last_seen = datetime.fromisoformat(last_seen_value)

                # Handle timestamps stored without timezone information.
                if last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)

                new_status = (
                    "unhealthy"
                    if now - last_seen > timeout
                    else "healthy"
                )

            connection.execute(
                """
                UPDATE nodes
                SET status = ?
                WHERE node_id = ?
                """,
                (new_status, row["node_id"]),
            )

            if (
                previous_status == "healthy"
                and new_status == "unhealthy"
            ):
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
                        "NODE_BECAME_UNHEALTHY",
                        None,
                        row["node_id"],
                        json.dumps({
                            "previous_status": previous_status,
                            "new_status": new_status,
                            "reason": "heartbeat_timeout",
                        }),
                        now.isoformat(),
                    ),
                )


def heartbeat_node(
    node_id: str,
    system_info: dict[str, Any] | None = None,
    runtime_info: dict[str, Any] | None = None,
) -> NodeRecord | None:
    """Update a registered node and record recovery transitions."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM nodes WHERE node_id = ?",
            (node_id,),
        ).fetchone()

        if row is None:
            return None

        previous_status = row["status"]

        now = datetime.now(timezone.utc)

        connection.execute(
            """
            UPDATE nodes
            SET last_seen = ?,
                status = 'healthy',
                system_info = ?,
                runtime_info = ?
            WHERE node_id = ?
            """,
            (
                now.isoformat(),
                json.dumps(
                    system_info
                    if system_info is not None
                    else json.loads(row["system_info"])
                ),
                json.dumps(
                    runtime_info
                    if runtime_info is not None
                    else json.loads(row["runtime_info"])
                ),
                node_id,
            ),
        )

        if previous_status == "unhealthy":
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
                    "NODE_BECAME_HEALTHY",
                    None,
                    node_id,
                    json.dumps({
                        "previous_status": previous_status,
                        "new_status": "healthy",
                        "reason": "heartbeat_received",
                    }),
                    now.isoformat(),
                ),
            )

        updated_row = connection.execute(
            "SELECT * FROM nodes WHERE node_id = ?",
            (node_id,),
        ).fetchone()

    return _row_to_node(updated_row)