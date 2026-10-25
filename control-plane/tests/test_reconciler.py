from unittest.mock import Mock, patch
from uuid import uuid4, UUID

import httpx

from cloudheal_control_plane.registry import NodeRecord, register_node
from cloudheal_control_plane.workloads.models import (
    WorkloadCreate,
    WorkloadState,
)
from cloudheal_control_plane.workloads.registry import WorkloadRegistry
from cloudheal_control_plane.workloads.service import WorkloadService
from cloudheal_control_plane.workloads.reconciler import WorkloadReconciler
from cloudheal_control_plane.workloads.scheduler import SchedulingError


def setup_reconciler():
    registry = WorkloadRegistry()
    service = WorkloadService(registry)

    workload = service.create_workload(
        WorkloadCreate(
            name="reconciler-test",
            image="nginx:latest",
        )
    )

    node_id = uuid4()
    node = NodeRecord(
        node_id=str(node_id),
        hostname="test-node",
        address="127.0.0.1",
        status="healthy",
        system_info={},
        runtime_info={
            "available": True,
            "cpu_count": 4,
            "memory_bytes": 4 * 1024 * 1024 * 1024,
        },
    )
    register_node(node)

    workload.node_id = UUID(str(node_id))
    workload.actual_state = WorkloadState.RUNNING
    service.update_workload(workload)

    return WorkloadReconciler(service), workload


@patch(
    "cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule"
)
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_stopped_container_marks_workload_failed(mock_get, mock_schedule):
    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None

    def fail_recovery(workload_id):
        raise SchedulingError("Simulated recovery failure")

    mock_schedule.side_effect = fail_recovery

    failures = reconciler.reconcile()

    assert str(workload.workload_id) in failures
    mock_schedule.assert_called_once_with(workload.workload_id)
    stored_workload = reconciler.workload_service.get_workload(
          workload.workload_id
    )
    assert stored_workload is not None
    assert stored_workload.actual_state == WorkloadState.FAILED


@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_running_container_stays_running(mock_get):
    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "RUNNING"},
    )
    mock_get.return_value.raise_for_status.return_value = None

    failures = reconciler.reconcile()

    assert failures == []
    assert workload.actual_state == WorkloadState.RUNNING


@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_unreachable_node_does_not_mark_workload_failed(mock_get):
    reconciler, workload = setup_reconciler()

    mock_get.side_effect = httpx.ConnectError("Node unreachable")

    failures = reconciler.reconcile()

    assert failures == []
    assert workload.actual_state == WorkloadState.RUNNING

@patch(
    "cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule"
)
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_stopped_container_triggers_recovery(mock_get, mock_schedule):
    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None

    def recover(workload_id):
        workload.actual_state = WorkloadState.RUNNING
        return workload

    mock_schedule.side_effect = recover

    failures = reconciler.reconcile()

    assert str(workload.workload_id) in failures
    mock_schedule.assert_called_once_with(workload.workload_id)
    assert workload.actual_state == WorkloadState.RUNNING

@patch("cloudheal_control_plane.workloads.reconciler.get_node")
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_unhealthy_node_does_not_trigger_recovery(
    mock_get,
    mock_get_node,
):
    reconciler, workload = setup_reconciler()

    mock_get_node.return_value = NodeRecord(
        node_id=str(workload.node_id),
        hostname="test-node",
        address="127.0.0.1",
        status="unhealthy",
        runtime_info={"available": True},
    )

    failures = reconciler.reconcile()

    assert failures == []
    assert workload.actual_state == WorkloadState.RUNNING
    mock_get.assert_not_called()

@patch(
    "cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule"
)
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_stopped_container_records_failure_event(
    mock_get,
    mock_schedule,
):
    from cloudheal_control_plane.database import get_connection

    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None

    mock_schedule.return_value = workload

    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type, workload_id
            FROM events
            WHERE workload_id = ?
            ORDER BY event_id
            """,
            (str(workload.workload_id),),
        ).fetchall()

    event_types = [row["event_type"] for row in rows]

    assert "CONTAINER_FAILURE_DETECTED" in event_types

@patch(
    "cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule"
)
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_stopped_container_records_recovery_attempt(
    mock_get,
    mock_schedule,
):
    from cloudheal_control_plane.database import get_connection

    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None
    mock_schedule.return_value = workload

    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type
            FROM events
            WHERE workload_id = ?
            ORDER BY event_id
            """,
            (str(workload.workload_id),),
        ).fetchall()

    event_types = [row["event_type"] for row in rows]

    assert "CONTAINER_FAILURE_DETECTED" in event_types
    assert "RECOVERY_ATTEMPTED" in event_types

