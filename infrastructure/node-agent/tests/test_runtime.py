import json
import subprocess
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

from cloudheal_node_agent.runtime import (
    ContainerExecutionError,
    get_container_status,
    run_container,
)


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_run_container_success(mock_run):
    workload_id = uuid4()
    container_id = "abc123"

    mock_run.side_effect = [
        MagicMock(returncode=1, stdout="", stderr="not found"),
        MagicMock(returncode=0, stdout=f"{container_id}\n", stderr=""),
        MagicMock(
            returncode=0,
            stdout=json.dumps(
                [{"Id": container_id, "State": {"Running": True}}]
            ),
            stderr="",
        ),
    ]

    result = run_container(
        workload_id=workload_id,
        image="nginx:latest",
        cpu_limit=1.0,
        memory_limit_mb=256,
    )

    assert result["workload_id"] == str(workload_id)
    assert result["container_id"] == container_id
    assert result["status"] == "RUNNING"
    assert mock_run.call_count == 3


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_run_container_already_running(mock_run):
    workload_id = uuid4()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(
            [{"Id": "existing123", "State": {"Running": True}}]
        ),
        stderr="",
    )

    result = run_container(
        workload_id=workload_id,
        image="nginx:latest",
        cpu_limit=1.0,
        memory_limit_mb=256,
    )

    assert result["status"] == "RUNNING"
    assert result["container_id"] == "existing123"
    assert mock_run.call_count == 2


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_run_container_existing_but_stopped(mock_run):
    workload_id = uuid4()

    mock_run.side_effect = [
        # First inspect: container exists but is stopped.
        MagicMock(
            returncode=0,
            stdout=json.dumps(
                [{
                    "Id": "existing123",
                    "State": {"Running": False},
                }]
            ),
            stderr="",
        ),
        # docker start succeeds.
        MagicMock(
            returncode=0,
            stdout="existing123\n",
            stderr="",
        ),
        # Second inspect: container is now running.
        MagicMock(
            returncode=0,
            stdout=json.dumps(
                [{
                    "Id": "existing123",
                    "State": {"Running": True},
                }]
            ),
            stderr="",
        ),
    ]

    result = run_container(
        workload_id=workload_id,
        image="nginx:latest",
        cpu_limit=1.0,
        memory_limit_mb=256,
    )

    assert result["status"] == "RUNNING"
    assert result["container_id"] == "existing123"
    assert mock_run.call_count == 3

    # Verify the stopped container was restarted.
    assert mock_run.call_args_list[1].args[0] == [
        "docker", "start", f"cloudheal-{workload_id}"
    ]


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_run_container_docker_failure(mock_run):
    workload_id = uuid4()

    mock_run.side_effect = [
        MagicMock(returncode=1, stdout="", stderr="not found"),
        MagicMock(
            returncode=1,
            stdout="",
            stderr="image pull failed",
        ),
    ]

    with pytest.raises(ContainerExecutionError, match="image pull failed"):
        run_container(
            workload_id=workload_id,
            image="invalid-image",
            cpu_limit=1.0,
            memory_limit_mb=256,
        )


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_get_container_status_running(mock_run):
    workload_id = uuid4()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(
            [{"Id": "abc123", "State": {"Running": True, "Status": "running"}}]
        ),
        stderr="",
    )

    result = get_container_status(workload_id)

    assert result["status"] == "RUNNING"
    assert result["container_id"] == "abc123"


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_get_container_status_stopped(mock_run):
    workload_id = uuid4()

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(
            [{"Id": "abc123", "State": {"Running": False, "Status": "exited"}}]
        ),
        stderr="",
    )

    result = get_container_status(workload_id)

    assert result["status"] == "STOPPED"


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_get_container_status_not_found(mock_run):
    workload_id = uuid4()

    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr="No such container",
    )

    result = get_container_status(workload_id)

    assert result["status"] == "NOT_FOUND"
    assert result["workload_id"] == str(workload_id)


@patch("cloudheal_node_agent.runtime.subprocess.run")
def test_run_container_timeout(mock_run):
    workload_id = uuid4()

    mock_run.side_effect = [
        MagicMock(returncode=1, stdout="", stderr="not found"),
        subprocess.TimeoutExpired(cmd="docker run", timeout=300),
    ]

    with pytest.raises(ContainerExecutionError, match="timed out"):
        run_container(
            workload_id=workload_id,
            image="nginx:latest",
            cpu_limit=1.0,
            memory_limit_mb=256,
        )
