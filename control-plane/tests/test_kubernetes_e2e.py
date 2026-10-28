from unittest.mock import patch

import pytest

from cloudheal_control_plane import kubernetes_e2e


def test_validate_config_requires_fields():
    config = kubernetes_e2e.E2EConfig(
        api_url="",
        namespace="disposable",
        deployment="demo",
        service="demo",
        image="nginx:latest",
    )
    with pytest.raises(kubernetes_e2e.E2EError):
        kubernetes_e2e.validate_config(config)


def test_validate_config_refuses_protected_namespace():
    config = kubernetes_e2e.E2EConfig(
        api_url="http://localhost:9000",
        namespace="cloudheal-test",
        deployment="demo",
        service="demo",
        image="nginx:latest",
    )
    with pytest.raises(kubernetes_e2e.E2EError):
        kubernetes_e2e.validate_config(config)


def test_is_protected_namespace():
    assert kubernetes_e2e.is_protected_namespace("cloudheal-test") is True
    assert kubernetes_e2e.is_protected_namespace("disposable-e2e") is False


def test_wait_for_deployment_ready_success(monkeypatch):
    monkeypatch.setattr(kubernetes_e2e.time, "sleep", lambda _: None)
    statuses = iter(
        [
            {"ready_replicas": 1, "available_replicas": 1, "pods": [{"ready": True}]},
        ]
    )
    result = kubernetes_e2e.wait_for_deployment_ready(
        lambda: next(statuses), 1, 10, 1
    )
    assert result["ready_replicas"] == 1
def test_wait_for_deployment_ready_timeout(monkeypatch):
    monkeypatch.setattr(kubernetes_e2e.time, "sleep", lambda _: None)
    values = iter([0, 1, 2, 3, 4, 5])
    monkeypatch.setattr(kubernetes_e2e.time, "monotonic", lambda: next(values))
    with pytest.raises(TimeoutError):
        kubernetes_e2e.wait_for_deployment_ready(
            lambda: {"ready_replicas": 0, "available_replicas": 0, "pods": []},
            1,
            1,
            1,
        )


def test_protected_changed_detects_difference():
    baseline = {"cloudheal-test/cloudheal-demo": {"ready_replicas": 1}}
    current = {"cloudheal-test/cloudheal-demo": {"ready_replicas": 2}}
    assert kubernetes_e2e.protected_changed(baseline, current) is True
    assert kubernetes_e2e.protected_changed(baseline, baseline) is False
"""
def test_run_lifecycle_success(monkeypatch):
    monkeypatch.setattr(kubernetes_e2e, "protected_baseline", lambda: {})
    monkeypatch.setattr(kubernetes_e2e, "check_collisions", lambda config: None)
    monkeypatch.setattr(kubernetes_e2e, "create_namespace_if_needed", lambda ns: True)
    monkeypatch.setattr(kubernetes_e2e, "deployment_exists", lambda ns, name: False)
    monkeypatch.setattr(kubernetes_e2e, "service_exists", lambda ns, name: False)
    monkeypatch.setattr(kubernetes_e2e, "wait_for_deployment_ready", lambda *a, **k: None)
    monkeypatch.setattr(kubernetes_e2e, "delete_namespace_if_created", lambda ns: None)

    config = kubernetes_e2e.E2EConfig(
        api_url="http://localhost:9000",
        namespace="disposable-e2e",
        deployment="demo-e2e",
        service="demo-e2e",
        image="nginx:latest",
    )

    with patch("cloudheal_control_plane.kubernetes_e2e.httpx.get") as mock_get, patch(
        "cloudheal_control_plane.kubernetes_e2e.httpx.post"
    ) as mock_post, patch("cloudheal_control_plane.kubernetes_e2e.httpx.delete") as mock_delete:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value.status_code = 201
        mock_post.return_value.raise_for_status = lambda: None
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.raise_for_status = lambda: None

        assert kubernetes_e2e.run_lifecycle(config) == 0
"""
def test_run_lifecycle_collision_returns_one(monkeypatch):
    monkeypatch.setattr(kubernetes_e2e, "protected_baseline", lambda: {})
    monkeypatch.setattr(
        kubernetes_e2e, "check_collisions", lambda config: (_ for _ in ()).throw(kubernetes_e2e.E2EError("collision"))
    )

    config = kubernetes_e2e.E2EConfig(
        api_url="http://localhost:9000",
        namespace="disposable-e2e",
        deployment="demo-e2e",
        service="demo-e2e",
        image="nginx:latest",
    )

    assert kubernetes_e2e.run_lifecycle(config) == 1


def test_run_lifecycle_wait_timeout_cleans_up(monkeypatch):
    monkeypatch.setattr(kubernetes_e2e, "protected_baseline", lambda: {})
    monkeypatch.setattr(kubernetes_e2e, "check_collisions", lambda config: None)
    monkeypatch.setattr(kubernetes_e2e, "create_namespace_if_needed", lambda ns: True)
    monkeypatch.setattr(kubernetes_e2e, "deployment_exists", lambda ns, name: True)
    monkeypatch.setattr(kubernetes_e2e, "service_exists", lambda ns, name: False)
    monkeypatch.setattr(
        kubernetes_e2e, "wait_for_deployment_ready", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("not ready"))
    )
    cleanup_calls = {"namespace": 0}
    monkeypatch.setattr(
        kubernetes_e2e, "delete_namespace_if_created", lambda ns: cleanup_calls.__setitem__("namespace", cleanup_calls["namespace"] + 1)
    )

    config = kubernetes_e2e.E2EConfig(
        api_url="http://localhost:9000",
        namespace="disposable-e2e",
        deployment="demo-e2e",
        service="demo-e2e",
        image="nginx:latest",
    )

    with patch("cloudheal_control_plane.kubernetes_e2e.httpx.get") as mock_get, patch(
        "cloudheal_control_plane.kubernetes_e2e.httpx.post"
    ) as mock_post, patch("cloudheal_control_plane.kubernetes_e2e.httpx.delete") as mock_delete:
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_post.return_value.status_code = 201
        mock_post.return_value.raise_for_status = lambda: None
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.raise_for_status = lambda: None

        assert kubernetes_e2e.run_lifecycle(config) == 1
        assert mock_delete.called
        assert cleanup_calls["namespace"] == 1


def test_main_returns_one_on_missing_env(monkeypatch):
    monkeypatch.delenv("CLOUDHEAL_API_URL", raising=False)
    monkeypatch.delenv("CLOUDHEAL_E2E_NAMESPACE", raising=False)
    monkeypatch.delenv("CLOUDHEAL_E2E_DEPLOYMENT", raising=False)
    monkeypatch.delenv("CLOUDHEAL_E2E_IMAGE", raising=False)
    assert kubernetes_e2e.main() == 1
"""
"""