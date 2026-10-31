from cloudheal_control_plane.database import claim_recovery_attempt, observe_incident, finish_recovery_attempt
from datetime import UTC, datetime


def make_incident():
    return observe_incident(
        resource_key="kubernetes:deployment:default:api",
        classification="DEPLOYMENT_DEGRADED",
        evidence={"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
        observed_at=datetime.now(UTC).isoformat(),
    )


def test_recovery_attempt_limit_is_enforced():
    incident = make_incident()
    first = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "manual"},
        max_attempts=1,
    )
    assert first["claimed"] is True
    finish_recovery_attempt(
        attempt_id=first["attempt_id"],
        status="FAILED",
        reason_code="RECOVERY_FAILED",
    )
    second = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "manual"},
        max_attempts=1,
    )
    assert second["claimed"] is False
    assert second["reason_code"] == "RECOVERY_ATTEMPT_LIMIT_REACHED"


def test_recovery_cooldown_is_enforced():
    incident = make_incident()
    first = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "manual"},
        cooldown_seconds=3600,
        max_attempts=10,
    )
    assert first["claimed"] is True
    finish_recovery_attempt(
        attempt_id=first["attempt_id"],
        status="FAILED",
        reason_code="RECOVERY_FAILED",
    )
    second = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details={"trigger": "manual"},
        cooldown_seconds=3600,
        max_attempts=10,
    )
    assert second["claimed"] is False
    assert second["reason_code"] == "RECOVERY_COOLDOWN_ACTIVE"

import threading

def test_concurrent_recovery_claims_are_serialized():
    incident = make_incident()
    results = []

    def worker():
        results.append(claim_recovery_attempt(
            incident_id=incident["incident_id"],
            action="RESTART_DEPLOYMENT",
            details={"trigger": "manual"},
        ))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    claimed = [r for r in results if r["claimed"]]
    rejected = [r for r in results if not r["claimed"]]

    assert len(claimed) == 1
    assert len(rejected) == 1
    assert rejected[0]["reason_code"] == "RECOVERY_ALREADY_ACTIVE"
