from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from kubernetes import config
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.api import app


def test_kubernetes_deployment_endpoint_returns_status():
    expected = {
        "namespace": "cloudheal-test",
        "deployment": "nginx-test",
        "desired_replicas": 1,
        "ready_replicas": 1,
        "available_replicas": 1,
        "conditions": [],
        "pods": [],
    }

    with patch(
        "cloudheal_control_plane.api.get_deployment_status",
        return_value=expected,
    ) as mock_get_status:
        with TestClient(app) as client:
            response = client.get(
                "/infrastructure/kubernetes/namespaces/"
                "cloudheal-test/deployments/nginx-test"
            )

    assert response.status_code == 200
    assert response.json() == expected

    mock_get_status.assert_called_once_with(
        namespace="cloudheal-test",
        name="nginx-test",
    )


def test_missing_deployment_returns_404():
    with patch(
        "cloudheal_control_plane.api.get_deployment_status",
        side_effect=ApiException(status=404, reason="Not Found"),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/infrastructure/kubernetes/namespaces/"
                "cloudheal-test/deployments/missing"
            )

    assert response.status_code == 404
    assert response.json()["detail"] == "Kubernetes Deployment not found"


def test_kubernetes_api_failure_returns_502():
    with patch(
        "cloudheal_control_plane.api.get_deployment_status",
        side_effect=ApiException(
            status=500,
            reason="Internal Server Error",
        ),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/infrastructure/kubernetes/namespaces/"
                "cloudheal-test/deployments/nginx-test"
            )

    assert response.status_code == 502
    assert response.json()["detail"] == "Kubernetes API request failed"


def test_missing_kubernetes_configuration_returns_503():
    with patch(
        "cloudheal_control_plane.api.get_deployment_status",
        side_effect=config.ConfigException("Kubeconfig unavailable"),
    ):
        with TestClient(app) as client:
            response = client.get(
                "/infrastructure/kubernetes/namespaces/"
                "cloudheal-test/deployments/nginx-test"
            )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Kubernetes configuration is unavailable"
    )

def test_create_kubernetes_deployment_endpoint():
    deployment = {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "image": "nginx:latest",
        "replicas": 1,
        "container_port": 80,
        "created": True,
    }
    service = {
        "namespace": "cloudheal-test",
        "service": "demo-web",
        "type": "NodePort",
        "port": 80,
        "target_port": 80,
        "node_port": 30080,
        "created": True,
    }

    with patch("cloudheal_control_plane.api.ensure_k8s_namespace") as mock_namespace, patch(
        "cloudheal_control_plane.api.create_k8s_deployment", return_value=deployment
    ) as mock_deployment, patch(
        "cloudheal_control_plane.api.create_k8s_service", return_value=service
    ) as mock_service:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 201
    assert response.json() == {"deployment": deployment, "service": service}
    mock_namespace.assert_called_once_with("cloudheal-test")
    mock_deployment.assert_called_once_with(
        namespace="cloudheal-test",
        name="demo-web",
        image="nginx:latest",
        replicas=1,
        container_port=80,
    )
    mock_service.assert_called_once_with(
        namespace="cloudheal-test",
        name="demo-web",
        selector={"app": "demo-web"},
        port=80,
        target_port=80,
        service_type="NodePort",
    )


def test_scale_kubernetes_deployment_endpoint():
    result = {"namespace": "cloudheal-test", "deployment": "demo-web", "replicas": 3, "accepted": True}

    with patch("cloudheal_control_plane.api.scale_k8s_deployment", return_value=result) as mock_scale:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments/demo-web/scale",
                json={"replicas": 3},
            )

    assert response.status_code == 200
    assert response.json() == result
    mock_scale.assert_called_once_with(
        namespace="cloudheal-test",
        name="demo-web",
        replicas=3,
    )


def test_delete_kubernetes_deployment_endpoint():
    result = {"namespace": "cloudheal-test", "deployment": "demo-web", "deleted": True}

    with patch("cloudheal_control_plane.api.delete_k8s_deployment", return_value=result) as mock_delete:
        with TestClient(app) as client:
            response = client.delete(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments/demo-web"
            )

    assert response.status_code == 200
    assert response.json() == result
    mock_delete.assert_called_once_with(namespace="cloudheal-test", name="demo-web")


def test_create_kubernetes_deployment_service_failure_cleans_up():
    deployment = {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "image": "nginx:latest",
        "replicas": 1,
        "container_port": 80,
        "created": True,
    }

    with patch("cloudheal_control_plane.api.ensure_k8s_namespace"), patch(
        "cloudheal_control_plane.api.create_k8s_deployment", return_value=deployment
    ), patch(
        "cloudheal_control_plane.api.create_k8s_service",
        side_effect=ApiException(status=500, reason="Internal Server Error"),
    ), patch("cloudheal_control_plane.api.delete_k8s_deployment") as mock_delete:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 502
    mock_delete.assert_called_once_with(namespace="cloudheal-test", name="demo-web")


