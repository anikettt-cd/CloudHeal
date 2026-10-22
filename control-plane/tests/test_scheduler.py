from unittest.mock import Mock, patch
from uuid import uuid4 , UUID
import httpx
import pytest
from cloudheal_control_plane.database import get_connection
from cloudheal_control_plane.registry import NodeRecord
from cloudheal_control_plane.workloads.models import (
    WorkloadCreate,
    WorkloadState,
)
from cloudheal_control_plane.workloads.registry import WorkloadRegistry
from cloudheal_control_plane.workloads.scheduler import (
    SchedulingError,
    WorkloadScheduler,
)
from cloudheal_control_plane.workloads.service import WorkloadService
from cloudheal_control_plane.workloads.scheduler import (
    ExecutionError,
    SchedulingError,
)


@pytest.fixture
def setup_scheduler():
    registry = WorkloadRegistry()
    service = WorkloadService(registry)
    scheduler = WorkloadScheduler(service)

    workload = service.create_workload(
        WorkloadCreate(
            name="test-workload",
            image="nginx:latest",
            cpu_limit=1.0,
            memory_limit_mb=256,
        )
    )

    node = NodeRecord(
        node_id=str(uuid4()),
        hostname="test-node",
        address="127.0.0.1",
        status="healthy",
        system_info={},
        runtime_info={
            "available": True,
            "cpu_count": 2,
            "memory_bytes": 2 * 1024**3,
        },
    )

    return scheduler, workload, node


@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_sufficient_resources_schedule_success(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    mock_get_nodes.return_value = [node]
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "RUNNING"},
    )
    mock_post.return_value.raise_for_status.return_value = None

    result = scheduler.schedule(workload.workload_id)

    assert result.actual_state == WorkloadState.RUNNING
    assert result.node_id is not None


