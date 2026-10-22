import json

from cloudheal_control_plane.database import (
    get_connection,
    record_event,
)


def test_record_event_persists_event():
    record_event(
        event_type="EXECUTION_SUCCEEDED",
        workload_id="workload-123",
        node_id="node-456",
        details={"image": "nginx:latest", "attempt": 1},
    )

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM events"
        ).fetchone()

    assert row is not None
    assert row["event_type"] == "EXECUTION_SUCCEEDED"
    assert row["workload_id"] == "workload-123"
    assert row["node_id"] == "node-456"
    assert json.loads(row["details"]) == {
        "image": "nginx:latest",
        "attempt": 1,
    }
    assert row["created_at"]