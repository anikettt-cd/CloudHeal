from types import SimpleNamespace
from unittest.mock import patch

import pytest
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.infrastructure.kubernetes_deployments import (
    create_deployment as kd_create_deployment,
    delete_deployment as kd_delete_deployment,
    delete_service as kd_delete_service,
    ensure_namespace as kd_ensure_namespace,
)
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    DEFAULT_KUBECONFIG_PATH,
    _load_kubernetes_config,
    _resolve_kubeconfig_path,
    get_deployment_status,
)


def test_resolve_kubeconfig_defaults_to_cloudheal_file(monkeypatch):
    monkeypatch.delenv("KUBECONFIG", raising=False)

    assert _resolve_kubeconfig_path() == str(DEFAULT_KUBECONFIG_PATH)


def test_resolve_kubeconfig_honors_single_path(monkeypatch):
    monkeypatch.setenv("KUBECONFIG", "/tmp/cloudheal-kubeconfig")

    assert _resolve_kubeconfig_path() == "/tmp/cloudheal-kubeconfig"


def test_resolve_kubeconfig_preserves_multi_path_value(monkeypatch):
    monkeypatch.setenv("KUBECONFIG", "/tmp/first:/tmp/second")

    assert _resolve_kubeconfig_path() == "/tmp/first:/tmp/second"


@patch("cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config")
def test_load_kubernetes_config_does_not_persist(mock_load_kube_config, monkeypatch):
    monkeypatch.setenv("KUBECONFIG", "/tmp/cloudheal-kubeconfig")

    _load_kubernetes_config()

    mock_load_kube_config.assert_called_once_with(
        config_file="/tmp/cloudheal-kubeconfig",
        persist_config=False,
    )


@patch("cloudheal_control_plane.infrastructure.kubernetes_adapter.config.load_kube_config")
def test_load_kubernetes_config_propagates_invalid_config(mock_load_kube_config, monkeypatch):
    from kubernetes import config

    monkeypatch.delenv("KUBECONFIG", raising=False)
    mock_load_kube_config.side_effect = config.ConfigException("bad kubeconfig")

    with pytest.raises(config.ConfigException):
        _load_kubernetes_config()


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_calls_kubernetes_api(mock_load, mock_apps, mock_core):
    mock_core.return_value.read_namespaced_service.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )

    result = kd_delete_deployment(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "deleted": True,
    }
    mock_apps.return_value.delete_namespaced_deployment.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )
    mock_core.return_value.read_namespaced_service.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_missing_deployment(mock_load, mock_apps):
    mock_apps.return_value.delete_namespaced_deployment.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )

    with pytest.raises(ApiException) as exc_info:
        kd_delete_deployment(namespace="cloudheal-test", name="missing")

    assert exc_info.value.status == 404


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_api_error(mock_load, mock_apps):
    mock_apps.return_value.delete_namespaced_deployment.side_effect = ApiException(
        status=500,
        reason="Internal Server Error",
    )

    with pytest.raises(ApiException) as exc_info:
        kd_delete_deployment(namespace="cloudheal-test", name="demo-web")

    assert exc_info.value.status == 500


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_deletes_owned_service(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels={"cloudheal.io/managed-by": "cloudheal"},
            annotations={"cloudheal.io/managed-by": "cloudheal"},
        )
    )

    result = kd_delete_service(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "service": "demo-web",
        "deleted": True,
    }
    mock_core.return_value.delete_namespaced_service.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )



@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_missing_service_is_idempotent(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )

    result = kd_delete_service(namespace="cloudheal-test", name="missing")

    assert result == {
        "namespace": "cloudheal-test",
        "service": "missing",
        "deleted": True,
    }
    mock_core.return_value.delete_namespaced_service.assert_not_called()



@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_propagates_unexpected_delete_failure(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels={"cloudheal.io/managed-by": "cloudheal"},
            annotations=None,
        )
    )
    mock_core.return_value.delete_namespaced_service.side_effect = ApiException(
        status=500,
        reason="Internal Server Error",
    )

    with pytest.raises(ApiException) as exc_info:
        kd_delete_service(namespace="cloudheal-test", name="demo-web")

    assert exc_info.value.status == 500



