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
