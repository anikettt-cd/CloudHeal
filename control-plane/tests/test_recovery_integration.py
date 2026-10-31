from cloudheal_control_plane.database import (
    claim_recovery_attempt,
    finish_recovery_attempt,
    observe_incident,
)


def test_automatic_recovery_claim_persists_across_restart():
    incident = observe_incident(
        resource_key="kubernetes:deployment:default:test-api",
        classification="DEPLOYMENT_DEGRADED",
        evidence={"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
        observed_at="2026-10-29T00:00:00+00:00",
    )

    first = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "automatic"},
    )
    assert first["claimed"] is True

    # A second claim while the first is still active is blocked, simulating a
    # control-plane restart where the persisted attempt remains visible.
    second = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "automatic"},
    )
    assert second["claimed"] is False
    assert second["reason_code"] == "RECOVERY_ALREADY_ACTIVE"


def test_cooldown_blocks_second_recovery_attempt():
    incident = observe_incident(
        resource_key="kubernetes:deployment:default:cooldown-api",
        classification="DEPLOYMENT_DEGRADED",
        evidence={"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
        observed_at="2026-10-29T00:00:00+00:00",
    )

    first = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "automatic"},
        cooldown_seconds=100,
    )
    assert first["claimed"] is True

    finish_recovery_attempt(
        attempt_id=first["attempt_id"],
        status="SUCCEEDED",
        reason_code="DEPLOYMENT_HEALTHY_AFTER_RESTART",
    )

    second = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "automatic"},
        cooldown_seconds=100,
    )
    assert second["claimed"] is False
    assert second["reason_code"] == "RECOVERY_COOLDOWN_ACTIVE"