@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_does_not_trust_alternative_marker(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels=None,
            annotations={"cloudheal.io/managed-by": "cloudheal"},
        )
    )

    result = kd_delete_service(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "service": "demo-web",
        "deleted": False,
        "reason": "not_owned",
    }
    mock_core.return_value.delete_namespaced_service.assert_not_called()


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_does_not_trust_owner_reference(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels=None,
            annotations=None,
            ownerReferences=[
                SimpleNamespace(kind="Deployment", name="demo-web")
            ],
        )
    )

    result = kd_delete_service(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "service": "demo-web",
        "deleted": False,
        "reason": "not_owned",
    }
    mock_core.return_value.delete_namespaced_service.assert_not_called()




@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_service_helper_protects_unowned_service(mock_load, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(labels={"app": "demo-web"}, annotations=None)
    )

    result = kd_delete_service(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "service": "demo-web",
        "deleted": False,
        "reason": "not_owned",
    }
    mock_core.return_value.delete_namespaced_service.assert_not_called()





@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_cleans_up_owned_service(mock_load, mock_apps, mock_core):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels={"cloudheal.io/managed-by": "cloudheal"},
            annotations=None,
        )
    )

    result = kd_delete_deployment(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "deleted": True,
    }
    mock_apps.return_value.delete_namespaced_deployment.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )
    mock_core.return_value.delete_namespaced_service.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )



@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_propagates_service_deletion_failure(

    mock_load, mock_apps, mock_core
):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(
            labels={"cloudheal.io/managed-by": "cloudheal"},
            annotations=None,
        )
    )
    mock_core.return_value.delete_namespaced_service.side_effect = ApiException(
        status=500,
        reason="Internal Server Error",
    )

    with pytest.raises(ApiException) as exc_info:
        kd_delete_deployment(namespace="cloudheal-test", name="demo-web")

    assert exc_info.value.status == 500
    mock_apps.return_value.delete_namespaced_deployment.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )
    mock_core.return_value.delete_namespaced_service.assert_called_once_with(
        name="demo-web",
        namespace="cloudheal-test",
    )


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_delete_deployment_helper_protects_unowned_service(
    mock_load, mock_apps, mock_core
):
    mock_core.return_value.read_namespaced_service.return_value = SimpleNamespace(
        metadata=SimpleNamespace(labels={"app": "demo-web"}, annotations=None)
    )

    result = kd_delete_deployment(namespace="cloudheal-test", name="demo-web")

    assert result == {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "deleted": True,
    }
    mock_core.return_value.delete_namespaced_service.assert_not_called()


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_ensure_namespace_handles_creation_race(mock_load, mock_core):
    mock_core.return_value.read_namespace.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )
    mock_core.return_value.create_namespace.side_effect = ApiException(
        status=409,
        reason="Conflict",
    )

    result = kd_ensure_namespace("cloudheal-test")

    assert result == {"namespace": "cloudheal-test", "created": False}


@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_deployments._load_kubernetes_config")
def test_ensure_namespace_propagates_unexpected_create_error(mock_load, mock_core):
    mock_core.return_value.read_namespace.side_effect = ApiException(
        status=404,
        reason="Not Found",
    )
    mock_core.return_value.create_namespace.side_effect = ApiException(
        status=500,
        reason="Internal Server Error",
    )

    with pytest.raises(ApiException) as exc_info:
        kd_ensure_namespace("cloudheal-test")

    assert exc_info.value.status == 500


def test_kubernetes_name_validation_rejects_invalid_values():
    from cloudheal_control_plane.infrastructure.kubernetes_deployments import _name

    with pytest.raises(ValueError):
        _name("Invalid Name", "name")
    with pytest.raises(ValueError):
        _name("", "name")
    with pytest.raises(ValueError):
        _name("a" * 254, "name")
    with pytest.raises(ValueError):
        _name("bad_namespace", "namespace", namespace=True)

    assert _name("  demo-web  ", "name") == "demo-web"
    assert _name("cloudheal-test", "namespace", namespace=True) == "cloudheal-test"


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

    mock_config.assert_called_once()
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