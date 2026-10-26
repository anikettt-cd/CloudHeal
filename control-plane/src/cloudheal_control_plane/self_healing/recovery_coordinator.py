from typing import Any, Callable

from cloudheal_control_plane.database import claim_recovery_attempt
from cloudheal_control_plane.self_healing.recovery_policy import (
    evaluate_recovery_action,
)


def coordinate_recovery(
    detection: dict[str, Any],
    action: str = "RESTART_DEPLOYMENT",
    trigger: str = "manual",
    claim_attempt_fn: Callable = claim_recovery_attempt,
    evaluate_policy_fn: Callable = evaluate_recovery_action,
) -> dict[str, Any]:
    """Validate and claim a recovery attempt without executing remediation."""

    if not isinstance(detection, dict):
        return {
            "accepted": False,
            "stage": "VALIDATION",
            "reason_code": "INVALID_DETECTION",
        }

    incident = detection.get("incident")

    if not isinstance(incident, dict):
        return {
            "accepted": False,
            "stage": "VALIDATION",
            "reason_code": "INVALID_INCIDENT",
        }

    namespace = detection.get("namespace")
    deployment_name = detection.get("deployment")

    if (
        not isinstance(namespace, str)
        or not namespace.strip()
        or not isinstance(deployment_name, str)
        or not deployment_name.strip()
    ):
        return {
            "accepted": False,
            "stage": "VALIDATION",
            "reason_code": "INVALID_TARGET",
        }

    policy = evaluate_policy_fn(
        incident=incident,
        action=action,
    )

    if not policy["allowed"]:
        return {
            "accepted": False,
            "stage": "POLICY",
            "reason_code": policy["reason_code"],
            "reason": policy["reason"],
        }

    incident_id = incident.get("incident_id")

    if not isinstance(incident_id, int) or isinstance(incident_id, bool):
        return {
            "accepted": False,
            "stage": "VALIDATION",
            "reason_code": "INVALID_INCIDENT_ID",
        }

    claim = claim_attempt_fn(
    incident_id=incident_id,
    action=action,
        details={
            "namespace": namespace,
            "deployment": deployment_name,
            "resource_key": (
                f"kubernetes:deployment:{namespace}:{deployment_name}"
            ),
            "trigger": trigger,
        },
    )

    if not claim["claimed"]:
        return {
            "accepted": False,
            "stage": "CLAIM",
            "reason_code": claim["reason_code"],
            "attempt_id": claim.get("attempt_id"),
        }

    return {
        "accepted": True,
        "stage": "CLAIMED",
        "reason_code": "RECOVERY_ATTEMPT_CLAIMED",
        "attempt_id": claim["attempt_id"],
        "incident_id": incident_id,
        "action": action,
        "status": "IN_PROGRESS",
        "execution_started": False,
    }
