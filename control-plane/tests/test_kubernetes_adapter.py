from types import SimpleNamespace
from unittest.mock import patch

import pytest
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)


def make_container_status(
    name="nginx",
    ready=True,
    restart_count=0,
    state="running",
):
    container_state = SimpleNamespace(
        running=object() if state == "running" else None,
        waiting=object() if state == "waiting" else None,
        terminated=object() if state == "terminated" else None,
    )

    return SimpleNamespace(
        name=name,
        ready=ready,
        restart_count=restart_count,
        state=container_state,
    )


def make_pod(
    name="nginx-pod",
    phase="Running",
    ready=True,
    restart_count=0,
):
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name),
        spec=SimpleNamespace(node_name="test-node"),
        status=SimpleNamespace(
            phase=phase,
            pod_ip="10.244.0.5",
            container_statuses=[
                make_container_status(
                    ready=ready,
                    restart_count=restart_count,
                )
            ],
        ),
    )


def make_deployment():
    return SimpleNamespace(
        spec=SimpleNamespace(
            replicas=1,
            selector=SimpleNamespace(
                match_labels={"app": "nginx"},
            ),
        ),
        status=SimpleNamespace(
            ready_replicas=1,
            available_replicas=1,
            conditions=[
                SimpleNamespace(
                    type="Available",
                    status="True",
                    reason="MinimumReplicasAvailable",
                    message="Deployment is available",
                )
            ],
        ),
    )


@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.CoreV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.AppsV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config"
)
def test_healthy_deployment(mock_config, mock_apps, mock_core):
    mock_apps.return_value.read_namespaced_deployment.return_value = (
        make_deployment()
    )
    mock_core.return_value.list_namespaced_pod.return_value = SimpleNamespace(
        items=[make_pod()]
    )

    result = get_deployment_status(
        namespace="cloudheal-test",
        name="nginx-test",
    )

    assert result["namespace"] == "cloudheal-test"
    assert result["deployment"] == "nginx-test"
    assert result["desired_replicas"] == 1
    assert result["ready_replicas"] == 1
    assert result["available_replicas"] == 1
    assert result["pods"][0]["ready"] is True
    assert result["pods"][0]["containers"][0]["state"] == "running"

    mock_config.assert_called_once_with()
    mock_apps.return_value.read_namespaced_deployment.assert_called_once_with(
        name="nginx-test",
        namespace="cloudheal-test",
    )


@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.CoreV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.AppsV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config"
)
def test_unready_pod_reports_restart_count(mock_config, mock_apps, mock_core):
    mock_apps.return_value.read_namespaced_deployment.return_value = (
        make_deployment()
    )
    mock_core.return_value.list_namespaced_pod.return_value = SimpleNamespace(
        items=[
            make_pod(
                phase="Running",
                ready=False,
                restart_count=3,
            )
        ]
    )

    result = get_deployment_status(
        namespace="cloudheal-test",
        name="nginx-test",
    )

    pod = result["pods"][0]

    assert pod["phase"] == "Running"
    assert pod["ready"] is False
    assert pod["containers"][0]["ready"] is False
    assert pod["containers"][0]["restart_count"] == 3


@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.CoreV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.AppsV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config"
)
def test_deployment_without_pods(mock_config, mock_apps, mock_core):
    mock_apps.return_value.read_namespaced_deployment.return_value = (
        make_deployment()
    )
    mock_core.return_value.list_namespaced_pod.return_value = SimpleNamespace(
        items=[]
    )

    result = get_deployment_status(
        namespace="cloudheal-test",
        name="nginx-test",
    )

    assert result["desired_replicas"] == 1
    assert result["pods"] == []


@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.AppsV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config"
)
def test_missing_deployment_raises_api_exception(mock_config, mock_apps):
    mock_apps.return_value.read_namespaced_deployment.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )

    with pytest.raises(ApiException) as exc_info:
        get_deployment_status(
            namespace="cloudheal-test",
            name="missing-deployment",
        )

    assert exc_info.value.status == 404


@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.client.AppsV1Api"
)
@patch(
    "cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config"
)
def test_kubernetes_api_failure_is_propagated(mock_config, mock_apps):
    mock_apps.return_value.read_namespaced_deployment.side_effect = ApiException(
        status=500,
        reason="Internal Server Error",
    )

    with pytest.raises(ApiException) as exc_info:
        get_deployment_status(
            namespace="cloudheal-test",
            name="nginx-test",
        )

    assert exc_info.value.status == 500