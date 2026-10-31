import pytest

from cloudheal_control_plane.self_healing.recovery_policy import (
    evaluate_recovery_action,
)


@pytest.fixture
def degraded_incident():
    return {
        "incident_id": 1,
        "status": "OPEN",
        "classification": "DEPLOYMENT_DEGRADED",
        "evidence": {
            "desired_replicas": 3,
            "ready_replicas": 1,
            "available_replicas": 1,
            "reasons": ["READY_REPLICAS_BELOW_DESIRED"],
        },
    }


def test_allows_supported_action_for_degraded_incident(
    degraded_incident,
):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is True
    assert result["reason_code"] == "POLICY_APPROVED"


def test_blocks_unsupported_action(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="DELETE_CLUSTER",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "UNSUPPORTED_ACTION"


def test_blocks_duplicate_recovery(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        recovery_in_progress=True,
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "RECOVERY_ALREADY_IN_PROGRESS"


def test_blocks_missing_incident():
    result = evaluate_recovery_action(
        incident=None,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "INVALID_INCIDENT"


def test_blocks_resolved_incident(degraded_incident):
    degraded_incident["status"] = "RESOLVED"

    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "INCIDENT_NOT_OPEN"


def test_blocks_unsupported_classification(degraded_incident):
    degraded_incident["classification"] = "UNKNOWN_FAILURE"

    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "UNSUPPORTED_CLASSIFICATION"


def test_blocks_missing_evidence(degraded_incident):
    degraded_incident["evidence"]["reasons"] = []

    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "MISSING_EVIDENCE"


def test_blocks_insufficient_capacity(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        capacity_available=False,
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "CAPACITY_INSUFFICIENT"


def test_blocks_insufficient_capacity(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        capacity_available=False,
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "CAPACITY_INSUFFICIENT"


def test_blocks_unavailable_capacity_when_required(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        capacity_available=None,
        capacity_required=True,
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "CAPACITY_UNKNOWN"


def test_allows_unavailable_capacity_when_not_required(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        capacity_available=None,
        capacity_required=False,
    )

    assert result["allowed"] is True


def test_blocks_kubernetes_recovery_in_progress(degraded_incident):
    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
        kubernetes_recovery_in_progress=True,
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "KUBERNETES_RECOVERY_IN_PROGRESS"


def test_blocks_zero_desired_replicas(degraded_incident):
    degraded_incident["evidence"]["desired_replicas"] = 0

    result = evaluate_recovery_action(
        incident=degraded_incident,
        action="RESTART_DEPLOYMENT",
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "CAPACITY_INSUFFICIENT"
