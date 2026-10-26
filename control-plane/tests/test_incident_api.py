from unittest.mock import patch

from fastapi.testclient import TestClient
from kubernetes import config
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.api import app


BASE_PATH = (
    "/incidents/kubernetes/namespaces/"
    "cloudheal-test/deployments/nginx-test"
)


def test_healthy_deployment_returns_no_incident():
    expected = {
        "incident_detected": False,
        "classification": "HEALTHY",
        "namespace": "cloudheal-test",
        "deployment": "nginx-test",
        "observed_at": "2026-10-25T10:00:00+00:00",
        "evidence": {
            "desired_replicas": 1,
            "ready_replicas": 1,
            "available_replicas": 1,
            "unhealthy_pods": [],
            "reasons": [],
        },
    }

    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        return_value=expected,
    ) as mock_detector:
        with TestClient(app) as client:
            response = client.get(BASE_PATH)

    assert response.status_code == 200
    assert response.json() == expected

    mock_detector.assert_called_once_with(
        namespace="cloudheal-test",
        deployment_name="nginx-test",
    )


def test_missing_deployment_returns_404():
    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        side_effect=ApiException(status=404, reason="Not Found"),
    ):
        with TestClient(app) as client:
            response = client.get(BASE_PATH)

    assert response.status_code == 404
    assert response.json()["detail"] == "Kubernetes Deployment not found"


def test_kubernetes_api_failure_returns_502():
    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        side_effect=ApiException(status=500, reason="Internal Server Error"),
    ):
        with TestClient(app) as client:
            response = client.get(BASE_PATH)

    assert response.status_code == 502
    assert response.json()["detail"] == "Kubernetes API request failed"


def test_missing_kubeconfig_returns_503():
    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        side_effect=config.ConfigException("Kubeconfig unavailable"),
    ):
        with TestClient(app) as client:
            response = client.get(BASE_PATH)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Kubernetes configuration is unavailable"
    )

def test_recovery_endpoint_rejects_healthy_deployment():
    healthy_detection = {
        "incident_detected": False,
        "classification": "HEALTHY",
        "namespace": "cloudheal-test",
        "deployment": "nginx-test",
    }

    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        return_value=healthy_detection,
    ), patch(
        "cloudheal_control_plane.api.execute_recovery"
    ) as mock_executor:
        with TestClient(app) as client:
            response = client.post(
                BASE_PATH + "/recover"
            )

    assert response.status_code == 409
    mock_executor.assert_not_called()


def test_recovery_endpoint_executes_for_degraded_deployment():
    degraded_detection = {
        "incident_detected": True,
        "classification": "DEPLOYMENT_DEGRADED",
        "namespace": "cloudheal-test",
        "deployment": "nginx-test",
        "incident": {
            "incident_id": 123,
            "status": "OPEN",
            "classification": "DEPLOYMENT_DEGRADED",
            "evidence": {"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
        },
    }
    recovery_result = {
        "accepted": True,
        "stage": "VERIFICATION",
        "status": "SUCCEEDED",
        "reason_code": "DEPLOYMENT_HEALTHY_AFTER_RESTART",
    }

    with patch(
        "cloudheal_control_plane.api.detect_deployment_incident",
        return_value=degraded_detection,
    ), patch(
        "cloudheal_control_plane.api.execute_recovery",
        return_value=recovery_result,
    ) as mock_executor:
        with TestClient(app) as client:
            response = client.post(
                BASE_PATH + "/recover"
            )

    assert response.status_code == 200
    assert response.json() == recovery_result
    mock_executor.assert_called_once_with(degraded_detection)
