from unittest.mock import Mock , patch

from cloudheal_control_plane.self_healing.recovery_coordinator import (
    coordinate_recovery,
)


def make_detection():
    return {
        "namespace": "default",
        "deployment": "test-api",
        "incident": {
            "incident_id": 7,
            "status": "OPEN",
            "classification": "DEPLOYMENT_DEGRADED",
            "evidence": {
                "reasons": ["READY_REPLICAS_BELOW_DESIRED"],
            },
        },
    }


def test_claims_recovery_without_executing_it():
    claim = Mock(
        return_value={
            "claimed": True,
            "attempt_id": 12,
        }
    )

    result = coordinate_recovery(
        make_detection(),
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is True
    assert result["attempt_id"] == 12
    assert result["execution_started"] is False

    claim.assert_called_once_with(
        incident_id=7,
        action="RESTART_DEPLOYMENT",
        details={
            "namespace": "default",
            "deployment": "test-api",
            "resource_key": "kubernetes:deployment:default:test-api",
            "trigger": "manual",
        },
    )


def test_rejects_invalid_detection_without_claiming():
    claim = Mock()

    result = coordinate_recovery(
        {},
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is False
    assert result["reason_code"] == "INVALID_INCIDENT"
    claim.assert_not_called()


def test_rejects_missing_target_without_claiming():
    detection = make_detection()
    detection["namespace"] = ""
    claim = Mock()

    result = coordinate_recovery(
        detection,
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is False
    assert result["reason_code"] == "INVALID_TARGET"
    claim.assert_not_called()


def test_policy_block_prevents_claim():
    claim = Mock()

    result = coordinate_recovery(
        make_detection(),
        action="DELETE_CLUSTER",
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is False
    assert result["stage"] == "POLICY"
    assert result["reason_code"] == "UNSUPPORTED_ACTION"
    claim.assert_not_called()


def test_duplicate_claim_is_rejected():
    claim = Mock(
        return_value={
            "claimed": False,
            "reason_code": "RECOVERY_ALREADY_ACTIVE",
            "attempt_id": 12,
        }
    )

    result = coordinate_recovery(
        make_detection(),
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is False
    assert result["stage"] == "CLAIM"
    assert result["reason_code"] == "RECOVERY_ALREADY_ACTIVE"
    assert result["attempt_id"] == 12


def test_invalid_incident_id_prevents_claim():
    detection = make_detection()
    detection["incident"]["incident_id"] = None
    claim = Mock()

    result = coordinate_recovery(
        detection,
        claim_attempt_fn=claim,
    )

    assert result["accepted"] is False
    assert result["reason_code"] == "INVALID_INCIDENT_ID"
    claim.assert_not_called()
