from unittest.mock import patch

from cloudheal_control_plane.infrastructure.incident_detector import (
    detect_deployment_incident,
)


def make_deployment(
    desired=1,
    ready=1,
    available=1,
    pods=None,
):
    return {
        "namespace": "cloudheal-test",
        "deployment": "nginx-test",
        "desired_replicas": desired,
        "ready_replicas": ready,
        "available_replicas": available,
        "conditions": [],
        "pods": pods or [],
    }


def test_healthy_deployment_does_not_create_incident():
    deployment = make_deployment(
        pods=[
            {
                "name": "nginx-pod",
                "phase": "Running",
                "ready": True,
                "containers": [],
            }
        ]
    )

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "get_deployment_status",
            return_value=deployment,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "observe_incident"
        ) as mock_observe,
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "resolve_incident",
            return_value=None,
        ) as mock_resolve,
    ):
        result = detect_deployment_incident(
            namespace="cloudheal-test",
            deployment_name="nginx-test",
        )

    assert result["incident_detected"] is False
    assert result["classification"] == "HEALTHY"
    assert result["evidence"]["ready_replicas"] == 1
    assert result["incident"] is None
    mock_observe.assert_not_called()
    mock_resolve.assert_called_once()


def test_degraded_replicas_record_incident():
    deployment = make_deployment(
        desired=3,
        ready=1,
        available=1,
    )

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "get_deployment_status",
            return_value=deployment,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "observe_incident",
            return_value={
                "incident_id": 1,
                "resource_key": (
                    "kubernetes:deployment:cloudheal-test:nginx-test"
                ),
                "status": "OPEN",
                "classification": "DEPLOYMENT_DEGRADED",
                "first_seen": "2026-10-25T10:00:00+00:00",
                "last_seen": "2026-10-25T10:00:00+00:00",
                "evidence": {},
                "created": True,
            },
        ) as mock_observe_incident,
    ):
        result = detect_deployment_incident(
            namespace="cloudheal-test",
            deployment_name="nginx-test",
        )

    assert result["incident_detected"] is True
    assert result["classification"] == "DEPLOYMENT_DEGRADED"
    assert "READY_REPLICAS_BELOW_DESIRED" in result["evidence"]["reasons"]
    assert "AVAILABLE_REPLICAS_BELOW_DESIRED" in result["evidence"]["reasons"]

    mock_observe_incident.assert_called_once()
    assert result["incident"]["incident_id"] == 1
    assert result["incident"]["created"] is True

def test_unready_pod_is_included_in_incident_evidence():
    deployment = make_deployment(
        pods=[
            {
                "name": "nginx-pod",
                "phase": "Running",
                "ready": False,
                "containers": [
                    {
                        "name": "nginx",
                        "ready": False,
                        "restart_count": 4,
                        "state": "running",
                    }
                ],
            }
        ]
    )

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "get_deployment_status",
            return_value=deployment,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "observe_incident",
            return_value={
                "incident_id": 2,
                "status": "OPEN",
                "created": True,
            },
        ),
    ):
        result = detect_deployment_incident(
            namespace="cloudheal-test",
            deployment_name="nginx-test",
        )

    assert result["incident_detected"] is True
    assert "UNHEALTHY_PODS_PRESENT" in result["evidence"]["reasons"]
    assert result["evidence"]["unhealthy_pods"][0]["name"] == "nginx-pod"
    assert (
        result["evidence"]["unhealthy_pods"][0]["containers"][0]["restart_count"]
        == 4
    )


def test_zero_desired_replicas_is_healthy_when_no_pods_exist():
    deployment = make_deployment(
        desired=0,
        ready=0,
        available=0,
        pods=[],
    )

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "get_deployment_status",
            return_value=deployment,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "observe_incident"
        ) as mock_observe,
        patch(
            "cloudheal_control_plane.infrastructure.incident_detector."
            "resolve_incident",
            return_value=None,
        ) as mock_resolve,
    ):
        result = detect_deployment_incident(
            namespace="cloudheal-test",
            deployment_name="nginx-test",
        )

    assert result["incident_detected"] is False
    assert result["classification"] == "HEALTHY"
    mock_observe.assert_not_called()
    mock_resolve.assert_called_once()