@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_insufficient_cpu_rejected(
    mock_get_nodes, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    node.runtime_info["cpu_count"] = 0.5
    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    assert workload.actual_state == WorkloadState.PENDING


@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_insufficient_memory_rejected(
    mock_get_nodes, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    node.runtime_info["memory_bytes"] = 128 * 1024**2
    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    assert workload.actual_state == WorkloadState.PENDING


@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_unavailable_docker_rejected(
    mock_get_nodes, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    node.runtime_info["available"] = False
    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    assert workload.actual_state == WorkloadState.PENDING


@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_unhealthy_node_rejected(
    mock_get_nodes, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    node.status = "unhealthy"
    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    assert workload.actual_state == WorkloadState.PENDING

@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_execution_failure_marks_workload_failed(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler
    mock_get_nodes.return_value = [node]

    mock_post.side_effect = httpx.HTTPStatusError(
        "Container execution failed",
        request=Mock(),
        response=Mock(status_code=409),
    )
    with pytest.raises(ExecutionError, match="execution request failed"):
        scheduler.schedule(workload.workload_id)
    stored_workload = scheduler.workload_service.get_workload(
        workload.workload_id
    )
    assert stored_workload is not None
    assert stored_workload.actual_state == WorkloadState.FAILED
    assert stored_workload.node_id is not None


@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_running_workloads_consume_node_capacity(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    # Node has 2 CPUs and 2 GiB memory.
    # An existing workload consumes 1.5 CPUs.
    existing_workload = scheduler.workload_service.create_workload(
        WorkloadCreate(
            name="existing-workload",
            image="nginx:latest",
            cpu_limit=1.5,
            memory_limit_mb=256,
        )
    )
    existing_workload.node_id = UUID(str(node.node_id))
    existing_workload.actual_state = WorkloadState.RUNNING
    scheduler.workload_service.update_workload(existing_workload)

    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    mock_post.assert_not_called()
    assert workload.actual_state == WorkloadState.PENDING

@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_node_agent_unreachable_marks_workload_failed(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler
    mock_get_nodes.return_value = [node]
    mock_post.side_effect = httpx.ConnectError("Node unreachable")

    with pytest.raises(ExecutionError, match="execution request failed"):
        scheduler.schedule(workload.workload_id)
    stored_workload = scheduler.workload_service.get_workload(
        workload.workload_id
    )
    assert stored_workload is not None
    assert stored_workload.actual_state == WorkloadState.FAILED
    assert stored_workload.node_id is not None



@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_invalid_json_response_marks_workload_failed(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler
    mock_get_nodes.return_value = [node]

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = mock_response
    with pytest.raises(ExecutionError, match="returned invalid JSON"):
        scheduler.schedule(workload.workload_id)
    stored_workload = scheduler.workload_service.get_workload(
        workload.workload_id
    )
    assert stored_workload is not None
    assert stored_workload.actual_state == WorkloadState.FAILED



@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_missing_status_marks_workload_failed(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler
    mock_get_nodes.return_value = [node]

    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"workload_id": str(workload.workload_id)},
    )
    mock_post.return_value.raise_for_status.return_value = None
    with pytest.raises(SchedulingError, match="did not confirm"):
        scheduler.schedule(workload.workload_id)
    stored_workload = scheduler.workload_service.get_workload(
        workload.workload_id
    )
    assert stored_workload is not None
    assert stored_workload.actual_state == WorkloadState.FAILED


@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_scheduler_selects_node_with_best_remaining_capacity(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node_a = setup_scheduler

    node_b = NodeRecord(
        node_id=str(uuid4()),
        hostname="better-node",
        address="127.0.0.2",
        status="healthy",
        runtime_info={
            "available": True,
            "cpu_count": 8,
            "memory_bytes": 8 * 1024**3,
        },
    )

    # Node A: 2 CPUs, 2 GiB memory.
    # Node B: 8 CPUs, 8 GiB memory.
    mock_get_nodes.return_value = [node_a, node_b]

    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"status": "RUNNING"},
    )
    mock_post.return_value.raise_for_status.return_value = None
    print("Node A:", node_a.node_id, node_a.runtime_info)
    print("Node B:", node_b.node_id, node_b.runtime_info)
    print("Active workloads:", scheduler.workload_service.list_workloads())

    result = scheduler.schedule(workload.workload_id)

    assert result.actual_state == WorkloadState.RUNNING
    assert result.node_id == UUID(node_b.node_id)


@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_scheduled_workloads_consume_node_capacity(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler

    existing_workload = scheduler.workload_service.create_workload(
        WorkloadCreate(
            name="scheduled-workload",
            image="nginx:latest",
            cpu_limit=1.5,
            memory_limit_mb=256,
        )
    )

    existing_workload.node_id = UUID(node.node_id)
    existing_workload.actual_state = WorkloadState.SCHEDULED
    scheduler.workload_service.update_workload(existing_workload)

    mock_get_nodes.return_value = [node]

    with pytest.raises(SchedulingError, match="No healthy Docker nodes"):
        scheduler.schedule(workload.workload_id)

    mock_post.assert_not_called()
    assert workload.actual_state == WorkloadState.PENDING

@patch("cloudheal_control_plane.workloads.scheduler.httpx.post")
@patch("cloudheal_control_plane.workloads.scheduler.get_nodes")
def test_missing_status_records_execution_failure(
    mock_get_nodes, mock_post, setup_scheduler
):
    scheduler, workload, node = setup_scheduler
    mock_get_nodes.return_value = [node]

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "workload_id": str(workload.workload_id)
    }
    mock_post.return_value = mock_response

    with pytest.raises(SchedulingError, match="did not confirm"):
        scheduler.schedule(workload.workload_id)

    with get_connection() as connection:
        event = connection.execute(
            """
            SELECT event_type, workload_id
            FROM events
            WHERE workload_id = ?
              AND event_type = 'EXECUTION_FAILED'
            """,
            (str(workload.workload_id),),
        ).fetchone()

    assert event is not None
    assert event["workload_id"] == str(workload.workload_id)    
    