@patch(
    "cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule"
)
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_successful_recovery_records_success_event(
    mock_get,
    mock_schedule,
):
    from cloudheal_control_plane.database import get_connection
    from cloudheal_control_plane.workloads.models import WorkloadState

    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None

    def simulate_successful_recovery(workload_id):
        workload.actual_state = WorkloadState.RUNNING
        reconciler.workload_service.update_workload(workload)
        return workload

    mock_schedule.side_effect = simulate_successful_recovery

    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type
            FROM events
            WHERE workload_id = ?
            ORDER BY event_id
            """,
            (str(workload.workload_id),),
        ).fetchall()

    event_types = [row["event_type"] for row in rows]

    assert "CONTAINER_FAILURE_DETECTED" in event_types
    assert "RECOVERY_ATTEMPTED" in event_types
    assert "RECOVERY_SUCCEEDED" in event_types

@patch("cloudheal_control_plane.workloads.reconciler.WorkloadScheduler.schedule")
@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
def test_failed_recovery_records_failure_event(
    mock_get,
    mock_schedule,
):
    from cloudheal_control_plane.database import get_connection
    from cloudheal_control_plane.workloads.scheduler import SchedulingError

    reconciler, workload = setup_reconciler()

    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "STOPPED"},
    )
    mock_get.return_value.raise_for_status.return_value = None
    mock_schedule.side_effect = SchedulingError("No suitable node available")

    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type, details
            FROM events
            WHERE workload_id = ?
            ORDER BY event_id
            """,
            (str(workload.workload_id),),
        ).fetchall()

    event_types = [row["event_type"] for row in rows]

    assert "CONTAINER_FAILURE_DETECTED" in event_types
    assert "RECOVERY_ATTEMPTED" in event_types
    assert "RECOVERY_FAILED" in event_types
    assert "RECOVERY_SUCCEEDED" not in event_types

@patch("cloudheal_control_plane.workloads.reconciler.get_node")
def test_unhealthy_node_records_availability_event(mock_get_node):
    from cloudheal_control_plane.database import get_connection

    reconciler, workload = setup_reconciler()

    mock_get_node.return_value = NodeRecord(
        node_id=str(workload.node_id),
        hostname="test-node",
        address="127.0.0.1",
        status="unhealthy",
        runtime_info={"available": True},
    )

    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type
            FROM events
            WHERE workload_id = ?
              AND event_type = 'WORKLOAD_NODE_UNAVAILABLE'
            """,
            (str(workload.workload_id),),
        ).fetchall()

    assert len(rows) == 1
    assert workload.actual_state == WorkloadState.RUNNING

@patch("cloudheal_control_plane.workloads.reconciler.get_node")
def test_repeated_unhealthy_checks_do_not_duplicate_event(mock_get_node):
    from cloudheal_control_plane.database import get_connection

    reconciler, workload = setup_reconciler()

    unhealthy_node = NodeRecord(
        node_id=str(workload.node_id),
        hostname="test-node",
        address="127.0.0.1",
        status="unhealthy",
        runtime_info={"available": True},
    )

    mock_get_node.return_value = unhealthy_node

    reconciler.reconcile()
    reconciler.reconcile()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS event_count
            FROM events
            WHERE workload_id = ?
              AND event_type = 'WORKLOAD_NODE_UNAVAILABLE'
            """,
            (str(workload.workload_id),),
        ).fetchone()

    assert row["event_count"] == 1

@patch("cloudheal_control_plane.workloads.reconciler.httpx.get")
@patch("cloudheal_control_plane.workloads.reconciler.get_node")
def test_healthy_node_records_availability_recovery(
    mock_get_node,
    mock_http_get,
):
    from cloudheal_control_plane.database import get_connection

    reconciler, workload = setup_reconciler()

    node_data = {
        "node_id": str(workload.node_id),
        "hostname": "test-node",
        "address": "127.0.0.1",
        "runtime_info": {
            "available": True,
            "cpu_count": 4,
            "memory_bytes": 4 * 1024 * 1024 * 1024,
        },
    }

    mock_get_node.side_effect = [
        NodeRecord(**node_data, status="unhealthy"),
        NodeRecord(**node_data, status="healthy"),
    ]

    mock_http_get.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "RUNNING"},
    )
    mock_http_get.return_value.raise_for_status.return_value = None

    reconciler.reconcile()
    reconciler.reconcile()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT event_type
            FROM events
            WHERE workload_id = ?
              AND event_type IN (
                  'WORKLOAD_NODE_UNAVAILABLE',
                  'WORKLOAD_NODE_AVAILABLE'
              )
            ORDER BY event_id
            """,
            (str(workload.workload_id),),
        ).fetchall()

    assert [row["event_type"] for row in rows] == [
        "WORKLOAD_NODE_UNAVAILABLE",
        "WORKLOAD_NODE_AVAILABLE",
    ]
    assert workload.actual_state == WorkloadState.RUNNING
