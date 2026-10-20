import json
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from cloudheal_control_plane.database import get_connection


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
    """Register a node or update its existing record."""
    node.last_seen = datetime.now(timezone.utc)
    node.status = "healthy"

    _save_node(node)

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
    """Mark nodes healthy or unhealthy based on heartbeat age."""
    now = datetime.now(timezone.utc)
    timeout = timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT node_id, last_seen FROM nodes"
        ).fetchall()

        for row in rows:
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


def heartbeat_node(
    node_id: str,
    system_info: dict[str, Any] | None = None,
    runtime_info: dict[str, Any] | None = None,
) -> NodeRecord | None:
    """Update a registered node after receiving its heartbeat."""
    node = get_node(node_id)

    if node is None:
        return None

    node.last_seen = datetime.now(timezone.utc)
    node.status = "healthy"

    if system_info is not None:
        node.system_info = system_info

    if runtime_info is not None:
        node.runtime_info = runtime_info

    _save_node(node)

    return node