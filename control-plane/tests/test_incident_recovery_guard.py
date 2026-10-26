import json
from datetime import UTC, datetime

from cloudheal_control_plane.database import (
    claim_recovery_attempt,
    get_connection,
    observe_incident,
    resolve_incident,
    finish_recovery_attempt,
)


def create_open_incident():
    return observe_incident(
        resource_key="kubernetes:deployment:default:api",
        classification="DEPLOYMENT_DEGRADED",
        evidence={
            "reasons": ["READY_REPLICAS_BELOW_DESIRED"],
            "desired_replicas": 2,
            "ready_replicas": 1,
        },
        observed_at=datetime.now(UTC).isoformat(),
    )


def claim_attempt(incident_id):
    return claim_recovery_attempt(
        incident_id=incident_id,
        action="RESTART_DEPLOYMENT",
        details={
            "namespace": "default",
            "deployment": "api",
        },
    )


def test_in_progress_attempt_blocks_incident_resolution():
    incident = create_open_incident()
    attempt = claim_attempt(incident["incident_id"])

    assert attempt["claimed"] is True

    result = resolve_incident(
        resource_key=incident["resource_key"],
        resolved_at=datetime.now(UTC).isoformat(),
    )

    assert result["status"] == "OPEN"
    assert result["resolution_blocked"] is True
    assert result["reason_code"] == "RECOVERY_OUTCOME_UNRESOLVED"
    assert result["active_attempt_id"] == attempt["attempt_id"]

    with get_connection() as connection:
        row = connection.execute(
            "SELECT status FROM incidents WHERE incident_id = ?",
            (incident["incident_id"],),
        ).fetchone()

    assert row["status"] == "OPEN"


def test_unknown_attempt_blocks_incident_resolution():
    incident = create_open_incident()
    attempt = claim_attempt(incident["incident_id"])

    finish_result = finish_recovery_attempt(
        attempt_id=attempt["attempt_id"],
        status="UNKNOWN",
        reason_code="EXECUTION_OUTCOME_UNCERTAIN",
    )

    assert finish_result["updated"] is True

    result = resolve_incident(
        resource_key=incident["resource_key"],
        resolved_at=datetime.now(UTC).isoformat(),
    )

    assert result["status"] == "OPEN"
    assert result["resolution_blocked"] is True
    assert result["active_attempt_status"] == "UNKNOWN"


def test_failed_attempt_does_not_block_incident_resolution():
    incident = create_open_incident()
    attempt = claim_attempt(incident["incident_id"])

    finish_result = finish_recovery_attempt(
        attempt_id=attempt["attempt_id"],
        status="FAILED",
        reason_code="RECOVERY_FAILED",
    )

    assert finish_result["updated"] is True

    result = resolve_incident(
        resource_key=incident["resource_key"],
        resolved_at=datetime.now(UTC).isoformat(),
    )

    assert result["status"] == "RESOLVED"


def test_repeated_resolution_does_not_duplicate_event():
    incident = create_open_incident()
    resolved_at = datetime.now(UTC).isoformat()

    first = resolve_incident(
        resource_key=incident["resource_key"],
        resolved_at=resolved_at,
    )
    second = resolve_incident(
        resource_key=incident["resource_key"],
        resolved_at=datetime.now(UTC).isoformat(),
    )

    assert first["status"] == "RESOLVED"
    assert second is None

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT details
            FROM events
            WHERE event_type = 'INCIDENT_RESOLVED'
            """
        ).fetchall()

    matching_events = [
        json.loads(row["details"])
        for row in rows
        if json.loads(row["details"])["incident_id"]
        == incident["incident_id"]
    ]

    assert len(matching_events) == 1

def test_failed_automatic_attempt_blocks_another_automatic_attempt():
    incident = create_open_incident()

    details = {
        "namespace": "default",
        "deployment": "api",
        "trigger": "automatic",
    }

    first = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details=details,
    )

    assert first["claimed"] is True

    finish_result = finish_recovery_attempt(
        attempt_id=first["attempt_id"],
        status="FAILED",
        reason_code="RECOVERY_FAILED",
    )

    assert finish_result["updated"] is True

    second = claim_recovery_attempt(
        incident_id=incident["incident_id"],
        action="RESTART_DEPLOYMENT",
        details=details,
    )

    assert second["claimed"] is False
    assert second["reason_code"] == "AUTO_RECOVERY_ALREADY_ATTEMPTED"