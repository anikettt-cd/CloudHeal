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