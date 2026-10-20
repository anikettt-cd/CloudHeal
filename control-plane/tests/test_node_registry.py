from datetime import datetime, timezone
from uuid import uuid4

from cloudheal_control_plane.database import get_connection
from cloudheal_control_plane.registry import (
    NodeRecord,
    get_node,
    get_nodes,
    heartbeat_node,
    register_node,
)


def make_node() -> NodeRecord:
    return NodeRecord(
        node_id=str(uuid4()),
        hostname="test-node",
        address="127.0.0.1",
        system_info={"cpu_count": 4},
        runtime_info={
            "available": True,
            "cpu_count": 4,
            "memory_bytes": 4 * 1024**3,
        },
    )


def test_register_node_persists_to_database():
    node = make_node()

    registered = register_node(node)

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM nodes WHERE node_id = ?",
            (node.node_id,),
        ).fetchone()

    assert row is not None
    assert row["hostname"] == "test-node"
    assert row["address"] == "127.0.0.1"
    assert registered.status == "healthy"


def test_get_node_reads_persisted_record():
    node = make_node()
    register_node(node)

    # Retrieve the record through the SQLite-backed registry.
    retrieved = get_node(node.node_id)

    assert retrieved is not None
    assert retrieved.node_id == node.node_id
    assert retrieved.system_info == {"cpu_count": 4}
    assert retrieved.runtime_info["available"] is True


def test_heartbeat_updates_persisted_node():
    node = make_node()
    register_node(node)

    updated = heartbeat_node(
        node.node_id,
        system_info={"cpu_count": 8},
        runtime_info={
            "available": True,
            "cpu_count": 8,
            "memory_bytes": 8 * 1024**3,
        },
    )

    retrieved = get_node(node.node_id)

    assert updated is not None
    assert retrieved is not None
    assert retrieved.system_info == {"cpu_count": 8}
    assert retrieved.runtime_info["cpu_count"] == 8
    assert retrieved.last_seen is not None
    assert retrieved.last_seen.tzinfo is not None


def test_get_nodes_returns_persisted_nodes():
    node = make_node()
    register_node(node)

    nodes = get_nodes()

    assert len(nodes) == 1
    assert nodes[0].node_id == node.node_id