import pytest


from datetime import datetime, timezone , timedelta
from uuid import uuid4
import json

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

def test_unhealthy_node_transition_records_event():
    node = make_node()
    register_node(node)

    # Simulate a heartbeat older than the allowed timeout.
    with get_connection() as connection:
        connection.execute(
            "UPDATE nodes SET last_seen = ? WHERE node_id = ?",
            (
                (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat(),
                node.node_id,
            ),
        )

    # Trigger health evaluation.
    get_node(node.node_id)

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT event_type, node_id, details
            FROM events
            WHERE node_id = ?
            ORDER BY event_id
            """,
            (node.node_id,),
        ).fetchall()

    health_events = [
        event for event in events
        if event["event_type"] == "NODE_BECAME_UNHEALTHY"
    ]

    assert len(health_events) == 1
    assert health_events[0]["node_id"] == node.node_id
    assert json.loads(health_events[0]["details"])["previous_status"] == "healthy"


def test_repeated_health_checks_do_not_duplicate_transition_events():
    node = make_node()
    register_node(node)

    with get_connection() as connection:
        connection.execute(
            "UPDATE nodes SET last_seen = ? WHERE node_id = ?",
            (
                (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat(),
                node.node_id,
            ),
        )

    # Multiple reads should not create repeated transition events.
    get_node(node.node_id)
    get_node(node.node_id)
    get_nodes()

    with get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE node_id = ?
              AND event_type = 'NODE_BECAME_UNHEALTHY'
            """,
            (node.node_id,),
        ).fetchone()[0]

    assert count == 1

def test_recovered_node_records_healthy_transition_event():
    node = make_node()
    register_node(node)

    old_timestamp = (
        datetime.now(timezone.utc) - timedelta(seconds=120)
    ).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE nodes
            SET last_seen = ?, status = 'unhealthy'
            WHERE node_id = ?
            """,
            (old_timestamp, node.node_id),
        )

    recovered = heartbeat_node(node.node_id)

    with get_connection() as connection:
        events = connection.execute(
            """
            SELECT event_type, details
            FROM events
            WHERE node_id = ?
              AND event_type = 'NODE_BECAME_HEALTHY'
            """,
            (node.node_id,),
        ).fetchall()

    assert recovered is not None
    assert recovered.status == "healthy"
    assert len(events) == 1

    details = json.loads(events[0]["details"])
    assert details["previous_status"] == "unhealthy"
    assert details["new_status"] == "healthy"


def test_repeated_healthy_heartbeats_do_not_duplicate_recovery_events():
    node = make_node()
    register_node(node)

    old_timestamp = (
        datetime.now(timezone.utc) - timedelta(seconds=120)
    ).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE nodes
            SET last_seen = ?, status = 'unhealthy'
            WHERE node_id = ?
            """,
            (old_timestamp, node.node_id),
        )

    heartbeat_node(node.node_id)
    heartbeat_node(node.node_id)
    heartbeat_node(node.node_id)

    with get_connection() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM events
            WHERE node_id = ?
              AND event_type = 'NODE_BECAME_HEALTHY'
            """,
            (node.node_id,),
        ).fetchone()[0]

    assert count == 1
def test_same_node_id_registered_twice_updates_one_record():
    node = make_node()

    first = register_node(node)
    second_node = NodeRecord(
        node_id=node.node_id,
        hostname="updated-host",
        address="10.0.0.2",
        system_info={"cpu_count": 8},
        runtime_info={"available": True},
    )
    second = register_node(second_node)

    assert first.node_id == second.node_id
    assert len(get_nodes()) == 1

    stored = get_node(node.node_id)
    assert stored is not None
    assert stored.hostname == "updated-host"
    assert stored.address == "10.0.0.2"


def test_different_node_ids_same_hostname_and_address_are_rejected():
    from cloudheal_control_plane.registry import NodeIdentityConflictError

    first = make_node()
    register_node(first)

    conflicting = NodeRecord(
        node_id=str(uuid4()),
        hostname=first.hostname,
        address=first.address,
        system_info={"cpu_count": 2},
        runtime_info={"available": False},
    )

    with pytest.raises(NodeIdentityConflictError):
        register_node(conflicting)

    assert len(get_nodes()) == 1


def test_rejected_registration_does_not_modify_original_record():
    from cloudheal_control_plane.registry import NodeIdentityConflictError

    first = make_node()
    register_node(first)

    original = get_node(first.node_id)

    conflicting = NodeRecord(
        node_id=str(uuid4()),
        hostname=first.hostname,
        address=first.address,
        system_info={"cpu_count": 99},
        runtime_info={"available": False},
    )

    with pytest.raises(NodeIdentityConflictError):
        register_node(conflicting)

    after = get_node(first.node_id)
    assert after == original


def test_same_node_id_can_update_address():
    node = make_node()
    register_node(node)

    updated = NodeRecord(
        node_id=node.node_id,
        hostname=node.hostname,
        address="192.168.1.5",
        system_info=node.system_info,
        runtime_info=node.runtime_info,
    )
    register_node(updated)

    stored = get_node(node.node_id)
    assert stored is not None
    assert stored.address == "192.168.1.5"
    assert len(get_nodes()) == 1


def test_same_hostname_different_addresses_allowed():
    first = make_node()
    first.hostname = "shared-host"
    first.address = "10.0.0.1"
    register_node(first)

    second = make_node()
    second.hostname = "shared-host"
    second.address = "10.0.0.2"
    register_node(second)

    assert len(get_nodes()) == 2


def test_different_hostnames_same_address_allowed():
    first = make_node()
    first.hostname = "host-a"
    first.address = "10.0.0.1"
    register_node(first)

    second = make_node()
    second.hostname = "host-b"
    second.address = "10.0.0.1"
    register_node(second)

    assert len(get_nodes()) == 2

def test_register_node_conflict_returns_409():
    from fastapi.testclient import TestClient

    from cloudheal_control_plane.api import app

    first = make_node()
    register_node(first)

    conflicting = NodeRecord(
        node_id=str(uuid4()),
        hostname=first.hostname,
        address=first.address,
        system_info={"cpu_count": 2},
        runtime_info={"available": False},
    )

    with TestClient(app) as client:
        response = client.post(
            "/nodes/register",
            json=conflicting.model_dump(mode="json"),
        )

    assert response.status_code == 409
    assert "already owns" in response.json()["detail"]