def test_create_kubernetes_deployment_service_failure_cleanup_error_preserves_original():
    deployment = {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "image": "nginx:latest",
        "replicas": 1,
        "container_port": 80,
        "created": True,
    }

    with patch("cloudheal_control_plane.api.ensure_k8s_namespace"), patch(
        "cloudheal_control_plane.api.create_k8s_deployment", return_value=deployment
    ), patch(
        "cloudheal_control_plane.api.create_k8s_service",
        side_effect=ApiException(status=500, reason="Internal Server Error"),
    ), patch(
        "cloudheal_control_plane.api.delete_k8s_deployment",
        side_effect=RuntimeError("cleanup failed"),
    ) as mock_delete:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 502
    mock_delete.assert_called_once_with(namespace="cloudheal-test", name="demo-web")


def test_create_kubernetes_deployment_existing_deployment_conflict_does_not_cleanup():
    with patch("cloudheal_control_plane.api.ensure_k8s_namespace"), patch(
        "cloudheal_control_plane.api.create_k8s_deployment",
        side_effect=ApiException(status=409, reason="Conflict"),
    ), patch("cloudheal_control_plane.api.delete_k8s_deployment") as mock_delete:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 409
    mock_delete.assert_not_called()


def test_create_kubernetes_deployment_existing_service_conflict_cleans_up():
    deployment = {
        "namespace": "cloudheal-test",
        "deployment": "demo-web",
        "image": "nginx:latest",
        "replicas": 1,
        "container_port": 80,
        "created": True,
    }

    with patch("cloudheal_control_plane.api.ensure_k8s_namespace"), patch(
        "cloudheal_control_plane.api.create_k8s_deployment", return_value=deployment
    ), patch(
        "cloudheal_control_plane.api.create_k8s_service",
        side_effect=ApiException(status=409, reason="Conflict"),
    ), patch("cloudheal_control_plane.api.delete_k8s_deployment") as mock_delete:
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 409
def test_create_kubernetes_deployment_validation_error():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": ""},
        )

    assert response.status_code == 422


def test_create_kubernetes_deployment_invalid_name_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "Invalid Name", "image": "nginx:latest"},
        )

    assert response.status_code == 422


def test_create_kubernetes_deployment_whitespace_image_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "   "},
        )

    assert response.status_code == 422


def test_create_kubernetes_deployment_invalid_replicas_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "nginx:latest", "replicas": 0},
        )

    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "nginx:latest", "replicas": 21},
        )

    assert response.status_code == 422


def test_create_kubernetes_deployment_invalid_ports_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "nginx:latest", "container_port": 0},
        )

    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "nginx:latest", "service_port": 70000},
        )

    assert response.status_code == 422


def test_create_kubernetes_deployment_invalid_service_type_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments",
            json={"name": "demo-web", "image": "nginx:latest", "service_type": "Invalid"},
        )

    assert response.status_code == 422


def test_scale_kubernetes_deployment_invalid_replicas_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments/demo-web/scale",
            json={"replicas": -1},
        )

    assert response.status_code == 422

    with TestClient(app) as client:
        response = client.post(
            "/infrastructure/kubernetes/namespaces/cloudheal-test/deployments/demo-web/scale",
            json={"replicas": 21},
        )

    assert response.status_code == 422


def test_delete_kubernetes_deployment_invalid_namespace_returns_400():
    with TestClient(app) as client:
        response = client.delete(
            "/infrastructure/kubernetes/namespaces/Invalid%20Name/deployments/demo-web"
        )

    assert response.status_code == 400


def test_create_kubernetes_deployment_invalid_namespace_returns_400():
    with patch("cloudheal_control_plane.api.ensure_k8s_namespace") as mock_namespace:
        mock_namespace.side_effect = ValueError("namespace is not a valid Kubernetes name")
        with TestClient(app) as client:
            response = client.post(
                "/infrastructure/kubernetes/namespaces/Invalid%20Name/deployments",
                json={"name": "demo-web", "image": "nginx:latest"},
            )

    assert response.status_code == 400

def test_kubernetes_discovery_endpoint_returns_payload():
    expected = {"status": "ok", "connected": True, "nodes": []}
    with patch("cloudheal_control_plane.api.discover_kubernetes_cluster", return_value=expected):
        with TestClient(app) as client:
            response = client.get("/infrastructure/kubernetes/discovery")
    assert response.status_code == 200
    assert response.json() == expected


def test_kubernetes_discovery_auth_failure_returns_401():
    from cloudheal_control_plane.infrastructure.kubernetes_discovery import (
        KubernetesAuthenticationError,
    )

    with patch("cloudheal_control_plane.api.discover_kubernetes_cluster",
               side_effect=KubernetesAuthenticationError("bad creds")):
        with TestClient(app) as client:
            response = client.get("/infrastructure/kubernetes/discovery")
    assert response.status_code == 401